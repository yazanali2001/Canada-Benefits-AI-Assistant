"""
Semantic search over the ingested benefits collection.
"""

import logging
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "canada_benefits"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Loaded once at import time — reused across requests instead of
# reloading the model/collection on every chat message.
_client = chromadb.PersistentClient(path=CHROMA_DIR)
_model = SentenceTransformer(EMBEDDING_MODEL)

try:
    _collection = _client.get_collection(name=COLLECTION_NAME)
except Exception:
    logger.error(
        "ChromaDB collection '%s' not found. Run "
        "python -m backend.vector_db.ingest first.",
        COLLECTION_NAME,
    )
    raise


def search_benefits(query: str, n_results: int = 3) -> list[dict[str, Any]]:
    """
    Return the top-N benefit programs most semantically relevant to the query.

    Args:
        query: The user's free-text message.
        n_results: How many results to return.

    Returns:
        A list of benefit metadata dicts (program_name, description, etc).
        Returns an empty list if the search fails, so the caller can
        degrade gracefully instead of crashing.
    """
    try:
        embedding = _model.encode(query).tolist()
        results = _collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
        )
        return results.get("metadatas", [[]])[0]
    except Exception:
        logger.exception("Vector search failed for query: %s", query)
        return []