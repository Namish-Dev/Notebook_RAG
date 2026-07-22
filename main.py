
import os
from openai import OpenAI
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import chunk
from database import conn, cursor
from embedding import build_retrieval_text, generate_embedding, rerank
from rag import answer_question
from vector import delete_vectors_for_folder, save_vector, search_vector
from chunking.semantic_chunker import create_semantic_chunk
from rag import answer_question
from document_analyzer import get_file_type
from extractor import extract_text
from retrieval import keyword_search, hybrid_merged

load_dotenv()

st.title("Hello, Streamlit!")
st.write("This is a simple Streamlit app.")

Gemini_API_KEY=os.getenv("Gemini_API_KEY")
client = genai.Client(api_key=Gemini_API_KEY)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OpenRouter_API_KEY"),
)





    

def save_chunk(file_id, section,chunk_index, title, chunk_text,keywords):
    cursor.execute(
        """
        INSERT INTO chunks (file_id, section, chunk_index, title, chunk_text, keywords)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (file_id, section, chunk_index, title, chunk_text, ",".join(keywords))
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

    delete_vectors_for_folder(selected_folder_id)

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





with st.form("upload_form", clear_on_submit=True):
    upload = st.file_uploader("Upload your image here")

    if upload:
        file_type = get_file_type(upload.name)
        

    process_upload = st.form_submit_button("Process Upload")


if process_upload and upload is not None:

    # Send uploaded image to the VLM for note extraction.
    response = extract_text(upload, file_type)

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
        text_for_embedding = f"""
        Section: {chunk_data["section"]}

        Title: {chunk_data["title"]}

        Keywords: {", ".join(chunk_data["keywords"])}

        Content:
        {chunk_data["chunk_text"]}
            """
        
        embedding = generate_embedding(text_for_embedding)
        payload={
            "folder_id": selected_folder_id,
            "file_id": file_id,
            "section": chunk_data["section"],
            "chunk_index": chunk_data["chunk_index"],
            "title": chunk_data["title"],
            "chunk_text": chunk_data["chunk_text"],
            "keywords": chunk_data["keywords"],
        }
        chunk_id=save_chunk(
            file_id=file_id,
            chunk_index=chunk_data["chunk_index"],
            section=chunk_data["section"],
            title=chunk_data["title"],
            chunk_text=chunk_data["chunk_text"],
            keywords=chunk_data["keywords"]
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
    vector_results=search_vector(question_embedding, top_k=20, folder_id=selected_folder_id)
    keyword_results=keyword_search(question, limit=20, folder_id=selected_folder_id)
    merged_results=hybrid_merged(vector_results, keyword_results)
    reranked=rerank(question, merged_results)
    top_chunks=reranked[:5]

    context = ""

    for i, result in enumerate(top_chunks, start=1):
                context += f"""
                            Chunk {i}

                            {build_retrieval_text(result)}

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

    st.subheader("Retrieved Chunks")

    for i, result in enumerate(top_chunks, start=1):
        st.write(
        i,
        result["rerank_score"],
        result["section"],
        result["title"]
    )


    for i, chunk in enumerate(top_chunks, 1):
        print("=" * 50)
        print(f"Rank {i}")
        print(f"Rerank Score: {chunk['rerank_score']:.4f}")
        print(f"Vector Score: {chunk['score']:.4f}")
        print(f"CrossEncoder Score: {chunk.get('cross_encoder_score', 0):.4f}")
        print(f"Metadata Score: {chunk.get('metadata_score', 0):.4f}")
        print(f"Title: {chunk['title']}")
        print(f"Section: {chunk['section']}")
