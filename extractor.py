
import base64

from annotated_types import doc
from formatter import format_text
from gemini_client import client
from google.genai import types
import fitz
import pymupdf4llm


import openrouter_client

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
        # st.info("Using Gemini...")
        return transcribe_with_gemini(upload)

    except Exception as e:
        # st.warning(f"Gemini failed: {e}")
        # st.info("Switching to OpenRouter...")

        return transcribe_with_openrouter(upload)
    

def extract_pdf(upload):
    # Read PDF bytes from the uploaded file
    pdf_bytes = upload.getvalue()

    # Open the PDF from memory
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    if text.strip():
        return text

    return None

def extract_text(upload, file_type):
    if file_type == "image":
        return transcribe(upload)
    elif file_type == "pdf":
        text= extract_pdf(upload)
        if text:
            pdf_bytes = upload.getvalue()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            markdown = pymupdf4llm.to_markdown(doc)

            doc.close()

            return markdown
        else:
            return transcribe(upload)

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
