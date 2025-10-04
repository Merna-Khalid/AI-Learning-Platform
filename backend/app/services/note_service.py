from typing import Dict, Any
from app.services.llm_service import LLMService
from rag.retriever import Retriever

class NoteService:
    """
    Generates study notes using RAG (Retriever + LLM).
    """

    def __init__(self, llm_service: LLMService = None, retriever: Retriever = None):
        self.llm_service = llm_service or LLMService()
        self.retriever = retriever or Retriever()

    def generate_notes(self, course: str, topic: str) -> Dict[str, Any]:
        """
        Retrieve relevant context from Weaviate and generate structured notes.
        """
        query = f"Generate study notes for {course}, topic: {topic}"
        context_chunks = self.retriever.retrieve_context(course, query, top_k=5)

        if not context_chunks:
            return {
                "topic": topic,
                "summary": "No context found in knowledge base.",
                "key_points": []
            }

        response = self.llm_service.answer_with_context(query=query, context=context_chunks)

        # You could parse key points if the model outputs them as bullets
        return {
            "topic": topic,
            "summary": response,
            "key_points": []
        }
