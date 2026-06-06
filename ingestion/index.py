"""
index.py
--------
Builds FAISS indexes for incident reports and crime reports.
Saves two files per index:
    *.faiss       — the vector index (what FAISS searches)
    *_meta.json   — chunk text and metadata (what we return to the agent)

Run once after generating mock data:
    python ingestion/index.py

Output goes to indexes/ folder.
"""

import json
import os
import numpy as np
import faiss

from chunk import load_incidents, load_crime_reports
from embed import embed_chunks


# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR    = os.path.join(BASE_DIR, "data")
INDEX_DIR   = os.path.join(BASE_DIR, "indexes")


def build_index(chunks, vectors):
    """
    Takes chunks and their corresponding vectors.
    Builds a FAISS IndexFlatIP index (inner product / cosine similarity).
    Returns the index and the metadata list.

    IndexFlatIP is exact search — finds the true nearest neighbors.
    Fine for 69 chunks. At 100k+ chunks you'd switch to IndexIVFFlat.
    """
    dimension = len(vectors[0])
    
    # Convert to numpy array — FAISS requires float32
    vector_array = np.array(vectors, dtype=np.float32)
    
    # Normalize vectors for cosine similarity
    faiss.normalize_L2(vector_array)
    
    # Build index
    index = faiss.IndexFlatIP(dimension)
    index.add(vector_array)
    
    # Metadata list — position matches vector position in index
    metadata = [
        {
            "text":     chunk["text"],
            "metadata": chunk["metadata"],
        }
        for chunk in chunks
    ]
    
    return index, metadata


def save_index(index, metadata, name):
    """
    Saves the FAISS index and metadata to the indexes/ folder.
    name: "incidents" or "crime"
    """
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    faiss_path = os.path.join(INDEX_DIR, f"{name}.faiss")
    meta_path  = os.path.join(INDEX_DIR, f"{name}_meta.json")
    
    faiss.write_index(index, faiss_path)
    
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  ✓ Saved {name}.faiss ({index.ntotal} vectors)")
    print(f"  ✓ Saved {name}_meta.json ({len(metadata)} entries)")


def build_incidents_index():
    print("\nBuilding incidents index...")
    chunks  = load_incidents(os.path.join(DATA_DIR, "incidents.jsonl"))
    print(f"  Loaded {len(chunks)} incident chunks")
    
    print("  Embedding chunks via Vertex AI...")
    vectors = embed_chunks(chunks, task_type="RETRIEVAL_DOCUMENT")
    
    index, metadata = build_index(chunks, vectors)
    save_index(index, metadata, "incidents")


def build_crime_index():
    print("\nBuilding crime reports index...")
    chunks  = load_crime_reports(os.path.join(DATA_DIR, "crime_reports"))
    print(f"  Loaded {len(chunks)} crime report chunks")
    
    print("  Embedding chunks via Vertex AI...")
    vectors = embed_chunks(chunks, task_type="RETRIEVAL_DOCUMENT")
    
    index, metadata = build_index(chunks, vectors)
    save_index(index, metadata, "crime")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Building FAISS indexes...")
    print(f"Reading from: {os.path.abspath(DATA_DIR)}")
    print(f"Saving to:    {os.path.abspath(INDEX_DIR)}")
    
    build_incidents_index()
    build_crime_index()
    
    print("\n✓ All indexes built successfully.")
    print("  The application will load these indexes at startup.")
    print("  Re-run this script only if incident data changes.\n")