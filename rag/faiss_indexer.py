"""FAISS Indexer — sentence-transformers only, no LangChain."""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import json
import numpy as np
from pathlib import Path
from typing import List, Dict
import faiss
import pickle
from loguru import logger

MODELS_DIR  = Path("outputs/models")
INDEX_PATH  = MODELS_DIR / "faiss_index.bin"
CHUNKS_PATH = MODELS_DIR / "faiss_chunks.pkl"


def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def build_index(chunks: List[Dict], batch_size: int = 50, **kwargs):
    MODELS_DIR.mkdir(exist_ok=True)
    model = _get_model()
    texts = [c["text"] for c in chunks]

    logger.info(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, batch_size=batch_size,
                               show_progress_bar=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    meta = {
        "n_chunks"     : len(chunks),
        "embedding_dim": int(embeddings.shape[1]),
        "embedder"     : "all-MiniLM-L6-v2",
    }
    with open(MODELS_DIR / "faiss_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    logger.success(f"FAISS index built | {len(chunks)} chunks | dim={embeddings.shape[1]}")
    return index, chunks


def load_index():
    if not INDEX_PATH.exists():
        raise FileNotFoundError("Run python -m rag.faiss_indexer first")
    index = faiss.read_index(str(INDEX_PATH))
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def search(query: str, top_k: int = 5) -> List[Dict]:
    index, chunks = load_index()
    model  = _get_model()
    q_vec  = model.encode([query], show_progress_bar=False).astype(np.float32)
    faiss.normalize_L2(q_vec)
    scores, indices = index.search(q_vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(chunks):
            results.append({**chunks[idx],
                             "similarity_score": round(float(score), 4)})
    return results


if __name__ == "__main__":
    from rag.document_ingestion import load_all
    chunks = load_all()
    build_index(chunks)
    print("\nTest search:")
    results = search("gearbox bearing replacement", top_k=3)
    for r in results:
        print(f"  [{r['similarity_score']:.4f}] {r['source']}: {r['text'][:80]}...")