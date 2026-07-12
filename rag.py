from gemini_client import client
def answer_question(rag_prompt):
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[rag_prompt]
)
    return response.text