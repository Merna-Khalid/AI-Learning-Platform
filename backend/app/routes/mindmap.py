from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.services.mindmap_service import MindMapService
from app.models.models import Course

router = APIRouter(prefix="/mindmap", tags=["mindmap"])

# Request model
class MindMapGenerateRequest(BaseModel):
    course_id: int
    central_topic: Optional[str] = None

@router.post("/generate")
async def generate_mind_map(
    request: MindMapGenerateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate a mind map for a course"""
    try:
        # Get course name
        course = db.query(Course).filter(Course.id == request.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # If no central topic provided, get the most common topic from materials
        central_topic = request.central_topic
        if not central_topic:
            central_topic = await get_primary_topic(request.course_id, db)
        
        mindmap_service = MindMapService(db)
        result = await mindmap_service.generate_mind_map(course.name, central_topic)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating mind map: {str(e)}")

@router.get("/courses/{course_id}/topics")
async def get_course_topics(course_id: int, db: Session = Depends(get_db)):
    """Get all unique topics for a course"""
    try:
        # Simple implementation - get topics from materials
        from app.models.models import Material
        import json
        
        materials = db.query(Material).filter(Material.course_id == course_id).all()
        all_topics = set()
        
        for material in materials:
            if material.extracted_topics:
                try:
                    if isinstance(material.extracted_topics, str):
                        topics = json.loads(material.extracted_topics)
                    else:
                        topics = material.extracted_topics
                    
                    if isinstance(topics, list):
                        for topic in topics:
                            if topic and isinstance(topic, str):
                                all_topics.add(topic.strip())
                except Exception as e:
                    print(f"Error parsing topics for material {material.id}: {e}")
                    continue
        
        return {"topics": list(all_topics)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching topics: {str(e)}")

async def get_primary_topic(course_id: int, db: Session) -> str:
    """Get the most frequent topic from course materials"""
    try:
        from collections import Counter
        from app.models.models import Material
        import json
        
        materials = db.query(Material).filter(Material.course_id == course_id).all()
        all_topics = []
        
        for material in materials:
            if material.extracted_topics:
                try:
                    if isinstance(material.extracted_topics, str):
                        topics = json.loads(material.extracted_topics)
                    else:
                        topics = material.extracted_topics
                    
                    if isinstance(topics, list):
                        all_topics.extend([t.strip() for t in topics if t and isinstance(t, str)])
                except:
                    continue
        
        if all_topics:
            # Find most common topic
            topic_counter = Counter(all_topics)
            return topic_counter.most_common(1)[0][0]
        else:
            return "Course Overview"
            
    except Exception as e:
        print(f"Error getting primary topic: {e}")
        return "Course Overview"