"""
Agent 1 — Isolation Forest for Anomaly Detection
Unsupervised multivariate anomaly detection on sensor features.
"""

import numpy as np
import json
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")


def train(contamination: float = 0.1, n_estimators: int = 200, random_state: int = 42):
    # Use flat (non-sequence) features for IF
    X_train = np.load(PROCESSED / "X_train_flat.npy")
    y_train = np.load(PROCESSED / "y_train_anom.npy")

    # Note: y_train here corresponds to flat samples, not sequences
    # Use contamination param to match expected anomaly ratio
    actual_contamination = float(np.mean(y_train))
    contamination = min(max(actual_contamination, 0.01), 0.5)
    logger.info(f"Contamination set to: {contamination:.3f}")

    # Scale features
    scaler  = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    # Train Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples="auto",
        random_state=random_state,
        n_jobs=-1,
        verbose=0,
    )
    iso_forest.fit(X_scaled)

    # Anomaly scores: negative = more anomalous
    raw_scores = iso_forest.decision_function(X_scaled)
    # Normalize to [0,1] where 1 = most anomalous
    norm_scores = 1.0 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-8)
    predictions = iso_forest.predict(X_scaled)   # -1=anomaly, 1=normal
    flags       = (predictions == -1).astype(int)

    logger.info(f"Isolation Forest detected {flags.sum()} anomalies in training set")

    # Save model + scaler
    joblib.dump(iso_forest, MODELS_DIR / "isolation_forest.pkl")
    joblib.dump(scaler,     MODELS_DIR / "if_scaler.pkl")

    meta = {
        "n_estimators"  : n_estimators,
        "contamination" : contamination,
        "n_features"    : X_train.shape[1],
        "anomaly_rate"  : float(flags.mean()),
    }
    with open(MODELS_DIR / "if_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    logger.success("Isolation Forest training complete.")
    return iso_forest, scaler, meta


def predict(X: np.ndarray) -> dict:
    """
    X: flat feature array (n_samples, n_features)
    Returns: {anomaly_flags, anomaly_scores}
    """
    iso_forest = joblib.load(MODELS_DIR / "isolation_forest.pkl")
    scaler     = joblib.load(MODELS_DIR / "if_scaler.pkl")

    X_scaled    = scaler.transform(X)
    raw_scores  = iso_forest.decision_function(X_scaled)
    norm_scores = 1.0 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-8)
    predictions = iso_forest.predict(X_scaled)
    flags       = (predictions == -1).astype(int)

    return {
        "anomaly_flags" : flags,
        "anomaly_scores": norm_scores,
    }


if __name__ == "__main__":
    MODELS_DIR.mkdir(exist_ok=True)
    iso_forest, scaler, meta = train()
    print(f"\n✅ Isolation Forest saved | Anomaly rate: {meta['anomaly_rate']:.3f}")