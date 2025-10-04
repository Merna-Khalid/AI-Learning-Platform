from typing import List, Optional
from llm.gemma_client import GemmaClient
from rag.retriever import Retriever


class RAGService:
    """
    Service layer that wires together Retriever (Weaviate) + GemmaClient (LLM).
    Provides high-level methods for answering questions and generating quizzes.
    """

    def __init__(self, collection_name: str = "AILearningApp"):
        self.retriever = Retriever()
        self.llm = None

    async def init(self):
        self.llm = await GemmaClient(auto_start=False).init()
        return self

    async def ask_question(self, collection_name: str, query: str, top_k: int = 5) -> str:
        """
        Retrieve context from Weaviate and ask the LLM for an answer.
        """
        contexts = self.retriever.retrieve_context(collection_name, query, top_k=top_k)

        context_str = "\n\n".join(contexts)
        prompt = (
            f"You are a teaching assistant. Use the context below to answer the question.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {query}\n"
            f"Answer in a clear and structured way."
        )

        response = await self.llm.generate_text(prompt)
        return response

    async def generate_quiz(self, collection_name: str, topic: str, num_questions: int = 5, top_k: int = 10) -> List[dict]:
        """
        Generate quiz questions for a given topic, grounded in retrieved context.
        Returns a list of {question, options, correct_answer}.
        """
        contexts = self.retriever.retrieve_context(collection_name, topic, top_k=top_k)
        context_str = "\n\n".join(contexts)

        prompt = (
            f"Generate {num_questions} multiple-choice quiz questions for the topic: {topic}.\n"
            f"Use the context provided:\n\n{context_str}\n\n"
            f"Format your response as JSON with the structure:\n"
            f"[{{'question': str, 'options': [str, str, str, str], 'correct_answer': str}}]"
        )

        raw_response = await self.llm.generate_text(prompt)

        try:
            # naive parsing – you may want to improve this with `json.loads`
            import json
            questions = json.loads(raw_response)
        except Exception:
            # fallback: wrap the response as a single question if parsing fails
            questions = [{
                "question": raw_response,
                "options": [],
                "correct_answer": None
            }]

        return questions

    async def explain_answer(self, collection_name: str, question: str, student_answer: str, correct_answer: str, top_k: int = 5) -> str:
        """
        Provide feedback on a student's answer, grounded in retrieved context.
        """
        contexts = self.retriever.retrieve_context(collection_name, question, top_k=top_k)
        context_str = "\n\n".join(contexts)

        prompt = (
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n"
            f"Student's answer: {student_answer}\n"
            f"Correct answer: {correct_answer}\n\n"
            f"Explain whether the student's answer is correct and provide a helpful explanation."
        )

        return await self.llm.generate_text(prompt)
