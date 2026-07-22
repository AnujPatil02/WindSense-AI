"""
Agent 1 — Anomaly Localizer
Identifies WHICH sensors contributed most to the anomaly.
Uses per-sensor reconstruction error from LSTM Autoencoder.
"""

import numpy as np
import json
from pathlib import Path
import tensorflow as tf
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")


def localize(X: np.ndarray, top_k: int = 3) -> list:
    """
    For each sample in X, identify top_k sensors with highest reconstruction error.
    
    Args:
        X    : shape (n_samples, timesteps, n_features)
        top_k: number of top contributing sensors to return
    
    Returns:
        List of dicts with sensor names and error contributions per sample
    """
    # Load model and sensor metadata
    model = tf.keras.models.load_model(MODELS_DIR / "lstm_autoencoder.keras")
    with open(PROCESSED / "dataset_meta.json") as f:
        meta = json.load(f)

    sensor_names = meta["useful_sensors"]

    X_pred = model.predict(X, batch_size=256, verbose=0)
    # Per-sensor reconstruction error: mean over timesteps
    # shape: (n_samples, n_features)
    per_sensor_err = np.mean(np.square(X - X_pred), axis=1)

    results = []
    for i in range(len(X)):
        errors      = per_sensor_err[i]
        total_err   = errors.sum() + 1e-8
        sorted_idx  = np.argsort(errors)[::-1][:top_k]

        contributing = []
        for idx in sorted_idx:
            sensor = sensor_names[idx] if idx < len(sensor_names) else f"sensor_{idx}"
            contributing.append({
                "sensor"      : sensor,
                "error"       : round(float(errors[idx]), 6),
                "contribution": round(float(errors[idx] / total_err), 4),
            })

        results.append({
            "sample_idx"     : i,
            "total_error"    : round(float(errors.sum()), 6),
            "top_sensors"    : contributing,
            "primary_cause"  : contributing[0]["sensor"],
        })

    return results


def localize_single(x: np.ndarray, top_k: int = 3) -> dict:
    """Localize anomaly for a single reading. x shape: (timesteps, n_features)"""
    result = localize(x[np.newaxis, ...], top_k=top_k)
    return result[0]


def explain_anomaly(localization: dict, turbine_id: str = "") -> str:
    """Generate plain-English explanation of which sensors caused the anomaly."""
    top = localization["top_sensors"]
    lines = [
        f"Anomaly detected on {turbine_id}." if turbine_id else "Anomaly detected.",
        f"Total reconstruction error: {localization['total_error']:.6f}",
        "Top contributing sensors:",
    ]
    for rank, s in enumerate(top, 1):
        lines.append(
            f"  {rank}. {s['sensor']} — error: {s['error']:.6f} "
            f"({s['contribution']*100:.1f}% of total)"
        )
    lines.append(f"Primary cause sensor: {localization['primary_cause']}")
    return "\n".join(lines)


if __name__ == "__main__":
    X_val = np.load(PROCESSED / "X_val_seq.npy")
    y_val = np.load(PROCESSED / "y_val_anom.npy")

    # Find anomalous samples
    anomaly_idx = np.where(y_val == 1)[0][:3]
    X_anomalous = X_val[anomaly_idx]

    print("=== Anomaly Localization Test ===\n")
    results = localize(X_anomalous, top_k=3)
    for i, res in enumerate(results):
        print(explain_anomaly(res, turbine_id=f"WT-00{i+1}"))
        print()