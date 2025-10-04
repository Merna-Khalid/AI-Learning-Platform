from sqlalchemy.orm import Session
from app.models.models import Progress
from app.schemas.schemas import ProgressCreate

def create_progress(db: Session, progress: ProgressCreate):
    db_progress = Progress(
        course_id=progress.course_id,
        num_of_topics_mastered=progress.num_of_topics_mastered,
        num_of_quizzes_taken=progress.num_of_quizzes_taken,
    )
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress

def update_progress(db: Session, course_id: int, mastered: int, quizzes: int):
    db_progress = db.query(Progress).filter(Progress.course_id == course_id).first()
    if db_progress:
        db_progress.num_of_topics_mastered = mastered
        db_progress.num_of_quizzes_taken = quizzes
        db.commit()
        db.refresh(db_progress)
    return db_progress

def get_progress(db: Session, course_id: int):
    return db.query(Progress).filter(Progress.course_id == course_id).first()
