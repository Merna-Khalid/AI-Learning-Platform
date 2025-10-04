from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.schemas import AttemptCreate, AttemptOut
from app.services import attempt_service

router = APIRouter(prefix="/attempts", tags=["Attempts"])

@router.post("/", response_model=AttemptOut)
def create_attempt(attempt: AttemptCreate, time_taken: int, db: Session = Depends(get_db)):
    return attempt_service.create_attempt(db, attempt, time_taken)

@router.get("/{quiz_id}", response_model=List[AttemptOut])
def get_attempts(quiz_id: int, db: Session = Depends(get_db)):
    return attempt_service.get_attempts_by_quiz(db, quiz_id)
