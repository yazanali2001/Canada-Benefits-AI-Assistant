"""
One-off script to embed the benefits dataset into ChromaDB.
Run with: python -m backend.vector_db.ingest
"""

import json
import logging
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = Path("data/benefits.json")
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "canada_benefits"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

REQUIRED_FIELDS = [
    "id",
    "program_name",
    "category",
    "description",
    "eligibility_summary",
    "official_url",
]


def load_benefits(path: Path) -> list[dict[str, Any]]:
    """Load and validate the raw benefits dataset from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Benefits data file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    valid_records = []
    for i, record in enumerate(data):
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            logger.warning("Skipping record %s: missing fields %s", i, missing)
            continue
        valid_records.append(record)

    logger.info("Loaded %d valid records out of %d total.", len(valid_records), len(data))
    return valid_records


def build_document_text(record: dict[str, Any]) -> str:
    """Combine the relevant fields into one text blob for embedding."""
    return (
        f"Program: {record['program_name']}\n"
        f"Category: {record['category']}\n"
        f"Description: {record['description']}\n"
        f"Eligibility: {record['eligibility_summary']}"
    )


def ingest() -> None:
    """Embed all benefit records and store them in ChromaDB (idempotent)."""
    records = load_benefits(DATA_PATH)
    if not records:
        logger.error("No valid records to ingest. Aborting.")
        return

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    existing_count = collection.count()
    if existing_count > 0:
        logger.info(
            "Collection '%s' already has %d items. Skipping ingest "
            "(delete the chroma_db folder to force a rebuild).",
            COLLECTION_NAME, existing_count,
        )
        return

    model = SentenceTransformer(EMBEDDING_MODEL)

    documents = [build_document_text(r) for r in records]
    embeddings = model.encode(documents, show_progress_bar=True).tolist()
    ids = [r["id"] for r in records]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=records,
    )

    logger.info("Ingested %d benefit records into ChromaDB.", len(records))


if __name__ == "__main__":
    ingest()