"""Load and chunk all documents for RAG indexing."""

from pathlib import Path
from typing import List, Dict
from loguru import logger
import pypdf

RAG_DOCS = Path("data/rag_docs")
CHUNK_SIZE    = 500   # characters
CHUNK_OVERLAP = 100


def load_pdfs() -> List[Dict]:
    """Extract text from all PDFs in rag_docs."""
    chunks = []
    for pdf_path in RAG_DOCS.glob("*.pdf"):
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            full_text = ""
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                full_text += f"\n[Page {page_num+1}]\n{text}"

            doc_chunks = _chunk_text(full_text, str(pdf_path.name))
            chunks.extend(doc_chunks)
            logger.info(f"PDF loaded: {pdf_path.name} → {len(doc_chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to load {pdf_path.name}: {e}")
    return chunks


def load_csv_logs() -> List[Dict]:
    """Convert maintenance logs CSV to text chunks."""
    import pandas as pd
    chunks = []
    csv_path = RAG_DOCS / "maintenance_logs.csv"
    if not csv_path.exists():
        logger.warning("maintenance_logs.csv not found in rag_docs")
        return chunks

    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        text = (
            f"Fault Log {row.get('log_id','')}: "
            f"Turbine {row.get('turbine_id','')} on {row.get('date','')}. "
            f"Fault: {row.get('fault_type','')}. "
            f"Severity: {row.get('severity','')}. "
            f"Action: {row.get('action_taken','')}. "
            f"Downtime: {row.get('downtime_hours','')}h. "
            f"Cost: ${row.get('repair_cost_usd','')}. "
            f"Resolution: {row.get('resolution','')}."
        )
        chunks.append({
            "text"    : text,
            "source"  : "maintenance_logs.csv",
            "doc_type": "fault_log",
            "metadata": row.to_dict(),
        })

    logger.info(f"CSV logs loaded: {len(chunks)} records")
    return chunks


def _chunk_text(text: str, source: str) -> List[Dict]:
    """Split text into overlapping chunks."""
    chunks = []
    start  = 0
    while start < len(text):
        end   = start + CHUNK_SIZE
        chunk = text[start:end]
        if chunk.strip():
            chunks.append({
                "text"    : chunk.strip(),
                "source"  : source,
                "doc_type": "manual",
                "metadata": {"start_char": start, "end_char": end},
            })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def load_all() -> List[Dict]:
    """Load all documents — PDFs + CSV logs."""
    all_chunks = []
    all_chunks.extend(load_pdfs())
    all_chunks.extend(load_csv_logs())
    logger.info(f"Total chunks loaded: {len(all_chunks)}")
    return all_chunks


if __name__ == "__main__":
    chunks = load_all()
    print(f"Total chunks: {len(chunks)}")
    print(f"Sample chunk:\n{chunks[0]['text'][:200]}")