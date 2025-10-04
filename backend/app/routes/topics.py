from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.schemas import TopicCreate, TopicOut
from app.services import topic_service

router = APIRouter(prefix="/topics", tags=["Topics"])

@router.post("/", response_model=TopicOut)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    return topic_service.create_topic(db, topic)

@router.get("/{course_id}", response_model=List[TopicOut])
def get_topics(course_id: int, db: Session = Depends(get_db)):
    return topic_service.get_topics_by_course(db, course_id)
