"""RAG Evaluation — no LangChain."""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
from pathlib import Path
from loguru import logger

REPORTS = Path("outputs/reports")

EVAL_PAIRS = [
    {"query": "gearbox bearing replacement procedure steps",
     "relevant_sources": ["gearbox_maintenance_manual.pdf"]},
    {"query": "oil analysis thresholds water content viscosity",
     "relevant_sources": ["gearbox_maintenance_manual.pdf"]},
    {"query": "bearing failure early warning vibration stage",
     "relevant_sources": ["bearing_failure_guide.pdf"]},
    {"query": "emergency shutdown procedure steps",
     "relevant_sources": ["safety_and_operations_manual.pdf"]},
    {"query": "maintenance window low wind schedule",
     "relevant_sources": ["safety_and_operations_manual.pdf"]},
]


def evaluate(top_k: int = 5) -> dict:
    from rag.faiss_indexer import search
    hits, mrr = 0, 0.0

    for pair in EVAL_PAIRS:
        results  = search(pair["query"], top_k=top_k)
        found_at = None
        for rank, r in enumerate(results, 1):
            if any(rel in r["source"] for rel in pair["relevant_sources"]):
                found_at = rank
                break
        if found_at:
            hits += 1
            mrr  += 1.0 / found_at

    hit_rate  = hits / len(EVAL_PAIRS)
    mrr_score = mrr  / len(EVAL_PAIRS)

    metrics = {
        "n_queries": len(EVAL_PAIRS),
        "hit_at_k" : round(hit_rate, 4),
        "mrr"      : round(mrr_score, 4),
        "top_k"    : top_k,
        "embedder" : "sentence-transformers/all-MiniLM-L6-v2",
    }

    REPORTS.mkdir(exist_ok=True)
    with open(REPORTS / "rag_evaluation.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n=== RAG Evaluation (top-{top_k}) ===")
    print(f"  Hit@{top_k} : {hit_rate:.4f} ({hits}/{len(EVAL_PAIRS)})")
    print(f"  MRR       : {mrr_score:.4f}")
    logger.success(f"RAG eval | Hit@{top_k}={hit_rate:.3f} MRR={mrr_score:.3f}")
    return metrics


if __name__ == "__main__":
    evaluate(top_k=5)