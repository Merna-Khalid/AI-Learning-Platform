from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import asyncio
import os
import json
import uuid
from typing import List
from app.core.database import get_db
from app.schemas.schemas import CourseCreate, CourseOut, MaterialOut, SourceType
from app.services import course_service
from rag.ingestion import DocumentIngestor
from app.services.material_service import MaterialService
from app.models.models import Course, Material

router = APIRouter(prefix="/courses", tags=["Courses"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

active_ingestions = {}


async def process_file_with_topic_extraction(course_id: int, file_path: str, course_name: str, material_id: int, source_type: str, db: Session):
    """Background task that uses MaterialService but updates the existing material"""
    try:
        # Update database status
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            material.ingestion_status = "processing"
            db.commit()
        
        # Initialize progress tracking
        active_ingestions[material_id] = {
            "material_id": material_id,
            "status": "processing",
            "progress": 10,
            "message": "Starting ingestion process..."
        }
        
        # Update progress: Reading file
        active_ingestions[material_id].update({
            "progress": 20,
            "message": "Reading and parsing file..."
        })
        
        # Use DocumentIngestor directly for RAG
        ingestor = DocumentIngestor(data_dir=UPLOAD_DIR)
        
        # Update progress: Extracting content
        active_ingestions[material_id].update({
            "progress": 40,
            "message": "Extracting text content..."
        })
        
        # Do RAG ingestion
        result = await ingestor.ingest(
            collection_name=course_name,
            file_paths=[file_path]
        )
        
        # Update progress: Extracting topics using your existing service
        active_ingestions[material_id].update({
            "progress": 70,
            "message": "Analyzing content and extracting topics..."
        })
        
        # Use your MaterialService just for topic extraction
        material_service = MaterialService(db)
        
        combined_text = result.get("combined_text", "")
        extracted_topics = await material_service.extract_topics(combined_text)
        
        # Update progress based on results
        chunk_count = len(result.get('inserted_text_chunks', []))
        topic_count = len(extracted_topics)
        
        active_ingestions[material_id].update({
            "progress": 90,
            "message": f"Processed {chunk_count} text chunks, extracted {topic_count} topics"
        })
        
        # Update the material with extracted topics
        if material:
            material.extracted_topics = extracted_topics
            material.ingestion_status = "completed"
            db.commit()
        
        await asyncio.sleep(1)
        
        # Final update
        active_ingestions[material_id].update({
            "progress": 100,
            "status": "completed",
            "message": f"Ingestion completed! {chunk_count} chunks and {topic_count} topics added."
        })
        
        print(f"✅ Successfully processed material {material_id} with {topic_count} topics")
        if topic_count > 0:
            print(f"📚 Topics: {extracted_topics}")
        
        await asyncio.sleep(30)
        
    except Exception as e:
        error_msg = f"Error processing file with topic extraction: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        active_ingestions[material_id] = {
            "material_id": material_id,
            "status": "failed", 
            "progress": 0,
            "message": error_msg
        }
        
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            material.ingestion_status = "failed"
            db.commit()
        
        await asyncio.sleep(60)
    finally:
        await asyncio.sleep(10)
        if material_id in active_ingestions:
            del active_ingestions[material_id]


@router.post("/", response_model=CourseOut)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    try:
        return course_service.create_course(db, course)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating course: {str(e)}")

@router.get("/", response_model=List[CourseOut])
def get_courses(db: Session = Depends(get_db)):
    return course_service.get_courses(db)

@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course



@router.websocket("/ws/ingestion/{material_id}")
async def websocket_ingestion_status(websocket: WebSocket, material_id: int):
    await websocket.accept()
    try:
        while True:
            # Check if we have active ingestion status
            if material_id in active_ingestions:
                status = active_ingestions[material_id]
                await websocket.send_json(status)
                
                # If completed or failed, stop sending updates after a short time
                if status.get("status") in ["completed", "failed"]:
                    # Send a few more updates then close
                    for _ in range(3):
                        await asyncio.sleep(1)
                        await websocket.send_json(status)
                    break
            else:
                # No active ingestion - send unknown status
                await websocket.send_json({
                    "material_id": material_id,
                    "status": "unknown", 
                    "progress": 0,
                    "message": "No ingestion process found"
                })
                
            await asyncio.sleep(1)  # Send updates every second
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for material {material_id}")
    except Exception as e:
        print(f"WebSocket error for material {material_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass


@router.get("/materials/{material_id}/status")
async def get_ingestion_status(material_id: int, db: Session = Depends(get_db)):
    """Get current ingestion status for a specific material"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Check if there's an active ingestion process
    active_status = active_ingestions.get(material_id)
    if active_status:
        return active_status
    
    # Return the database status
    return {
        "material_id": material_id,
        "status": material.ingestion_status,
        "progress": 100 if material.ingestion_status == "completed" else 0,
        "message": f"Ingestion {material.ingestion_status}"
    }

async def process_file_for_rag(course_id: int, file_path: str, course_name: str, material_id: int, db: Session):
    """Background task to process uploaded file for RAG with real-time progress"""
    try:
        # Update database status
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            material.ingestion_status = "processing"
            db.commit()
        
        # Initialize progress tracking
        active_ingestions[material_id] = {
            "material_id": material_id,
            "status": "processing",
            "progress": 10,
            "message": "Starting ingestion process..."
        }
        
        ingestor = DocumentIngestor(data_dir=UPLOAD_DIR)
        collection_name = f"{course_name}"
        
        # Update progress: Reading file
        active_ingestions[material_id].update({
            "progress": 20,
            "message": "Reading and parsing file..."
        })
        
        await asyncio.sleep(1)  # Simulate file reading
        
        # Update progress: Extracting content
        active_ingestions[material_id].update({
            "progress": 40,
            "message": "Extracting text content..."
        })
        
        # Actual ingestion
        result = await ingestor.ingest(
            collection_name=collection_name,
            file_paths=[file_path]
        )
        
        # Update progress based on actual results
        chunk_count = len(result.get('inserted_text_chunks', []))
        
        active_ingestions[material_id].update({
            "progress": 80,
            "message": f"Processed {chunk_count} text chunks"
        })
        
        await asyncio.sleep(1)  # Simulate final processing
        
        # Final update
        active_ingestions[material_id].update({
            "progress": 100,
            "status": "completed",
            "message": f"Ingestion completed! {chunk_count} chunks added to vector database."
        })
        
        # Update database status
        if material:
            material.ingestion_status = "completed"
            db.commit()
        
        print(f"✅ Successfully processed material {material_id} for RAG")
        
        # Keep the status for a while, then clean up
        await asyncio.sleep(30)  # Keep status for 30 seconds after completion
        
    except Exception as e:
        error_msg = f"Error processing file for RAG: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Update progress with error
        active_ingestions[material_id] = {
            "material_id": material_id,
            "status": "failed",
            "progress": 0,
            "message": error_msg
        }
        
        # Update database status
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            material.ingestion_status = "failed"
            db.commit()
        
        # Keep error status for a while
        await asyncio.sleep(60)  # Keep error status for 60 seconds
    finally:
        # Clean up - but wait a bit longer to ensure clients get final status
        await asyncio.sleep(10)
        if material_id in active_ingestions:
            del active_ingestions[material_id]


@router.post("/{course_id}/upload", response_model=MaterialOut)
async def upload_course_material(
    course_id: int, 
    file: UploadFile = File(...),
    content_type: str = "lecture",
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    try:
        course = course_service.get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Validate file type and map to SourceType enum
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Map file extensions to SourceType enum
        extension_to_source_type = {
            '.pdf': SourceType.PDF,
            '.mp4': SourceType.VIDEO,
            '.mov': SourceType.VIDEO,
            '.avi': SourceType.VIDEO,
            '.txt': SourceType.ARTICLE,
            '.md': SourceType.ARTICLE,
            '.doc': SourceType.ARTICLE,
            '.docx': SourceType.ARTICLE,
            '.ppt': SourceType.SLIDES,
            '.pptx': SourceType.SLIDES,
        }
        
        source_type_enum = extension_to_source_type.get(file_extension, SourceType.OTHER)
        
        if source_type_enum == SourceType.OTHER:
            allowed_extensions = ['.pdf', '.mp4', '.mov', '.avi', '.txt', '.md', '.doc', '.docx', '.ppt', '.pptx']
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate content_type
        valid_content_types = ["lecture", "tutorial", "reference"]
        if content_type not in valid_content_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type. Must be one of: {', '.join(valid_content_types)}"
            )
        
        # Generate unique filename and path
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save the file
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Create material record first
        material = Material(
            course_id=course_id,
            filename=file.filename,
            source_type=source_type_enum,
            content_type=content_type,
            file_path=file_path,
            ingestion_status="processing"
        )
        
        db.add(material)
        db.commit()
        db.refresh(material)
        
        # Process file for RAG in background using MaterialService (which includes topic extraction)
        if source_type_enum in [SourceType.PDF, SourceType.ARTICLE, SourceType.SLIDES]:
            if background_tasks:
                background_tasks.add_task(
                    process_file_with_topic_extraction,  # Use the new function
                    course_id, 
                    file_path, 
                    course.name,
                    material.id,
                    source_type_enum.value,  # Pass source type as string
                    db
                )
        else:
            # For videos and other non-text files, mark as completed but not processed for RAG
            material.ingestion_status = "completed"
            db.commit()
            print(f"✅ File uploaded but not processed for RAG (unsupported type: {source_type_enum})")
        
        return material
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/{course_id}/upload-batch")
async def upload_batch_materials(
    course_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),  # Add this parameter
    background_tasks: BackgroundTasks = None
):
    """Upload multiple files at once"""
    try:
        # Validate course exists
        course = course_service.get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        results = []
        for file in files:
            # Validate file type
            allowed_extensions = {'.pdf', '.txt', '.md', '.doc', '.docx', '.ppt', '.pptx'}
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                results.append({
                    "filename": file.filename,
                    "status": "rejected", 
                    "reason": "Unsupported file type"
                })
                continue
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            # Save the file
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Create material record
            material = Material(
                course_id=course_id,
                filename=file.filename,
                source_type=SourceType.PDF,  # You might want to detect this properly
                content_type="lecture",  # Default or make configurable
                file_path=file_path,
                ingestion_status="processing"
            )
            
            db.add(material)
            db.commit()
            db.refresh(material)
            
            # Schedule RAG processing
            if background_tasks:
                background_tasks.add_task(
                    process_file_for_rag, 
                    course_id, 
                    file_path, 
                    course.name,
                    material.id,
                    db  # Add db parameter
                )
            
            results.append({
                "filename": file.filename,
                "status": "processing",
                "material_id": material.id,
                "file_path": file_path
            })
        
        return {
            "message": f"Batch upload completed for {len(files)} files",
            "course_id": course_id,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")
    

@router.get("/{course_id}/ingestion-status")
async def get_ingestion_status(course_id: int, db: Session = Depends(get_db)):
    """Get the current ingestion status for a course"""
    course = course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {
        "course_id": course_id,
        "ingestion_status": course.ingestion_status,
        "last_updated": course.updated_at if hasattr(course, 'updated_at') else course.created_at
    }


@router.get("/{course_id}/materials", response_model=List[MaterialOut])
def get_course_materials(course_id: int, db: Session = Depends(get_db)):
    """Get all materials for a specific course"""
    course = course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    materials = db.query(Material).filter(Material.course_id == course_id).order_by(Material.date_uploaded.desc()).all()
    return materials


@router.get("/materials/{material_id}/status")
async def get_material_status(material_id: int, db: Session = Depends(get_db)):
    """Get the current ingestion status for a specific material"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Check if there's an active ingestion process
    active_status = active_ingestions.get(material_id)
    if active_status:
        return active_status
    
    # Return the database status with appropriate progress
    progress = 100 if material.ingestion_status == "completed" else (
        80 if material.ingestion_status == "processing" else 0
    )
    
    status_messages = {
        "pending": "Waiting to start processing...",
        "processing": "Processing file for RAG ingestion...",
        "completed": "Ingestion completed successfully!",
        "failed": "Ingestion failed - please try again"
    }
    
    return {
        "material_id": material_id,
        "status": material.ingestion_status,
        "progress": progress,
        "message": status_messages.get(material.ingestion_status, "Unknown status")
    }