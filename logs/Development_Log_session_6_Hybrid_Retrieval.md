# Development Log --- Day 4: Multi-Format Extraction & Hybrid Retrieval Foundation

**Date:** July 16, 2026

## Objective

Today's goal was to: - Support multiple document formats. - Reduce
unnecessary LLM usage. - Begin implementing Hybrid Retrieval (Vector +
Keyword Search). - Improve the architecture by separating
responsibilities.

## Progress Made

### 1. Multi-format document support

``` text
Image -> Gemini OCR -> Markdown
PDF -> PyMuPDF -> Markdown
```

``` python
def extract_text(upload, file_type):
    if file_type == "image":
        return transcribe(upload)
    elif file_type == "pdf":
        ...
```

### 2. File type detection

``` python
file_type = upload.name.split(".")[-1].lower()
```

### 3. PDF extraction using PyMuPDF

``` python
pdf_bytes = upload.getvalue()

doc = fitz.open(stream=pdf_bytes, filetype="pdf")

text = ""
for page in doc:
    text += page.get_text()
```

### 4. Detect scanned PDFs

``` python
if text.strip():
    ...
else:
    ...
```

Pipeline:

``` text
PDF
 ↓
Extract Text
 ↓
Text Exists?
├── Yes → Markdown
└── No  → Gemini OCR
```

### 5. Markdown extraction using PyMuPDF4LLM

``` python
doc = fitz.open(stream=upload.getvalue(), filetype="pdf")
markdown = pymupdf4llm.to_markdown(doc)
```

### 6. Created retrieval.py

Responsibilities: - Keyword extraction - Keyword search - Hybrid search
(future) - Result merging (future)

### 7. Keyword extraction

``` python
query = query.lower()
words = query.split()
```

Input:

    What are the projects?

Output:

``` python
["projects"]
```

### 8. Remove punctuation

``` python
query = query.translate(
    str.maketrans("", "", string.punctuation)
)
```

**Learned**

`str.maketrans()` creates a translation table that `translate()` uses to
replace or remove characters.

### 9. SQLite keyword search

``` sql
SELECT chunk_index,title,chunk_text,keywords,section
FROM chunks
WHERE
LOWER(section) LIKE ?
OR LOWER(title) LIKE ?
OR LOWER(keywords) LIKE ?
OR LOWER(chunk_text) LIKE ?
LIMIT ?
```

Bug fixed:

Wrong:

``` sql
LIKE f"%{keyword}%"
```

Correct:

``` python
cursor.execute(
    sql,
    (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        limit
    )
)
```

### 10. extend() vs append()

``` python
all_results.extend(cursor.fetchall())
```

-   append() adds one object.
-   extend() adds every element.

### 11. LIMIT

Purpose: - Restrict returned rows. - Reduce prompt size. - Improve
speed. - Reduce LLM cost.

### 12. Hybrid Retrieval Progress

Current:

``` text
Question
   │
   ├── Vector Search
   └── Keyword Search
```

Next:

``` text
Question
   │
   ├── Vector Search
   ├── Keyword Search
   └── Merge Results
         │
         ├── Remove Duplicates
         └── Gemini
```

## Concepts Learned

-   Hybrid Retrieval combines semantic and keyword search.
-   Vector search alone may miss exact matches.
-   Parameterized SQL should be used instead of Python f-strings inside
    SQL.
-   `str.maketrans()` creates translation mappings.
-   `extend()` combines iterables efficiently.
-   PyMuPDF is preferred for digital PDFs, while OCR should be reserved
    for scanned PDFs.

## Interview Questions

1.  Why Hybrid Retrieval?
2.  Why parameterized SQL?
3.  Why PyMuPDF instead of an LLM for digital PDFs?
4.  Why detect scanned PDFs?
5.  Why use LIMIT in SQL?

## Today's Progress

-   ✅ Added multi-format document support.
-   ✅ Added PyMuPDF extraction.
-   ✅ Added PyMuPDF4LLM Markdown conversion.
-   ✅ Added scanned PDF fallback.
-   ✅ Created retrieval.py.
-   ✅ Built keyword extraction.
-   ✅ Built SQLite keyword search.
-   ✅ Fixed SQL parameterization.
-   ✅ Verified keyword retrieval.
-   ✅ Designed the hybrid retrieval architecture.

**Next Goal:** Merge vector search and keyword search into a unified
hybrid retrieval pipeline with duplicate removal and reranking.
