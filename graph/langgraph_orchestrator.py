"""
LangGraph Multi-Agent Orchestrator — WindSense-AI
Coordinates all 4 agents in a directed graph pipeline.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, TypedDict
from loguru import logger

from langgraph.graph import StateGraph, END

from graph.agent_communication import (AgentState, SensorReading,
                                        AnomalyMessage, RULMessage,
                                        MaintenanceDecision)
from graph.conflict_resolver import resolve

MODELS_DIR = Path("outputs/models")
PROCESSED  = Path("data/processed")


# ── Load dataset meta ─────────────────────────────────────────────────────────
def _load_meta() -> Dict:
    meta_path = PROCESSED / "dataset_meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {"useful_sensors": [f"sensor_{i}" for i in range(1,15)],
            "window_size": 30, "n_features": 14}


META = _load_meta()


# ══════════════════════════════════════════════════════════════════════════════
# NODE 1 — Agent 1: Health Monitor
# ══════════════════════════════════════════════════════════════════════════════

def node_health_monitor(state: Dict) -> Dict:
    """Detect anomalies for all turbine readings."""
    logger.info("▶ Agent 1: Health Monitor running...")

    from agents.agent1_health_monitor.isolation_forest import predict as if_predict
    from agents.agent1_health_monitor.anomaly_localizer import localize

    readings   = state.get("readings", [])
    anomalies  = []
    winner_path = MODELS_DIR / "agent1_winner.json"

    # Choose model
    use_lstm = False
    if winner_path.exists():
        with open(winner_path) as f:
            use_lstm = json.load(f).get("winner") == "LSTM Autoencoder"

    for r in readings:
        try:
            # Build flat feature vector from reading dict
            sensor_vals = [r.get(s, 0.0) for s in META["useful_sensors"]]
            x_flat      = np.array(sensor_vals + [0.0, 0.0, 0.0, 0.0],
                                    dtype=np.float32)

            if use_lstm:
                from agents.agent1_health_monitor.lstm_autoencoder import predict as ae_predict
                # Build dummy sequence — repeat flat vector for window
                x_seq = np.tile(x_flat[:META["n_features"]],
                                 (META["window_size"], 1))[np.newaxis, ...]
                result = ae_predict(x_seq)
                flag   = int(result["anomaly_flags"][0])
                score  = float(result["anomaly_scores"][0])
            else:
                result = if_predict(x_flat.reshape(1, -1))
                flag   = int(result["anomaly_flags"][0])
                score  = float(result["anomaly_scores"][0])

            # Localize if anomalous
            primary_cause = "none"
            top_sensors   = []
            if flag == 1:
                x_seq_loc = np.tile(x_flat[:META["n_features"]],
                                     (META["window_size"], 1))[np.newaxis, ...]
                loc = localize(x_seq_loc, top_k=3)[0]
                primary_cause = loc["primary_cause"]
                top_sensors   = loc["top_sensors"]

            anomalies.append({
                "turbine_id"   : r["turbine_id"],
                "anomaly_flag" : flag,
                "anomaly_score": round(score, 4),
                "primary_cause": primary_cause,
                "top_sensors"  : top_sensors,
            })

        except Exception as e:
            logger.error(f"Agent 1 error on {r.get('turbine_id')}: {e}")
            anomalies.append({
                "turbine_id": r.get("turbine_id","UNKNOWN"),
                "anomaly_flag": 0, "anomaly_score": 0.0,
                "primary_cause": "error", "top_sensors": [],
            })

    state["anomalies"] = anomalies
    logger.info(f"Agent 1 done | {sum(a['anomaly_flag'] for a in anomalies)} anomalies detected")
    return state


# ══════════════════════════════════════════════════════════════════════════════
# NODE 2 — Agent 2: Failure Predictor
# ══════════════════════════════════════════════════════════════════════════════

def node_failure_predictor(state: Dict) -> Dict:
    """Predict RUL for all turbines."""
    logger.info("▶ Agent 2: Failure Predictor running...")

    from agents.agent2_failure_predictor.uncertainty_estimator import predict_with_uncertainty

    readings    = state.get("readings", [])
    rul_results = []

    for r in readings:
        try:
            sensor_vals = [r.get(s, 0.0) for s in META["useful_sensors"]]
            x_flat      = np.array(sensor_vals + [0.0, 0.0, 0.0, 0.0],
                                    dtype=np.float32).reshape(1, -1)

            result = predict_with_uncertainty(x_flat, alpha=0.1)
            rul_results.append({
                "turbine_id" : r["turbine_id"],
                "rul_hours"  : round(float(result["rul_estimate"][0]), 1),
                "lower_hours": round(float(result["lower_bound"][0]), 1),
                "upper_hours": round(float(result["upper_bound"][0]), 1),
                "coverage"   : result["coverage"],
            })

        except Exception as e:
            logger.error(f"Agent 2 error on {r.get('turbine_id')}: {e}")
            rul_results.append({
                "turbine_id" : r.get("turbine_id","UNKNOWN"),
                "rul_hours"  : 125.0, "lower_hours": 100.0,
                "upper_hours": 125.0, "coverage": "90%",
            })

    state["rul_results"] = rul_results
    logger.info(f"Agent 2 done | Min RUL: "
                f"{min(r['rul_hours'] for r in rul_results):.1f}h")
    return state


# ══════════════════════════════════════════════════════════════════════════════
# NODE 3 — Agent 4: Energy Forecaster (runs before coordinator)
# ══════════════════════════════════════════════════════════════════════════════

def node_energy_forecaster(state: Dict) -> Dict:
    """Generate 72h energy forecast."""
    logger.info("▶ Agent 4: Energy Forecaster running...")

    try:
        from agents.agent4_energy_forecaster.prophet_forecast import predict_next_72h
        forecast = predict_next_72h()
        state["forecast_72h"] = forecast["yhat"].tolist()
        logger.info(f"Agent 4 done | Avg forecast: "
                    f"{np.mean(state['forecast_72h']):.0f} kW")
    except Exception as e:
        logger.warning(f"Prophet forecast failed ({e}) — using LSTM fallback")
        try:
            from agents.agent4_energy_forecaster.lstm_forecast import predict_next_72h as lstm_72h
            state["forecast_72h"] = lstm_72h().tolist()
        except Exception as e2:
            logger.error(f"LSTM forecast also failed: {e2}")
            state["forecast_72h"] = [1000.0] * 72

    return state


# ══════════════════════════════════════════════════════════════════════════════
# NODE 4 — Agent 3: Maintenance Coordinator
# ══════════════════════════════════════════════════════════════════════════════

def node_maintenance_coordinator(state: Dict) -> Dict:
    """Schedule maintenance using rule-based + RL + conflict resolution."""
    
    logger.info("▶ Agent 3: Maintenance Coordinator running...")

    from agents.agent3_maintenance_coordinator.rule_based_scheduler import (
        schedule
    )

    from agents.agent3_maintenance_coordinator.rl_scheduler import (
        predict as rl_predict,
        state_from_reading,
        MaintenanceEnv
    )

    from agents.agent3_maintenance_coordinator.crew_optimizer import (
        assign_crews
    )

    from agents.agent3_maintenance_coordinator.load_adjuster import (
        adjust
    )

    from agents.agent4_energy_forecaster.revenue_loss_estimator import (
        estimate
    )

    anomalies   = state.get("anomalies", [])
    rul_results = state.get("rul_results", [])
    readings    = state.get("readings", [])

    forecast = np.array(
        state.get("forecast_72h", [1000.0] * 72)
    )

    decisions = []

    # ─────────────────────────────────────────────────────────────
    # Build lookup maps
    # ─────────────────────────────────────────────────────────────
    anom_map = {
        a["turbine_id"]: a
        for a in anomalies
    }

    rul_map = {
        r["turbine_id"]: r
        for r in rul_results
    }

    read_map = {
        r["turbine_id"]: r
        for r in readings
    }

    raw_decisions = []

    # ─────────────────────────────────────────────────────────────
    # Process each turbine
    # ─────────────────────────────────────────────────────────────
    for turbine_id, anom in anom_map.items():

        rul = rul_map.get(
            turbine_id,
            {
                "rul_hours": 125,
                "lower_hours": 100,
                "upper_hours": 125
            }
        )

        read = read_map.get(turbine_id, {})

        # =========================================================
        # Rule-based decision
        # =========================================================
        rule_dec = schedule(
            anom,
            rul,
            forecast.tolist()
        )

        # =========================================================
        # Ensure duration_hours exists
        # =========================================================
        try:
            from datetime import datetime

            start_dt = datetime.fromisoformat(
                rule_dec["scheduled_start"]
            )

            end_dt = datetime.fromisoformat(
                rule_dec["scheduled_end"]
            )

            duration_hours = max(
                4.0,
                (end_dt - start_dt).total_seconds() / 3600
            )

            rule_dec["duration_hours"] = round(
                duration_hours,
                1
            )

        except Exception as e:

            logger.warning(
                f"Duration calculation failed for "
                f"{turbine_id}: {e}"
            )

            rule_dec["duration_hours"] = 6.0

        # =========================================================
        # RL decision
        # =========================================================
        try:

            rl_state = state_from_reading(
                {
                    **read,
                    **anom,
                    **rul
                }
            )

            rl_dec = rl_predict(rl_state)

        except Exception as e:

            logger.warning(
                f"RL scheduler failed for "
                f"{turbine_id}: {e}"
            )

            rl_dec = {
                "action": rule_dec["action"]
            }

        # =========================================================
        # Conflict resolution
        # =========================================================
        resolved = resolve(
            anom,
            rul,
            rl_dec,
            rule_dec
        )

        rule_dec["action"] = resolved["final_action"]

        rule_dec["chosen_by"] = resolved.get(
            "chosen_by",
            "RULE_BASED"
        )

        rule_dec["conflict_reasoning"] = resolved.get(
            "reason",
            "No reasoning available"
        )

        # =========================================================
        # Revenue loss estimation
        # =========================================================
        try:

            rev = estimate(
                rule_dec,
                forecast
            )

            rule_dec["revenue_loss_usd"] = (
                rev["revenue_loss_usd"]
            )

            rule_dec["net_saving_usd"] = (
                rev["net_saving_usd"]
            )

            rule_dec["lost_generation_kwh"] = (
                rev["lost_generation_kwh"]
            )

            rule_dec["roi_justified"] = (
                rev.get("roi_justified", True)
            )

        except Exception as e:

            logger.error(
                f"Revenue estimation failed for "
                f"{turbine_id}: {e}"
            )

            rule_dec["revenue_loss_usd"] = 0.0
            rule_dec["net_saving_usd"] = 0.0
            rule_dec["lost_generation_kwh"] = 0.0
            rule_dec["roi_justified"] = False

        raw_decisions.append(rule_dec)

    # ─────────────────────────────────────────────────────────────
    # Assign maintenance crews
    # ─────────────────────────────────────────────────────────────
    try:

        assign_crews(raw_decisions)

    except Exception as e:

        logger.warning(
            f"Crew assignment failed: {e}"
        )

    # ─────────────────────────────────────────────────────────────
    # Load adjustment
    # ─────────────────────────────────────────────────────────────
    for dec in raw_decisions:

        try:

            read = read_map.get(
                dec["turbine_id"],
                {}
            )

            setpoint = adjust(
                dec,
                current_power_kw=read.get(
                    "power_kw",
                    1000.0
                )
            )

            dec["load_setpoint"] = setpoint

        except Exception as e:

            logger.warning(
                f"Load adjustment failed for "
                f"{dec.get('turbine_id')}: {e}"
            )

            dec["load_setpoint"] = read.get(
                "power_kw",
                1000.0
            )

        decisions.append(dec)

    # ─────────────────────────────────────────────────────────────
    # Save to graph state
    # ─────────────────────────────────────────────────────────────
    state["decisions"] = decisions

    critical_count = sum(
        1
        for d in decisions
        if d.get("priority") == "CRITICAL"
    )

    logger.info(
        f"Agent 3 done | "
        f"{len(decisions)} decisions made | "
        f"Critical: {critical_count}"
    )

    return state


# ══════════════════════════════════════════════════════════════════════════════
# NODE 5 — LLM Explanation + Work Orders
# ══════════════════════════════════════════════════════════════════════════════

def node_llm_explainer(state: Dict) -> Dict:
    """Generate plain-English explanations and PDF work orders."""
    logger.info("▶ LLM Explainer running...")

    try:
        from llm.explanation_generator import explain_decision
        from agents.agent3_maintenance_coordinator.work_order_generator import generate

        decisions   = state.get("decisions", [])
        anom_map    = {a["turbine_id"]: a for a in state.get("anomalies", [])}
        rul_map     = {r["turbine_id"]: r for r in state.get("rul_results", [])}

        for dec in decisions:
            tid  = dec["turbine_id"]
            anom = anom_map.get(tid, {})
            rul  = rul_map.get(tid, {})

            # LLM explanation
            try:
                explanation = explain_decision(dec, anom, rul)
                dec["llm_explanation"] = explanation
            except Exception as e:
                dec["llm_explanation"] = dec.get("reasoning", "Explanation unavailable.")
                logger.warning(f"LLM failed for {tid}: {e}")

            # Generate PDF work order for HIGH/CRITICAL
            if dec.get("priority") in ["HIGH", "CRITICAL"]:
                try:
                    pdf_path = generate(dec, rul, anom, dec["llm_explanation"])
                    dec["work_order_path"] = str(pdf_path)
                except Exception as e:
                    logger.warning(f"Work order generation failed: {e}")

    except Exception as e:
        logger.error(f"LLM explainer node error: {e}")

    logger.info("LLM Explainer done.")
    return state


# ══════════════════════════════════════════════════════════════════════════════
# NODE 6 — Causal RCA
# ══════════════════════════════════════════════════════════════════════════════

def node_causal_rca(state: Dict) -> Dict:
    """Run causal root cause analysis on anomalous turbines."""
    logger.info("▶ Causal RCA running...")

    anomalies = state.get("anomalies", [])
    flagged   = [a for a in anomalies if a["anomaly_flag"] == 1]

    if not flagged:
        state["causal_report"] = {"message": "No anomalies — causal RCA skipped"}
        return state

    try:
        from llm.causal_rca import analyze
        readings = state.get("readings", [])
        report   = analyze(readings, flagged)
        state["causal_report"] = report
        logger.info(f"Causal RCA done | {len(report.get('causes', []))} root causes identified")
    except Exception as e:
        logger.warning(f"Causal RCA failed: {e}")
        state["causal_report"] = {"error": str(e)}

    return state


# ══════════════════════════════════════════════════════════════════════════════
# LOG + SAVE NODE
# ══════════════════════════════════════════════════════════════════════════════

def node_save_results(state: Dict) -> Dict:
    """Save all agent decisions to CSV + JSON."""
    import pandas as pd
    from pathlib import Path

    out = Path("outputs/decision_logs")
    out.mkdir(exist_ok=True)

    decisions = state.get("decisions", [])
    if decisions:
        df = pd.DataFrame(decisions)
        ts = state.get("run_id", "run")
        df.to_csv(out / f"decisions_{ts}.csv", index=False)

        with open(out / f"full_state_{ts}.json", "w") as f:
            # Serialize — remove non-serializable items
            safe_state = {k: v for k, v in state.items()
                          if k not in ["readings"]}
            json.dump(safe_state, f, indent=2, default=str)

    logger.success(f"Results saved | {len(decisions)} decisions logged")
    return state


# ══════════════════════════════════════════════════════════════════════════════
# BUILD GRAPH
# ══════════════════════════════════════════════════════════════════════════════

def build_graph():
    """Build and compile the LangGraph agent pipeline."""
    graph = StateGraph(dict)

    # Add nodes
    graph.add_node("health_monitor",         node_health_monitor)
    graph.add_node("failure_predictor",      node_failure_predictor)
    graph.add_node("energy_forecaster",      node_energy_forecaster)
    graph.add_node("maintenance_coordinator",node_maintenance_coordinator)
    graph.add_node("llm_explainer",          node_llm_explainer)
    graph.add_node("causal_rca",             node_causal_rca)
    graph.add_node("save_results",           node_save_results)

    # Define edges (execution order)
    graph.set_entry_point("health_monitor")
    graph.add_edge("health_monitor",          "failure_predictor")
    graph.add_edge("failure_predictor",       "energy_forecaster")
    graph.add_edge("energy_forecaster",       "maintenance_coordinator")
    graph.add_edge("maintenance_coordinator", "causal_rca")
    graph.add_edge("causal_rca",              "llm_explainer")
    graph.add_edge("llm_explainer",           "save_results")
    graph.add_edge("save_results",             END)

    return graph.compile()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(readings: List[Dict]) -> Dict:
    """
    Run full WindSense-AI pipeline for a list of turbine readings.
    
    Args:
        readings: List of sensor reading dicts (one per turbine)
    Returns:
        Final state with all agent outputs
    """
    from datetime import datetime
    app = build_graph()

    initial_state = {
        "readings"     : readings,
        "anomalies"    : [],
        "rul_results"  : [],
        "decisions"    : [],
        "forecast_72h" : [],
        "causal_report": {},
        "errors"       : [],
        "run_id"       : datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
    }

    logger.info(f"🚀 Pipeline started | {len(readings)} turbines")
    final_state = app.invoke(initial_state)
    logger.success("✅ Pipeline complete")
    return final_state


if __name__ == "__main__":
    # Generate synthetic readings for testing
    import random

    test_readings = []
    for i in range(1, 6):
        test_readings.append({
            "turbine_id"    : f"WT-00{i}",
            "timestamp"     : "2024-06-01T06:00:00",
            "wind_speed_ms" : random.uniform(5, 12),
            "power_kw"      : random.uniform(500, 1800),
            "vibration_mms" : random.uniform(1.5, 8.0),
            "gearbox_temp_c": random.uniform(45, 90),
            "bearing_wear"  : random.uniform(0.0, 0.9),
            "oil_quality"   : random.uniform(0.3, 1.0),
            "health_score"  : random.uniform(0.2, 1.0),
            "cmapss_rul"    : random.uniform(10, 125),
            **{f"sensor_{j}": random.uniform(0, 1) for j in range(1, 15)},
        })

    final = run_pipeline(test_readings)

    print("\n=== PIPELINE RESULTS ===")
    for dec in final.get("decisions", []):
        print(f"{dec['turbine_id']} | {dec.get('priority','?'):8s} | "
              f"RUL: {dec.get('rul_hours','?')} | "
              f"Action: {dec.get('action','?')}")