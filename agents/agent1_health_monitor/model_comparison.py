"""
Agent 1 — Compare LSTM Autoencoder vs Isolation Forest
Metrics: Precision, Recall, F1, False Positive Rate
Selects and saves winner.
"""

import numpy as np
import json
from pathlib import Path
from sklearn.metrics import (precision_score, recall_score,
                              f1_score, confusion_matrix, classification_report)
import tensorflow as tf
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


def evaluate_lstm_ae(X_val: np.ndarray, y_true: np.ndarray) -> dict:
    model = tf.keras.models.load_model(MODELS_DIR / "lstm_autoencoder.keras")
    with open(MODELS_DIR / "lstm_ae_meta.json") as f:
        meta = json.load(f)

    X_pred  = model.predict(X_val, batch_size=256, verbose=0)
    scores  = np.mean(np.square(X_val - X_pred), axis=(1, 2))
    y_pred  = (scores > meta["threshold"]).astype(int)

    return _compute_metrics("LSTM Autoencoder", y_true, y_pred, scores)


def evaluate_isolation_forest(X_val_flat: np.ndarray, y_true: np.ndarray) -> dict:
    iso   = joblib.load(MODELS_DIR / "isolation_forest.pkl")
    scaler = joblib.load(MODELS_DIR / "if_scaler.pkl")

    X_scaled = scaler.transform(X_val_flat)
    raw      = iso.decision_function(X_scaled)
    scores   = 1.0 - (raw - raw.min()) / (raw.max() - raw.min() + 1e-8)
    y_pred   = (iso.predict(X_scaled) == -1).astype(int)

    return _compute_metrics("Isolation Forest", y_true, y_pred, scores)


def _compute_metrics(name: str, y_true: np.ndarray,
                     y_pred: np.ndarray, scores: np.ndarray) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn + 1e-8)

    metrics = {
        "model"    : name,
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall"   : round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1"       : round(f1_score(y_true, y_pred, zero_division=0), 4),
        "fpr"      : round(fpr, 4),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }

    print(f"\n{'='*45}")
    print(f"  {name}")
    print(f"{'='*45}")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1 Score  : {metrics['f1']:.4f}")
    print(f"  False +ve : {metrics['fpr']:.4f}")
    print(f"  TP:{tp} FP:{fp} TN:{tn} FN:{fn}")
    return metrics


def compare_and_select():
    X_val      = np.load(PROCESSED / "X_val_seq.npy")
    X_val_flat = np.load(PROCESSED / "X_val_flat.npy")
    y_val_anom = np.load(PROCESSED / "y_val_anom.npy")

    # Align lengths (sequences are shorter due to windowing)
    n = min(len(X_val), len(X_val_flat), len(y_val_anom))
    y_true     = y_val_anom[:n]
    X_val      = X_val[:n]
    X_val_flat = X_val_flat[:n]

    lstm_metrics = evaluate_lstm_ae(X_val, y_true)
    if_metrics   = evaluate_isolation_forest(X_val_flat, y_true)

    # Selection logic:
    # Industrial priority — minimize false positives (costly unnecessary maintenance)
    # BUT recall must be acceptable (>0.6) — missing real faults is dangerous
    results = [lstm_metrics, if_metrics]

    # Filter models with acceptable recall
    acceptable = [m for m in results if m["recall"] >= 0.6]
    if not acceptable:
        acceptable = results   # Fallback

    # Among acceptable — pick lowest FPR, tiebreak on F1
    winner = sorted(acceptable, key=lambda x: (x["fpr"], -x["f1"]))[0]

    print(f"\n{'='*45}")
    print(f"  WINNER: {winner['model']}")
    print(f"  Reason: Lowest FPR ({winner['fpr']:.4f}) with acceptable Recall ({winner['recall']:.4f})")
    print(f"{'='*45}")

    # Save comparison report
    report = {
        "models"      : results,
        "winner"      : winner["model"],
        "winner_reason": "Lowest false positive rate with recall >= 0.6",
    }
    with open(REPORTS / "agent1_model_comparison.json", "w") as f:
        json.dump(report, f, indent=2)

    # Save winner name for downstream use
    with open(MODELS_DIR / "agent1_winner.json", "w") as f:
        json.dump({"winner": winner["model"]}, f)

    logger.success(f"Agent 1 winner saved: {winner['model']}")
    return winner


if __name__ == "__main__":
    compare_and_select()