# Streamlit App Documentation

This document explains what the app in [main.py](main.py) does, how the UI is organized, and how data moves from an uploaded image/PDF into SQLite tables.

## High-Level Purpose

The app lets a user:

1. Create a folder.
2. Choose a folder.
3. Upload an image or PDF.
4. Send the uploaded file to a vision model for text extraction.
5. Save the extracted notes into SQLite.
6. Split the extracted notes into chunks and save those chunks too.
7. View previously saved files and chunk records.

The app uses Streamlit for the UI, Google Gemini first for transcription, and OpenRouter as a fallback.

## Main Data Flow

The flow in [main.py](main.py) is:

```python
with st.form("upload_form", clear_on_submit=True):
    upload = st.file_uploader("Upload your image here")
    process_upload = st.form_submit_button("Process Upload")

if process_upload and upload is not None:
    response = transcribe(upload)

    cursor.execute(
        """
        INSERT INTO files(folder_id, file_name, content)
        VALUES (?, ?, ?)
        """,
        (selected_folder_id, upload.name, response)
    )

    file_id = cursor.lastrowid
    chunks = chunk.create_chunks(response)

    for chunk_data in chunks:
        save_chunk(
            file_id=file_id,
            chunk_index=chunk_data["chunk_index"],
            title=chunk_data["title"],
            chunk_text=chunk_data["chunk_text"]
        )

    conn.commit()
```

This is the important sequence:

- The user selects a file and clicks **Process Upload**.
- The app extracts text with `transcribe(upload)`.
- The extracted response is inserted into the `files` table.
- `cursor.lastrowid` captures the new file id.
- The response is split into chunks.
- Each chunk is stored in the `chunks` table using the correct `file_id`.
- A single `conn.commit()` saves everything together.

## Imports

At the top of [main.py](main.py), these imports are used:

```python
import base64
import hashlib
import os
from openai import OpenAI
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import chunk
from database import conn, cursor
```

What each one does:

- `base64`: encodes uploaded image bytes for OpenRouter.
- `hashlib`: builds a fingerprint for uploaded files to reduce duplicate processing.
- `os`: reads environment variables such as API keys.
- `OpenAI`: used for OpenRouter API access.
- `streamlit`: builds the app UI.
- `genai` and `types`: used for Gemini transcription.
- `load_dotenv`: loads API keys from `.env`.
- `chunk`: splits extracted notes into chunks.
- `conn` and `cursor`: SQLite connection and cursor from [database.py](database.py).

## Environment Setup

The app loads environment variables and creates API clients:

```python
load_dotenv()

Gemini_API_KEY = os.getenv("Gemini_API_KEY")
client = genai.Client(api_key=Gemini_API_KEY)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OpenRouter_API_KEY"),
)
```

This means the app expects:

- `Gemini_API_KEY` for the Gemini model.
- `OpenRouter_API_KEY` for fallback transcription.

## UI Header

These lines create the basic page title and intro text:

```python
st.title("Hello, Streamlit!")
st.write("This is a simple Streamlit app.")
```

They only affect the page heading and do not impact data processing.

## Prompt

The app uses one shared prompt for both VLM calls:

```python
Prompt = ''' You are an expert note formatter.

Extract all text from the image and rewrite it as well-structured Markdown notes.

Requirements:
- Return ONLY the formatted notes.
- Do NOT include any introduction, conclusion, explanation, or commentary.
- Do NOT say things like:
  - "Here's the text from the image..."
  - "Below are the notes..."
  - "The image contains..."
- Start immediately with the first heading or bullet point.
- Preserve all important information.
- Use Markdown headings, bullet points, numbered lists, and tables where appropriate.
- Do not invent information that is not present in the image.
'''
```

This prompt tells the model to return clean Markdown notes with no extra commentary.

## Functions

### `transcribe_with_gemini(upload)`

```python
def transcribe_with_gemini(upload):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            Prompt,
            types.Part.from_bytes(
                data=upload.getvalue(),
                mime_type=upload.type,
            ),
        ],
    )

    return response.text
```

Purpose:

- Sends the uploaded file to Gemini.
- Uses the shared prompt plus the raw bytes of the upload.
- Returns the generated Markdown text.

Why it matters:

- This is the primary transcription path.
- It converts image/PDF content into notes.

### `transcribe_with_openrouter(upload)`

```python
def transcribe_with_openrouter(upload):
    image_b64 = base64.b64encode(upload.getvalue()).decode("utf-8")

    response = openrouter_client.chat.completions.create(
        model="google/gemma-4-26b-a4b-it:free",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": Prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{upload.type};base64,{image_b64}"
                        },
                    },
                ],
            }
        ],
    )

    return response.choices[0].message.content
```

Purpose:

- Acts as a backup if Gemini fails.
- Converts the file bytes to base64.
- Sends a multimodal request through OpenRouter.

### `transcribe(upload)`

```python
def transcribe(upload):
    try:
        st.info("Using Gemini...")
        return transcribe_with_gemini(upload)
    except Exception:
        st.info("Switching to OpenRouter...")
        return transcribe_with_openrouter(upload)
```

Purpose:

- Wraps both transcription methods.
- Tries Gemini first.
- Falls back to OpenRouter if Gemini raises an exception.

Why it matters:

- The app stays usable even if one provider fails.

### `save_chunk(file_id, chunk_index, title, chunk_text)`

```python
def save_chunk(file_id, chunk_index, title, chunk_text):
    cursor.execute(
        """
        INSERT INTO chunks (file_id, chunk_index, title, chunk_text)
        VALUES (?, ?, ?, ?)
        """,
        (file_id, chunk_index, title, chunk_text)
    )
```

Purpose:

- Inserts one chunk into the `chunks` table.
- Connects each chunk to the correct `files.id` through `file_id`.

Important detail:

- `conn.commit()` is intentionally not inside this function.
- The app commits once after all chunks are saved.
- That keeps the file and its chunks in one transaction.

### `get_upload_fingerprint(upload, folder_id)`

```python
def get_upload_fingerprint(upload, folder_id):
    upload_bytes = upload.getvalue()

    return hashlib.sha256(
        f"{folder_id}:{upload.name}:{upload.type}:{len(upload_bytes)}".encode("utf-8") + upload_bytes
    ).hexdigest()
```

Purpose:

- Creates a unique fingerprint for the upload.
- Combines the folder id, file name, file type, and file bytes.

Why it matters:

- It helps prevent reprocessing the same upload during reruns.
- The app stores processed fingerprints in `st.session_state["processed_uploads"]`.

## Folder Management UI

### Create Folder Form

```python
with st.form("create_folder_form", clear_on_submit=True):
    folder_name = st.text_input("Folder Name", key="folder_name")
    submitted = st.form_submit_button("Create Folder")

    if submitted and folder_name.strip():
        cursor.execute(
            """
            INSERT INTO folders(title)
            VALUES(?)
            """,
            (folder_name,)
        )
        conn.commit()
        st.rerun()
```

What this does:

- Gives the user a text box to enter a folder name.
- Creates a folder only when the form is submitted.
- Calls `st.rerun()` so the new folder appears immediately in the dropdown.

Why the form matters:

- Streamlit reruns the script often.
- Using a form prevents accidental repeated inserts while typing.

### Folder List Query

```python
cursor.execute("""
    SELECT id, title
    FROM folders
    ORDER BY title
    """)

folders = cursor.fetchall()
```

What this does:

- Reads all folders from SQLite.
- Orders them alphabetically.
- Feeds the results into the selectbox.

### Empty Folder Guard

```python
if not folders:
    st.info("Create a folder before uploading or viewing files.")
    st.stop()
```

What this does:

- Prevents `selected_folder` from being used when no folder exists.
- Stops the app early until a folder is created.

Why it matters:

- Avoids `NoneType` errors.
- Prevents upload code and file queries from running without a valid folder.

### Folder Selectbox

```python
selected_folder = st.selectbox(
    "Choose Folder",
    folders,
    format_func=lambda folder: folder[1]
)

selected_folder_id = selected_folder[0]
```

What this does:

- Lets the user choose an existing folder.
- Displays the folder title while keeping the tuple internally.
- Stores the chosen folder id for reuse.

Why it matters:

- `selected_folder_id` is used for uploads, deletions, and file filtering.

### Delete Folder Button

```python
if st.button("🗑 Delete Folder"):
    cursor.execute(
        """
        DELETE FROM folders
        WHERE id = ?
        """,
        (selected_folder_id,)
    )

    conn.commit()
    st.success("Folder deleted!")
    st.rerun()
```

What this does:

- Deletes the currently selected folder.
- Commits the change.
- Reruns the app so the dropdown and file list update.

Important dependency:

- Because the schema uses `ON DELETE CASCADE`, deleting a folder also removes related files and chunks.

## Upload Form

```python
with st.form("upload_form", clear_on_submit=True):
    upload = st.file_uploader("Upload your image here")
    process_upload = st.form_submit_button("Process Upload")
```

What this does:

- Lets the user pick a file.
- Requires an explicit button click to process the file.
- Avoids duplicate inserts caused by Streamlit reruns.

Why this is better than plain `if upload is not None`:

- Without a form, every rerun re-enters the upload logic.
- With the form, processing happens only when the user submits.

## Upload Processing Logic

```python
if process_upload and upload is not None:
    response = transcribe(upload)

    cursor.execute(
        """
        INSERT INTO files(folder_id, file_name, content)
        VALUES (?, ?, ?)
        """,
        (selected_folder_id, upload.name, response)
    )

    file_id = cursor.lastrowid
    chunks = chunk.create_chunks(response)
```

What this does:

- Runs only after the upload form is submitted.
- Sends the file to the transcription pipeline.
- Inserts the result into the `files` table.
- Captures the inserted file id immediately.
- Builds chunks from the extracted notes.

Why `cursor.lastrowid` matters:

- It gives the id of the exact file row just inserted.
- Every chunk uses this same id so the relationship stays correct.

### Saving Chunks

```python
for chunk_data in chunks:
    save_chunk(
        file_id=file_id,
        chunk_index=chunk_data["chunk_index"],
        title=chunk_data["title"],
        chunk_text=chunk_data["chunk_text"]
    )

conn.commit()
```

What this does:

- Stores each generated chunk in SQLite.
- Links each chunk to the inserted file row.
- Commits once after all inserts are complete.

Why it matters:

- Keeps file and chunk writes consistent.
- Prevents partial saves if something goes wrong mid-process.

## Showing Saved Files

```python
cursor.execute("""
SELECT file_name, content
FROM files
WHERE folder_id = ?
ORDER BY created_at DESC
""", (selected_folder_id,))

files = cursor.fetchall()

for file_name, content in files:
    with st.expander(file_name):
        st.markdown(content)
```

What this does:

- Reads all files for the selected folder.
- Shows each saved document inside an expander.
- Renders the extracted notes as Markdown.

Why it matters:

- Gives the user a folder-scoped history of uploads.
- Makes it easy to review extracted content.

## Chunks Table View

```python
st.header("Chunks Table")

cursor.execute("""
SELECT file_id, chunk_index, title
FROM chunks
ORDER BY file_id, chunk_index
""")

rows = cursor.fetchall()

st.table(rows)
```

What this does:

- Displays chunk metadata for all saved chunks.
- Shows which file each chunk belongs to.
- Orders chunks by file and chunk index.

## Database Tables

The schema lives in [database.py](database.py).

### `folders`

```python
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

Stores folder names.

### `files`

```python
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(folder_id)
    REFERENCES folders(id)
    ON DELETE CASCADE
)
```

Stores the extracted Markdown content for each upload.

### `chunks`

```python
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    title TEXT,
    chunk_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(file_id)
    REFERENCES files(id)
    ON DELETE CASCADE
)
```

Stores chunked sections of each extracted note.

## Chunking Logic

The chunking behavior is in [chunk.py](chunk.py):

```python
def create_chunks(content: str):
    chunks = []
    sections = re.split(r"(?=^### )", content, flags=re.MULTILINE)

    chunk_index = 0

    for section in sections:
        section = section.strip()

        if not section:
            continue

        if not section.startswith("###"):
            continue

        lines = section.splitlines()
        title = lines[0].replace("###", "").strip()

        chunks.append({
            "chunk_index": chunk_index,
            "title": title,
            "chunk_text": section
        })

        chunk_index += 1

    return chunks
```

What it does:

- Splits extracted notes on Markdown headings that start with `###`.
- Uses the heading text as the chunk title.
- Returns a list of chunk dictionaries.

How it fits the app:

- The app sends the transcription result into this function.
- Each returned chunk becomes a row in the `chunks` table.

## Streamlit Best-Practice Notes

A few patterns in this app are important:

- Use `st.form(...)` + `st.form_submit_button(...)` for actions that should happen once.
- Use session state when you need to track something across reruns.
- Insert the parent row first, then capture `cursor.lastrowid`, then insert child rows.
- Commit after a group of related DB writes instead of committing every small insert.

## Summary

In short, the app is a folder-based note extraction pipeline:

- UI controls folder creation and selection.
- Upload form triggers transcription only once per submission.
- The extracted content is saved in `files`.
- Chunked sections are saved in `chunks`.
- Saved data is displayed back to the user by folder.

If you want, I can also create a second version of this documentation that is shorter and reads like inline developer notes, or I can add comments directly into [main.py](main.py) next to the relevant blocks.