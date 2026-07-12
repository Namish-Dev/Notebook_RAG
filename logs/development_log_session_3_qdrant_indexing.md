# AI Notes RAG System - Development Log

## Session 3: Integrating Qdrant & Completing the Indexing Pipeline

**Date:** 2026-07-03

## Session Goal

Today's objective was to integrate Qdrant into the project and complete
the document indexing pipeline.

The project progressed from:

Chunk -\> Embedding

to:

Chunk -\> Embedding -\> Qdrant

------------------------------------------------------------------------

## Topics Learned

### Separation of Concerns

We redesigned the project so each file has a single responsibility.

-   main.py: orchestrates the workflow.
-   database.py: SQLite operations.
-   chunk.py: chunk generation.
-   embedding.py: embedding generation.
-   vector_store.py: all Qdrant operations.

This keeps the code maintainable and hides Qdrant implementation details
from the application workflow.

### Qdrant Point

A Qdrant Point contains:

-   Unique ID
-   Embedding Vector
-   Payload

The SQLite chunk ID was chosen as the Point ID because it is unique and
provides a direct mapping between SQLite and Qdrant.

### Payload

Payload stores metadata such as:

-   folder_id
-   file_id
-   chunk_index
-   title
-   chunk_text

The payload is not searched. Qdrant searches only vectors and returns
the payload of the nearest matches.

### Collections

A Qdrant Collection is equivalent to a SQL table.

The collection 'notes' was created using:

-   Vector size: 384
-   Distance metric: Cosine

------------------------------------------------------------------------

## Problems Faced

### 1. PointStruct not defined

Cause: PointStruct was being created inside main.py.

Solution: Moved all Qdrant-specific implementation into vector_store.py
and exposed a save_vector() function.

------------------------------------------------------------------------

### 2. No chunks were being stored

Initially it looked like a Qdrant issue.

Investigation showed the chunker expected \### headings while the
formatter generated \## headings.

Result:

No headings detected → No chunks → No embeddings → No vectors

Solution: Updated the chunking logic to support generic Markdown
headings.

------------------------------------------------------------------------

### 3. Empty Qdrant collection

Running client.scroll() returned an empty list.

Cause: Since chunking failed, nothing was inserted.

After fixing the chunker, vectors were successfully stored.

------------------------------------------------------------------------

### 4. Python shutdown warning

Observed:

ImportError: sys.meta_path is None

Explanation:

This warning occurs while Python is shutting down and cleaning up the
embedded Qdrant client. It is generally harmless during local
development.

------------------------------------------------------------------------

## Verification

Verified:

-   Collection created successfully.
-   Vectors stored successfully.
-   Payload stored correctly.
-   Point IDs match SQLite chunk IDs.
-   Vector size is 384.

Example:

ID: 6

Title: Categorical Index Creation

Vector length: 384

------------------------------------------------------------------------

## Architecture After Today's Session

Upload ↓ Gemini Vision ↓ Markdown ↓ SQLite Files ↓ Chunking ↓ SQLite
Chunks ↓ Embedding Generation ↓ Payload Creation ↓ save_vector() ↓
Qdrant

The document indexing pipeline is now complete.

------------------------------------------------------------------------

## Interview Notes

Why use SQLite chunk IDs as Qdrant Point IDs?

-   Unique
-   Auto-generated
-   Easy mapping between SQLite and Qdrant

Why store payload?

Vectors are searched. Payload is returned.

Why keep Qdrant logic in vector_store.py?

To separate application workflow from storage implementation.

------------------------------------------------------------------------

## Next Session

Implement the Retrieval Pipeline:

Question ↓ Question Embedding ↓ Qdrant Search ↓ Top-K Chunks ↓ Prompt
Construction ↓ Gemini Answer
