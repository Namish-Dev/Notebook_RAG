import base64
import os
from openai import OpenAI
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import chunk
from database import conn, cursor
from embedding import generate_embedding
from rag import answer_question
from vector import  save_vector, search_vector
from chunking.semantic_chunker import create_semantic_chunk
from rag import answer_question

load_dotenv()

st.title("Hello, Streamlit!")
st.write("This is a simple Streamlit app.")

Gemini_API_KEY=os.getenv("Gemini_API_KEY")
client = genai.Client(api_key=Gemini_API_KEY)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OpenRouter_API_KEY"),
)

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

def transcribe_with_openrouter(upload):
    image_b64 = base64.b64encode(upload.getvalue()).decode("utf-8")

    response = openrouter_client.chat.completions.create(
        model="google/gemma-4-26b-a4b-it:free",   # or another vision model
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


def transcribe(upload):
    try:
        st.info("Using Gemini...")
        return transcribe_with_gemini(upload)

    except Exception as e:
        # st.warning(f"Gemini failed: {e}")
        st.info("Switching to OpenRouter...")

        return transcribe_with_openrouter(upload)
    

def save_chunk(file_id, chunk_index, title, chunk_text):
    cursor.execute(
        """
        INSERT INTO chunks (file_id, chunk_index, title, chunk_text)
        VALUES (?, ?, ?, ?)
        """,
        (file_id, chunk_index, title, chunk_text)
    )

    # SQLite gives the ID of the row that was just inserted
    chunk_id = cursor.lastrowid


    # Return that ID to whoever called this function
    return chunk_id




    
with st.form("create_folder_form",clear_on_submit=True):

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

cursor.execute("""
    SELECT id, title
    FROM folders
    ORDER BY title
    """)

folders = cursor.fetchall()

if not folders:
    st.info("Create a folder before uploading or viewing files.")
    st.stop()

selected_folder = st.selectbox(
    "Choose Folder",
    folders,
    format_func=lambda folder: folder[1]
)

selected_folder_id = selected_folder[0]

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

# upload =st.file_uploader("Upload your image here")

Prompt = ''' You are an expert note formatter.

Extract all text from the image and rewrite it as well-structured Markdown notes.

Requirements:
- Return ONLY the formatted notes.
# - Include any introduction, conclusion, explanation, or commentary.
# - If there are any headings, subheadings, or bullet points in the image, preserve them in the output.
# - If there are no headings, create appropriate headings based on the content.
- Do NOT say things like:
  - "Here's the text from the image..."
  - "Below are the notes..."
  - "The image contains..."
- Start immediately with the first heading or bullet point.
- Preserve all important information.
- Use Markdown headings, bullet points, numbered lists, and tables where appropriate.
- Do not invent information that is not present in the image.
'''




with st.form("upload_form", clear_on_submit=True):
    upload = st.file_uploader("Upload your image here")
    process_upload = st.form_submit_button("Process Upload")


if process_upload and upload is not None:

    # Send uploaded image to the VLM for note extraction.
    response = transcribe(upload)

    # Save the extracted notes into the files table.
    cursor.execute(
        """
        INSERT INTO files(folder_id, file_name, content)
        VALUES (?, ?, ?)
        """,
        (selected_folder_id, upload.name, response)
    )

    # SQLite automatically generates a unique id for every file.
    # This id is used to link all chunks back to the correct file.
    file_id = cursor.lastrowid

    # Split the extracted notes into topic-wise chunks.
    chunks = create_semantic_chunk(response)
    


        

    # Save every chunk into the chunks table.
    for chunk_data in chunks:
        embedding = generate_embedding(chunk_data["chunk_text"])
        payload={
            "folder_id": selected_folder_id,
            "file_id": file_id,
            "chunk_index": chunk_data["chunk_index"],
            "title": chunk_data["title"],
            "chunk_text": chunk_data["chunk_text"],
        }
        chunk_id=save_chunk(
            file_id=file_id,
            chunk_index=chunk_data["chunk_index"],
            title=chunk_data["title"],
            chunk_text=chunk_data["chunk_text"]
        )

        save_vector(
            chunk_id=chunk_id,
            embedding=embedding,
            payload=payload
        )
    
    # Commit both the file and its chunks together.
    conn.commit()

    st.success("Notes extracted successfully!")

    # Display the formatted markdown notes.
    st.markdown(response)

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

st.header("Chunks Table")

cursor.execute("""
SELECT file_id, chunk_index, title
FROM chunks
ORDER BY file_id, chunk_index
""")

rows = cursor.fetchall()

st.table(rows)


#--------Chatbot----------
question=st.text_input("Ask a question about your notes:")
if question:
    question_embedding=generate_embedding(question)
    search_results=search_vector(question_embedding, top_k=5)
    

    context = ""

    for i, result in enumerate(search_results, start=1):
                context += f"""
                            Chunk {i}

                            Title: {result.payload['title']}

                            {result.payload['chunk_text']}

                            --------------------------------
                            """
        
    rag_prompt=f"""You are an AI assistant that answers questions using the provided notes.

        =========================
        Retrieved Notes
        =========================

        {context}


        =========================
        Question
        =========================

        {question}

        =========================
        Rules
        =========================

        1. Answer only from the notes.
        2. If the answer isn't available, say so.
        3. Don't hallucinate.
        4. Be concise.
        5. Include code when useful.
        """

    answer = answer_question(rag_prompt)
    st.markdown(f"**Answer:** {answer}")
