from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import logging

from app.core.database import get_db
from app.services.exercise_service import ExerciseService
from app.schemas.schemas import DifficultyLevel

router = APIRouter(prefix="/exercises", tags=["exercises"])
logger = logging.getLogger(__name__)

class GenerateExercisesRequest(BaseModel):
    course: str
    topics: List[str]
    num_questions: int = 5
    difficulty: str = "medium"

@router.post("/generate")
async def generate_exercises(req: GenerateExercisesRequest, db: Session = Depends(get_db)):
    service = ExerciseService(db)
    await service.ensure_llm_initialized()
    
    try:
        difficulty_enum = DifficultyLevel(req.difficulty.lower())
    except ValueError:
        logger.warning(f"Invalid difficulty level: {req.difficulty}. Using 'medium' as default.")
        difficulty_enum = DifficultyLevel.MEDIUM
    
    return await service.generate_exercises(
        course=req.course, 
        topics=req.topics, 
        num_questions=req.num_questions, 
        difficulty=difficulty_enum
    )