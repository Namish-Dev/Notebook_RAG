from embedding import generate_embedding

text = "Hello world"

embedding = generate_embedding(text)

print(type(embedding))
print(len(embedding))
print(embedding[:10])