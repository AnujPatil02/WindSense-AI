"""SHAP Explainability for RUL model — Agent 2"""

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


def compute_shap_values(n_samples: int = 300):
    model = joblib.load(MODELS_DIR / "xgboost_rul.pkl")

    with open(PROCESSED / "dataset_meta.json") as f:
        meta = json.load(f)

    X_val         = np.load(PROCESSED / "X_val_flat.npy")[:n_samples]
    sensor_names  = (meta["useful_sensors"] +
                     ["op_set_1", "op_set_2", "op_set_3", "cycle"])
    n_feat        = X_val.shape[1]
    feature_names = sensor_names[:n_feat]

    logger.info(f"Computing SHAP for {n_samples} samples...")
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_val)

    # Summary bar plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_val, feature_names=feature_names,
                      show=False, max_display=15, plot_type="bar")
    plt.title("Agent 2 — RUL Feature Importance (SHAP)")
    plt.tight_layout()
    plt.savefig(REPORTS / "shap_agent2_summary.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Beeswarm plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_val, feature_names=feature_names,
                      show=False, max_display=15)
    plt.title("Agent 2 — SHAP Beeswarm (RUL)")
    plt.tight_layout()
    plt.savefig(REPORTS / "shap_agent2_beeswarm.png", dpi=150, bbox_inches="tight")
    plt.close()

    mean_abs = np.abs(shap_values).mean(axis=0)
    importance = dict(sorted(zip(feature_names, mean_abs.tolist()),
                              key=lambda x: -x[1]))

    with open(REPORTS / "shap_importance_agent2.json", "w") as f:
        json.dump(importance, f, indent=2)

    np.save(REPORTS / "shap_values_agent2.npy", shap_values)
    logger.success("Agent 2 SHAP complete.")

    print("Top 5 RUL features:")
    for feat, val in list(importance.items())[:5]:
        print(f"  {feat}: {val:.4f}")

    return shap_values, importance


def explain_single(x_flat: np.ndarray) -> dict:
    model         = joblib.load(MODELS_DIR / "xgboost_rul.pkl")
    with open(PROCESSED / "dataset_meta.json") as f:
        meta = json.load(f)
    sensor_names  = (meta["useful_sensors"] +
                     ["op_set_1", "op_set_2", "op_set_3", "cycle"])
    explainer     = shap.TreeExplainer(model)
    shap_vals     = explainer.shap_values(x_flat.reshape(1, -1))[0]
    n_feat        = len(shap_vals)
    explanation   = dict(zip(sensor_names[:n_feat], shap_vals.tolist()))
    return dict(sorted(explanation.items(), key=lambda x: -abs(x[1])))


if __name__ == "__main__":
    REPORTS.mkdir(exist_ok=True)
    compute_shap_values()