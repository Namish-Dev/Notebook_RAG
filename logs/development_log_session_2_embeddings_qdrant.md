# AI Notes RAG System - Development Log

## Session: Embeddings & Introduction to Qdrant

**Date:** 2026-07-01

## Objective

Today's goal was to move the project from a document ingestion system
toward a true Retrieval-Augmented Generation (RAG) architecture.

By the end of the session the project can:

-   Generate embeddings for every chunk.
-   Create a local Qdrant database.
-   Create a Qdrant collection.
-   Prepare payloads and unique IDs for vector storage.

The retrieval stage has **not** been implemented yet.

------------------------------------------------------------------------

# 1. Virtual Environment

## Problem

While importing `SentenceTransformer`, the project raised:

``` text
ModuleNotFoundError: Could not import module 'PreTrainedModel'
```

## Cause

The global Python environment had incompatible package versions. Python
3.13 also caused compatibility concerns.

## Solution

Created a dedicated Python 3.10 virtual environment and installed
project dependencies inside it.

------------------------------------------------------------------------

# 2. Embedding Model

Selected model:

``` python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
```

Wrapper function:

``` python
def generate_embedding(text):
    embedding = model.encode(
        text,
        normalize_embeddings=True
    )
    return embedding.tolist()
```

------------------------------------------------------------------------

# 3. Embedding Verification

Created a standalone script to ensure the model worked independently of
Streamlit.

Verified:

-   Output type: list
-   Embedding size: 384
-   Embeddings successfully generated

This confirmed the embedding model itself was functioning correctly.

------------------------------------------------------------------------

# 4. Chunking Bug

## Problem

Embeddings were not appearing.

## Investigation

The issue was not the embedding model.

The prompt had changed and Markdown headings were no longer being
generated.

Since the chunker relied on headings, no chunks were produced.

No chunks meant no embeddings.

## Solution

Adjusted the prompt so headings were generated consistently.

Chunking resumed successfully.

------------------------------------------------------------------------

# 5. Learning Qdrant

Concepts studied:

-   Vector databases
-   Collections
-   Payloads
-   Cosine similarity
-   Vector dimensions
-   Why embeddings are searched instead of text
-   Why metadata is stored with vectors

------------------------------------------------------------------------

# 6. Local Qdrant

Instead of Docker, embedded mode was chosen.

``` python
from qdrant_client import QdrantClient

client = QdrantClient(path="qdrant_data")
```

Reason:

-   Easier development
-   Local persistence
-   No Docker required

------------------------------------------------------------------------

# 7. Creating the Collection

``` python
from qdrant_client.models import Distance, VectorParams

if not client.has_collection("notes"):
    client.create_collection(
        collection_name="notes",
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )
```

Learned:

-   Collection name
-   Vector size
-   Distance metric
-   Idempotent creation

------------------------------------------------------------------------

# 8. Payload Design

Created:

``` python
payload = {
    "folder_id": folder_id,
    "file_id": file_id,
    "chunk_index": chunk_data["chunk_index"],
    "title": chunk_data["title"],
    "chunk_text": chunk_data["chunk_text"],
}
```

Purpose:

Payload stores metadata that is returned after vector search.

------------------------------------------------------------------------

# 9. Point ID Decision

Several possibilities were considered.

Rejected:

-   file_id
-   chunk_index

Chosen:

SQLite `chunks.id`

Reason:

-   Unique
-   Auto-generated
-   Maps directly between SQLite and Qdrant

------------------------------------------------------------------------

# 10. save_chunk()

Modified from:

``` python
def save_chunk(...):
    cursor.execute(...)
    conn.commit()
```

to:

``` python
def save_chunk(...):
    cursor.execute(...)

    chunk_id = cursor.lastrowid

    conn.commit()

    return chunk_id
```

This allows every inserted chunk to immediately obtain its unique
database ID.

------------------------------------------------------------------------

# Current Pipeline

``` text
Upload
    │
    ▼
Gemini Vision
    │
    ▼
Markdown
    │
    ▼
SQLite Files
    │
    ▼
Chunking
    │
    ▼
SQLite Chunks
    │
    ▼
Generate Embedding
    │
    ▼
Create Payload
```

Qdrant insertion is the next milestone.

------------------------------------------------------------------------

# Next Session

Implement:

``` text
Qdrant upsert()

↓

Point ID

+

Embedding

+

Payload

↓

Vector stored successfully

↓

Similarity search
```
