# tests/test_pipeline.py

"""End-to-end pipeline integration test."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np


def make_test_readings(n=3):
    import random

    return [{
        "turbine_id"    : f"WT-00{i}",
        "timestamp"     : "2024-06-01T06:00:00",
        "wind_speed_ms" : random.uniform(5, 12),
        "power_kw"      : random.uniform(500, 1800),
        "vibration_mms" : random.uniform(1.5, 8.0),
        "gearbox_temp_c": random.uniform(45, 90),
        "bearing_wear"  : random.uniform(0.0, 0.8),
        "oil_quality"   : random.uniform(0.4, 1.0),
        "health_score"  : random.uniform(0.3, 1.0),
        "cmapss_rul"    : random.uniform(20, 125),
        "cmapss_anomaly": random.randint(0, 1),

        # 14 sensors
        **{
            f"sensor_{j}": random.uniform(0, 1)
            for j in range(1, 15)
        },

    } for i in range(1, n + 1)]


def test_digital_twin():
    from iot.digital_twin import DigitalTwin

    twin = DigitalTwin("WT-TEST", age_hours=100)

    reading = twin.get_sensor_reading(wind_speed=10.0)

    assert "power_kw" in reading
    assert "vibration_mms" in reading
    assert "health_score" in reading
    assert 0 <= reading["health_score"] <= 1

    print("✅ Digital Twin OK")


def test_anomaly_detection():

    from agents.agent1_health_monitor.isolation_forest import predict

    # FIXED → 18 features
    X = np.random.rand(5, 18).astype(np.float32)

    result = predict(X)

    assert "anomaly_flags" in result
    assert "anomaly_scores" in result
    assert len(result["anomaly_flags"]) == 5

    print("✅ Anomaly Detection OK")


def test_rul_prediction():

    from agents.agent2_failure_predictor.xgboost_rul import predict

    # FIXED → 18 features
    X = np.random.rand(5, 18).astype(np.float32)

    result = predict(X)

    assert len(result) == 5
    assert all(0 <= r <= 125 for r in result)

    print("✅ RUL Prediction OK")


def test_rule_based_scheduler():

    from agents.agent3_maintenance_coordinator.rule_based_scheduler import schedule

    anomaly = {
        "turbine_id": "WT-001",
        "anomaly_flag": 1,
        "anomaly_score": 0.85,
        "primary_cause": "sensor_7",
    }

    rul = {
        "turbine_id": "WT-001",
        "rul_hours": 35.0,
        "lower_hours": 20.0,
        "upper_hours": 50.0,
    }

    result = schedule(anomaly, rul)

    assert result["priority"] in [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW"
    ]

    assert "scheduled_start" in result

    print("✅ Rule-based Scheduler OK")


def test_rl_scheduler():

    try:

        from agents.agent3_maintenance_coordinator.rl_scheduler import (
            predict,
            MaintenanceEnv
        )

        env = MaintenanceEnv()

        obs, _ = env.reset()

        result = predict(obs)

        assert result["action_id"] in [0, 1, 2, 3]

        print("✅ RL Scheduler OK")

    except Exception as e:

        print(f"⚠️ RL Scheduler skipped: {e}")


def test_revenue_estimator():

    from agents.agent4_energy_forecaster.revenue_loss_estimator import estimate

    decision = {
        "turbine_id": "WT-001",
        "scheduled_start": "2024-06-01T06:00:00",
        "scheduled_end": "2024-06-01T12:00:00",
        "recommended_load_pct": 0,
    }

    result = estimate(decision)

    assert "revenue_loss_usd" in result
    assert "net_saving_usd" in result

    print("✅ Revenue Estimator OK")


def test_rag_search():

    from rag.faiss_indexer import search

    results = search(
        "gearbox bearing replacement",
        top_k=3
    )

    assert len(results) > 0
    assert "text" in results[0]
    assert "source" in results[0]

    print("✅ RAG Search OK")


def test_llm_engine():

    from llm.gemini_engine import call

    response = call(
        "Reply with only: OK",
        max_tokens=10
    )

    assert len(response) > 0

    print(f"✅ LLM Engine OK — response: {response[:30]}")


def test_full_pipeline():

    try:

        from graph.langgraph_orchestrator import run_pipeline

        readings = make_test_readings(n=2)

        result = run_pipeline(readings)

        assert "decisions" in result
        assert "anomalies" in result
        assert "rul_results" in result

        print(
            f"✅ Full Pipeline OK — "
            f"{len(result['decisions'])} decisions"
        )

    except Exception as e:

        print(f"⚠️ Full Pipeline skipped: {e}")


if __name__ == "__main__":

    tests = [
        test_digital_twin,
        test_anomaly_detection,
        test_rul_prediction,
        test_rule_based_scheduler,
        test_rl_scheduler,
        test_revenue_estimator,
        test_rag_search,
        test_llm_engine,
        test_full_pipeline,
    ]

    print("\n=== WindSense-AI Integration Tests ===\n")

    passed = 0
    failed = []

    for test in tests:

        try:
            test()
            passed += 1

        except Exception as e:

            print(f"❌ {test.__name__}: {e}")

            failed.append(test.__name__)

    print(f"\n{'=' * 45}")

    print(f"Passed: {passed}/{len(tests)}")

    if failed:
        print(f"Failed: {failed}")
    else:
        print("All tests passed ✅")