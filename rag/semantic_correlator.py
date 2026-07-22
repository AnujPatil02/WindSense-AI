"""Semantic Anomaly Correlator — pure FAISS, no LangChain."""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from typing import Dict, List
from loguru import logger


def correlate(anomaly: Dict) -> Dict:
    from rag.faiss_indexer import search

    cause    = anomaly.get("primary_cause", "sensor anomaly")
    score    = anomaly.get("anomaly_score", 0.0)
    sensors  = [s["sensor"] for s in anomaly.get("top_sensors", [])[:2]]
    severity = "critical" if score > 0.8 else "moderate" if score > 0.6 else "low"
    sensor_str = " and ".join(sensors) if sensors else cause

    query = (
        f"{severity} anomaly on {sensor_str}. "
        f"Score {score:.2f}. Similar faults and repair procedures."
    )

    logger.info(f"Correlator query: {query[:80]}")
    results   = search(query, top_k=5)
    fault_logs = [r for r in results if r.get("doc_type") == "fault_log"]
    procedures = [r for r in results if r.get("doc_type") == "manual"]

    actions = []
    for log in fault_logs[:3]:
        meta = log.get("metadata", {})
        if "action_taken" in meta:
            actions.append({
                "fault_type": meta.get("fault_type", ""),
                "action"    : meta.get("action_taken", ""),
                "downtime_h": meta.get("downtime_hours", ""),
                "similarity": log["similarity_score"],
            })

    return {
        "turbine_id"         : anomaly.get("turbine_id"),
        "auto_query"         : query,
        "similar_faults"     : fault_logs[:3],
        "relevant_procedures": procedures[:2],
        "recommended_actions": actions,
        "n_results"          : len(results),
    }


def correlate_fleet(anomalies: List[Dict]) -> List[Dict]:
    flagged = [a for a in anomalies if a.get("anomaly_flag") == 1]
    results = []
    for anomaly in flagged:
        try:
            results.append(correlate(anomaly))
        except Exception as e:
            logger.error(f"Correlation failed for {anomaly.get('turbine_id')}: {e}")
    return results


if __name__ == "__main__":
    test = {
        "turbine_id": "WT-003", "anomaly_flag": 1,
        "anomaly_score": 0.87, "primary_cause": "sensor_7",
        "top_sensors": [{"sensor": "sensor_7", "contribution": 0.45}],
    }
    r = correlate(test)
    print(f"Query: {r['auto_query']}")
    print(f"Results: {r['n_results']}")