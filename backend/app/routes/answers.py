from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.schemas import AnswerCreate, AnswerOut
from app.services import answer_service

router = APIRouter(prefix="/answers", tags=["Answers"])

@router.post("/", response_model=AnswerOut)
def create_answer(answer: AnswerCreate, db: Session = Depends(get_db)):
    return answer_service.create_answer(db, answer)

@router.get("/{attempt_id}", response_model=List[AnswerOut])
def get_answers(attempt_id: int, db: Session = Depends(get_db)):
    return answer_service.get_answers_by_attempt(db, attempt_id)
