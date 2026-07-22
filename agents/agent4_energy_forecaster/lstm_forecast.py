"""LSTM Hybrid Energy Forecast — Agent 4"""

import numpy as np
import json
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")

LOOKBACK = 24    # Use 24 hours to predict next hour
HORIZON  = 1     # Predict 1 step ahead, roll 72 times for 72h forecast


def _load_power_series() -> np.ndarray:
    import pandas as pd
    csv = PROCESSED / "wind_scada_processed.csv"
    if csv.exists():
        df  = pd.read_csv(csv)
        col = next((c for c in df.columns if "power" in c.lower()), df.columns[1])
        series = df[col].clip(lower=0).fillna(method="ffill").values.astype(np.float32)
        # Scale to 2MW if values look like they're in different units
        if series.max() < 100:
            series = series * 2000 / series.max()
        return series
    else:
        # Realistic 2MW turbine power series
        t      = np.arange(8760)
        wind   = np.random.weibull(2.0, 8760) * 8.5
        power  = np.where(wind < 3, 0,
                 np.where(wind < 12, 2000*((wind-3)/9)**3, 2000)
                 ).clip(0, 2000).astype(np.float32)
        power += np.random.normal(0, 30, 8760).astype(np.float32)
        return power.clip(0, 2000)

def _create_sequences(series: np.ndarray):
    X, y = [], []
    for i in range(len(series) - LOOKBACK):
        X.append(series[i:i+LOOKBACK])
        y.append(series[i+LOOKBACK])
    return np.array(X)[..., np.newaxis], np.array(y)


def train(epochs: int = 50, batch_size: int = 64):
    series = _load_power_series()

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(series.reshape(-1, 1)).flatten()

    X, y      = _create_sequences(scaled)
    split     = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    inputs = Input(shape=(LOOKBACK, 1))
    x = LSTM(64, return_sequences=True)(inputs)
    x = Dropout(0.2)(x)
    x = LSTM(32)(x)
    x = Dropout(0.2)(x)
    outputs = Dense(1)(x)

    model = Model(inputs, outputs, name="lstm_forecast")
    model.compile(optimizer="adam", loss="mse")

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[EarlyStopping(patience=8, restore_best_weights=True)],
        verbose=1,
    )

    # Evaluate
    y_pred_scaled = model.predict(X_val, verbose=0).flatten()
    y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1,1)).flatten()
    y_true = scaler.inverse_transform(y_val.reshape(-1,1)).flatten()

    mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    metrics = {"model": "LSTM_Forecast", "mape": round(mape, 3), "rmse": round(rmse, 3)}

    model.save(MODELS_DIR / "lstm_forecast.keras")
    joblib.dump(scaler, MODELS_DIR / "forecast_scaler.pkl")
    with open(MODELS_DIR / "lstm_forecast_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"LSTM Forecast | MAPE:{mape:.2f}% RMSE:{rmse:.2f}")
    return model, metrics


def predict_next_72h(seed_series: np.ndarray = None) -> np.ndarray:
    """
    Predict next 72 hours using rolling forecast.
    seed_series: last LOOKBACK hours of actual data.
    """
    model  = tf.keras.models.load_model(MODELS_DIR / "lstm_forecast.keras")
    scaler = joblib.load(MODELS_DIR / "forecast_scaler.pkl")

    if seed_series is None:
        seed_series = _load_power_series()[-LOOKBACK:]

    scaled_seed = scaler.transform(seed_series.reshape(-1,1)).flatten()
    window      = list(scaled_seed)
    predictions = []

    for _ in range(72):
        X    = np.array(window[-LOOKBACK:]).reshape(1, LOOKBACK, 1)
        pred = model.predict(X, verbose=0)[0][0]
        predictions.append(pred)
        window.append(pred)

    result = scaler.inverse_transform(
        np.array(predictions).reshape(-1,1)).flatten().clip(0, 2000)
    return result


if __name__ == "__main__":
    MODELS_DIR.mkdir(exist_ok=True)
    model, metrics = train()
    forecast = predict_next_72h()
    print(f"\nNext 72h LSTM forecast (first 5h): {forecast[:5]}")
    print(f"MAPE: {metrics['mape']}% | RMSE: {metrics['rmse']}")