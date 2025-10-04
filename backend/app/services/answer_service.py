from sqlalchemy.orm import Session
from app.models.models import Answer
from app.schemas.schemas import AnswerCreate

def create_answer(db: Session, answer: AnswerCreate):
    db_answer = Answer(
        question_id=answer.question_id,
        attempt_id=answer.attempt_id,
        answer=answer.answer,
        is_correct=answer.is_correct,
        grading_notes=answer.grading_notes
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def get_answers_by_attempt(db: Session, attempt_id: int):
    return db.query(Answer).filter(Answer.attempt_id == attempt_id).all()

def get_answer(db: Session, answer_id: int):
    return db.query(Answer).filter(Answer.id == answer_id).first()
