"""Plain-English decision explainer using Ollama directly."""

from typing import Dict
from loguru import logger


PROMPT = """You are an industrial maintenance report generator for wind turbines.
Write a factual 5-sentence maintenance report using this data:

Turbine: {turbine_id}
Anomaly Detected: {anomaly_flag} (score: {anomaly_score})
Primary Fault Sensor: {primary_cause}
RUL Estimate: {rul_hours}h (90% CI: {lower_hours}h - {upper_hours}h)
Priority: {priority}
Action: {action}
Scheduled: {scheduled_start} to {scheduled_end}
Crew: {assigned_crew}
Load: {load_pct}% of rated power
Revenue Loss: ${revenue_loss_usd}
Net Saving: ${net_saving_usd}

Write exactly 5 sentences covering: detection, risk, action, schedule, financial impact."""


def explain_decision(decision: Dict, anomaly: Dict, rul: Dict) -> str:
    prompt = PROMPT.format(
        turbine_id      = decision.get("turbine_id", "Unknown"),
        anomaly_flag    = "YES" if anomaly.get("anomaly_flag") else "NO",
        anomaly_score   = anomaly.get("anomaly_score", 0),
        primary_cause   = anomaly.get("primary_cause", "unknown"),
        rul_hours       = rul.get("rul_hours", "N/A"),
        lower_hours     = rul.get("lower_hours", "N/A"),
        upper_hours     = rul.get("upper_hours", "N/A"),
        priority        = decision.get("priority", "UNKNOWN"),
        action          = decision.get("action", "UNKNOWN"),
        scheduled_start = decision.get("scheduled_start", "TBD")[:19],
        scheduled_end   = decision.get("scheduled_end", "TBD")[:19],
        assigned_crew   = decision.get("assigned_crew", "TBD"),
        load_pct        = decision.get("recommended_load_pct", 100),
        revenue_loss_usd= decision.get("revenue_loss_usd", 0),
        net_saving_usd  = decision.get("net_saving_usd", 0),
    )
    try:
        from llm.gemini_engine import call
        return call(prompt, temperature=0.2, max_tokens=300)
    except Exception as e:
        logger.warning(f"LLM failed — using fallback: {e}")
        return _fallback(decision, anomaly, rul)


def _fallback(decision: Dict, anomaly: Dict, rul: Dict) -> str:
    return (
        f"{decision.get('turbine_id')} anomaly detected "
        f"(score: {anomaly.get('anomaly_score',0):.3f}) on "
        f"{anomaly.get('primary_cause','unknown sensor')}. "
        f"RUL: {rul.get('rul_hours','N/A')}h "
        f"(lower: {rul.get('lower_hours','N/A')}h). "
        f"Priority: {decision.get('priority')}. "
        f"Action: {decision.get('action')}. "
        f"Revenue impact: ${decision.get('revenue_loss_usd',0):,.2f}."
    )


def explain_fleet_summary(decisions: list) -> str:
    critical   = sum(1 for d in decisions if d.get("priority") == "CRITICAL")
    high       = sum(1 for d in decisions if d.get("priority") == "HIGH")
    total_loss = sum(d.get("revenue_loss_usd", 0) for d in decisions)
    prompt = (
        f"Summarize wind farm status in 3 sentences for operations manager: "
        f"{len(decisions)} turbines, {critical} critical, {high} high priority, "
        f"${total_loss:,.2f} total revenue impact."
    )
    try:
        from llm.gemini_engine import call
        return call(prompt, temperature=0.1, max_tokens=150)
    except Exception:
        return (f"{len(decisions)} turbines assessed. "
                f"{critical} critical, {high} high priority. "
                f"Total revenue impact: ${total_loss:,.2f}.")


if __name__ == "__main__":
    decision = {
        "turbine_id": "WT-003", "priority": "HIGH",
        "action": "SCHEDULE_WITHIN_48H",
        "scheduled_start": "2024-06-01T06:00:00",
        "scheduled_end": "2024-06-01T12:00:00",
        "assigned_crew": "CREW_A", "recommended_load_pct": 50,
        "revenue_loss_usd": 1250.50, "net_saving_usd": 43749.50,
    }
    anomaly = {"anomaly_flag": 1, "anomaly_score": 0.82, "primary_cause": "sensor_7"}
    rul     = {"rul_hours": 38.0, "lower_hours": 22.0, "upper_hours": 55.0}
    print(explain_decision(decision, anomaly, rul))