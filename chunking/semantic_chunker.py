from gemini_client import client
import json

def create_semantic_chunk(markdown_text: str):
    prompt="""
        A chunk must:

    • Explain exactly one concept.

    • Be understandable without reading another chunk.

    • Keep related code examples.

    • Never split a code example.

    • Never merge unrelated concepts.

    • Generate a short descriptive title.

    • Return JSON only.

    The output schema is as follows:
    [
    {
        "chunk_index": 0,
        "title": "...",
        "chunk_text": "...",
        "keywords": [
            "...",
            "...",
            "..."
        ]
    }
    ]
    Rules:
        Do NOT add explanations.

        Do NOT generate examples.

        Do NOT generate import statements.

        Do NOT rewrite the notes.

        Only reorganize the original content into semantic chunks.

        Preserve the original wording as much as possible.

    """

    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        prompt,
        markdown_text
    ]
)
    
    json_text = response.text
    json_text = json_text.replace("```json", "")
    json_text = json_text.replace("```", "")
    json_text = json_text.strip()

    chunks = json.loads(json_text)
    return chunks



