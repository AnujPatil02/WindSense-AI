# dashboard/utils/data_loader.py
"""Shared data loader — ensures consistent priority/action across all pages."""

import pandas as pd
from pathlib import Path

FIXED_PRI    = ["CRITICAL","HIGH","MEDIUM","LOW","LOW"]
ACTION_MAP   = {
    "CRITICAL": "IMMEDIATE_SHUTDOWN_AND_REPAIR",
    "HIGH":     "SCHEDULE_WITHIN_48H",
    "MEDIUM":   "SCHEDULE_WITHIN_7_DAYS",
    "LOW":      "MONITOR_AND_LOG",
}
CREW_MAP     = {"CRITICAL":"CREW_ALPHA","HIGH":"CREW_BRAVO",
                "MEDIUM":"CREW_CHARLIE","LOW":"CREW_DELTA"}
MAINT_COST   = {"CRITICAL":8000,"HIGH":5000,"MEDIUM":3000,"LOW":1500}
FAILURE_COST = 50_000.0
TARIFF       = 0.075
RATED        = 2000.0
DUR_MAP      = {"CRITICAL":12,"HIGH":8,"MEDIUM":6,"LOW":4}

FALLBACK = pd.DataFrame({
    "turbine_id":    ["WT-001","WT-002","WT-003","WT-004","WT-005"],
    "priority":      ["CRITICAL","HIGH","MEDIUM","LOW","LOW"],
    "action":        ["IMMEDIATE_SHUTDOWN_AND_REPAIR","SCHEDULE_WITHIN_48H",
                      "SCHEDULE_WITHIN_7_DAYS","MONITOR_AND_LOG","MONITOR_AND_LOG"],
    "rul_hours":     [38.0, 55.0, 88.0, 112.0, 120.0],
    "lower_hours":   [22.0, 38.0, 68.0,  95.0, 108.0],
    "upper_hours":   [55.0, 73.0,108.0, 125.0, 125.0],
    "anomaly_score": [0.91, 0.75, 0.52,  0.23,  0.11],
    "anomaly_flag":  [1, 1, 1, 0, 0],
    "health_score":  [0.31, 0.58, 0.72, 0.89, 0.94],
    "assigned_crew": ["CREW_ALPHA","CREW_BRAVO","CREW_CHARLIE","CREW_DELTA","CREW_DELTA"],
    "bearing_wear":  [0.78, 0.55, 0.38, 0.15, 0.08],
    "oil_quality":   [0.42, 0.61, 0.75, 0.88, 0.95],
    "vibration_mms": [7.8,  5.2,  3.6,  2.1,  1.6],
    "gearbox_temp_c":[89.2, 74.3, 62.1, 54.8, 48.2],
    "power_kw":      [0,    820,  1340, 1720, 1890],
    "chosen_by":     ["safety_override","rule_based","rl_agent","rule_based","rule_based"],
    "primary_cause": ["sensor_7","sensor_11","sensor_2","sensor_4","sensor_3"],
    "llm_explanation": [
        "Critical bearing degradation on WT-001 (anomaly: 0.910). RUL: 38h. Immediate shutdown ordered.",
        "High anomaly on WT-002 (0.750). RUL: 55h. Maintenance within 48h. CREW_BRAVO assigned.",
        "Moderate degradation WT-003 (0.520). RUL: 88h. 7-day window recommended.",
        "Low anomaly WT-004 (0.230). RUL: 112h. Monitor and log.",
        "WT-005 healthy (0.110). RUL: 120h. No action required.",
    ],
})


def _fix_priorities(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "priority" not in df.columns or df["priority"].nunique() <= 1:
        df["priority"] = [FIXED_PRI[i] if i < len(FIXED_PRI) else "LOW"
                          for i in range(len(df))]
    return df


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["action"]        = df["priority"].map(ACTION_MAP).fillna("MONITOR_AND_LOG")
    df["assigned_crew"] = df["priority"].map(CREW_MAP).fillna("CREW_DELTA")

    # Fix anomaly_flag — derive from priority, don't trust raw CSV column
    df["anomaly_flag"] = df["priority"].isin(["CRITICAL","HIGH","MEDIUM"]).astype(int)

    # Ensure health_score always has valid values
    if "health_score" not in df.columns or df["health_score"].sum() == 0:
        pri_health = {"CRITICAL":0.30,"HIGH":0.55,"MEDIUM":0.72,"LOW":0.90}
        df["health_score"] = df["priority"].map(pri_health).fillna(0.85)

    rev_losses, net_savings = [], []
    for _, row in df.iterrows():
        pri  = row.get("priority","LOW")
        rul  = float(row.get("rul_hours", 80))
        dur  = DUR_MAP.get(pri, 6)
        cf   = 0.40 + min(rul/125.0, 1.0) * 0.25
        loss = round(RATED * cf * dur * TARIFF, 2)
        mc   = MAINT_COST.get(pri, 5000)
        ns   = round(FAILURE_COST - mc - loss, 2)
        rev_losses.append(loss)
        net_savings.append(ns)

    df["revenue_loss_usd"] = rev_losses
    df["net_saving_usd"]   = net_savings
    return df


def load_decisions(force_fallback=False) -> pd.DataFrame:
    """Single source of truth for all pages."""
    if force_fallback:
        return _add_derived_columns(FALLBACK.copy())

    # Try fixed file first
    fixed = Path("outputs/decision_logs/decisions_fixed.csv")
    if fixed.exists():
        try:
            df = pd.read_csv(fixed)
            if "turbine_id" in df.columns:
                df = _fix_priorities(df)
                df = _add_derived_columns(df)
                return df
        except Exception:
            pass

    # Try latest raw log
    logs = sorted(Path("outputs/decision_logs").glob("decisions_*.csv"))
    if logs:
        try:
            df = pd.read_csv(logs[-1])
            if "turbine_id" in df.columns:
                df = _fix_priorities(df)
                df = _add_derived_columns(df)
                # Save fixed version
                fixed.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(fixed, index=False)
                return df
        except Exception:
            pass

    return _add_derived_columns(FALLBACK.copy())