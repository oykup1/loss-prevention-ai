"""
embed.py
--------
Converts text chunks into vectors using Google's gemini-embedding-001 model
via the Gemini Enterprise Agent Platform.

Requires these environment variables to be set:
    GOOGLE_CLOUD_PROJECT=your-project-id
    GOOGLE_CLOUD_LOCATION=global
    GOOGLE_GENAI_USE_ENTERPRISE=True

Install: pip install google-genai
"""

import os
import time
from google import genai
from google.genai import types


# ── Constants ──────────────────────────────────────────────────────────────────
MODEL         = "gemini-embedding-001"
DIMENSIONS    = 768    # We use 768 instead of the full 3072 — good balance
                       # of quality vs storage size for this project
BATCH_SIZE    = 20     # How many texts to send per API call
                       # Keeps requests small and avoids rate limits


def get_client():
    """
    Creates and returns a Gen AI client connected to Vertex AI.
    Uses your gcloud Application Default Credentials.
    """
    os.environ["GOOGLE_CLOUD_PROJECT"]      = "studied-client-412623"
    os.environ["GOOGLE_CLOUD_LOCATION"]     = "global"
    os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"
    
    return genai.Client(
        vertexai=True,
        project="studied-client-412623",
        location="global",
    )


def embed_chunks(chunks, task_type="RETRIEVAL_DOCUMENT"):
    """
    Takes a list of chunks from chunk.py and returns a list of vectors.

    Each chunk looks like:
        {"text": "Incident: ...", "metadata": {...}}

    Returns a list of vectors in the same order as the input chunks.
    Each vector is a list of 768 numbers.

    task_type options:
        "RETRIEVAL_DOCUMENT" — use when indexing documents (building the index)
        "RETRIEVAL_QUERY"    — use when embedding a search query
    """
    client  = get_client()
    texts   = [chunk["text"] for chunk in chunks]
    vectors = []

    # Process in batches to avoid hitting API rate limits
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]

        response = client.models.embed_content(
            model=MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=DIMENSIONS,
            ),
        )

        for embedding in response.embeddings:
            vectors.append(embedding.values)

        # Small pause between batches to be respectful of rate limits
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)

        print(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks...")

    return vectors


def embed_query(query_text):
    """
    Embeds a single search query.
    Uses RETRIEVAL_QUERY task type — optimized for queries, not documents.
    Called by search.py when an LP manager asks a question.
    """
    client   = get_client()
    response = client.models.embed_content(
        model=MODEL,
        contents=[query_text],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=DIMENSIONS,
        ),
    )
    return response.embeddings[0].values


# ── Test ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing embed.py with 2 sample chunks...\n")

    sample_chunks = [
        {
            "text": "Incident: Subject concealed scarves from accessories wall. Outcome: Subject fled before approach.",
            "metadata": {"report_id": "TEST001", "zone": "accessories"}
        },
        {
            "text": "Crime Report: Organized retail crime activity increased in Q1 targeting accessories and beauty departments.",
            "metadata": {"source": "crime_reports", "quarter": "Q1"}
        },
    ]

    vectors = embed_chunks(sample_chunks)

    print(f"\n✓ Got {len(vectors)} vectors")
    print(f"✓ Each vector has {len(vectors[0])} dimensions")
    print(f"✓ First 5 values of vector 1: {vectors[0][:5]}")

    print("\nTesting embed_query...")
    q_vector = embed_query("incidents near the accessories wall")
    print(f"✓ Query vector has {len(q_vector)} dimensions")
    print("\nembed.py working correctly.")