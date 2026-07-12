from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.models import PointStruct

client = QdrantClient(path="qdrant_data")

if not client.collection_exists("notes"):
    client.create_collection(
    collection_name="notes",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

def save_vector(chunk_id, embedding, payload):

    point = PointStruct(
        id=chunk_id,
        vector=embedding,
        payload=payload
    )

    client.upsert(
        collection_name="notes",
        points=[point]
    )

points, _ = client.scroll(
    collection_name="notes",
    limit=100
)

def search_vector(embedding, top_k=5):
    search_result = client.query_points(
        collection_name="notes",
        query=embedding,
        limit=top_k
    )
    return search_result.points