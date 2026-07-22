"""Operational Load Adjuster — Agent 3"""

from typing import Dict
from loguru import logger


def adjust(decision: Dict, current_power_kw: float,
           rated_power_kw: float = 2000.0) -> Dict:
    """
    Given a maintenance decision, calculate adjusted operating parameters.
    Returns setpoint commands to send to SCADA.
    """
    load_pct    = decision.get("recommended_load_pct", 100)
    priority    = decision.get("priority", "LOW")
    turbine_id  = decision.get("turbine_id", "UNKNOWN")

    target_power = rated_power_kw * (load_pct / 100.0)
    power_delta  = current_power_kw - target_power

    setpoint = {
        "turbine_id"         : turbine_id,
        "power_setpoint_kw"  : round(target_power, 1),
        "load_pct"           : load_pct,
        "current_power_kw"   : round(current_power_kw, 1),
        "power_reduction_kw" : round(max(0, power_delta), 1),
        "rpm_setpoint"       : _rpm_from_load(load_pct),
        "pitch_angle_deg"    : _pitch_from_load(load_pct),
        "command"            : _build_command(priority, load_pct),
        "revenue_loss_per_h" : round(power_delta * 0.075, 2),  # ~$0.075/kWh
    }

    logger.info(
        f"{turbine_id} load adjusted: "
        f"{current_power_kw:.0f}kW → {target_power:.0f}kW "
        f"({load_pct}% load)"
    )
    return setpoint


def _rpm_from_load(load_pct: int) -> float:
    """Approximate RPM setpoint based on load percentage."""
    return round(16.5 * (load_pct / 100.0), 2)


def _pitch_from_load(load_pct: int) -> float:
    """
    Pitch angle — higher pitch = less wind capture = less power.
    0° = max power, 90° = feathered (no power).
    """
    if load_pct == 0:    return 90.0
    if load_pct == 50:   return 15.0
    if load_pct == 75:   return 8.0
    return 0.0


def _build_command(priority: str, load_pct: int) -> str:
    if priority == "CRITICAL" or load_pct == 0:
        return "EMERGENCY_STOP_AND_FEATHER"
    if load_pct == 50:
        return "DERATE_TO_50PCT_AND_MONITOR"
    if load_pct == 75:
        return "DERATE_TO_75PCT"
    return "NORMAL_OPERATION"


if __name__ == "__main__":
    decision = {
        "turbine_id": "WT-002",
        "priority"  : "HIGH",
        "recommended_load_pct": 50,
    }
    result = adjust(decision, current_power_kw=1600.0)
    for k, v in result.items():
        print(f"  {k:25s}: {v}")