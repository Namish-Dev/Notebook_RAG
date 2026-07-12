# AI Notes RAG System -- Development Log (Phase 1)

> This document records the engineering decisions, problems encountered,
> and solutions implemented while building the first phase of the AI
> Notes RAG project.

------------------------------------------------------------------------

# Project Goal

The objective is to build a NotebookLM-like application where users can
create folders, upload handwritten notes or PDFs, convert them into
structured Markdown using a Vision Language Model (VLM), store them, and
later chat with all uploaded knowledge using Retrieval-Augmented
Generation (RAG).

Current progress covers the complete ingestion pipeline.

------------------------------------------------------------------------

# Current Architecture

``` text
User Upload
      │
      ▼
Vision Language Model
      │
      ▼
Formatted Markdown
      │
      ▼
SQLite
      │
      ▼
Heading-aware Chunking
      │
      ▼
Chunks Table
```

Embeddings and vector search have intentionally not been implemented
yet.

------------------------------------------------------------------------

# Development Timeline

## Step 1 --- Vision Model Selection

### Initial Problem

The first idea was to use OCR.

Tests with PaddleOCR showed good text extraction but poor understanding
of document structure.

Typical issues included:

-   Broken code formatting
-   Split words
-   Lost indentation
-   Missing arrows
-   Incorrect grouping

### Investigation

Several OCR engines were explored:

-   PaddleOCR
-   Surya OCR
-   TrOCR
-   CRAFT
-   Chandra OCR

It became clear that OCR solves character recognition, not document
understanding.

### Decision

The pipeline changed from:

``` text
OCR → LLM
```

to

``` text
Vision Language Model → Markdown
```

Reason: the VLM understands layout, hierarchy and semantics
simultaneously.

------------------------------------------------------------------------

## Step 2 --- Prompt Engineering

### Problem

The initial prompt returned mostly plain text, which was unsuitable for
retrieval.

### Solution

The prompt was refined to:

-   Produce Markdown
-   Preserve all information
-   Avoid hallucinations
-   Use headings and lists
-   Return only formatted notes

Result:

``` markdown
### Plotting Functions

...

### String Manipulation
```

------------------------------------------------------------------------

## Step 3 --- Database Design

### Initial Design

A single document table.

### Problem

The product required folders.

### Solution

The schema became:

``` text
folders
   ↓
files
   ↓
chunks
```

------------------------------------------------------------------------

## Step 4 --- Saving Documents

Every extracted document is stored in SQLite.

``` python
cursor.execute(
    '''
    INSERT INTO files(folder_id, file_name, content)
    VALUES (?, ?, ?)
    ''',
    (folder_id, upload.name, response)
)
```

------------------------------------------------------------------------

## Step 5 --- Choosing Chunking

### Considered

-   Fixed-size
-   Recursive
-   Semantic
-   Markdown Heading Chunking

### Decision

Markdown Heading Chunking.

Reason:

The VLM already outputs semantic sections.

------------------------------------------------------------------------

### Initial Implementation

``` python
sections = re.split(r"\n\s*\n", content)
```

### Problem

Chunk boundaries depended on blank lines.

### Final Solution

``` python
sections = re.split(
    r"(?=^### )",
    content,
    flags=re.MULTILINE
)
```

Advantages:

-   Stable
-   Topic-aware
-   Independent of spacing

------------------------------------------------------------------------

## Step 6 --- Chunk Storage

Chunks are stored separately.

``` python
for chunk_data in chunks:
    save_chunk(
        file_id=file_id,
        chunk_index=chunk_data["chunk_index"],
        title=chunk_data["title"],
        chunk_text=chunk_data["chunk_text"]
    )
```

------------------------------------------------------------------------

### Problem

Confusion between `folder_id` and `file_id`.

### Root Cause

Chunks belong to files, not folders.

### Solution

``` python
file_id = cursor.lastrowid
```

Every chunk references the generated file id.

------------------------------------------------------------------------

## Step 7 --- Streamlit Duplicate Upload Bug

### Problem

The same file was inserted repeatedly.

### Root Cause

The upload logic used:

``` python
if upload is not None:
```

Every Streamlit rerun executed the insert again.

### Solution

Move uploads into a form.

``` python
with st.form("upload_form"):
    upload = st.file_uploader(...)
    process_upload = st.form_submit_button(...)
```

Now uploads occur only after explicit submission.

------------------------------------------------------------------------

## Step 8 --- Simplifying the Pipeline

A fingerprint mechanism was briefly introduced to prevent duplicates.

After reviewing the architecture it was removed because the form-based
workflow already solved the rerun issue.

Final ingestion pipeline:

``` text
Upload
   ↓
Extract
   ↓
Save File
   ↓
Get file_id
   ↓
Create Chunks
   ↓
Save Chunks
   ↓
Commit
```

------------------------------------------------------------------------

# Lessons Learned

-   OCR is not document understanding.
-   Better prompts reduce downstream complexity.
-   Heading-aware chunking is more appropriate than recursive chunking
    for structured VLM output.
-   Build and validate the ingestion pipeline before introducing
    embeddings.
-   Model the database around the user's workflow (Folders → Files →
    Chunks).

------------------------------------------------------------------------

# Current Status

Completed

-   Folder management
-   File uploads
-   Markdown extraction
-   SQLite storage
-   Heading-aware chunking
-   Chunk persistence

Next

-   File deletion
-   Embeddings
-   Qdrant
-   Retrieval
-   Chat
