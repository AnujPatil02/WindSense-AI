"""Revenue Loss Estimator from Maintenance Downtime — Agent 4"""

import numpy as np
from typing import Dict, List
from loguru import logger

TARIFF_PER_KWH  = 0.075
RATED_POWER_KW  = 2000.0


def estimate(decision: dict, forecast_72h=None) -> dict:
    import numpy as np
    from datetime import datetime

    turbine_id = decision.get("turbine_id", "UNKNOWN")

    # Priority 1: use saved duration_hours from scheduler
    if "duration_hours" in decision and float(decision["duration_hours"]) > 0:
        downtime_hours = float(decision["duration_hours"])
    else:
        # Priority 2: calculate from timestamps
        try:
            start = datetime.fromisoformat(str(decision["scheduled_start"]))
            end   = datetime.fromisoformat(str(decision["scheduled_end"]))
            downtime_hours = max(2.0, (end - start).total_seconds() / 3600)
        except Exception:
            # Priority 3: derive from priority
            downtime_hours = {
                "CRITICAL": 12.0,
                "HIGH"    : 8.0,
                "MEDIUM"  : 6.0,
                "LOW"     : 4.0,
            }.get(decision.get("priority","MEDIUM"), 6.0)
    
    # rest of function stays the same...

    # ----------------------------------------------------------------------
    # Load reduction
    # ----------------------------------------------------------------------

    load_pct = decision.get("recommended_load_pct", 100) / 100.0

    # ----------------------------------------------------------------------
    # Estimate expected generation
    # ----------------------------------------------------------------------

    expected_power = None

    if (
        forecast_72h is not None
        and len(forecast_72h) >= int(downtime_hours)
    ):

        arr = np.array(
            forecast_72h[:int(downtime_hours)],
            dtype=float
        )

        # --------------------------------------------------------------
        # If values look like wind speed (m/s)
        # --------------------------------------------------------------

        if arr.mean() < 30:

            # Wind turbine power curve approximation
            # Cut-in: 3 m/s
            # Rated: 12 m/s
            # Cut-out: 25 m/s

            v = arr.clip(0, 25)

            power = np.where(
                v < 3,
                0.0,

                np.where(
                    v < 12,
                    RATED_POWER_KW * ((v - 3) / 9) ** 3,
                    RATED_POWER_KW
                )
            )

            expected_power = float(
                np.clip(
                    power.mean(),
                    0,
                    RATED_POWER_KW
                )
            )

        # --------------------------------------------------------------
        # Already power forecast (kW)
        # --------------------------------------------------------------

        else:
            expected_power = float(arr.mean())

    # ----------------------------------------------------------------------
    # Fallback estimation using RUL-based capacity factor
    # ----------------------------------------------------------------------

    else:

        rul = float(
            decision.get(
                "rul_hours",
                decision.get("rul_lower_bound", 60)
            )
        )

        # Capacity factor between 45% and 65%
        cf = 0.45 + min(rul / 125.0, 1.0) * 0.20

        expected_power = RATED_POWER_KW * cf

    # ----------------------------------------------------------------------
    # Actual generation during maintenance
    # ----------------------------------------------------------------------

    if load_pct > 0:
        actual_power = expected_power * load_pct
    else:
        actual_power = 0.0

    # ----------------------------------------------------------------------
    # Energy + revenue loss
    # ----------------------------------------------------------------------

    lost_kwh = (
        (expected_power - actual_power)
        * downtime_hours
    )

    revenue_loss = round(
        lost_kwh * TARIFF_PER_KWH,
        2
    )

    # ----------------------------------------------------------------------
    # Maintenance economics
    # ----------------------------------------------------------------------

    priority = decision.get("priority", "MEDIUM")

    maint_cost = {
        "CRITICAL": 8000,
        "HIGH": 5000,
        "MEDIUM": 3000,
        "LOW": 1500,
    }.get(priority, 5000)

    # Failure avoidance assumptions
    failure_cost = 50_000.0

    net_saving = round(
        failure_cost
        - maint_cost
        - revenue_loss,
        2
    )

    # ----------------------------------------------------------------------
    # Final result
    # ----------------------------------------------------------------------

    result = {

        "turbine_id": turbine_id,

        "downtime_hours": round(
            downtime_hours,
            1
        ),

        "expected_power_kw": round(
            expected_power,
            1
        ),

        "actual_power_kw": round(
            actual_power,
            1
        ),

        "lost_generation_kwh": round(
            lost_kwh,
            1
        ),

        "revenue_loss_usd": revenue_loss,

        "planned_maint_cost": maint_cost,

        "failure_cost_avoided": failure_cost,

        "net_saving_usd": net_saving,

        "roi_justified": net_saving > 0,

        "summary": (
            f"Planned maintenance saves "
            f"${net_saving:,.0f} net "
            f"(avoids ${failure_cost:,.0f} failure vs "
            f"${maint_cost:,.0f} maintenance + "
            f"${revenue_loss:,.0f} lost revenue)"
        )
    }

    # ----------------------------------------------------------------------
    # Logging
    # ----------------------------------------------------------------------

    logger.info(
        f"{turbine_id} | "
        f"Expected Power: {expected_power:.0f}kW | "
        f"Downtime: {downtime_hours:.1f}h | "
        f"Revenue Loss: ${revenue_loss:,.2f} | "
        f"Net Saving: ${net_saving:,.2f}"
    )

    return result


def estimate_fleet(decisions: List[Dict], forecast_72h: np.ndarray = None) -> Dict:
    """Estimate revenue loss for entire fleet."""
    results      = [estimate(d, forecast_72h) for d in decisions]
    total_loss   = sum(r["revenue_loss_usd"] for r in results)
    total_saving = sum(r["net_saving_usd"] for r in results)

    return {
        "turbine_results" : results,
        "total_revenue_loss_usd": round(total_loss, 2),
        "total_net_saving_usd"  : round(total_saving, 2),
        "fleet_roi_positive"    : total_saving > 0,
    }


if __name__ == "__main__":
    decision = {
        "turbine_id"      : "WT-003",
        "scheduled_start" : "2024-06-01T06:00:00",
        "scheduled_end"   : "2024-06-01T12:00:00",
        "recommended_load_pct": 0,
        "priority"        : "HIGH",
    }
    forecast = np.random.uniform(800, 1800, 72)
    result   = estimate(decision, forecast)
    for k, v in result.items():
        print(f"  {k:30s}: {v}")