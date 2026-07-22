"""
Agent 1 — LSTM Autoencoder for Anomaly Detection
Learns normal sensor patterns, flags high reconstruction error as anomaly.
"""

import numpy as np
import json
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


def build_lstm_autoencoder(timesteps: int, n_features: int) -> Model:
    inputs = Input(shape=(timesteps, n_features))
    # Encoder
    x = LSTM(64, activation="relu", return_sequences=False)(inputs)
    # Bottleneck
    x = RepeatVector(timesteps)(x)
    # Decoder
    x = LSTM(64, activation="relu", return_sequences=True)(x)
    outputs = TimeDistributed(Dense(n_features))(x)

    model = Model(inputs, outputs, name="lstm_autoencoder")
    model.compile(optimizer="adam", loss="mse")
    return model


def train(epochs: int = 30, batch_size: int = 64, threshold_percentile: float = 95.0):
    # Load data
    X_train = np.load(PROCESSED / "X_train_seq.npy")
    X_val   = np.load(PROCESSED / "X_val_seq.npy")
    y_train_anom = np.load(PROCESSED / "y_train_anom.npy")

    # Train ONLY on healthy samples (anomaly=0)
    healthy_idx = np.where(y_train_anom == 0)[0]
    X_healthy   = X_train[healthy_idx]
    logger.info(f"Training on {len(X_healthy)} healthy samples | shape: {X_healthy.shape}")

    timesteps, n_features = X_healthy.shape[1], X_healthy.shape[2]
    model = build_lstm_autoencoder(timesteps, n_features)
    model.summary()

    callbacks = [
        EarlyStopping(patience=5, restore_best_weights=True, verbose=1),
        ModelCheckpoint(str(MODELS_DIR / "lstm_autoencoder.keras"),
                        save_best_only=True, verbose=0),
    ]

    history = model.fit(
        X_healthy, X_healthy,
        validation_split=0.1,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    # Compute reconstruction error on all training data
    X_pred     = model.predict(X_train, batch_size=256, verbose=0)
    recon_err  = np.mean(np.square(X_train - X_pred), axis=(1, 2))

    # Threshold = 95th percentile of healthy reconstruction errors
    healthy_errs  = recon_err[healthy_idx]
    threshold     = float(np.percentile(healthy_errs, threshold_percentile))
    logger.info(f"Anomaly threshold (p{threshold_percentile:.0f}): {threshold:.6f}")

    # Save threshold + metadata
    meta = {
        "threshold"   : threshold,
        "percentile"  : threshold_percentile,
        "timesteps"   : timesteps,
        "n_features"  : n_features,
        "train_samples": len(X_healthy),
    }
    with open(MODELS_DIR / "lstm_ae_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Save training history
    np.save(MODELS_DIR / "lstm_ae_history.npy", history.history)
    logger.success("LSTM Autoencoder training complete.")
    return model, threshold, meta


def predict(X: np.ndarray) -> dict:
    """
    Given sequences X, return anomaly flags + scores.
    Returns: {anomaly_flags, anomaly_scores, threshold}
    """
    model = tf.keras.models.load_model(MODELS_DIR / "lstm_autoencoder.keras")
    with open(MODELS_DIR / "lstm_ae_meta.json") as f:
        meta = json.load(f)

    X_pred   = model.predict(X, batch_size=256, verbose=0)
    scores   = np.mean(np.square(X - X_pred), axis=(1, 2))
    flags    = (scores > meta["threshold"]).astype(int)

    return {
        "anomaly_flags" : flags,
        "anomaly_scores": scores,
        "threshold"     : meta["threshold"],
    }


if __name__ == "__main__":
    MODELS_DIR.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    model, threshold, meta = train()
    print(f"\n✅ Model saved | Threshold: {threshold:.6f}")