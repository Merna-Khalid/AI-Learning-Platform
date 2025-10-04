import os
from dotenv import load_dotenv

import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.classes.config import Property, DataType, Configure

from rag.embedding_service import EmbeddingService  # custom embedder

load_dotenv()


class WeaviateClientWrapper:
    """
    A client class to manage the connection and operations with Weaviate.
    Handles embeddings internally (via EmbeddingService).
    """

    def __init__(self):
        self.client = self._connect_to_weaviate()
        self.embedder = EmbeddingService()  # <-- built-in embedder

    def _connect_to_weaviate(self):
        try:
            client = weaviate.WeaviateClient(
                connection_params=ConnectionParams.from_params(
                    http_host="weaviate-db",   # Docker service name
                    http_port=8080,
                    http_secure=False,
                    grpc_host="weaviate-db",
                    grpc_port=50051,
                    grpc_secure=False,
                ),
                # no auth since AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=30, query=60, insert=120),
                ),
                skip_init_checks=False,
            )

            client.connect()  # must call manually

            if client.is_ready():
                print("✅ Connected to Weaviate at weaviate-db:8080")
            else:
                print("⚠️ Weaviate not ready")

            return client

        except Exception as e:
            print(f"❌ Failed to connect to Weaviate: {e}")
            return None

    def get_collection(self, collection_name: str):
        """Retrieves a collection object from the client."""
        if not self.client:
            return None
        return self.client.collections.get(collection_name)

    def create_collection_if_not_exists(self, collection_name: str):
        """
        Creates a new collection for storing embeddings.
        Uses vectorizer=none since embeddings come from external models.
        """
        if not self.client:
            return

        if self.client.collections.exists(collection_name):
            print(f"ℹCollection '{collection_name}' already exists.")
            return

        print(f"Creating collection: '{collection_name}'...")
        self.client.collections.create(
            name=collection_name,
            properties=[
                Property(
                    name="text",
                    data_type=DataType.TEXT,
                    description="Document chunk."
                ),
                Property(
                    name="source",
                    data_type=DataType.TEXT,
                    description="Source file or URL."
                ),
                Property(
                    name="modality",
                    data_type=DataType.TEXT,
                    description="Modality type (text, image, audio)."
                ),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
        )
        print(f"✅ Collection '{collection_name}' created.")

    def insert_text(self, collection_name: str, text: str, source: str):
        """Embeds and inserts a text chunk into the collection."""
        collection = self.get_collection(collection_name)
        if collection is None:
            print(f"❌ Collection not found for {collection_name}.")
            return

        vector = self.embedder.embed_text(text)
        collection.data.insert(
            properties={"text": text, "source": source, "modality": "text"},
            vector=vector,
        )
        print(f"Inserted text from '{source}' into '{collection_name}'.")

    def insert_image(self, collection_name: str, image_path: str, source: str):
        """Embeds and inserts an image into the collection."""
        collection = self.get_collection(collection_name)
        if collection is None:
            print(f"❌ Collection not found for {collection_name}.")
            return

        vector = self.embedder.embed_image(image_path)
        collection.data.insert(
            properties={"text": "[IMAGE]", "source": source, "modality": "image"},
            vector=vector,
        )
        print(f"Inserted image from '{source}' into '{collection_name}'.")

    def insert_audio(self, collection_name: str, audio_path: str, source: str):
        """Embeds and inserts an audio file into the collection."""
        collection = self.get_collection(collection_name)
        if collection is None:
            print(f"❌ Collection not found for {collection_name}.")
            return

        vector = self.embedder.embed_audio(audio_path)
        collection.data.insert(
            properties={"text": "[AUDIO]", "source": source, "modality": "audio"},
            vector=vector,
        )
        print(f"🎶 Inserted audio from '{source}' into '{collection_name}'.")

    def hybrid_search(self, collection_name: str, query: str, limit: int = 5):
        """Performs a hybrid search (keyword + embedding)."""
        collection = self.get_collection(collection_name)
        if not collection:
            return []

        query_vec = self.embedder.embed_text(query)

        try:
            results = collection.query.hybrid(
                query=query,
                vector=query_vec,
                limit=limit,
            )
            return [obj.properties for obj in results.objects]
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            return []


# --- Example Usage ---
if __name__ == "__main__":
    weaviate_db = WeaviateClientWrapper()
    test_collection = "AILearningApp"

    if weaviate_db.client:
        weaviate_db.create_collection_if_not_exists(test_collection)

        # Insert text
        weaviate_db.insert_text(
            test_collection, "Transformers use self-attention.", "lecture1.pdf"
        )

        # Insert image
        weaviate_db.insert_image(test_collection, "example.png", "slide1.png")

        # Search
        results = weaviate_db.hybrid_search(
            test_collection, "What uses self-attention?"
        )
        print("\nSearch Results:")
        for r in results:
            print(r)
