"""
Agent 1 — SHAP Explainability
Explains Isolation Forest predictions using TreeExplainer.
Saves SHAP values for dashboard visualization.
"""

import numpy as np
import json
from pathlib import Path
import shap
import joblib
import matplotlib.pyplot as plt
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


def compute_shap_values(n_samples: int = 200):
    """Compute SHAP values for Isolation Forest on validation set."""
    iso    = joblib.load(MODELS_DIR / "isolation_forest.pkl")
    scaler = joblib.load(MODELS_DIR / "if_scaler.pkl")

    with open(PROCESSED / "dataset_meta.json") as f:
        meta = json.load(f)

    X_val    = np.load(PROCESSED / "X_val_flat.npy")[:n_samples]
    X_scaled = scaler.transform(X_val)

    sensor_names = (meta["useful_sensors"] +
                    ["op_set_1", "op_set_2", "op_set_3", "cycle"])

    # Trim names to match feature count
    n_feat = X_scaled.shape[1]
    feature_names = sensor_names[:n_feat]

    logger.info(f"Computing SHAP values for {n_samples} samples...")
    explainer   = shap.TreeExplainer(iso)
    shap_values = explainer.shap_values(X_scaled)

    # Save SHAP values
    np.save(REPORTS / "shap_values_agent1.npy", shap_values)

    # ── Summary Plot ──────────────────────────────────────────────────────
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values, X_scaled,
        feature_names=feature_names,
        show=False, max_display=15,
        plot_type="bar"
    )
    plt.title("Agent 1 — Feature Importance (SHAP)", fontsize=13)
    plt.tight_layout()
    plt.savefig(REPORTS / "shap_agent1_summary.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.success("SHAP summary plot saved.")

    # ── Mean absolute SHAP per feature (for dashboard) ───────────────────
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance    = dict(zip(feature_names, mean_abs_shap.tolist()))
    importance    = dict(sorted(importance.items(), key=lambda x: -x[1]))

    with open(REPORTS / "shap_importance_agent1.json", "w") as f:
        json.dump(importance, f, indent=2)

    logger.info("Top 5 features by SHAP importance:")
    for i, (feat, val) in enumerate(list(importance.items())[:5]):
        logger.info(f"  {i+1}. {feat}: {val:.4f}")

    return shap_values, importance


def explain_single_prediction(x_flat: np.ndarray) -> dict:
    """
    Explain a single sample prediction.
    x_flat: shape (n_features,)
    Returns dict of feature → shap_value
    """
    iso    = joblib.load(MODELS_DIR / "isolation_forest.pkl")
    scaler = joblib.load(MODELS_DIR / "if_scaler.pkl")

    with open(PROCESSED / "dataset_meta.json") as f:
        meta = json.load(f)

    sensor_names  = (meta["useful_sensors"] +
                     ["op_set_1", "op_set_2", "op_set_3", "cycle"])
    x_scaled      = scaler.transform(x_flat.reshape(1, -1))
    explainer     = shap.TreeExplainer(iso)
    shap_vals     = explainer.shap_values(x_scaled)[0]

    n_feat        = len(shap_vals)
    feature_names = sensor_names[:n_feat]
    explanation   = dict(zip(feature_names, shap_vals.tolist()))
    explanation   = dict(sorted(explanation.items(), key=lambda x: -abs(x[1])))
    return explanation


if __name__ == "__main__":
    REPORTS.mkdir(exist_ok=True)
    shap_values, importance = compute_shap_values(n_samples=300)
    print("\n✅ SHAP analysis complete.")
    print("Top features:", list(importance.keys())[:5])