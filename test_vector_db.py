from src.database.vector_db import QdrantVectorStore, get_embedding_model

if __name__ == "__main__":
    embedding_model = get_embedding_model(model_name="text-embedding-3-small")

    vector_store = QdrantVectorStore(embedding_model=embedding_model)

    vector_store.create_collection(collection_name="test_collection")

    texts = ["This is a test document for the vector database."]

    metadata = [{"source": "test_source", "timestamp": "2024-06-01T12:00:00Z"}]

    inserted_ids = vector_store.insert(collection_name="test_collection", texts=texts, metadatas=metadata)
    print(f"Inserted point IDs: {inserted_ids}")