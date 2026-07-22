"""Evidently AI — Production Model Drift Detection."""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from loguru import logger

PROCESSED = Path("data/processed")
REPORTS   = Path("outputs/reports")


def detect_drift(reference_path: str = None,
                 current_path: str = None) -> dict:
    """
    Compare reference (training) vs current (production) sensor distributions.
    Detects data drift using Evidently.
    """
    try:
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset
        from evidently.metrics import DatasetDriftMetric

        # Load reference data
        if reference_path:
            ref_df = pd.read_csv(reference_path)
        else:
            ref_df = pd.read_csv(PROCESSED / "train_cmapss_processed.csv")

        # Load or simulate current data
        if current_path:
            cur_df = pd.read_csv(current_path)
        else:
            cur_df = _simulate_drifted_data(ref_df)

        # Select sensor columns only
        sensor_cols = [c for c in ref_df.columns
                       if c.startswith("sensor_")][:10]
        ref_sample  = ref_df[sensor_cols].sample(min(500, len(ref_df)),
                                                   random_state=42)
        cur_sample  = cur_df[sensor_cols].sample(min(500, len(cur_df)),
                                                   random_state=42)

        # Run Evidently drift report
        report = Report(metrics=[DataDriftPreset(), DatasetDriftMetric()])
        report.run(reference_data=ref_sample, current_data=cur_sample)

        REPORTS.mkdir(exist_ok=True)
        report.save_html(str(REPORTS / "drift_report.html"))

        result_dict = report.as_dict()
        drift_detected = result_dict["metrics"][1]["result"]["dataset_drift"]
        n_drifted      = result_dict["metrics"][1]["result"].get(
            "number_of_drifted_columns", 0)

        summary = {
            "drift_detected"      : drift_detected,
            "n_drifted_columns"   : n_drifted,
            "total_columns"       : len(sensor_cols),
            "drift_share"         : round(n_drifted / len(sensor_cols), 3),
            "report_path"         : str(REPORTS / "drift_report.html"),
        }

        logger.info(f"Drift detected: {drift_detected} | "
                    f"Drifted cols: {n_drifted}/{len(sensor_cols)}")
        with open(REPORTS / "drift_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    except ImportError:
        logger.warning("Evidently not installed — using statistical fallback")
        return _statistical_drift(ref_df if 'ref_df' in dir() else None)
    except Exception as e:
        logger.error(f"Drift detection error: {e}")
        return {"drift_detected": False, "error": str(e)}


def _simulate_drifted_data(ref_df: pd.DataFrame) -> pd.DataFrame:
    """Simulate drifted production data for testing."""
    drifted = ref_df.copy()
    sensor_cols = [c for c in drifted.columns if c.startswith("sensor_")][:5]
    for col in sensor_cols:
        drifted[col] = drifted[col] + np.random.normal(0.3, 0.1, len(drifted))
    return drifted


def _statistical_drift(ref_df=None) -> dict:
    """Fallback: KS test for drift detection."""
    from scipy import stats

    if ref_df is None:
        ref_df = pd.read_csv(PROCESSED / "train_cmapss_processed.csv")

    cur_df      = _simulate_drifted_data(ref_df)
    sensor_cols = [c for c in ref_df.columns if c.startswith("sensor_")][:10]

    drifted = []
    for col in sensor_cols:
        stat, p = stats.ks_2samp(ref_df[col].dropna(), cur_df[col].dropna())
        if p < 0.05:
            drifted.append(col)

    summary = {
        "drift_detected"    : len(drifted) > 0,
        "n_drifted_columns" : len(drifted),
        "drifted_columns"   : drifted,
        "method"            : "KS_test_fallback",
    }
    with open(REPORTS / "drift_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    result = detect_drift()
    print(f"\nDrift detected: {result['drift_detected']}")
    print(f"Drifted columns: {result.get('n_drifted_columns', 0)}")