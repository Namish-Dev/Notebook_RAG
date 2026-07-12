
# AI Notes RAG System - Development Log
## Session 4: Retrieval Improvements & Semantic Chunking

**Date:** 2026-07-07

## Session Goal

Improve retrieval quality by replacing the regex heading chunker with an LLM-based semantic chunker.

## What Was Completed

- Retrieval pipeline implemented:
  - Question → Embedding → Qdrant → Top-K chunks
- Investigated retrieval quality.
- Designed the architecture for a Gemini-based semantic chunker.
- Created `semantic_chunker.py`.
- Designed the JSON schema for semantic chunks.

## Concepts Learned

### Why Retrieval Works

Question → Embedding → Qdrant compares vectors using cosine similarity → Top-K chunks are returned with their payload.

The embedding model converts both documents and questions into the same 384-dimensional vector space.

### Why Retrieval Was Inaccurate

The problem was not Qdrant.

The problem was the chunk quality.

Large chunks mixed several unrelated concepts, producing embeddings that represented an average meaning instead of a single topic.

### Semantic Chunking

Instead of splitting by Markdown headings, an LLM identifies independent concepts.

Benefits:

- Better chunk quality
- Better embeddings
- Better retrieval accuracy
- Better answers from the LLM

## Architecture Decision

Old:

Image
→ Gemini OCR
→ Markdown
→ Regex Chunking
→ Embeddings

New:

Image
→ Gemini OCR
→ Markdown
→ Gemini Semantic Chunker
→ Embeddings

## Problems Faced

### 1. Retrieval ranking

Relevant chunks were retrieved but not always ranked first because the chunks contained multiple concepts.

Decision:
Replace regex chunking with semantic chunking.

### 2. Deleting notes.db and qdrant_data repeatedly

After changing chunk boundaries and indexing logic, previously indexed data no longer matched the new pipeline.

Deleting both databases ensured SQLite and Qdrant were rebuilt consistently during development.

### 3. Forgot to import a function

A function was called before importing it into main.py.

Lesson:
Python only knows about functions that exist in the current module namespace.

### 4. Reused old code patterns

Some code was copied from existing modules without adapting it for the new semantic chunker.

Lesson:
Each module should be designed independently instead of assuming copied code will always work.

### 5. Gemini API key error

Error:

ValueError: No API key was provided

Reason:

`semantic_chunker.py` created a Gemini client using `os.getenv("Gemini_API_KEY")`, but `.env` had never been loaded in that module.

Therefore:

Gemini_API_KEY = None

The correct solution is to either call `load_dotenv()` before reading environment variables or centralize the Gemini client in a shared module and import it everywhere.

### 6. Worrying about free Gemini credits

A practical concern today was consuming free API credits while features were still incomplete.

Lesson:

Build one stage at a time and verify it before making additional API calls.

### 7. Current stopping point

Current error:

TypeError: string indices must be integers

Reason:

The semantic chunker currently returns raw text.

The embedding pipeline expects:

- chunk_index
- title
- chunk_text

The next step will be to parse Gemini's JSON into Python dictionaries before reconnecting the embedding pipeline.

## Personal Reflection

Today's session was the most frustrating so far.

Main reasons:

- Calling functions before importing them.
- Accidentally reusing old implementation patterns.
- Rebuilding SQLite and Qdrant repeatedly after architectural changes.
- Concern about exhausting the free Gemini quota.
- Debugging environment variable loading across multiple modules.
- Finishing the day with a JSON parsing issue.

Even though progress felt slow, these are normal engineering problems that appear when a project evolves from a simple script into a modular application.

## Current Status

Completed:

- OCR
- Markdown generation
- SQLite storage
- Heading chunking
- Embeddings
- Qdrant indexing
- Semantic retrieval

In Progress:

- LLM semantic chunking
- JSON parsing
- Final RAG prompt construction

Next Session:

Gemini Semantic Chunker
→ JSON Parsing
→ Embeddings
→ SQLite
→ Qdrant
→ Gemini Answer
