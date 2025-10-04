from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
import re
from app.models.models import Material, Course
from rag.ingestion import DocumentIngestor
from llm.gemma_client import GemmaClient

class MaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = GemmaClient(auto_start=False)

    async def init(self):
        self.llm = await self.llm.init()
        return self
    
    async def create_and_ingest(self, course_id: int, file_path: str, source_type: str):
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found")

        ingestor = DocumentIngestor(data_dir=os.path.dirname(file_path))
        res = await ingestor.ingest(
            collection_name=course.name,
            file_paths=[file_path]
        )

        text_content = res.get("combined_text", "")
        extracted_topics = await self.extract_topics(text_content)

        material = Material(
            course_id=course_id,
            date_uploaded=datetime.utcnow(),
            file_path=file_path,
            extracted_topics=extracted_topics,
            source_type=source_type,
        )
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)
        return material

    async def extract_topics(self, text: str):
        """
        Ask the LLM to extract 5–10 key topics from the uploaded material.
        Returns a list of topic strings.
        """
        # More explicit prompt with better formatting instructions
        prompt = f"""
        Extract the 5-10 most important educational topics from the following course material.
        
        IMPORTANT: Return ONLY a valid JSON array of topic strings. No other text, no explanations.
        
        Example format: ["Machine Learning", "Neural Networks", "Backpropagation"]
        
        Requirements:
        - Return exactly 5-10 topics
        - Each topic should be a short, clear string (2-4 words max)
        - Topics should be relevant to educational content
        - Remove any numbering, bullet points, or special characters
        - Make topics distinct and meaningful
        
        Course Material:
        {text[:3000]}
        
        Return ONLY the JSON array:
        """

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.1, max_tokens=500)
            print(f"LLM Raw Response: {raw_response}")  # Debug logging
            
            # Try multiple extraction strategies
            topics = await self._parse_topics_response(raw_response)
            
            # Validate and clean topics
            cleaned_topics = self._clean_topics(topics)
            
            print(f"✅ Extracted {len(cleaned_topics)} topics: {cleaned_topics}")
            return cleaned_topics
            
        except Exception as e:
            print(f"❌ Error extracting topics: {e}")
            # Fallback: extract simple words from text
            return self._fallback_topic_extraction(text)

    async def _parse_topics_response(self, raw_response: str):
        """Multiple strategies to parse topics from LLM response"""
        
        # Strategy 1: Try to extract JSON array
        try:
            from llm.gemma_client import _extract_json
            json_str = _extract_json(raw_response)
            if json_str:
                topics = json.loads(json_str)
                if isinstance(topics, list) and topics:
                    return topics
        except Exception as e:
            print(f"JSON extraction failed: {e}")

        # Strategy 2: Look for array-like patterns
        array_patterns = [
            r'\[[^\]]*\]',  # Basic array pattern
            r'"[^"]*"(?:\s*,\s*"[^"]*")*',  # Comma-separated quoted strings
        ]
        
        for pattern in array_patterns:
            matches = re.findall(pattern, raw_response)
            for match in matches:
                try:
                    # Try to parse as JSON
                    if match.startswith('[') and match.endswith(']'):
                        topics = json.loads(match)
                    else:
                        # Handle comma-separated strings without brackets
                        topics = json.loads(f'[{match}]')
                    
                    if isinstance(topics, list) and topics:
                        return topics
                except:
                    continue

        # Strategy 3: Extract lines that look like topics
        lines = raw_response.split('\n')
        topics = []
        for line in lines:
            line = line.strip()
            # Skip empty lines, numbers, and obvious non-topics
            if not line or line.isdigit() or ':' in line or line in ['', '```']:
                continue
            
            # Remove common prefixes and clean up
            line = re.sub(r'^[\d\-•*]\s*', '', line)  # Remove numbering/bullets
            line = re.sub(r'^["\']|["\']$', '', line)  # Remove quotes
            line = line.strip()
            
            # Only keep reasonable topic strings
            if (2 <= len(line) <= 50 and 
                not line.startswith(('{', '[', '```')) and
                not any(word in line.lower() for word in ['example', 'format', 'return', 'json'])):
                topics.append(line)
        
        return topics[:10]  # Limit to 10 topics

    def _clean_topics(self, topics):
        """Clean and validate extracted topics"""
        if not topics:
            return []
            
        cleaned = []
        seen = set()
        
        for topic in topics:
            if not isinstance(topic, str):
                topic = str(topic)
            
            # Clean the topic
            topic = topic.strip()
            topic = re.sub(r'^[\d\-•*\.\s]+', '', topic)  # Remove leading numbers/bullets
            topic = re.sub(r'[^\w\s\-&]', '', topic)  # Remove special chars except spaces, hyphens, &
            topic = ' '.join(topic.split())  # Normalize whitespace
            
            # Validate topic
            if (topic and 
                len(topic) >= 2 and 
                len(topic) <= 40 and
                topic.lower() not in seen):
                
                # Title case for consistency
                topic = topic.title()
                cleaned.append(topic)
                seen.add(topic.lower())
        
        # Remove duplicates while preserving order
        unique_topics = []
        for topic in cleaned:
            if topic not in unique_topics:
                unique_topics.append(topic)
        
        return unique_topics[:10]  # Return max 10 topics

    def _fallback_topic_extraction(self, text: str):
        """Fallback method if LLM extraction fails"""
        # Extract capitalized words and phrases
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter and clean
        topics = []
        for word in words:
            if len(word) > 3 and word not in ['The', 'And', 'For', 'With']:
                topics.append(word)
        
        # Remove duplicates and limit
        unique_topics = list(dict.fromkeys(topics))[:8]
        
        print(f"Using fallback extraction: {unique_topics}")
        return unique_topics