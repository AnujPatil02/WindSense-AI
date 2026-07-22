"""Compare XGBoost vs LSTM RUL — select winner — Agent 2"""

import numpy as np
import json
from pathlib import Path
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


def compare_and_select():
    X_val_flat = np.load(PROCESSED / "X_val_flat.npy")
    X_val_seq  = np.load(PROCESSED / "X_val_seq.npy")
    y_val_rul  = np.load(PROCESSED / "y_val_rul.npy")

    # Align lengths
    n = min(len(X_val_flat), len(X_val_seq), len(y_val_rul))
    y_true     = y_val_rul[:n]
    X_val_flat = X_val_flat[:n]
    X_val_seq  = X_val_seq[:n]

    # XGBoost predictions
    xgb_model   = joblib.load(MODELS_DIR / "xgboost_rul.pkl")
    y_pred_xgb  = xgb_model.predict(X_val_flat).clip(0, 125)

    # LSTM predictions
    lstm_model  = tf.keras.models.load_model(MODELS_DIR / "lstm_rul.keras")
    y_pred_lstm = lstm_model.predict(X_val_seq, verbose=0).flatten().clip(0, 125)

    results = []
    for name, y_pred in [("XGBoost", y_pred_xgb), ("LSTM", y_pred_lstm)]:
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae  = float(mean_absolute_error(y_true, y_pred))
        r2   = float(r2_score(y_true, y_pred))
        m    = {"model": name, "rmse": rmse, "mae": mae, "r2": r2}
        results.append(m)
        print(f"{name:10s} | RMSE:{rmse:.3f}  MAE:{mae:.3f}  R²:{r2:.4f}")

    # Winner = lowest RMSE
    winner = min(results, key=lambda x: x["rmse"])
    print(f"\n✅ WINNER: {winner['model']} (lowest RMSE: {winner['rmse']:.3f})")

    report = {"models": results, "winner": winner["model"],
              "reason": "Lowest RMSE on validation set"}

    REPORTS.mkdir(exist_ok=True)
    with open(REPORTS / "agent2_model_comparison.json", "w") as f:
        json.dump(report, f, indent=2)
    with open(MODELS_DIR / "agent2_winner.json", "w") as f:
        json.dump({"winner": winner["model"]}, f)

    logger.success(f"Agent 2 winner: {winner['model']}")
    return winner


if __name__ == "__main__":
    compare_and_select()