"""
search.py
---------
Retrieves relevant chunks from FAISS indexes given a natural language query.
Called by the agent layer to find relevant incident reports or crime data.

This file ONLY retrieves — it does not generate answers.

Usage:
    from retrieval.search import search
    results = search("incidents near the accessories wall", index_name="incidents", k=5)
"""

import json
import os
import sys
import numpy as np
import faiss

# Add ingestion to path so we can import embed_query
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from embed import embed_query


# ── Paths ──────────────────────────────────────────────────────────────────────
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "indexes")

# ── Index cache — load once, reuse every search ────────────────────────────────
_index_cache = {}
_meta_cache  = {}


def _load_index(index_name):
    """
    Loads a FAISS index and its metadata from disk.
    Caches in memory so subsequent searches don't reload from disk.
    """
    if index_name not in _index_cache:
        faiss_path = os.path.join(INDEX_DIR, f"{index_name}.faiss")
        meta_path  = os.path.join(INDEX_DIR, f"{index_name}_meta.json")

        if not os.path.exists(faiss_path):
            raise FileNotFoundError(
                f"Index '{index_name}' not found at {faiss_path}. "
                f"Run ingestion/index.py first."
            )

        _index_cache[index_name] = faiss.read_index(faiss_path)

        with open(meta_path) as f:
            _meta_cache[index_name] = json.load(f)

    return _index_cache[index_name], _meta_cache[index_name]


def search(question, index_name="incidents", k=5):
    """
    Searches the specified index for chunks relevant to the question.

    Steps:
        1. Embed the question using embed_query (RETRIEVAL_QUERY task type)
        2. Normalize the query vector for cosine similarity
        3. Search FAISS for top-k nearest vectors
        4. Return matching chunks with text, metadata, and similarity score

    Args:
        question:   Natural language query string
        index_name: "incidents" or "crime"
        k:          Number of results to return (default 5)

    Returns:
        List of dicts, each containing:
            - text:     The chunk text
            - metadata: Report metadata (zone, date, shift, etc.)
            - score:    Similarity score (0-1, higher is more relevant)
    """
    # Step 1 — embed the question
    query_vector = embed_query(question)

    # Step 2 — convert to numpy float32 and normalize
    query_array = np.array([query_vector], dtype=np.float32)
    faiss.normalize_L2(query_array)

    # Step 3 — load index and search
    index, metadata = _load_index(index_name)
    scores, positions = index.search(query_array, k)

    # Step 4 — build results
    results = []
    for score, position in zip(scores[0], positions[0]):
        if position == -1:
            # FAISS returns -1 when fewer results exist than k
            continue
        results.append({
            "text":     metadata[position]["text"],
            "metadata": metadata[position]["metadata"],
            "score":    round(float(score), 4),
        })

    return results


def search_both(question, k=3):
    """
    Searches both indexes and returns combined results.
    Useful when the agent doesn't know which index is more relevant.
    Returns k results from each index, labeled by source.
    """
    incident_results = search(question, index_name="incidents", k=k)
    crime_results    = search(question, index_name="crime",     k=k)

    return {
        "incidents": incident_results,
        "crime":     crime_results,
    }


