from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.services.exercise_service import ExerciseService

router = APIRouter(prefix="/exams", tags=["exams"])

class CreateTimedExamRequest(BaseModel):
    course: str
    topics: List[str]
    num_questions: int = 20
    difficulty: str = "medium"
    duration_minutes: int = 60

@router.post("/create_timed")
def create_timed_exam(req: CreateTimedExamRequest, db: Session = Depends(get_db)):
    service = ExerciseService(db)
    return service.create_timed_exam(
        course=req.course,
        topics=req.topics,
        num_questions=req.num_questions,
        difficulty=req.difficulty,
        duration_minutes=req.duration_minutes
    )
