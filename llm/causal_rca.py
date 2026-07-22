"""
Causal Root Cause Analysis using DoWhy.
Identifies causal relationships between sensors and failures.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict
from loguru import logger

PROCESSED  = Path("data/processed")
REPORTS    = Path("outputs/reports")


def build_causal_graph() -> str:
    """
    Define causal graph as GML string.
    Domain knowledge: wind → RPM → vibration → bearing → gearbox temp → failure
    """
    return """
    graph [
        directed 1
        node [ id 0 label "wind_speed" ]
        node [ id 1 label "rotor_rpm" ]
        node [ id 2 label "generator_rpm" ]
        node [ id 3 label "vibration" ]
        node [ id 4 label "bearing_wear" ]
        node [ id 5 label "gearbox_temp" ]
        node [ id 6 label "oil_quality" ]
        node [ id 7 label "anomaly" ]
        edge [ source 0 target 1 ]
        edge [ source 1 target 2 ]
        edge [ source 1 target 3 ]
        edge [ source 4 target 3 ]
        edge [ source 4 target 5 ]
        edge [ source 6 target 5 ]
        edge [ source 3 target 7 ]
        edge [ source 5 target 7 ]
        edge [ source 4 target 7 ]
    ]
    """


def _readings_to_dataframe(readings: List[Dict]) -> pd.DataFrame:
    """Convert list of sensor readings to DataFrame for DoWhy."""
    rows = []
    for r in readings:
        rows.append({
            "wind_speed"   : r.get("wind_speed_ms", 8.0),
            "rotor_rpm"    : r.get("rotor_rpm", 12.0),
            "generator_rpm": r.get("generator_rpm", 1000.0),
            "vibration"    : r.get("vibration_mms", 2.0),
            "bearing_wear" : r.get("bearing_wear", 0.1),
            "gearbox_temp" : r.get("gearbox_temp_c", 55.0),
            "oil_quality"  : r.get("oil_quality", 0.9),
            "anomaly"      : r.get("cmapss_anomaly", 0),
        })
    return pd.DataFrame(rows)


def analyze(readings: List[Dict], flagged_anomalies: List[Dict]) -> Dict:
    """
    Run causal RCA using DoWhy.
    Identifies root causes of detected anomalies.
    """
    try:
        import dowhy
        from dowhy import CausalModel

        df = _readings_to_dataframe(readings)
        if len(df) < 10:
            return _statistical_fallback(df, flagged_anomalies)

        causal_graph = build_causal_graph()

        model = CausalModel(
            data=df,
            treatment="bearing_wear",
            outcome="anomaly",
            graph=causal_graph,
        )

        identified   = model.identify_effect(proceed_when_unidentifiable=True)
        estimate     = model.estimate_effect(
            identified,
            method_name="backdoor.linear_regression",
        )

        ate = float(estimate.value)

        # Correlation-based importance for all causes
        causes = _compute_cause_importance(df)

        report = {
            "method"          : "DoWhy causal inference",
            "treatment"       : "bearing_wear",
            "outcome"         : "anomaly",
            "ate"             : round(ate, 6),
            "ate_interpretation": (
                f"A unit increase in bearing wear increases anomaly "
                f"probability by {ate:.4f}"
            ),
            "causes"          : causes,
            "n_samples"       : len(df),
            "flagged_turbines": [a["turbine_id"] for a in flagged_anomalies],
            "llm_summary"     : _llm_rca_summary(causes, ate, flagged_anomalies),
        }

        REPORTS.mkdir(exist_ok=True)
        with open(REPORTS / "causal_rca_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.success(f"Causal RCA complete | ATE={ate:.4f}")
        return report

    except ImportError:
        logger.warning("DoWhy not installed — using statistical fallback")
        df = _readings_to_dataframe(readings)
        return _statistical_fallback(df, flagged_anomalies)
    except Exception as e:
        logger.error(f"Causal RCA error: {e}")
        df = _readings_to_dataframe(readings)
        return _statistical_fallback(df, flagged_anomalies)


def _compute_cause_importance(df: pd.DataFrame) -> List[Dict]:
    """Compute correlation-based causal importance scores."""
    cause_cols = ["bearing_wear", "gearbox_temp", "vibration",
                  "oil_quality", "rotor_rpm"]
    causes = []
    for col in cause_cols:
        if col in df.columns and "anomaly" in df.columns:
            corr = float(df[col].corr(df["anomaly"]))
            causes.append({
                "variable"   : col,
                "correlation": round(abs(corr), 4),
                "direction"  : "positive" if corr > 0 else "negative",
                "importance" : round(abs(corr), 4),
            })
    causes.sort(key=lambda x: -x["importance"])
    return causes


def _statistical_fallback(df: pd.DataFrame,
                           flagged_anomalies: List[Dict]) -> Dict:
    """Fallback when DoWhy unavailable — correlation-based RCA."""
    causes = _compute_cause_importance(df)
    return {
        "method"          : "correlation_fallback",
        "causes"          : causes,
        "n_samples"       : len(df),
        "flagged_turbines": [a["turbine_id"] for a in flagged_anomalies],
        "llm_summary"     : _llm_rca_summary(causes, None, flagged_anomalies),
    }


def _llm_rca_summary(causes: List[Dict], ate: float,
                      flagged: List[Dict]) -> str:
    """Get LLM to summarize RCA findings."""
    try:
        from llm.gemini_engine import call
        top_causes = causes[:3]
        prompt = f"""You are an industrial AI system. Summarize this root cause analysis in 2 sentences:
Top causal factors for wind turbine anomalies:
{json.dumps(top_causes, indent=2)}
ATE (causal effect of bearing wear): {ate}
Affected turbines: {[a['turbine_id'] for a in flagged]}

Focus on actionable insight for maintenance engineers."""
        return call(prompt, max_tokens=150)
    except Exception:
        top = causes[0]["variable"] if causes else "unknown"
        return (f"Primary root cause identified: {top}. "
                f"{len(flagged)} turbines affected. "
                f"Recommend immediate inspection of {top}.")


if __name__ == "__main__":
    import random
    readings = [{
        "turbine_id"    : f"WT-00{i}",
        "wind_speed_ms" : random.uniform(5, 12),
        "rotor_rpm"     : random.uniform(8, 18),
        "generator_rpm" : random.uniform(800, 1600),
        "vibration_mms" : random.uniform(1.5, 8.0),
        "bearing_wear"  : random.uniform(0.0, 0.9),
        "gearbox_temp_c": random.uniform(45, 90),
        "oil_quality"   : random.uniform(0.3, 1.0),
        "cmapss_anomaly": random.randint(0, 1),
    } for i in range(1, 20)]

    flagged = [{"turbine_id": "WT-003"}, {"turbine_id": "WT-007"}]
    report  = analyze(readings, flagged)

    print(f"\nMethod: {report['method']}")
    print(f"Top causes:")
    for c in report["causes"][:3]:
        print(f"  {c['variable']}: importance={c['importance']:.4f}")
    print(f"\nSummary: {report['llm_summary']}")