import json
import re
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from llm.gemma_client import GemmaClient
from app.schemas.schemas import QuestionType, DifficultyLevel

# Set up logging
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = None
        self._initialized = False
        self._last_request_time = 0
        self._min_request_interval = 2.0
        self.request_counter = 0
        self.max_items_per_call = 5
    
    async def init(self):
        if not self._initialized:
            self.client = GemmaClient(auto_start=False)
            self.client = await self.client.init()
            self._initialized = True
        return self
    
    async def ensure_initialized(self):
        """Ensure client is initialized before making requests"""
        if not self._initialized:
            await self.init()

    def _log_prompt_response(self, prompt: str, response: str, error: str = None, attempt: int = None):
        """Log prompt and response with request ID"""
        self.request_counter += 1
        request_id = self.request_counter
        
        log_entries = [
            f"LLM REQUEST #{request_id}" + (f" (Attempt {attempt})" if attempt else ""),
            f"PROMPT ({len(prompt)} chars):",
            f"```\n{prompt}\n```"
        ]
        
        if error:
            log_entries.append(f"❌ ERROR: {error}")
        else:
            log_entries.extend([
                f"RESPONSE ({len(response)} chars):",
                f"```\n{response}\n```"
            ])
        
        log_entries.append(f"END REQUEST #{request_id}")
        
        for entry in log_entries:
            logger.info(entry)

        # File logging
        try:
            with open("/app/logs/llm_requests.log", "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"REQUEST #{request_id} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n")
                f.write(f"PROMPT ({len(prompt)} chars):\n{prompt}\n\n")
                if error:
                    f.write(f"ERROR: {error}\n\n")
                else:
                    f.write(f"RESPONSE ({len(response)} chars):\n{response}\n")
                f.write(f"{'='*80}\n\n")
        except Exception as e:
            logger.warning(f"Could not write to log file: {e}")

    async def _rate_limit(self):
        """Implement rate limiting between requests"""
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            logger.info(f"⏳ Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

    async def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Generate text using LLM with rate limiting"""
        await self.ensure_initialized()
        
        logger.info(f"Starting generation: {len(prompt)} chars, {max_tokens} tokens, temp {temperature}")
        
        await self._rate_limit()
        self._last_request_time = time.time()
        
        start_time = time.time()
        try:
            logger.info("Sending request to LLM server...")
            result = await self.client.generate(
                prompt, 
                temperature=temperature, 
                max_tokens=max_tokens
            )
            elapsed = time.time() - start_time
            
            logger.info(f"Generation completed in {elapsed:.1f}s")
            self._log_prompt_response(prompt, result)
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Generation failed after {elapsed:.1f}s: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self._log_prompt_response(prompt, "", error=error_msg)
            raise

    async def generate_structured_response(self, prompt: str, expected_format: Dict[str, Any], 
                                        max_retries: int = 2) -> Dict[str, Any]:
        """Generate and parse structured JSON response with retries"""
        await self.ensure_initialized()
        
        logger.info(f"Structured request: {len(prompt)} chars, expecting {expected_format}, {max_retries} retries")
        
        for attempt in range(max_retries + 1):
            attempt_num = attempt + 1
            logger.info(f"Attempt {attempt_num}/{max_retries + 1}")
            
            try:
                current_prompt = self._build_retry_prompt(prompt, attempt_num, max_retries)
                response = await self.generate(current_prompt, temperature=0.1, max_tokens=1200)
                
                json_data = self._extract_and_validate_json(response, expected_format, attempt_num)
                if json_data:
                    logger.info(f"Valid JSON received on attempt {attempt_num}")
                    return json_data
                else:
                    logger.warning(f"Invalid JSON on attempt {attempt_num}")
                
                if attempt == max_retries:
                    return await self._final_structured_attempt(prompt, expected_format)
            
            except Exception as e:
                logger.error(f"Exception on attempt {attempt_num}: {str(e)}")
                if attempt == max_retries:
                    return self._build_error_result(prompt, str(e), attempt_num)
                await asyncio.sleep(1)
        
        return self._build_error_result(prompt, "All generation attempts failed", max_retries + 1)

    def _build_retry_prompt(self, prompt: str, attempt_num: int, max_retries: int) -> str:
        """Build prompt with retry instructions"""
        if attempt_num == 1:
            return prompt
        return f"{prompt}\n\nNOTE: This is attempt {attempt_num}. Please ensure valid JSON response."

    async def _final_structured_attempt(self, prompt: str, expected_format: Dict[str, Any]) -> Dict[str, Any]:
        """Final attempt with strict JSON instructions"""
        logger.info("Final attempt - using strict JSON instructions")
        retry_prompt = f"""
        CRITICAL: You MUST return ONLY valid JSON. No other text, no explanations, no markdown.

        REQUIRED JSON STRUCTURE:
        {json.dumps(expected_format, indent=2)}

        CONTENT REQUIREMENTS:
        {prompt}

        Remember: ONLY JSON, nothing else.
        """
        response = await self.generate(retry_prompt, temperature=0.0, max_tokens=1200)
        json_data = self._extract_and_validate_json(response, expected_format, "final")
        if json_data:
            logger.info("Valid JSON on final attempt!")
            return json_data
        return self._build_error_result(prompt, "Final structured attempt failed", "final")

    def _build_error_result(self, prompt: str, error: str, attempts: int) -> Dict[str, Any]:
        """Build consistent error result structure"""
        return {
            "error": error,
            "attempts": attempts,
            "last_prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt
        }

    def _extract_and_validate_json(self, text: str, expected_format: Dict[str, Any], attempt: str) -> Optional[Dict[str, Any]]:
        """Extract and validate JSON from text response"""
        logger.info(f"Attempting JSON extraction (attempt {attempt}, {len(text)} chars)")
        
        try:
            json_str = self._extract_json(text)
            if not json_str:
                logger.warning("No JSON found in response")
                return None
                
            logger.info(f"Extracted JSON string: {json_str[:200]}{'...' if len(json_str) > 200 else ''}")
            
            data = json.loads(json_str)
            logger.info(f"Parsed JSON type: {type(data).__name__}")
            
            return self._normalize_json_structure(data)
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"❌ JSON parse error: {e}")
            return None

    def _normalize_json_structure(self, data: Any) -> Optional[Dict[str, Any]]:
        """Normalize various JSON structures to consistent format"""
        # Handle single question object
        if isinstance(data, dict) and 'type' in data and 'question' in data:
            logger.warning("Got single question object instead of array - wrapping")
            return {"questions": [data]}
        
        # Handle array of questions
        if isinstance(data, list):
            logger.info("Detected JSON array - wrapping in questions object")
            return {"questions": data}
        
        # Handle object with questions/exercises
        if isinstance(data, dict):
            logger.info(f"JSON keys: {list(data.keys())}")
            
            # Accept both "questions" and "exercises" keys
            questions_key = "questions" if "questions" in data else "exercises"
            if questions_key in data:
                questions = data[questions_key]
                if questions:
                    logger.info(f"Found {len(questions)} {questions_key}")
                    return {"questions": questions}
            
            if data:
                logger.warning("⚠️ JSON structure doesn't match expected format but has data")
                if isinstance(data, dict):
                    data["_structure_warning"] = "Partial match to expected format"
                return data
        
        return None

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text using multiple strategies"""
        if not text:
            return ""
        
        # Clean markdown code blocks
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # Try the original Gemma client function
        from llm.gemma_client import _extract_json as gemma_extract
        result = gemma_extract(text)
        
        if result:
            return result
        
        # Fallback patterns
        json_patterns = [
            r'\{[^{}]*\{[^{}]*\{[^{}]*\}[^{}]*\}[^{}]*\}',  # Triple nested
            r'\{[^{}]*\{[^{}]*\}[^{}]*\}',  # Double nested
            r'\{[^{}]*"[^{}]*"[^{}]*\}',  # Object with content
            r'\[[^\[\]]*\]',  # Array
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except:
                    continue
        
        return ""

    # Common batch generation logic
    async def _generate_in_batches(self, context: str, num_items: int, difficulty: str,
                                 item_type: str, batch_generator: Callable) -> Dict[str, Any]:
        """Unified batch generation logic for exercises and questions"""
        logger.info(f"Starting {item_type} generation: {num_items} items, {difficulty} difficulty")
        logger.info(f"Context length: {len(context)} chars")
        
        short_context = context[:1000] if len(context) > 1000 else context
        batch_sizes = self._calculate_batch_sizes(num_items)
        
        logger.info(f"Breaking into {len(batch_sizes)} batches: {batch_sizes}")
        
        all_items = []
        batch_results = []
        
        for batch_num, batch_size in enumerate(batch_sizes, 1):
            logger.info(f"Processing batch {batch_num}/{len(batch_sizes)} with {batch_size} {item_type}")
            
            try:
                batch_result = await batch_generator(short_context, batch_size, difficulty, batch_num, len(batch_sizes))
                batch_results.append(batch_result)
                
                items = batch_result.get(item_type, [])
                if items:
                    all_items.extend(items)
                    logger.info(f"✅ Batch {batch_num} successful: {len(items)} {item_type}")
                else:
                    logger.warning(f"⚠️ Batch {batch_num} failed or returned no {item_type}")
                    all_items.extend(self._create_fallback_items(short_context, batch_size, len(all_items), item_type))
                    
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {str(e)}")
                all_items.extend(self._create_fallback_items(short_context, batch_size, len(all_items), item_type))
        
        return self._finalize_items(all_items, num_items, short_context, item_type, batch_sizes, batch_results)

    def _calculate_batch_sizes(self, num_items: int) -> List[int]:
        """Calculate optimal batch sizes"""
        batch_sizes = []
        remaining = num_items
        
        while remaining > 0:
            batch_size = min(remaining, self.max_items_per_call)
            batch_sizes.append(batch_size)
            remaining -= batch_size
        
        return batch_sizes

    def _create_fallback_items(self, context: str, count: int, start_index: int, item_type: str) -> List[Dict[str, Any]]:
        """Create fallback items when generation fails"""
        return [self._create_fallback_item(context, start_index + i, item_type) for i in range(count)]

    def _finalize_items(self, items: List[Dict[str, Any]], requested_count: int, context: str,
                       item_type: str, batch_sizes: List[int], batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate, enhance and finalize generated items"""
        # Validate all items
        validated_items = []
        for i, item in enumerate(items[:requested_count]):
            if self._validate_item(item):
                validated_items.append(item)
            else:
                logger.warning(f"⚠️ {item_type[:-1]} {i+1} failed validation, enhancing...")
                enhanced_item = self._enhance_item(item, context, i, item_type)
                validated_items.append(enhanced_item)
        
        # Ensure exact count
        final_items = validated_items[:requested_count]
        if len(final_items) < requested_count:
            logger.warning(f"⚠️ Final count short: {len(final_items)}/{requested_count}, adding fallbacks")
            while len(final_items) < requested_count:
                fallback = self._create_fallback_item(context, len(final_items), item_type)
                final_items.append(fallback)
        
        successful_batches = len([r for r in batch_results if item_type in r])
        
        logger.info(f"FINAL: Generated {len(final_items)} {item_type} in {len(batch_sizes)} batches")
        
        return {
            item_type: final_items,
            "count": len(final_items),
            "batches_used": len(batch_sizes),
            "generated_in_single_call": len(batch_sizes) == 1,
            "_debug": {
                "requested_count": requested_count,
                "batch_sizes": batch_sizes,
                f"final_{item_type}": len(final_items),
                "batches_successful": successful_batches
            }
        }

    # Item validation and enhancement
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate that an item has minimum required fields"""
        if not isinstance(item, dict):
            return False
        
        # Must have type and question
        if not item.get('type') or not item.get('question'):
            return False
        
        # Type-specific validation
        item_type = item.get('type', '').upper()
        
        if item_type == 'MCQ':
            return (isinstance(item.get('options'), list) and 
                    len(item.get('options', [])) >= 2 and
                    item.get('correct_answer') is not None)
        
        return True

    def _enhance_item(self, item: Dict[str, Any], context: str, index: int, item_type: str) -> Dict[str, Any]:
        """Try to fix invalid items rather than replacing them"""
        enhanced = item.copy()
        
        # Ensure required fields
        if not enhanced.get('type'):
            enhanced['type'] = 'MCQ'
        
        if not enhanced.get('question'):
            enhanced['question'] = f"{item_type[:-1].title()} {index + 1} about the provided context"
        
        if not enhanced.get('explanation'):
            enhanced['explanation'] = "Review the course material for detailed understanding"
        
        # Add missing fields based on type
        if enhanced['type'].upper() == 'MCQ' and not enhanced.get('options'):
            enhanced['options'] = [
                "Review the key concepts",
                "Analyze the main ideas", 
                "Consider the context provided",
                "Synthesize the information"
            ]
            enhanced['correct_answer'] = 'A'
        
        enhanced['_enhanced'] = True
        return enhanced

    def _create_fallback_item(self, context: str, index: int, item_type: str) -> Dict[str, Any]:
        """Create a quality fallback item that's still useful"""
        short_context = context[:100] + "..." if len(context) > 100 else context
        item_singular = item_type[:-1]  # Remove 's'
        
        base_item = {
            "type": "SHORT_ANSWER",
            "question": f"Explain the key concepts from: {short_context}",
            "expected_answer": "The context covers important concepts that should be reviewed and understood.",
            "explanation": f"This {item_singular} encourages reviewing and synthesizing the key information from the provided material.",
            "key_points": [
                "Understand the main ideas",
                "Identify key terminology", 
                "Apply concepts to new situations"
            ],
            "_fallback": True
        }
        
        # Add difficulty for quiz questions
        if item_type == "questions":
            base_item["difficulty"] = "medium"
            
        return base_item

    # Public methods
    async def choose_and_generate_exercises(self, context_text: str, num_questions: int = 5, 
                                        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> Dict[str, Any]:
        """Choose question types AND generate exercises with batched calls"""
        difficulty_str = difficulty.value if isinstance(difficulty, DifficultyLevel) else str(difficulty)
        
        return await self._generate_in_batches(
            context_text, num_questions, difficulty_str, "exercises",
            self._generate_exercise_batch
        )

    async def generate_quiz_questions(self, context_text: str, num_questions: int = 20,
                                    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
                                    quiz_type: str = "practice") -> Dict[str, Any]:
        """Generate quiz questions with batched calls for large numbers"""
        difficulty_str = difficulty.value if isinstance(difficulty, DifficultyLevel) else str(difficulty)
        quiz_type_str = "comprehensive assessment" if quiz_type == "exam" else "practice quiz"
        
        result = await self._generate_in_batches(
            context_text, num_questions, difficulty_str, "questions",
            lambda context, batch_size, diff, batch_num, total: 
                self._generate_quiz_batch(context, batch_size, diff, quiz_type_str, batch_num, total)
        )
        
        # Add quiz-specific metadata
        type_counts = {}
        for q in result["questions"]:
            q_type = q.get('type', 'unknown').upper()
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        result.update({
            "difficulty": difficulty_str,
            "quiz_type": quiz_type,
            "question_types": type_counts
        })
        
        logger.info(f"Final quiz: {len(result['questions'])} questions - Types: {type_counts}")
        return result

    # Batch generators
    async def _generate_exercise_batch(self, context: str, batch_size: int, difficulty: str, 
                                    batch_num: int, total_batches: int) -> Dict[str, Any]:
        """Generate a single batch of exercises"""
        prompt = f"""
        Create {batch_size} {difficulty}-difficulty educational exercises based on this context:

        CONTEXT:
        {context}

        REQUIREMENTS:
        - Return exactly {batch_size} exercises
        - Vary question types appropriately (MCQ, short_answer, true_false, etc.)
        - Ensure questions are relevant to the context
        - Include proper answer keys and explanations
        - Make these questions unique and different from previous batches

        CRITICAL: You MUST return a JSON OBJECT (not array) with an "exercises" key containing an array of exercises.

        FORMAT: Return a JSON object with this exact structure:
        {{
            "exercises": [
                {{
                    "type": "MCQ",
                    "question": "What is the main topic?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "A",
                    "explanation": "Because..."
                }},
                {{
                    "type": "SHORT_ANSWER", 
                    "question": "Explain the key concept",
                    "expected_answer": "The key concept is...",
                    "explanation": "This is important because..."
                }}
            ]
        }}

        Return ONLY the JSON object. No other text, no code fences, no explanations.
        """
        
        expected_format = {
            "exercises": [
                {
                    "type": str,
                    "question": str,
                    "explanation": str
                }
            ]
        }
        
        return await self._process_batch_generation(prompt, expected_format, batch_size, batch_num, "exercises")

    async def _generate_quiz_batch(self, context: str, batch_size: int, difficulty: str, 
                                quiz_type: str, batch_num: int, total_batches: int) -> Dict[str, Any]:
        """Generate a single batch of quiz questions"""
        # Calculate question type distribution for this batch
        mcq_count = max(1, int(batch_size * 0.6))  # 60% MCQ
        tf_count = max(1, int(batch_size * 0.2))   # 20% True/False
        sa_count = batch_size - mcq_count - tf_count  # Remaining for Short Answer
        
        prompt = f"""
        Create {batch_size} {difficulty}-difficulty questions for a {quiz_type} based on this context:

        CONTEXT:
        {context}

        REQUIREMENTS FOR THIS BATCH:
        - Return exactly {batch_size} questions
        - Question type distribution: {mcq_count} MCQ, {tf_count} True/False, {sa_count} Short Answer
        - Ensure questions test different levels of understanding
        - Include clear correct answers and explanations
        - Make questions challenging but fair for {difficulty} difficulty
        - Make these questions unique and different from previous batches

        FORMAT: Return a JSON object with a "questions" array. Each question should have:
        - "type": "MCQ", "TRUE_FALSE", or "SHORT_ANSWER"
        - "question": the question text
        - For MCQ: "options" array (4 options) and "correct_answer" (A/B/C/D)
        - For TRUE_FALSE: "correct_answer" (true/false)
        - For SHORT_ANSWER: "expected_answer" (model answer)
        - "explanation": brief explanation of the answer
        - "difficulty": "{difficulty}"

        Example:
        {{
            "questions": [
                {{
                    "type": "MCQ",
                    "question": "What is the main concept?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "A",
                    "explanation": "Because...",
                    "difficulty": "{difficulty}"
                }},
                {{
                    "type": "TRUE_FALSE",
                    "question": "This statement is correct.",
                    "correct_answer": "true",
                    "explanation": "Explanation...",
                    "difficulty": "{difficulty}"
                }},
                {{
                    "type": "SHORT_ANSWER", 
                    "question": "Explain the key concept",
                    "expected_answer": "The key concept is...",
                    "explanation": "This is important because...",
                    "difficulty": "{difficulty}"
                }}
            ]
        }}

        Return ONLY valid JSON. No other text.
        """
        
        expected_format = {
            "questions": [
                {
                    "type": str,
                    "question": str,
                    "explanation": str,
                    "difficulty": str
                }
            ]
        }
        
        return await self._process_batch_generation(prompt, expected_format, batch_size, batch_num, "questions")

    async def _process_batch_generation(self, prompt: str, expected_format: Dict[str, Any],
                                     batch_size: int, batch_num: int, item_type: str) -> Dict[str, Any]:
        """Process a single batch generation request"""
        logger.info(f"Sending {item_type} batch {batch_num} with {batch_size} items...")
        result = await self.generate_structured_response(prompt, expected_format)
        
        # Handle the case where result might be a list (from recovery)
        if isinstance(result, list):
            logger.info(f"Result is a list - converting to {item_type} object")
            result = {item_type: result}
        
        if "error" in result:
            logger.error(f"❌ {item_type} batch {batch_num} failed: {result['error']}")
            return result
        
        # Extract items, accepting both primary and alternate keys
        items = result.get(item_type, [])
        if not items:
            alternate_key = "questions" if item_type == "exercises" else "exercises"
            if alternate_key in result:
                items = result[alternate_key]
                logger.info(f"Using '{alternate_key}' key instead of '{item_type}': {len(items)} items")
        
        # Trim to requested batch size
        if len(items) > batch_size:
            logger.info(f"Trimming {len(items)} {item_type} to requested {batch_size}")
            items = items[:batch_size]
        
        logger.info(f"Batch {batch_num} received {len(items)} {item_type}")
        
        # Log each item in this batch
        for i, item in enumerate(items):
            item_type_display = item.get('type', 'unknown')
            question_preview = item.get('question', 'no question')[:50]
            logger.info(f"Batch {batch_num} {item_type[:-1].title()} {i+1}: {item_type_display} - {question_preview}...")
        
        return {
            item_type: items,
            "batch_number": batch_num,
            "batch_size": batch_size,
            "received_count": len(items)
        }


async def get_llm_service() -> LLMService:
    """Dependency injection for LLMService"""
    service = LLMService()
    await service.init()
    return service