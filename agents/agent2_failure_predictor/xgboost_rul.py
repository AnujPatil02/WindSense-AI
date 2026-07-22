"""XGBoost RUL Regression — Agent 2"""

import numpy as np
import json
from pathlib import Path
import xgboost as xgb
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


def train():
    X_train = np.load(PROCESSED / "X_train_flat.npy")
    y_train = np.load(PROCESSED / "y_train_flat.npy")
    X_val   = np.load(PROCESSED / "X_val_flat.npy")
    y_val   = np.load(PROCESSED / "y_val_flat.npy")

    model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30,
        eval_metric="rmse",
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50,
    )

    y_pred = model.predict(X_val)
    metrics = _compute_metrics("XGBoost", y_val, y_pred)

    joblib.dump(model, MODELS_DIR / "xgboost_rul.pkl")
    with open(MODELS_DIR / "xgboost_rul_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"XGBoost saved | RMSE: {metrics['rmse']:.3f}")
    return model, metrics


def predict(X: np.ndarray) -> np.ndarray:
    model = joblib.load(MODELS_DIR / "xgboost_rul.pkl")
    return model.predict(X).clip(0, 125)


def _compute_metrics(name, y_true, y_pred):
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    print(f"\n{name} | RMSE:{rmse:.3f} MAE:{mae:.3f} R²:{r2:.4f}")
    return {"model": name, "rmse": rmse, "mae": mae, "r2": r2}


if __name__ == "__main__":
    MODELS_DIR.mkdir(exist_ok=True)
    train()