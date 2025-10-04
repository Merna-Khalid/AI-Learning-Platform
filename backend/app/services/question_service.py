from sqlalchemy.orm import Session
from app.models.models import Question
from app.schemas.schemas import QuestionCreate

def create_question(db: Session, question: QuestionCreate):
    db_question = Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_questions_by_course(db: Session, course_id: int):
    return db.query(Question).filter(Question.course_id == course_id).all()

def get_questions_by_topic(db: Session, topic_id: int):
    return db.query(Question).filter(Question.topic_id == topic_id).all()
