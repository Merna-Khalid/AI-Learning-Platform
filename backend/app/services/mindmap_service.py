from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re
import logging
from rag.retriever import Retriever
from app.services.llm_service import LLMService
from app.models.models import MindMap, Course, Material
from app.schemas.schemas import MindMapCreate

logger = logging.getLogger(__name__)

class MindMapService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = None
        self.retriever = Retriever()

    async def ensure_llm_initialized(self):
        if self.llm_service is None:
            self.llm_service = LLMService()
            await self.llm_service.init()

    async def generate_mind_map(self, course: str, central_topic: str, depth: int = 2) -> Dict[str, Any]:
        """Generate a mind map structure using multiple smaller LLM calls"""
        await self.ensure_llm_initialized()
        
        try:
            # Get context from Weaviate
            context_chunks = await self._get_context(course, [central_topic])
            if not context_chunks:
                logger.warning(f"No context found for topic: {central_topic}")
                return await self._create_fallback_mindmap(central_topic)

            # Use smaller context chunks
            context_text = "\n\n".join(context_chunks[:3])
            logger.info(f"Using {len(context_chunks)} context chunks for mind map generation")
            
            # Step 1: Generate main branches with better prompting
            main_branches = await self._generate_main_branches(central_topic, context_text)
            logger.info(f"Generated main branches: {main_branches}")
            
            # Step 2: Generate sub-branches for each main branch
            detailed_branches = []
            for i, branch in enumerate(main_branches[:4]):  # Limit to 4 main branches
                try:
                    logger.info(f"Generating details for branch {i+1}: {branch}")
                    detailed_branch = await self._generate_branch_details(
                        central_topic, branch, context_text
                    )
                    detailed_branches.append(detailed_branch)
                except Exception as e:
                    logger.warning(f"Failed to generate details for branch {branch}: {e}")
                    # Add basic branch as fallback
                    detailed_branches.append(self._create_basic_branch(branch))
            
            # Build final mind map structure
            mind_map_data = {
                "central_topic": central_topic,
                "main_branches": detailed_branches,
                "generation_method": "chunked_llm_calls"
            }
            
            return {
                "course": course,
                "central_topic": central_topic,
                "mind_map": mind_map_data,
                "generated_at": datetime.now().isoformat(),
                "context_used": len(context_chunks),
                "branches_generated": len(detailed_branches)
            }
            
        except Exception as e:
            logger.error(f"Error generating mind map: {e}")
            return await self._create_fallback_mindmap(central_topic)

    async def _generate_main_branches(self, central_topic: str, context: str) -> List[str]:
        """Generate 3-5 main branch topics with improved prompting"""
        # Create a more specific prompt based on the context
        prompt = self._build_main_branches_prompt(central_topic, context)
        
        try:
            # Use slightly higher temperature for creativity but still structured
            response = await self.llm_service.generate(prompt, temperature=0.3, max_tokens=500)
            logger.info(f"Raw branches response: {response}")
            
            branches = self._parse_branches_response(response)
            logger.info(f"Parsed branches: {branches}")
            
            # If parsing failed, extract from text
            if not branches:
                branches = self._extract_branches_from_text(response, central_topic)
                
            return branches[:5] if branches else ["Fundamental Concepts", "Key Principles", "Practical Applications"]
            
        except Exception as e:
            logger.error(f"Error generating main branches: {e}")
            return ["Fundamental Concepts", "Key Principles", "Practical Applications"]

    def _build_main_branches_prompt(self, central_topic: str, context: str) -> str:
        """Build a better prompt for main branches"""
        # Extract some key terms from context to guide the LLM
        key_terms = self._extract_key_terms_from_context(context[:1000])
        
        return f"""
        You are an expert educator creating a mind map for the topic: "{central_topic}"
        
        Based on this educational content:
        {context[:1200]}
        
        Identify 3-5 main educational subtopics that are most important for understanding {central_topic}.
        
        Key terms that might be relevant: {', '.join(key_terms[:8])}
        
        Requirements:
        - Each subtopic should be a clear, educational concept
        - Make them specific to the content provided
        - Focus on learning progression
        - Use 2-4 word phrases
        
        Return ONLY a valid JSON array of strings. No explanations, no code blocks.
        
        Example format for a different topic:
        ["Basic Principles", "Core Components", "Advanced Applications"]
        
        Now for "{central_topic}", return:
        """

    async def _generate_branch_details(self, central_topic: str, branch_name: str, context: str) -> Dict[str, Any]:
        """Generate detailed information for a single branch with better prompting"""
        prompt = self._build_branch_details_prompt(central_topic, branch_name, context)
        
        try:
            response = await self.llm_service.generate(prompt, temperature=0.3, max_tokens=600)
            logger.info(f"Raw branch details for {branch_name}: {response}")
            
            branch_data = self._parse_branch_details_response(response, branch_name)
            return branch_data
            
        except Exception as e:
            logger.error(f"Error generating branch details for {branch_name}: {e}")
            return self._create_basic_branch(branch_name)

    def _build_branch_details_prompt(self, central_topic: str, branch_name: str, context: str) -> str:
        """Build a better prompt for branch details"""
        return f"""
        Expand the mind map branch "{branch_name}" for the central topic "{central_topic}".
        
        Educational Context:
        {context[:1000]}
        
        Create detailed educational content for this branch.
        
        Return a JSON object with this exact structure:
        {{
            "name": "{branch_name}",
            "description": "2-3 sentence educational overview",
            "sub_branches": ["specific concept 1", "concept 2", "concept 3", "concept 4"],
            "key_points": ["important educational fact 1", "fact 2", "fact 3"],
            "importance": "high/medium/low"
        }}
        
        Make it specific to the educational content provided.
        Focus on learning outcomes and understanding.
        
        Return ONLY the JSON object. No other text.
        """

    def _extract_key_terms_from_context(self, context: str) -> List[str]:
        """Extract potential key terms from context to guide the LLM"""
        # Simple extraction of capitalized phrases
        terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', context)
        # Remove common words and duplicates
        common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'What', 'Which'}
        unique_terms = [term for term in terms if term not in common_words and len(term) > 3]
        return list(set(unique_terms))[:15]

    def _parse_branches_response(self, response: str) -> List[str]:
        """Parse main branches from LLM response with multiple strategies"""
        # Strategy 1: Try to find JSON array
        try:
            # Look for array pattern
            array_match = re.search(r'\[[^\]]*\]', response)
            if array_match:
                array_str = array_match.group()
                data = json.loads(array_str)
                if isinstance(data, list) and data:
                    return [str(item).strip() for item in data if item]
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"JSON array parsing failed: {e}")

        # Strategy 2: Try to parse as full JSON object
        try:
            # Remove code blocks if present
            cleaned = re.sub(r'```json|```', '', response).strip()
            data = json.loads(cleaned)
            if isinstance(data, dict) and 'topics' in data and isinstance(data['topics'], list):
                return [str(item).strip() for item in data['topics'] if item]
            elif isinstance(data, list):
                return [str(item).strip() for item in data if item]
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"Full JSON parsing failed: {e}")

        return []

    def _extract_branches_from_text(self, response: str, central_topic: str) -> List[str]:
        """Extract branches from plain text response as fallback"""
        lines = response.strip().split('\n')
        branches = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, code blocks, and example text
            if (not line or 
                line.startswith('```') or
                'example' in line.lower() or
                'format' in line.lower() or
                'subtopic' in line.lower() and '1' in line):
                continue
            
            # Clean the line
            line = re.sub(r'^[\d\-•*"\'\.\s]+|["\']$', '', line)
            line = line.strip()
            
            # Check if it looks like a valid topic
            if (2 <= len(line) <= 50 and 
                not line.startswith(('{', '[', '```')) and
                central_topic.lower() not in line.lower()):
                branches.append(line)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_branches = []
        for branch in branches:
            if branch.lower() not in seen:
                seen.add(branch.lower())
                unique_branches.append(branch)
        
        return unique_branches[:5]

    def _parse_branch_details_response(self, response: str, branch_name: str) -> Dict[str, Any]:
        """Parse branch details from LLM response with better error handling"""
        try:
            # Clean the response
            cleaned = re.sub(r'^```json\s*|\s*```$', '', response.strip())
            
            # Try to parse as JSON
            data = json.loads(cleaned)
            
            # Validate and ensure all required fields
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure all required fields with sensible defaults
            result = {
                "name": data.get("name", branch_name),
                "description": data.get("description", f"Educational concepts related to {branch_name}"),
                "sub_branches": data.get("sub_branches", []),
                "key_points": data.get("key_points", []),
                "importance": data.get("importance", "medium"),
                "color": self._get_branch_color(data.get("importance", "medium"))
            }
            
            # Validate arrays are actually arrays
            if not isinstance(result["sub_branches"], list):
                result["sub_branches"] = []
            if not isinstance(result["key_points"], list):
                result["key_points"] = []
                
            # Limit sizes
            result["sub_branches"] = result["sub_branches"][:4]
            result["key_points"] = result["key_points"][:3]
            
            return result
            
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.warning(f"Failed to parse branch details for {branch_name}: {e}")
            logger.warning(f"Raw response was: {response}")
            return self._create_basic_branch(branch_name)

    def _create_basic_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create a basic but meaningful branch structure"""
        # More specific fallbacks based on branch name
        if "fundamental" in branch_name.lower() or "basic" in branch_name.lower():
            sub_branches = ["Core Principles", "Basic Concepts", "Foundational Knowledge"]
            description = "Essential building blocks and fundamental concepts"
        elif "application" in branch_name.lower() or "practical" in branch_name.lower():
            sub_branches = ["Real-world Uses", "Practical Examples", "Implementation"]
            description = "Practical applications and real-world implementations"
        elif "advanced" in branch_name.lower():
            sub_branches = ["Complex Theories", "Specialized Areas", "Advanced Techniques"]
            description = "Advanced concepts and specialized knowledge areas"
        else:
            sub_branches = ["Key Aspects", "Main Components", "Important Elements"]
            description = f"Important concepts and components of {branch_name}"
        
        return {
            "name": branch_name,
            "description": description,
            "sub_branches": sub_branches,
            "key_points": [
                "Understand the core concepts",
                "Apply knowledge in relevant contexts",
                "Recognize relationships with other topics"
            ],
            "connections": [],
            "importance": "medium",
            "color": self._get_branch_color("medium")
        }

    async def _create_fallback_mindmap(self, central_topic: str) -> Dict[str, Any]:
        """Create a meaningful fallback mind map"""
        return {
            "course": "Unknown",
            "central_topic": central_topic,
            "mind_map": {
                "central_topic": central_topic,
                "main_branches": [
                    self._create_basic_branch("Fundamental Concepts"),
                    self._create_basic_branch("Key Principles"), 
                    self._create_basic_branch("Practical Applications"),
                    self._create_basic_branch("Advanced Topics")
                ],
                "connections": ["All concepts build upon fundamental principles"],
                "generation_method": "fallback"
            },
            "generated_at": datetime.now().isoformat(),
            "context_used": 0,
            "branches_generated": 4,
            "_fallback": True
        }

    def _get_branch_color(self, importance: str) -> str:
        """Get color based on importance level"""
        colors = {
            'high': '#EF4444',    # red
            'medium': '#3B82F6',  # blue
            'low': '#10B981'      # green
        }
        return colors.get(importance, '#6B7280')

    async def _get_context(self, course: str, topics: List[str]) -> List[str]:
        """Retrieve context from Weaviate"""
        context_chunks = []
        for topic in topics:
            try:
                chunks = self.retriever.retrieve_context(course, topic, top_k=2)
                context_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to retrieve context for {topic}: {e}")
                continue
        return context_chunks[:4]  # Limit total chunks

    async def save_mind_map(self, mindmap_data: Dict[str, Any], course_id: int, topic_id: Optional[int] = None) -> MindMap:
        """Save generated mind map to database"""
        mindmap = MindMap(
            course_id=course_id,
            topic_id=topic_id,
            title=f"Mind Map: {mindmap_data['central_topic']}",
            central_topic=mindmap_data['central_topic'],
            map_data=mindmap_data['mind_map'],
            generated_prompt=mindmap_data.get('generated_prompt', '')
        )
        
        self.db.add(mindmap)
        self.db.commit()
        self.db.refresh(mindmap)
        return mindmap