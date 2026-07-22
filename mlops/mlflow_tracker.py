"""MLflow Tracking — local file-based, no server needed."""

import mlflow
import json
from pathlib import Path
from loguru import logger

# Force local file storage BEFORE any mlflow calls
MLRUNS_DIR = Path("mlruns").absolute()
mlflow.set_tracking_uri(f"file:///{MLRUNS_DIR}")


def log_agent1_experiment(metrics: dict, params: dict = None):
    try:
        mlflow.set_experiment("Agent1_AnomalyDetection")
        with mlflow.start_run(run_name=metrics.get("model","unknown")):
            if params:
                mlflow.log_params(params)
            mlflow.log_metrics({
                "precision": float(metrics.get("precision", 0)),
                "recall"   : float(metrics.get("recall", 0)),
                "f1"       : float(metrics.get("f1", 0)),
                "fpr"      : float(metrics.get("fpr", 0)),
            })
        logger.success(f"MLflow Agent1: {metrics.get('model')} F1={metrics.get('f1')}")
    except Exception as e:
        logger.warning(f"MLflow Agent1 log failed: {e}")


def log_agent2_experiment(metrics: dict, params: dict = None):
    try:
        mlflow.set_experiment("Agent2_RULEstimation")
        with mlflow.start_run(run_name=metrics.get("model","unknown")):
            if params:
                mlflow.log_params(params)
            mlflow.log_metrics({
                "rmse": float(metrics.get("rmse", 0)),
                "mae" : float(metrics.get("mae", 0)),
                "r2"  : float(metrics.get("r2", 0)),
            })
        logger.success(f"MLflow Agent2: {metrics.get('model')} RMSE={metrics.get('rmse')}")
    except Exception as e:
        logger.warning(f"MLflow Agent2 log failed: {e}")


def log_pipeline_run(decisions: list, run_id: str):
    try:
        mlflow.set_experiment("WindSense_Pipeline")
        with mlflow.start_run(run_name=f"pipeline_{run_id}"):
            critical   = sum(1 for d in decisions if d.get("priority") == "CRITICAL")
            total_loss = sum(d.get("revenue_loss_usd", 0) for d in decisions)
            mlflow.log_metrics({
                "n_turbines"        : len(decisions),
                "critical_count"    : critical,
                "total_revenue_loss": total_loss,
            })
        logger.success(f"MLflow pipeline run logged: {run_id}")
    except Exception as e:
        logger.warning(f"MLflow pipeline log failed: {e}")


if __name__ == "__main__":
    reports = Path("outputs/reports")

    a1 = reports / "agent1_model_comparison.json"
    if a1.exists():
        with open(a1) as f:
            data = json.load(f)
        for m in data.get("models", []):
            log_agent1_experiment(m)

    a2 = reports / "agent2_model_comparison.json"
    if a2.exists():
        with open(a2) as f:
            data = json.load(f)
        for m in data.get("models", []):
            log_agent2_experiment(m)

    print(f"✅ MLflow logged to: {MLRUNS_DIR}")
    print(f"View: mlflow ui --backend-store-uri {MLRUNS_DIR}")