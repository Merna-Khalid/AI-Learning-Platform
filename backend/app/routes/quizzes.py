from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.core.database import get_db
from app.schemas.schemas import QuizCreate, QuizOut
from app.services.quiz_service import QuizService
from app.models.models import Quiz, Topic

router = APIRouter(prefix="/quiz", tags=["quiz"])

@router.post("/", response_model=QuizOut)
async def create_quiz_route(quiz: QuizCreate, db: Session = Depends(get_db)):
    """Create a new quiz manually"""
    try:
        # Create quiz instance
        db_quiz = Quiz(
            course_id=quiz.course_id,
            num_of_questions=quiz.num_of_questions,
            quiz_type=quiz.quiz_type,
            prev_grade=quiz.prev_grade,
            date_created=datetime.utcnow()
        )
        db.add(db_quiz)
        db.flush()
        
        # Associate topics
        if quiz.topic_ids:
            topics = db.query(Topic).filter(Topic.id.in_(quiz.topic_ids)).all()
            db_quiz.topics.extend(topics)
        
        db.commit()
        db.refresh(db_quiz)
        
        # Convert to QuizOut format
        return QuizOut(
            id=db_quiz.id,
            course_id=db_quiz.course_id,
            num_of_questions=db_quiz.num_of_questions,
            quiz_type=db_quiz.quiz_type,
            prev_grade=db_quiz.prev_grade,
            date_created=db_quiz.date_created,
            topics=[{"id": topic.id, "name": topic.name} for topic in db_quiz.topics]
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create quiz: {str(e)}")

@router.get("/course/{course_id}", response_model=List[QuizOut])
async def get_quizzes_by_course(course_id: int, db: Session = Depends(get_db)):
    """Get all quizzes for a course"""
    service = QuizService(db)
    quizzes_data = service.get_quizzes_by_course(course_id)
    
    # Convert to QuizOut format
    quiz_out_list = []
    for quiz_data in quizzes_data:
        quiz_out = QuizOut(
            id=quiz_data["id"],
            course_id=quiz_data["course_id"],
            num_of_questions=quiz_data["num_of_questions"],
            quiz_type=quiz_data["quiz_type"],
            prev_grade=quiz_data.get("prev_grade"),
            date_created=quiz_data["date_created"],
            topics=quiz_data["topics"]
        )
        quiz_out_list.append(quiz_out)
    
    return quiz_out_list

@router.post("/generate")
async def generate_quiz_route(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Generate a new quiz from topic names (Main endpoint)"""
    service = QuizService(db)
    
    # Extract parameters
    course_id = payload.get("course_id")
    topic_names = payload.get("topic_names", [])
    num_questions = payload.get("num_questions", 20)
    difficulty = payload.get("difficulty", "medium")
    quiz_type = payload.get("quiz_type", "practice")
    
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id is required")
    
    if not topic_names:
        raise HTTPException(status_code=400, detail="At least one topic must be selected")
    
    result = await service.generate_quiz_from_topics(
        course_id=course_id,
        topic_names=topic_names,
        num_questions=num_questions,
        difficulty=difficulty,
        quiz_type=quiz_type
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/{quiz_id}")
async def get_quiz_with_questions(quiz_id: int, db: Session = Depends(get_db)):
    """Get quiz details with questions"""
    service = QuizService(db)
    result = service.get_quiz_with_questions(quiz_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.post("/{quiz_id}/attempt")
async def submit_quiz_attempt(
    quiz_id: int, 
    payload: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """Submit quiz attempt and get results"""
    service = QuizService(db)
    answers = payload.get("answers", {})
    time_taken = payload.get("time_taken", 0)
    
    result = await service.submit_quiz_attempt(
        quiz_id=quiz_id,
        answers=answers,
        time_taken=time_taken
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result