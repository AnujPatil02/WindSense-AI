"""LSTM Sequence Model for RUL Estimation — Agent 2"""

import numpy as np
import json
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")


def build_model(timesteps: int, n_features: int) -> Model:
    inputs = Input(shape=(timesteps, n_features))
    x = LSTM(128, return_sequences=True)(inputs)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    x = LSTM(64, return_sequences=False)(x)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    x = Dense(32, activation="relu")(x)
    outputs = Dense(1, activation="relu")(x)
    model = Model(inputs, outputs, name="lstm_rul")
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def train(epochs: int = 50, batch_size: int = 64):
    X_train = np.load(PROCESSED / "X_train_seq.npy")
    y_train = np.load(PROCESSED / "y_train_rul.npy")
    X_val   = np.load(PROCESSED / "X_val_seq.npy")
    y_val   = np.load(PROCESSED / "y_val_rul.npy")

    timesteps, n_features = X_train.shape[1], X_train.shape[2]
    model = build_model(timesteps, n_features)
    model.summary()

    callbacks = [
        EarlyStopping(patience=8, restore_best_weights=True),
        ModelCheckpoint(str(MODELS_DIR / "lstm_rul.keras"), save_best_only=True),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    y_pred   = model.predict(X_val, verbose=0).flatten().clip(0, 125)
    rmse     = float(np.sqrt(mean_squared_error(y_val, y_pred)))
    mae      = float(mean_absolute_error(y_val, y_pred))
    r2       = float(r2_score(y_val, y_pred))
    metrics  = {"model": "LSTM", "rmse": rmse, "mae": mae, "r2": r2}

    with open(MODELS_DIR / "lstm_rul_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"LSTM saved | RMSE:{rmse:.3f} MAE:{mae:.3f} R²:{r2:.4f}")
    return model, metrics


def predict(X: np.ndarray) -> np.ndarray:
    model = tf.keras.models.load_model(MODELS_DIR / "lstm_rul.keras")
    return model.predict(X, verbose=0).flatten().clip(0, 125)


if __name__ == "__main__":
    MODELS_DIR.mkdir(exist_ok=True)
    train()