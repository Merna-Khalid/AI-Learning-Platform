from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])

class GenerateNotesRequest(BaseModel):
    course: str
    topic: str

@router.post("/generate")
def generate_notes(request: GenerateNotesRequest):
    service = NoteService()
    notes = service.generate_notes(course=request.course, topic=request.topic)
    return notes
