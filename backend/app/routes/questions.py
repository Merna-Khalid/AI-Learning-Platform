from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.schemas import QuestionCreate, QuestionOut
from app.services import question_service

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/", response_model=QuestionOut)
def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    return question_service.create_question(db, question)

@router.get("/{quiz_id}", response_model=List[QuestionOut])
def get_questions(quiz_id: int, db: Session = Depends(get_db)):
    return question_service.get_questions_by_quiz(db, quiz_id)
