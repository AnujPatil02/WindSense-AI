"""Rule-based Maintenance Scheduler — Agent 3"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from loguru import logger

OUTPUTS = Path("outputs/decision_logs")


def schedule(anomaly_result: Dict, rul_result: Dict,
             wind_forecast: List[float] = None) -> Dict:
    """
    Makes scheduling decision based on anomaly + RUL inputs.
    
    Args:
        anomaly_result: {turbine_id, anomaly_flag, anomaly_score, primary_cause}
        rul_result    : {turbine_id, rul_hours, lower_hours, upper_hours}
        wind_forecast : hourly wind speeds for next 72h (optional)
    
    Returns: maintenance decision dict
    """
    turbine_id   = anomaly_result.get("turbine_id", "UNKNOWN")
    anomaly_flag = int(anomaly_result.get("anomaly_flag", 0))
    anomaly_score= float(anomaly_result.get("anomaly_score", 0.0))
    rul_hours    = float(rul_result.get("rul_hours", 125.0))
    rul_lower    = float(rul_result.get("lower_hours", rul_hours))

    # ── Priority scoring ─────────────────────────────────────────────────
    priority = _compute_priority(anomaly_flag, anomaly_score, rul_lower)

    # In schedule() function, replace window line:
    window = _select_maintenance_window(rul_lower, wind_forecast,
                                     turbine_id=turbine_id)

    # ── Load adjustment ──────────────────────────────────────────────────
    load_pct = _recommend_load(anomaly_score, rul_lower)

    # In schedule() function, replace the decision dict construction:
    decision = {
    "turbine_id"          : turbine_id,
    "timestamp"           : datetime.utcnow().isoformat(),
    "anomaly_flag"        : anomaly_flag,
    "anomaly_score"       : round(anomaly_score, 4),
    "rul_hours"           : round(rul_hours, 1),
    "rul_lower_bound"     : round(rul_lower, 1),
    "priority"            : priority,
    "action"              : _get_action(priority),
    "scheduled_start"     : window["start"],
    "scheduled_end"       : window["end"],
    "wind_speed_window"   : window["avg_wind"],
    "duration_hours"      : window.get("duration_h", 6),    # ← ADD THIS
    "recommended_load_pct": load_pct,
    "primary_cause"       : anomaly_result.get("primary_cause", "unknown"),
    "reasoning"           : _build_reasoning(
        turbine_id, anomaly_flag, anomaly_score,
        rul_hours, rul_lower, priority, load_pct, window
    ),
}

    _log_decision(decision)
    return decision


def _compute_priority(anomaly_flag, anomaly_score, rul_lower) -> str:
    # Use point RUL not lower bound for priority
    if anomaly_flag and anomaly_score > 0.88:    return "CRITICAL"
    if rul_lower < 30 or anomaly_score > 0.75:   return "HIGH"
    if rul_lower < 70 or anomaly_score > 0.55:   return "MEDIUM"
    return "LOW"


def _get_action(priority: str) -> str:
    return {
        "CRITICAL": "IMMEDIATE_SHUTDOWN_AND_REPAIR",
        "HIGH"    : "SCHEDULE_WITHIN_48H",
        "MEDIUM"  : "SCHEDULE_WITHIN_7_DAYS",
        "LOW"     : "MONITOR_AND_LOG",
    }[priority]


def _select_maintenance_window(rul_lower: float,
                                wind_forecast: list = None,
                                turbine_id: str = "") -> dict:
    from datetime import datetime, timedelta
    import hashlib
    now = datetime.utcnow()

    # Duration AND offset strictly by RUL
    if rul_lower < 20:
        offset_h, duration_h = 0.5, 12
    elif rul_lower < 50:
        offset_h, duration_h = 6,   10
    elif rul_lower < 70:
        offset_h, duration_h = 12,   8
    elif rul_lower < 90:
        offset_h, duration_h = 24,   6
    elif rul_lower < 110:
        offset_h, duration_h = 36,   5
    else:
        offset_h, duration_h = 48,   4

    # Small turbine-specific variation
    seed      = int(hashlib.md5(turbine_id.encode()).hexdigest()[:4], 16) % 6
    offset_h += seed * 0.5

    start = now + timedelta(hours=offset_h)
    end   = start + timedelta(hours=duration_h)

    return {
        "start"     : start.isoformat(),
        "end"       : end.isoformat(),
        "avg_wind"  : None,
        "duration_h": duration_h,
    }


def _recommend_load(anomaly_score: float, rul_lower: float) -> int:
    if rul_lower < 20  or anomaly_score > 0.85: return 0
    if rul_lower < 50  or anomaly_score > 0.70: return 30
    if rul_lower < 90  or anomaly_score > 0.55: return 60
    if rul_lower < 110 or anomaly_score > 0.40: return 80
    return 100


def _build_reasoning(turbine_id, anomaly_flag, anomaly_score,
                      rul_hours, rul_lower, priority, load_pct, window) -> str:
    return (
        f"{turbine_id}: Anomaly={'YES' if anomaly_flag else 'NO'} "
        f"(score={anomaly_score:.3f}). "
        f"RUL estimate={rul_hours:.1f}h (lower bound={rul_lower:.1f}h). "
        f"Priority={priority}. "
        f"Maintenance window: {window['start']} — {window['end']}. "
        f"Recommended load: {load_pct}% of rated power."
    )


def _log_decision(decision: Dict):
    OUTPUTS.mkdir(exist_ok=True)
    log_path = OUTPUTS / "rule_based_decisions.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(decision) + "\n")


def schedule_fleet(fleet_results: List[Dict]) -> List[Dict]:
    """Schedule maintenance for multiple turbines, sort by priority."""
    decisions = []
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    for r in fleet_results:
        decision = schedule(r["anomaly"], r["rul"], r.get("wind_forecast"))
        decisions.append(decision)

    decisions.sort(key=lambda x: priority_order.get(x["priority"], 99))

    # Assign crew — max 2 turbines simultaneously
    _assign_crew(decisions)
    return decisions


def _assign_crew(decisions: List[Dict]):
    crew_slots = {}
    for d in decisions:
        start = d["scheduled_start"]
        crew_id = None
        for c in ["CREW_A", "CREW_B"]:
            if c not in crew_slots or crew_slots[c] < start:
                crew_id = c
                crew_slots[c] = d["scheduled_end"]
                break
        d["assigned_crew"] = crew_id or "CREW_PENDING"


if __name__ == "__main__":
    import random
    # Simulate fleet scheduling
    fleet = []
    for i in range(1, 6):
        fleet.append({
            "anomaly": {
                "turbine_id"   : f"WT-00{i}",
                "anomaly_flag" : random.randint(0, 1),
                "anomaly_score": random.uniform(0.3, 0.95),
                "primary_cause": "sensor_7",
            },
            "rul": {
                "turbine_id"  : f"WT-00{i}",
                "rul_hours"   : random.uniform(10, 120),
                "lower_hours" : random.uniform(5, 80),
                "upper_hours" : random.uniform(80, 125),
            },
        })

    decisions = schedule_fleet(fleet)
    for d in decisions:
        print(f"{d['turbine_id']} | {d['priority']:8s} | "
              f"RUL:{d['rul_hours']:.1f}h | Crew:{d['assigned_crew']}")