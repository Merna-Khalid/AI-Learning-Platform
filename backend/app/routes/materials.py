from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.services.material_service import MaterialService

router = APIRouter(prefix="/materials", tags=["Materials"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_material(
    course_id: int = Form(...),
    source_type: str = Form(...),
    file: UploadFile = None,
    db: Session = Depends(get_db),
):
    """
    Upload a material (PDF/TXT/etc) and index it into the RAG pipeline.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Call service layer to process + index into DB + RAG
    material_service = await MaterialService(db).init()
    material = await material_service.create_and_ingest(
        course_id=course_id,
        file_path=file_path,
        source_type=source_type,
    )

    return {"message": "File uploaded and processed", "material": material}
