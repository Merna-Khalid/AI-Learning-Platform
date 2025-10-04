import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.schemas.schemas import QuestionType, DifficultyLevel
from app.models.models import Material, Topic

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    """Shared service for generating and grading questions across exercises and quizzes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = None
    
    async def ensure_llm_initialized(self):
        """Ensure LLM service is initialized"""
        if self.llm_service is None:
            self.llm_service = LLMService()
            await self.llm_service.init()

    # Context Retrieval
    async def get_context_for_topics(self, course_id: int, topic_names: List[str]) -> str:
        """Get context from materials associated with topic names"""
        try:
            materials = self.db.query(Material).filter(Material.course_id == course_id).all()
            relevant_materials = []
            
            for material in materials:
                if material.extracted_topics:
                    try:
                        if isinstance(material.extracted_topics, str):
                            material_topics = json.loads(material.extracted_topics)
                        else:
                            material_topics = material.extracted_topics
                        
                        if any(topic in material_topics for topic in topic_names):
                            relevant_materials.append(material)
                            logger.info(f"Found relevant material: {material.filename}")
                    except Exception as e:
                        logger.warning(f"Could not parse topics for material {material.id}: {e}")
                        continue
            
            if not relevant_materials:
                logger.warning("No relevant materials found for topics")
                return f"Topics: {', '.join(topic_names)}. General course content covering these subjects."
            
            context_chunks = []
            for material in relevant_materials[:5]:
                context_chunks.append(f"Material: {material.filename}")
                if hasattr(material, 'description') and material.description:
                    context_chunks.append(f"Description: {material.description}")
                
                if material.extracted_topics:
                    try:
                        if isinstance(material.extracted_topics, str):
                            topics = json.loads(material.extracted_topics)
                        else:
                            topics = material.extracted_topics
                        context_chunks.append(f"Topics covered: {', '.join(topics)}")
                    except:
                        pass
            
            context = "\n\n".join(context_chunks)
            logger.info(f"📖 Built context from {len(relevant_materials)} materials")
            return context
            
        except Exception as e:
            logger.error(f"Error getting context from topic names: {e}")
            return f"Course topics: {', '.join(topic_names)}. Comprehensive coverage of these subjects."

    # Question Generation
    async def generate_questions(self, context_text: str, num_questions: int, 
                               difficulty: DifficultyLevel, question_type: str = "exercises") -> Dict[str, Any]:
        """Generate questions or exercises using LLM"""
        await self.ensure_llm_initialized()
        
        if question_type == "exercises":
            return await self.llm_service.choose_and_generate_exercises(
                context_text=context_text,
                num_questions=num_questions,
                difficulty=difficulty
            )
        else:  # quiz questions
            return await self.llm_service.generate_quiz_questions(
                context_text=context_text,
                num_questions=num_questions,
                difficulty=difficulty,
                quiz_type="practice"
            )

    # Grading Logic
    async def grade_answer(self, question_type: QuestionType, question_text: str, 
                         user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade an answer based on question type"""
        if not user_answer or not str(user_answer).strip():
            return False, "No answer provided"
        
        question_type_str = question_type.value if hasattr(question_type, 'value') else str(question_type)
        question_type_str = question_type_str.upper()
        
        grading_methods = {
            'MCQ': self._grade_mcq,
            'TRUE_FALSE': self._grade_true_false,
            'SHORT_ANSWER': self._grade_short_answer,
            'LONG_ANSWER': self._grade_long_answer,
            'FILL_BLANK': self._grade_fill_blank,
            'MATCHING': self._grade_matching
        }
        
        if question_type_str in grading_methods:
            return await grading_methods[question_type_str](user_answer, reference_data)
        else:
            return await self._grade_generic(user_answer, reference_data)

    async def _grade_mcq(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade Multiple Choice Question"""
        correct_answer = reference_data.get('correct_answer')
        options = reference_data.get('options', [])
        explanation = reference_data.get('explanation', '')
        
        if not correct_answer:
            return False, "Missing correct answer data"
        
        user_clean = str(user_answer).strip().upper()
        correct_clean = str(correct_answer).strip().upper()
        
        # Handle text-based correct answers by mapping to option letters
        if len(correct_clean) > 1 and options:
            correct_option_index = -1
            for i, option in enumerate(options):
                if correct_clean in option.upper() or option.upper() in correct_clean:
                    correct_option_index = i
                    break
            
            if correct_option_index >= 0:
                correct_clean = chr(65 + correct_option_index)
            else:
                return False, "Error in question data"
        
        is_correct = user_clean == correct_clean
        
        if is_correct:
            return True, f"Correct! {explanation}"
        else:
            # Find correct option text for feedback
            try:
                correct_index = ord(correct_clean) - ord('A')
                if 0 <= correct_index < len(options):
                    correct_text = options[correct_index]
                    return False, f"Incorrect. The correct answer is {correct_clean}: {correct_text}. {explanation}"
            except (TypeError, ValueError):
                pass
            
            return False, f"Incorrect. Correct answer is {correct_clean}. {explanation}"

    async def _grade_true_false(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade True/False Question"""
        correct_answer = reference_data.get('correct_answer')
        explanation = reference_data.get('explanation', '')
        
        if not correct_answer:
            return False, "Missing correct answer data"
        
        user_clean = str(user_answer).strip().lower()
        correct_clean = str(correct_answer).strip().lower()
        is_correct = user_clean == correct_clean
        
        if is_correct:
            return True, f"Correct! {explanation}"
        else:
            return False, f"Incorrect. The correct answer is {correct_clean}. {explanation}"

    async def _grade_short_answer(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade Short Answer using LLM"""
        expected_answer = reference_data.get('expected_answer')
        explanation = reference_data.get('explanation', '')
        
        if not expected_answer:
            return await self._grade_generic(user_answer, reference_data)
        
        try:
            await self.ensure_llm_initialized()
            
            prompt = f"""
            Evaluate the following student answer for an educational quiz question.
            
            EXPECTED ANSWER KEY POINTS: {expected_answer}
            
            STUDENT ANSWER: {user_answer}
            
            Grading Criteria:
            - Focus on whether the student demonstrates UNDERSTANDING of the core concepts
            - Accept answers that show comprehension even if wording differs
            - Consider answers that capture the essence correct, even if incomplete
            - "I don't know" or similar indicates lack of understanding = INCORRECT
            - Answers showing partial understanding but missing key points = INCORRECT
            - Answers must demonstrate actual knowledge, not just rephrasing the question
            
            Return ONLY "CORRECT" if the answer demonstrates understanding, otherwise "INCORRECT".
            """
            
            response = await self.llm_service.generate(prompt, temperature=0.1, max_tokens=10)
            response_clean = response.strip().upper()
            
            logger.info(f"🤖 LLM grading result: '{response_clean}' for answer: '{user_answer[:100]}...'")
            
            is_correct = "CORRECT" in response_clean
            
            if is_correct:
                feedback = f"Correct! Your answer demonstrates understanding of the key concepts. {explanation}"
            else:
                feedback = f"Your answer could be improved. Key points to include: {expected_answer}. {explanation}"
            
            return is_correct, feedback
            
        except Exception as e:
            logger.error(f"❌ LLM grading failed: {e}")
            is_correct = self._lenient_fallback_grading(user_answer)
            feedback = "Automated evaluation: " + ("Your answer shows engagement with the question." if is_correct else "Please provide a more substantive answer.")
            return is_correct, feedback

    async def _grade_long_answer(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade Long Answer using detailed rubrics"""
        expected_answer = reference_data.get('expected_answer')
        
        if not expected_answer:
            return await self._grade_generic(user_answer, reference_data)
        
        try:
            await self.ensure_llm_initialized()
            
            prompt = f"""
            Grade this long answer using comprehensive rubrics.
            
            EXPECTED ANSWER: {expected_answer}
            STUDENT ANSWER: {user_answer}
            
            Evaluate on:
            - Content accuracy (40%)
            - Completeness (30%)
            - Clarity and organization (20%)
            - Depth of analysis (10%)
            
            Return ONLY "CORRECT" if overall score >= 70%, otherwise "INCORRECT".
            """
            
            response = await self.llm_service.generate(prompt, temperature=0.0, max_tokens=10)
            response_clean = response.strip().upper()
            
            is_correct = "CORRECT" in response_clean
            feedback = "Your answer meets the required standards." if is_correct else "Please provide a more comprehensive answer with better organization and analysis."
            
            return is_correct, feedback
            
        except Exception as e:
            logger.error(f"❌ LLM grading failed for long answer: {e}")
            return await self._grade_generic(user_answer, reference_data)

    async def _grade_fill_blank(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade fill-in-the-blank questions"""
        correct_answer = reference_data.get('correct_answer')
        alternatives = reference_data.get('alternatives', [])
        explanation = reference_data.get('explanation', '')
        
        if not correct_answer:
            return False, "Missing correct answer data"
        
        user_clean = user_answer.lower().strip()
        correct_clean = correct_answer.lower().strip()
        
        # Check exact match or alternatives
        is_correct = (user_clean == correct_clean or 
                     any(user_clean == alt.lower().strip() for alt in alternatives))
        
        if is_correct:
            return True, f"Correct! {explanation}"
        else:
            return False, f"Incorrect. Expected: {correct_answer}. {explanation}"

    async def _grade_matching(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Grade matching questions"""
        try:
            correct_matches = reference_data.get('correct_matches', [])
            user_matches = json.loads(user_answer) if isinstance(user_answer, str) else user_answer
            
            if not isinstance(user_matches, list):
                return False, "Invalid answer format for matching question"
            
            correct_count = sum(1 for user_match in user_matches
                              for correct_match in correct_matches
                              if (user_match.get('left_index') == correct_match.get('left_index') and
                                  user_match.get('right_index') == correct_match.get('right_index')))
            
            total = len(correct_matches)
            is_correct = correct_count == total
            
            if is_correct:
                return True, "All matches correct! Well done."
            else:
                return False, f"{correct_count}/{total} matches correct. Review the material and try again."
                
        except Exception as e:
            logger.error(f"Error grading matching question: {e}")
            return False, "Error evaluating your matching answers."

    async def _grade_generic(self, user_answer: Any, reference_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Generic grading fallback"""
        expected_answer = reference_data.get('expected_answer') or reference_data.get('correct_answer')
        
        if not expected_answer:
            return False, "Unable to grade this answer automatically."
        
        # Simple text comparison
        user_clean = str(user_answer).lower().strip()
        expected_clean = str(expected_answer).lower().strip()
        
        is_correct = expected_clean in user_clean or user_clean in expected_clean
        
        if is_correct:
            return True, "Your answer appears to be correct."
        else:
            return False, f"Expected answer should include: {expected_answer}"

    def _lenient_fallback_grading(self, user_answer: str) -> bool:
        """Lenient fallback grading for when LLM fails"""
        if not user_answer or len(user_answer.strip()) < 3:
            return False
        
        negative_indicators = ["i don't know", "idk", "no idea", "not sure", "can't remember"]
        user_lower = user_answer.lower()
        
        if any(indicator in user_lower for indicator in negative_indicators):
            return False
        
        # If answer has reasonable length and doesn't contain negative indicators, be lenient
        return len(user_answer.strip()) > 10

    # Utility Methods
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return {"error": "Could not parse response", "raw_response": response[:200]}

    def create_fallback_question(self, question_type: QuestionType, context: str, index: int) -> Dict[str, Any]:
        """Create a quality fallback question"""
        short_context = context[:100] + "..." if len(context) > 100 else context
        
        base_question = {
            "type": question_type.value,
            "question": f"Question {index + 1}: Explain key concepts from: {short_context}",
            "explanation": "This question encourages reviewing and synthesizing key information.",
            "_fallback": True
        }
        
        if question_type == QuestionType.MCQ:
            base_question.update({
                "options": [
                    "Review the fundamental concepts",
                    "Analyze the main principles", 
                    "Consider the theoretical framework",
                    "Evaluate practical applications"
                ],
                "correct_answer": "A"
            })
        elif question_type == QuestionType.SHORT_ANSWER:
            base_question.update({
                "expected_answer": "The context covers important concepts that should be reviewed and understood.",
                "key_points": ["Understand main ideas", "Identify key terminology", "Apply concepts"]
            })
        elif question_type == QuestionType.TRUE_FALSE:
            base_question.update({
                "question": f"The concepts in '{short_context}' are important to understand.",
                "correct_answer": "true"
            })
        
        return base_question