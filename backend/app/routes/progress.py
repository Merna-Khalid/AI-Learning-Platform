from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import ProgressCreate, ProgressOut
from app.services import progress_service

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.post("/", response_model=ProgressOut)
def create_progress(progress: ProgressCreate, db: Session = Depends(get_db)):
    return progress_service.create_progress(db, progress)

@router.put("/{course_id}", response_model=ProgressOut)
def update_progress(course_id: int, mastered: int, quizzes: int, db: Session = Depends(get_db)):
    return progress_service.update_progress(db, course_id, mastered, quizzes)

@router.get("/{course_id}", response_model=ProgressOut)
def get_progress(course_id: int, db: Session = Depends(get_db)):
    return progress_service.get_progress(db, course_id)
