from sqlalchemy.orm import Session
from datetime import datetime
from app.models.models import Attempt
from app.schemas.schemas import AttemptCreate

def create_attempt(db: Session, attempt: AttemptCreate, time_taken: int):
    db_attempt = Attempt(
        quiz_id=attempt.quiz_id,
        date=datetime.utcnow(),
        time_taken=time_taken,
        final_grade=attempt.final_grade,
        grading_notes=attempt.grading_notes
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt

def get_attempts_by_quiz(db: Session, quiz_id: int):
    return db.query(Attempt).filter(Attempt.quiz_id == quiz_id).all()

def get_attempt(db: Session, attempt_id: int):
    return db.query(Attempt).filter(Attempt.id == attempt_id).first()
