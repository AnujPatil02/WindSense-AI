"""Conformal Prediction — RUL with confidence intervals — Agent 2"""

import numpy as np
import json
from pathlib import Path
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")


def train_conformal(alpha: float = 0.1):
    X_val = np.load(PROCESSED / "X_val_flat.npy")
    y_val = np.load(PROCESSED / "y_val_rul.npy")
    model = joblib.load(MODELS_DIR / "xgboost_rul.pkl")

    n_cal     = len(X_val) // 2
    X_cal     = X_val[:n_cal]
    y_cal     = y_val[:n_cal]
    y_pred    = model.predict(X_cal).clip(0, 125)
    residuals = np.abs(y_cal - y_pred)

    # Use 90th percentile — do NOT cap, let real uncertainty show
    quantile  = float(np.quantile(residuals, 1 - alpha))

    meta = {
        "alpha"        : alpha,
        "coverage"     : f"{(1-alpha)*100:.0f}%",
        "quantile"     : quantile,
        "n_calibration": n_cal,
    }
    with open(MODELS_DIR / "mapie_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    np.save(MODELS_DIR / "conformal_residuals.npy", residuals)
    logger.success(f"Conformal | quantile={quantile:.2f}h")
    return meta


def predict_with_uncertainty(X: np.ndarray, alpha: float = 0.1) -> dict:
    """
    Returns point estimate + confidence interval.
    Uses residual-based conformal prediction — no pickle issues.
    """
    model = joblib.load(MODELS_DIR / "xgboost_rul.pkl")

    # Load quantile
    meta_path = MODELS_DIR / "mapie_meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        quantile = meta.get("quantile", 20.0)
    else:
        quantile = 20.0   # Default fallback

    y_pred = model.predict(X).clip(0, 125)

    return {
        "rul_estimate": y_pred,
        "lower_bound" : (y_pred - quantile).clip(0, 125),
        "upper_bound" : (y_pred + quantile).clip(0, 125),
        "coverage"    : f"{(1-alpha)*100:.0f}%",
    }


def predict_single(x_flat: np.ndarray, alpha: float = 0.1) -> dict:
    result = predict_with_uncertainty(x_flat.reshape(1, -1), alpha)
    return {
        "rul_hours"  : round(float(result["rul_estimate"][0]), 1),
        "lower_hours": round(float(result["lower_bound"][0]), 1),
        "upper_hours": round(float(result["upper_bound"][0]), 1),
        "coverage"   : result["coverage"],
    }


if __name__ == "__main__":
    meta = train_conformal(alpha=0.1)
    print(f"Quantile: {meta['quantile']:.2f}h")

    X_test = np.load(PROCESSED / "X_val_flat.npy")[100:105]
    result = predict_with_uncertainty(X_test)
    print("\nSample predictions:")
    for i in range(len(X_test)):
        print(f"  RUL: {result['rul_estimate'][i]:.1f}h "
              f"[{result['lower_bound'][i]:.1f} — {result['upper_bound'][i]:.1f}]")