# RAG Development Log --- CrossEncoder Reranking Integration

**Date:** 2026-07-19

## Objective

Integrate a production-style CrossEncoder reranker into the existing RAG
pipeline and understand each stage of retrieval and reranking.

------------------------------------------------------------------------

## Topics Learned

### Embedding Model vs CrossEncoder

**Embedding Model** - Converts one piece of text into a vector. - Used
during ingestion and query embedding. - Qdrant retrieves candidate
chunks using vector similarity.

``` python
question_embedding = generate_embedding(question)
```

**CrossEncoder** - Reads the question and one chunk together. - Produces
a relevance score. - Reorders retrieved chunks but does not retrieve new
ones.

------------------------------------------------------------------------

### Understanding ScoredPoint

Qdrant returns `ScoredPoint` objects containing:

-   score
-   payload
-   id
-   vector

Example:

``` python
point.score
point.payload["title"]
```

------------------------------------------------------------------------

### Why Normalize Results

Convert `ScoredPoint` objects into dictionaries:

``` python
{
    "title": "...",
    "section": "...",
    "keywords": "...",
    "chunk_text": "...",
    "score": point.score
}
```

Benefits: - Cleaner architecture - Database independent - Easier
processing

------------------------------------------------------------------------

### CrossEncoder Input

``` python
[
    ("Question", "Chunk 1"),
    ("Question", "Chunk 2")
]
```

### CrossEncoder Output

``` python
scores = reranker.predict(pairs)
```

Example:

``` python
[0.98, 0.43, 0.15]
```

------------------------------------------------------------------------

## Function Created

``` python
def rerank(question, merged_results):

    pairs = []

    for result in merged_results:
        pairs.append(
            (
                question,
                result["chunk_text"]
            )
        )

    scores = reranker.predict(pairs)

    for i in range(len(scores)):
        merged_results[i]["rerank_score"] = scores[i]

    merged_results.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return merged_results
```

------------------------------------------------------------------------

## Updated Pipeline

``` text
User Question
      │
Generate Embedding
      │
Vector Search (Qdrant)
      │
Keyword Search (SQLite)
      │
Merge Results
      │
CrossEncoder Reranker
      │
Top 5 Chunks
      │
Build Context
      │
Gemini
      │
Final Answer
```

------------------------------------------------------------------------

## Debugging Performed

Changed retrieval from:

``` python
vector_results = search_vector(question_embedding, top_k=5)
```

to

``` python
vector_results = search_vector(question_embedding, top_k=20)
```

Observation: - Retrieval still favored internship and summary chunks
over project chunks. - This indicates the retrieval stage is likely the
current bottleneck rather than the reranker.

------------------------------------------------------------------------

## Next Session

1.  Inspect `search_vector()`.
2.  Verify stored embeddings.
3.  Improve retrieval quality.
4.  Include title and section in reranker input.
5.  Compare results before and after reranking.

------------------------------------------------------------------------

## Summary

Today the CrossEncoder reranker was successfully integrated into the RAG
pipeline. The main achievement was understanding the distinction between
retrieval and reranking, normalizing Qdrant results, implementing a
production-style reranker, and identifying that the current limitation
lies in retrieval quality rather than reranking.
