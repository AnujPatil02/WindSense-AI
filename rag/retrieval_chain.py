"""RAG Retrieval — pure FAISS + sentence-transformers + Ollama. No LangChain."""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from pathlib import Path
from typing import Dict
from loguru import logger

PROMPT = """You are WindSense-AI, expert wind turbine maintenance assistant.
Use ONLY the context below. Cite source document when possible.
If answer not in context, say so clearly.

Context:
{context}

Question: {question}

Answer:"""


def _ollama_call(prompt: str) -> str:
    import ollama
    try:
        r = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1, "num_predict": 500},
        )
        return r["message"]["content"].strip()
    except Exception:
        try:
            r = ollama.generate(
                model="llama3.2:3b", prompt=prompt,
                options={"temperature": 0.1, "num_predict": 500},
            )
            return r["response"].strip()
        except Exception as e:
            return f"LLM unavailable: {e}"


def query(question: str) -> Dict:
    from rag.faiss_indexer import search
    results = search(question, top_k=4)
    context = "\n\n".join([r["text"] for r in results])
    sources = [{"source": r["source"], "excerpt": r["text"][:120]}
               for r in results]
    prompt  = PROMPT.format(context=context, question=question)
    answer  = _ollama_call(prompt)
    return {"question": question, "answer": answer, "sources": sources}


if __name__ == "__main__":
    qs = [
        "What is the procedure for replacing a gearbox bearing?",
        "What are the oil analysis thresholds?",
    ]
    for q in qs:
        r = query(q)
        print(f"\nQ: {q}\nA: {r['answer'][:300]}")
        print(f"Sources: {[s['source'] for s in r['sources']]}")