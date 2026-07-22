"""Prophet Energy Generation Forecast — Agent 4"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from prophet import Prophet
import joblib
from loguru import logger

PROCESSED  = Path("data/processed")
MODELS_DIR = Path("outputs/models")
REPORTS    = Path("outputs/reports")


def prepare_prophet_data(csv_path: Path) -> pd.DataFrame:
    """Convert wind SCADA data to Prophet format (ds, y)."""
    df = pd.read_csv(csv_path)

    # Find timestamp and power columns
    ts_col    = next((c for c in df.columns if "time" in c or "date" in c), df.columns[0])
    power_col = next((c for c in df.columns if "power" in c.lower()), None)

    if power_col is None:
        raise ValueError("No power column found in wind SCADA data")

    prophet_df = pd.DataFrame({
        "ds": pd.to_datetime(
            df[ts_col],
            dayfirst=True,
            errors="coerce"
        ),
        "y" : df[power_col].clip(lower=0),
    }).dropna()

    # Resample to hourly if needed
    prophet_df = prophet_df.set_index("ds").resample("1h").mean().reset_index()
    prophet_df["y"] = prophet_df["y"].fillna(method="ffill").fillna(0)

    logger.info(f"Prophet data: {len(prophet_df)} hourly records")
    return prophet_df


def train():
    csv_path = PROCESSED / "wind_scada_processed.csv"
    if not csv_path.exists():
        logger.warning("Wind SCADA not found — generating synthetic data")
        prophet_df = _synthetic_wind_data()
    else:
        prophet_df = prepare_prophet_data(csv_path)

    # Split — last 20% for validation
    split_idx  = int(len(prophet_df) * 0.8)
    train_df   = prophet_df.iloc[:split_idx]
    val_df     = prophet_df.iloc[split_idx:]

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=True,
        changepoint_prior_scale=0.1,
        seasonality_prior_scale=10.0,
        interval_width=0.90,
    )
    model.fit(train_df)

    # Validate
    future   = model.make_future_dataframe(periods=len(val_df), freq="h")
    forecast = model.predict(future)
    val_pred = forecast.tail(len(val_df))["yhat"].values.clip(min=0)
    val_true = val_df["y"].values

    mape = float(np.mean(np.abs((val_true - val_pred) /
                                 (val_true + 1e-8))) * 100)
    rmse = float(np.sqrt(np.mean((val_true - val_pred) ** 2)))

    metrics = {"model": "Prophet", "mape": round(mape, 3), "rmse": round(rmse, 3)}
    logger.info(f"Prophet | MAPE: {mape:.2f}% | RMSE: {rmse:.2f}")

    joblib.dump(model, MODELS_DIR / "prophet_forecast.pkl")
    with open(MODELS_DIR / "prophet_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success("Prophet model saved.")
    return model, metrics


def predict_next_72h() -> pd.DataFrame:
    """Forecast next 72 hours of energy generation."""
    model    = joblib.load(MODELS_DIR / "prophet_forecast.pkl")
    future   = model.make_future_dataframe(periods=72, freq="h")
    forecast = model.predict(future)
    result   = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(72)
    result["yhat"]       = result["yhat"].clip(lower=0)
    result["yhat_lower"] = result["yhat_lower"].clip(lower=0)
    result["yhat_upper"] = result["yhat_upper"].clip(lower=0)
    return result


def _synthetic_wind_data() -> pd.DataFrame:
    """Realistic synthetic hourly wind power — 2MW turbine, ~35% CF."""
    import numpy as np
    periods = 8760
    dates   = pd.date_range("2023-01-01", periods=periods, freq="h")
    t       = np.arange(periods)
    np.random.seed(42)

    # Realistic wind speed: Weibull distribution mean ~7.5 m/s
    wind_speed = np.random.weibull(2.0, periods) * 8.5
    wind_speed = wind_speed.clip(0, 25)

    # Power curve: cubic between cut-in(3) and rated(12), flat above
    power = np.where(
        wind_speed < 3,  0,
        np.where(
            wind_speed < 12,
            2000 * ((wind_speed - 3) / 9) ** 3,
            np.where(wind_speed <= 25, 2000, 0)
        )
    ).clip(0, 2000)

    # Add realistic noise
    power += np.random.normal(0, 50, periods)
    power  = power.clip(0, 2000)

    cf = power.mean() / 2000
    print(f"Synthetic data CF: {cf:.1%}")   # Should be ~30-40%

    return pd.DataFrame({"ds": dates, "y": power})


if __name__ == "__main__":
    MODELS_DIR.mkdir(exist_ok=True)
    model, metrics = train()
    forecast = predict_next_72h()
    print(f"\nNext 72h forecast (sample):")
    print(forecast.head(5).to_string(index=False))
    print(f"\nMAPE: {metrics['mape']}% | RMSE: {metrics['rmse']}")