from sqlalchemy.orm import Session
from app.models.models import Topic
from app.schemas.schemas import TopicCreate

def create_topic(db: Session, topic: TopicCreate):
    db_topic = Topic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

def get_topics_by_course(db: Session, course_id: int):
    return db.query(Topic).filter(Topic.course_id == course_id).all()

