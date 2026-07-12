
# AI Notes RAG System – Development Log
## Session 5: Completing the Semantic RAG Pipeline

**Date:** 2026-07-08

## Session Objective

Replace heading-based chunking with Gemini semantic chunking and complete the end-to-end RAG pipeline.

## Final Architecture

```text
Image
  ↓
Gemini OCR
  ↓
Markdown
  ↓
Gemini Semantic Chunker
  ↓
Python List[dict]
  ↓
Embeddings (BGE)
  ↓
SQLite + Qdrant
  ↓
Question
  ↓
Question Embedding
  ↓
Qdrant Search
  ↓
Top-K Chunks
  ↓
RAG Prompt
  ↓
Gemini
  ↓
Answer
```

## Concepts Learned

### Why JSON?

Returning JSON gives structured data instead of plain text.

```python
import json
chunks = json.loads(response.text)
```

Now every chunk is a dictionary:

```python
chunk["title"]
chunk["chunk_text"]
chunk["keywords"]
```

### Why `json.loads()`?

Gemini always returns text.

`json.loads()` converts JSON text into Python objects.

Before:

```python
type(chunks)
# str
```

After:

```python
type(chunks)
# list

type(chunks[0])
# dict
```

### Why did `TypeError: string indices must be integers` happen?

Because the semantic chunker returned a string.

Your code expected:

```python
chunk["chunk_text"]
```

But Python was iterating over characters.

Parsing the JSON fixed the problem.

### Semantic Chunking

Old:

Heading → One large chunk

New:

Document → Independent concepts → Multiple focused chunks

Benefits:

- Better embeddings
- Better retrieval
- Better titles
- Better semantic search

### Retrieval

Question

↓

Embedding

↓

384-dimensional vector

↓

Qdrant compares vectors using cosine similarity

↓

Top-K chunks

↓

Payload returned

### Building Context

```python
context = ""

for i, result in enumerate(search_results, start=1):
    context += f"""
Chunk {i}

Title:
{result.payload['title']}

{result.payload['chunk_text']}
"""
```

### RAG Prompt

```python
rag_prompt = f"""
Retrieved Notes

{context}

Question

{question}
"""
```

### Final Answer

```python
answer = answer_question(rag_prompt)
st.markdown(answer)
```

## Interview Questions

### Why embeddings?

Embeddings convert text into vectors that capture meaning, enabling semantic retrieval.

### Why Qdrant?

SQLite stores metadata.

Qdrant stores vectors and performs nearest-neighbor search.

### Why semantic chunking?

Semantic chunking separates concepts by meaning rather than formatting, producing better retrieval.

### Why cosine similarity?

Cosine similarity measures how similar the direction of two vectors is.

### Why payload?

Payload stores metadata like title, chunk text, file id and folder id so it can be returned after retrieval.

### Why JSON?

JSON is structured, easy to validate and easy to convert into Python dictionaries.

## What I Can Explain Now

- Embeddings
- Sentence Transformers
- Vector dimensions
- Cosine similarity
- SQLite
- Qdrant
- Payloads
- Semantic search
- Semantic chunking
- Regex chunking
- JSON parsing
- RAG prompt construction
- End-to-end RAG pipeline

## Current Status

Completed:

- OCR
- Markdown formatting
- Semantic chunking
- Embeddings
- SQLite
- Qdrant
- Retrieval
- RAG answer generation

Next:

- Source attribution
- Citations
- Hybrid search
- Reranking
- Conversation memory
- Multi-document reasoning
- Streaming
- Evaluation
- Deployment

## Reflection

Today the project became a complete semantic RAG application.

The biggest lesson was that AI engineering is not only about models. It also requires modular software design, structured outputs, clean interfaces between components, and careful debugging.
