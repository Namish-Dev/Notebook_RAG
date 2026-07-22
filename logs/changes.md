# RAG Retrieval Fixes

Date: 2026-07-20

## Problem

The resume upload was extracted and chunked correctly. The database contained five chunks under `section = PROJECTS`, but the final answer did not use them for the question `what are the projects`.

The failure happened during retrieval/reranking:

- Vector search found the project chunks.
- Keyword search also found the project chunks.
- The CrossEncoder reranker pushed internship and professional-summary chunks above the project chunks because it only compared the question with `chunk_text`.
- The reranker ignored important metadata like `section = PROJECTS`, `title`, and `keywords`.

## Changes Made

### `embedding.py`

- Added `build_retrieval_text(result)` so the reranker sees:
  - section
  - title
  - keywords
  - chunk text
- Added metadata-aware scoring with `metadata_relevance_score(...)`.
- Combined CrossEncoder score, metadata score, and a small vector-score contribution into the final `rerank_score`.
- Kept `cross_encoder_score` and `metadata_score` separately for debugging.

### `retrieval.py`

- Added a fallback stop-word list so keyword extraction does not fail if NLTK stopwords are missing.
- Added folder-scoped keyword search using the selected folder id.
- Changed keyword search to return stable identifiers:
  - `chunk_id`
  - `file_id`
  - `folder_id`
- Changed hybrid merging to deduplicate by `chunk_id` instead of `chunk_index`.
- Added metadata backfill during merge, so SQLite keyword results can fill fields missing from older Qdrant payloads.
- Ordered keyword results to prefer section/title/keyword matches before general body-text matches.

### `vector.py`

- Added Qdrant folder filtering with `folder_id`.
- Changed vector search to return:
  - `chunk_id`
  - `file_id`
  - `folder_id`
  - `keywords`
- Added `delete_vectors_for_folder(folder_id)` to remove stale Qdrant points when a folder is deleted.

### `main.py`

- Passed `selected_folder_id` into both vector search and keyword search.
- Added `keywords` to newly saved Qdrant payloads.
- Used `build_retrieval_text(result)` when building final RAG context.
- Added vector cleanup before deleting a folder from SQLite.
- Added debug printing for:
  - final rerank score
  - vector score
  - CrossEncoder score
  - metadata score

## Validation

Compiled successfully:

```text
python -m py_compile main.py retrieval.py vector.py embedding.py
.\.venv\Scripts\python.exe -m py_compile main.py retrieval.py vector.py embedding.py
```

Re-tested the resume query:

```text
question: what are the projects
folder_id: 1
```

Final top 5 reranked chunks:

```text
1 PROJECTS Research Agent Project
2 PROJECTS Face Recognition System Project
3 PROJECTS Employee Salary Prediction Project
4 PROJECTS Netflix Clone Web App Project
5 PROJECTS Flight Price Prediction Project
```

Result: the project chunks now rank above internship and professional-summary chunks for the project question.

---

# Local Chunking Fixes

Date: 2026-07-20

## Problem

The app was using Gemini/OpenRouter for semantic chunking in `chunking/semantic_chunker.py`. That meant large uploads, such as a 100-page PDF, could spend a lot of API credits just to split already-extracted text into chunks.

## Changes Made

### `chunking/semantic_chunker.py`

- Replaced API-based chunking with a local deterministic chunker.
- Kept the same output schema expected by `main.py`:
  - `chunk_index`
  - `section`
  - `title`
  - `chunk_text`
  - `keywords`
- Added Markdown heading detection for headings like `#`, `##`, and `###`.
- Added all-caps section detection for resume/document sections like `PROJECTS`, `EDUCATION`, and `INTERNSHIP EXPERIENCE`.
- Added grouped-section handling so bold item titles inside sections become separate chunks while keeping the correct parent section.
- Added paragraph/block-based splitting with a max chunk size.
- Added overlap between large split chunks to preserve context.
- Added code-fence awareness so fenced code blocks are not split in the middle.
- Added local keyword extraction so the embedding and retrieval pipeline still gets useful metadata without an LLM call.
- Trimmed resume-style titles at `|`, so titles like `Research Agent | LangGraph...` become `Research Agent` while the tech stack remains in the chunk text.

## Validation

Compiled successfully:

```text
python -m py_compile main.py retrieval.py vector.py embedding.py chunking\semantic_chunker.py
.\.venv\Scripts\python.exe -m py_compile main.py retrieval.py vector.py embedding.py chunking\semantic_chunker.py
```

Tested against the saved resume content. The local chunker detected the five project chunks correctly:

```text
PROJECTS | Flight Price Prediction
PROJECTS | Research Agent
PROJECTS | Face Recognition System
PROJECTS | Employee Salary Prediction
PROJECTS | Netflix Clone Web App
```

Synthetic 100-section document test:

```text
chunks 100
first PAGE 1 PAGE 1 263
last PAGE 100 PAGE 100 267
max_len 267
```

Result: chunking now runs locally and can handle long PDFs without spending Gemini/OpenRouter credits for the chunking step.
