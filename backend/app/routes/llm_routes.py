from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.llm_service import LLMService, get_llm_service

router = APIRouter(prefix="/llm", tags=["LLM"])

# Request/response models
class SummarizeRequest(BaseModel):
    text: str

class SummarizeResponse(BaseModel):
    summary: str

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest, service: LLMService = Depends(get_llm_service)):
    summary = service.summarize_text(req.text)
    return SummarizeResponse(summary=summary)


class QuizRequest(BaseModel):
    context: str
    num_questions: int = 5
    difficulty: str = "medium"

class QuizResponse(BaseModel):
    questions: List[Dict[str, Any]]

@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(req: QuizRequest, service: LLMService = Depends(get_llm_service)) -> QuizResponse:
    questions = service.create_quiz(
        context=req.context, 
        num_questions=req.num_questions, 
        difficulty=req.difficulty
    )
    return QuizResponse(questions=questions)


class GradeRequest(BaseModel):
    question: str
    reference_answer: str
    student_answer: str

class GradeResponse(BaseModel):
    score: int
    feedback: str
    correctness: str

@router.post("/grade", response_model=GradeResponse)
async def grade_answer(req: GradeRequest, service: LLMService = Depends(get_llm_service)) -> GradeResponse:
    result = service.grade_answer(req.question, req.reference_answer, req.student_answer)
    return GradeResponse(**result)