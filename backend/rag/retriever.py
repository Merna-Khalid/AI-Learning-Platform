from rag.weaviate_client import WeaviateClientWrapper
from typing import List
import re


class Retriever:
    """
    Retrieves relevant chunks from Weaviate for a query.
    Used by LLM (Gemma) to provide RAG answers.
    """

    def __init__(self):
        self.client = WeaviateClientWrapper()


    def _slugify_collection(self, name: str) -> str:
        # Remove non-alphanumeric characters
        cleaned = re.sub(r'[^0-9a-zA-Z]+', ' ', name)
        # Split into words and capitalize
        parts = cleaned.strip().split()
        if not parts:
            raise ValueError("Collection name cannot be empty after slugify")
        # Join into PascalCase
        pascal = ''.join(p.capitalize() for p in parts)
        return pascal


    def retrieve_context(self, collection_name: str, query: str, top_k: int = 5) -> List[str]:
        """
        Returns a list of relevant text chunks for the query.
        """
        results = self.client.hybrid_search(self._slugify_collection(collection_name),
                                            query, 
                                            limit=top_k)
        contexts = []
        for r in results:
            if "text" in r:
                contexts.append(r["text"])
        return contexts
