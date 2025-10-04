from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])


class AskRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class AskResponse(BaseModel):
    answer: str


class QuizRequest(BaseModel):
    topic: str
    num_questions: Optional[int] = 5
    top_k: Optional[int] = 10


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: Optional[str]


class QuizResponse(BaseModel):
    questions: List[QuizQuestion]


class ExplainRequest(BaseModel):
    question: str
    student_answer: str
    correct_answer: str
    top_k: Optional[int] = 5


class ExplainResponse(BaseModel):
    explanation: str


@router.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    rag_service = await RAGService().init()
    answer = await rag_service.ask_question(req.query, top_k=req.top_k)
    return AskResponse(answer=answer)


@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(req: QuizRequest):
    rag_service = await RAGService().init()
    questions = await rag_service.generate_quiz(
        topic=req.topic,
        num_questions=req.num_questions,
        top_k=req.top_k,
    )
    return QuizResponse(questions=questions)


@router.post("/explain", response_model=ExplainResponse)
async def explain_answer(req: ExplainRequest):
    rag_service = await RAGService().init()
    explanation = await rag_service.explain_answer(
        question=req.question,
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        top_k=req.top_k,
    )
    return ExplainResponse(explanation=explanation)
