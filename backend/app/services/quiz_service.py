import json
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.models import Quiz, Topic, Question, Attempt, Answer, Course, Material
from app.schemas.schemas import QuizCreate, QuizOut, QuestionType, DifficultyLevel, QuizType
from app.services.question_generation_service import QuestionGenerationService


logger = logging.getLogger(__name__)


class QuizService:
    def __init__(self, db: Session):
        self.db = db
        self.question_service = QuestionGenerationService(db)

    async def generate_quiz_from_topics(self, course_id: int, topic_names: List[str], 
                                      num_questions: int = 20, 
                                      difficulty: str = "medium",
                                      quiz_type: str = "practice") -> Dict[str, Any]:
        """Generate a complete quiz with questions from topic names"""
        # Convert string parameters to enums
        try:
            difficulty_enum = DifficultyLevel(difficulty)
        except ValueError:
            difficulty_enum = DifficultyLevel.MEDIUM
            logger.warning(f"Invalid difficulty: {difficulty}, using 'medium'")
        
        try:
            quiz_type_enum = QuizType(quiz_type)
        except ValueError:
            quiz_type_enum = QuizType.PRACTICE
            logger.warning(f"Invalid quiz_type: {quiz_type}, using 'practice'")
        
        logger.info(f"Generating quiz: {num_questions} questions, {difficulty_enum.value} difficulty, {quiz_type_enum.value} type")
        logger.info(f"Topics: {topic_names}")
        
        try:
            # Get or create topics by name for this course
            topic_ids = await self._get_or_create_topics(course_id, topic_names)
            if not topic_ids:
                return {"error": "No valid topics found or created"}
            
            # Get context using shared service
            context_text = await self.question_service.get_context_for_topics(course_id, topic_names)
            if not context_text:
                return {"error": "No relevant content found for the selected topics"}
            
            logger.info(f"Context length: {len(context_text)} chars")
            
            # Generate quiz questions using shared service
            quiz_data = await self.question_service.generate_questions(
                context_text=context_text,
                num_questions=num_questions,
                difficulty=difficulty_enum,
                question_type="quiz"
            )
            
            if "error" in quiz_data:
                return quiz_data
            
            # Create quiz in database
            quiz = self._create_quiz_in_db(
                course_id=course_id,
                topic_ids=topic_ids,
                num_questions=num_questions,
                quiz_type=quiz_type_enum,
                questions_data=quiz_data.get("questions", [])
            )
            
            logger.info(f"✅ Quiz created with ID: {quiz.id}, {len(quiz.questions)} questions")
            
            return {
                "id": quiz.id,
                "course_id": course_id,
                "quiz_type": quiz.quiz_type.value,
                "num_of_questions": quiz.num_of_questions,
                "date_created": quiz.date_created,
                "questions": self._format_questions_for_response(quiz.questions),
                "topics": [{"id": topic.id, "name": topic.name} for topic in quiz.topics]
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating quiz: {str(e)}")
            return {"error": f"Failed to generate quiz: {str(e)}"}

    async def submit_quiz_attempt(self, quiz_id: int, answers: Dict[str, Any], 
                            time_taken: int = 0) -> Dict[str, Any]:
        """Submit quiz attempt and grade answers using shared service"""
        try:
            quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if not quiz:
                return {"error": "Quiz not found"}
            
            # Create attempt
            attempt = Attempt(
                quiz_id=quiz_id,
                date=datetime.utcnow(),
                time_taken=time_taken
            )
            self.db.add(attempt)
            self.db.flush()
            
            # Grade each answer using shared service
            total_questions = len(quiz.questions)
            correct_answers = 0
            
            for question in quiz.questions:
                user_answer = answers.get(str(question.id))
                reference_data = question.extra_metadata or {}
                
                is_correct, grading_feedback = await self.question_service.grade_answer(
                    question_type=question.type,
                    question_text=question.text,
                    user_answer=user_answer,
                    reference_data=reference_data
                )
                
                if is_correct:
                    correct_answers += 1
                
                answer = Answer(
                    question_id=question.id,
                    attempt_id=attempt.id,
                    answer_text=str(user_answer) if user_answer else None,
                    is_correct=is_correct,
                    grading_notes=grading_feedback
                )
                self.db.add(answer)
            
            # Calculate final grade
            final_grade = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            attempt.final_grade = final_grade
            attempt.grading_notes = f"{correct_answers}/{total_questions} correct"
            
            self.db.commit()
            self.db.refresh(attempt)
            
            return {
                "attempt_id": attempt.id,
                "final_grade": final_grade,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "time_taken": time_taken,
                "answers": [
                    {
                        "question_id": answer.question_id,
                        "answer_text": answer.answer_text,
                        "is_correct": answer.is_correct,
                        "grading_notes": answer.grading_notes
                    }
                    for answer in attempt.answers
                ]
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error submitting quiz attempt: {e}")
            return {"error": f"Failed to submit quiz attempt: {str(e)}"}

    # ... keep the remaining methods that are specific to QuizService
    async def _get_or_create_topics(self, course_id: int, topic_names: List[str]) -> List[int]:
        """Get existing topics or create new ones for the given names"""
        topic_ids = []
        
        for topic_name in topic_names:
            topic = self.db.query(Topic).filter(
                Topic.course_id == course_id,
                Topic.name == topic_name
            ).first()
            
            if topic:
                topic_ids.append(topic.id)
                logger.info(f"Found existing topic: {topic_name} (ID: {topic.id})")
            else:
                new_topic = Topic(
                    course_id=course_id,
                    name=topic_name,
                    description=f"Auto-generated topic for quiz: {topic_name}"
                )
                self.db.add(new_topic)
                self.db.flush()
                topic_ids.append(new_topic.id)
                logger.info(f"Created new topic: {topic_name} (ID: {new_topic.id})")
        
        self.db.commit()
        return topic_ids

    def _create_quiz_in_db(self, course_id: int, topic_ids: List[int], num_questions: int,
                      quiz_type: QuizType, questions_data: List[Dict[str, Any]]) -> Quiz:
        """Create quiz and questions in database"""
        quiz = Quiz(
            course_id=course_id,
            num_of_questions=num_questions,
            quiz_type=quiz_type,
            date_created=datetime.utcnow()
        )
        self.db.add(quiz)
        self.db.flush()
        
        topics = self.db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
        quiz.topics.extend(topics)
        
        for i, q_data in enumerate(questions_data):
            raw_type = q_data.get('type', 'MCQ').upper()
            
            type_mapping = {
                'MCQ': QuestionType.MCQ,
                'MULTIPLE_CHOICE': QuestionType.MCQ,
                'SHORT_ANSWER': QuestionType.SHORT_ANSWER,
                'TRUE_FALSE': QuestionType.TRUE_FALSE,
                'TRUE_FALSE_INPUT': QuestionType.TRUE_FALSE,
                'INPUT': QuestionType.SHORT_ANSWER
            }
            
            question_type = type_mapping.get(raw_type, QuestionType.MCQ)
            
            try:
                difficulty = DifficultyLevel(q_data.get('difficulty', 'medium'))
            except ValueError:
                difficulty = DifficultyLevel.MEDIUM
            
            question = Question(
                quiz_id=quiz.id,
                text=q_data.get('question', ''),
                type=question_type,
                difficulty=difficulty,
                extra_metadata={
                    'options': q_data.get('options', []),
                    'correct_answer': q_data.get('correct_answer'),
                    'explanation': q_data.get('explanation', ''),
                    'expected_answer': q_data.get('expected_answer'),
                    'key_points': q_data.get('key_points', [])
                }
            )
            self.db.add(question)
        
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def _format_questions_for_response(self, questions: List[Question]) -> List[Dict[str, Any]]:
        """Format questions for API response"""
        formatted_questions = []
        for question in questions:
            formatted = {
                "id": question.id,
                "text": question.text,
                "type": question.type.value,
                "difficulty": question.difficulty.value,
                "extra_metadata": question.extra_metadata or {}
            }
            formatted_questions.append(formatted)
        return formatted_questions

    def get_quiz_with_questions(self, quiz_id: int) -> Dict[str, Any]:
        """Get quiz details with questions"""
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return {"error": "Quiz not found"}
        
        return {
            "id": quiz.id,
            "course_id": quiz.course_id,
            "quiz_type": quiz.quiz_type.value,
            "num_of_questions": quiz.num_of_questions,
            "date_created": quiz.date_created,
            "prev_grade": quiz.prev_grade,
            "questions": self._format_questions_for_response(quiz.questions),
            "topics": [{"id": topic.id, "name": topic.name} for topic in quiz.topics],
            "latest_attempt": self._get_latest_attempt(quiz_id) if quiz.attempts else None
        }
    
    def _get_latest_attempt(self, quiz_id: int) -> Dict[str, Any]:
        """Get the latest attempt with answers"""
        attempt = self.db.query(Attempt).filter(
            Attempt.quiz_id == quiz_id
        ).order_by(Attempt.date.desc()).first()
        
        if not attempt:
            return None
        
        return {
            "id": attempt.id,
            "date": attempt.date,
            "final_grade": attempt.final_grade,
            "answers": [
                {
                    "question_id": answer.question_id,
                    "answer_text": answer.answer_text,
                    "is_correct": answer.is_correct,
                    "grading_notes": answer.grading_notes
                }
                for answer in attempt.answers
            ]
        }

    def get_quizzes_by_course(self, course_id: int) -> List[Dict[str, Any]]:
        """Get all quizzes for a course"""
        quizzes = self.db.query(Quiz).filter(Quiz.course_id == course_id).all()
        return [
            {
                "id": quiz.id,
                "course_id": quiz.course_id,
                "quiz_type": quiz.quiz_type.value,
                "num_of_questions": quiz.num_of_questions,
                "date_created": quiz.date_created,
                "prev_grade": quiz.prev_grade,
                "topics": [{"id": topic.id, "name": topic.name} for topic in quiz.topics]
            }
            for quiz in quizzes
        ]

    def create_quiz_manual(self, quiz_data: QuizCreate) -> Quiz:
        """Create a quiz manually"""
        try:
            quiz = Quiz(
                course_id=quiz_data.course_id,
                num_of_questions=quiz_data.num_of_questions,
                quiz_type=quiz_data.quiz_type,
                prev_grade=quiz_data.prev_grade,
                date_created=datetime.utcnow()
            )
            self.db.add(quiz)
            self.db.flush()
            
            if quiz_data.topic_ids:
                topics = self.db.query(Topic).filter(Topic.id.in_(quiz_data.topic_ids)).all()
                quiz.topics.extend(topics)
            
            self.db.commit()
            self.db.refresh(quiz)
            return quiz
            
        except Exception as e:
            self.db.rollback()
            raise e