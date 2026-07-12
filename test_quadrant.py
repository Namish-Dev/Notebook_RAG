from vector import client

points, _ = client.scroll(
    collection_name="notes",
    limit=100,
    with_payload=True,
    with_vectors=True
)

for point in points:
    print("=" * 60)
    print("ID:", point.id)
    print("Title:", point.payload["title"])
    print("Vector length:", len(point.vector))
    print("First 5 values:", point.vector[:5])