from sqlalchemy.orm import Session
from app.models.models import Course
from app.schemas.schemas import CourseCreate

def create_course(db: Session, course: CourseCreate):
    # Check if course with same name already exists
    existing_course = db.query(Course).filter(Course.name == course.name).first()
    if existing_course:
        raise ValueError("Course with this name already exists")
    
    db_course = Course(
        name=course.name,
        description=course.description,
        code=course.code,  # This will be None if code is not provided
        num_of_topics=0,
        ingestion_status="pending"
    )
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_courses(db: Session):
    return db.query(Course).all()

def get_course(db: Session, course_id: int):
    return db.query(Course).filter(Course.id == course_id).first()