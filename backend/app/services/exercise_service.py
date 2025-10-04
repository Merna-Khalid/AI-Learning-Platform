from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.question_generation_service import QuestionGenerationService
from app.services.llm_service import LLMService
from app.models.models import Exercise, Exam, ExerciseSubmission, Grade, CodeTestCase
from app.services.code_execution_service import CodeExecutionService
from app.schemas.schemas import QuestionType, DifficultyLevel


class ExerciseService:
    def __init__(self, db: Session):
        self.db = db
        self.question_service = QuestionGenerationService(db)
        self.code_executor = CodeExecutionService()
    
    async def generate_exercises(self, course: str, topics: List[str], 
                            num_questions: int = 5, 
                            difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
                            question_types: Optional[List[QuestionType]] = None) -> Dict[str, Any]:
        """Generate exercises with proper debugging"""
        try:
            # Get context using shared service
            context_text = await self.question_service.get_context_for_topics(1, topics)  # course_id placeholder
            
            if not context_text:
                return {"error": "No relevant materials found for these topics."}

            print(f"Context: {len(context_text)} chars")
            
            # Generate exercises using shared service
            result = await self.question_service.generate_questions(
                context_text=context_text,
                num_questions=num_questions,
                difficulty=difficulty,
                question_type="exercises"
            )
            
            exercises = result.get("exercises", [])
            
            response_data = {
                "course": course,
                "topics": topics,
                "exercises": exercises,
                "generated_at": datetime.now().isoformat(),
                "efficient_generation": result.get("generated_in_single_call", False),
                "count": len(exercises)
            }
            
            # Include debug info in development
            if "_debug" in result:
                response_data["_debug"] = result["_debug"]
            if "error" in result:
                response_data["error"] = result["error"]
                
            print(f"✅ Generated {len(exercises)} exercises")
            return response_data
            
        except Exception as e:
            print(f"❌ Error in generate_exercises: {e}")
            return {
                "error": f"Exercise generation failed: {str(e)}",
                "course": course,
                "topics": topics,
                "exercises": [],
                "generated_at": datetime.now().isoformat()
            }

    async def create_timed_exam(self, course: str, topics: List[str], 
                              duration_minutes: int = 60,
                              num_questions: int = 20,
                              difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> Dict[str, Any]:
        """Create a timed exam with mixed question types"""
        exercises_data = await self.generate_exercises(
            course=course, 
            topics=topics, 
            num_questions=num_questions,
            difficulty=difficulty
        )
        
        if "error" in exercises_data:
            return exercises_data
        
        exam = {
            "exam_id": f"exam_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "course": course,
            "topics": topics,
            "duration_minutes": duration_minutes,
            "total_points": len(exercises_data["exercises"]) * 10,
            "questions": exercises_data["exercises"],
            "instructions": self._get_exam_instructions(duration_minutes),
            "created_at": datetime.now().isoformat()
        }
        
        return exam

    async def grade_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Grade different types of questions using shared service"""
        question_type = submission_data.get("question_type")
        student_answer = submission_data.get("answer")
        reference_data = submission_data.get("reference_data", {})
        question_text = submission_data.get("question")
        
        if not question_type:
            return {"error": "Question type is required"}
        
        try:
            # Convert string to enum if needed
            if isinstance(question_type, str):
                question_type = QuestionType(question_type)
            
            # Use shared grading service
            is_correct, feedback = await self.question_service.grade_answer(
                question_type=question_type,
                question_text=question_text,
                user_answer=student_answer,
                reference_data=reference_data
            )
            
            return {
                "score": 100 if is_correct else 0,
                "correct": is_correct,
                "feedback": feedback,
                "max_score": 100
            }
            
        except Exception as e:
            return {
                "score": 0,
                "correct": False,
                "feedback": f"Grading error: {str(e)}",
                "max_score": 100
            }

    def _get_exam_instructions(self, duration_minutes: int) -> str:
        return f"""
        EXAM INSTRUCTIONS:
        - Time allowed: {duration_minutes} minutes
        - Answer all questions
        - For coding questions, write clean, working code
        - Show your work for math problems
        - Save your progress regularly
        """