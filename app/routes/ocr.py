import os
import json
import shutil
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
from fastapi.responses import FileResponse, JSONResponse

from app.db.session import get_db
from app.models.ocr import OCRData
from app.models.upload import Upload, ProcessingStatus, FileType
from app.schemas.ocr import OCRDataCreate, OCRDataResponse
from app.schemas.upload import UploadResponse
from app.utils.ocr_utils import process_file, allowed_file
from app.core.config import settings
import uuid
from typing import Dict
import asyncio
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.utils.security import get_password_hash
from fastapi import Query
from io import StringIO
import csv
from pathlib import Path
from fastapi import Request
import logging
from lxml import etree
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Store for tracking processing status
processing_status: Dict[str, dict] = {}

async def process_file_async(task_id: str, file_path: str, original_filename: str, db: Session, user_id: int):
    """Background task for processing large files with frontend-controlled progress"""
    upload_record = None
    try:
        # Initialize processing status - let frontend control progress
        processing_status[task_id] = {"status": "processing", "progress": 0}
        
        # Create Upload record immediately for tracking
        upload_record = Upload(
            user_id=user_id,
            file_name=original_filename, # Use the original filename for display
            file_path=file_path,         # Use the unique path for storage
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            file_type=FileType.PDF,  # Assume PDF for now
            status=ProcessingStatus.PROCESSING,
            progress=0,  # Start at 0%, frontend will update
            page_count=0,
            image_count=0,
            formula_count=0,
            processing_time=0.0,
            html_path=None,
            epub_path=None,
            mobi_path=None,
            xml_path=None,
            is_xml_valid=False
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)
        
        # Store upload_id in processing status for frontend updates
        processing_status[task_id]["result"] = {"id": upload_record.id}
        
        logger.info(f"🚀 Started processing task {task_id} for upload {upload_record.id}")
        
        # Process the file (frontend will update progress during this)
        text_output, json_output, extracted_images, html_path = process_file(file_path)
        
        # Update final results
        upload_record.page_count = len(json_output) if json_output else 0
        upload_record.image_count = len(extracted_images) if extracted_images else 0
        upload_record.html_path = html_path
        db.commit()
        
        # Save OCR data to database
        ocr_data = OCRData(
            filename=original_filename,
            extracted_text=text_output,
            extracted_json=json_output if json_output else [],
            extracted_images=extracted_images if extracted_images else []
        )
        db.add(ocr_data)
        db.commit()
        
        # Update final completion status
        processing_status[task_id] = {
            "status": "completed",
            "progress": 100,  # Final completion
            "result": {
                "id": upload_record.id,
                "file": original_filename,
                "extracted_text": text_output,
                "extracted_json": json_output if json_output else [],
                "extracted_images": extracted_images if extracted_images else []
            }
        }
        
        # Mark as completed in database (frontend may have already done this)
        upload_record.status = ProcessingStatus.COMPLETED
        upload_record.progress = 100
        db.commit()
        
        logger.info(f"✅ Completed processing task {task_id} for upload {upload_record.id}")
        
    except Exception as e:
        # Update error status
        processing_status[task_id] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }
        
        # Update database record if it exists
        if upload_record:
            upload_record.status = ProcessingStatus.FAILED
            upload_record.error_message = str(e)
            upload_record.progress = 0
            db.commit()
            
        logger.error(f"❌ Failed processing task {task_id}: {e}")
            
    finally:
        # The original file is now kept for preview purposes
        pass

@router.post("/upload", response_model=OCRDataResponse)
async def upload_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    filename = secure_filename(file.filename)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    # Check file size for async processing threshold (5MB)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset file pointer
    
    if file_size > 5 * 1024 * 1024:  # 5MB threshold
        # Large file - process asynchronously
        task_id = str(uuid.uuid4())
        
        # Save file temporarily
        temp_filename = f"{task_id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, temp_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Start background processing
        background_tasks.add_task(process_file_async, task_id, file_path, secure_filename(file.filename), db, current_user.id)
        
        return JSONResponse(
            status_code=202,
            content={
                "task_id": task_id,
                "status": "processing",
                "message": "Large file detected. Processing in background. Use /status/{task_id} to check progress."
            }
        )
    
    else:
        # Small file - process synchronously
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the file
        text_output, json_output, extracted_images, html_path = process_file(file_path)
        
        # Debug: Print extracted text to console
        print(f"DEBUG: Extracted text length: {len(text_output) if text_output else 0}")
        print(f"DEBUG: First 200 chars of text: {text_output[:200] if text_output else 'None'}")

        # Save to DB
        db_entry = OCRData(
            filename=filename,
            extracted_text=text_output,
            extracted_json=json_output if json_output else [],
            extracted_images=extracted_images
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        # Also create Upload record for dashboard
        upload_record = Upload(
            user_id=current_user.id,
            file_name=filename, # Use the original, secure filename
            file_path=file_path, # Use the actual path where the file is saved
            file_size=file_size,
            file_type=FileType.PDF,  # Assume PDF for now
            status=ProcessingStatus.COMPLETED,
            page_count=len(json_output) if json_output else 0,
            image_count=len(extracted_images) if extracted_images else 0,
            formula_count=0,  # Could be calculated from text
            processing_time=0.0,
            html_path=html_path,
            epub_path=None,
            mobi_path=None,
            xml_path=None,
            is_xml_valid=False
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        return OCRDataResponse(
            id=upload_record.id,
            filename=db_entry.filename,
            uploaded_at=db_entry.uploaded_at,
            extracted_text=text_output,
            extracted_json=json_output if json_output else [],
            extracted_images=extracted_images if extracted_images else []
        )

@router.get("/history", response_model=list[OCRDataResponse])
def get_history(db: Session = Depends(get_db)):
    entries = db.query(OCRData).order_by(OCRData.uploaded_at.desc()).all()
    response = []
    for entry in entries:
        response.append(OCRDataResponse(
            id=entry.id,
            filename=entry.filename,
            uploaded_at=entry.uploaded_at,
            extracted_text=entry.extracted_text,
            extracted_json=entry.extracted_json if entry.extracted_json else [],
            extracted_images=entry.extracted_images or []
        ))
    return response

@router.get("/view/{entry_id}", response_model=OCRDataResponse)
def view_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(OCRData).filter(OCRData.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return OCRDataResponse(
        id=entry.id,
        filename=entry.filename,
        uploaded_at=entry.uploaded_at,
        extracted_text=entry.extracted_text,
        extracted_json=entry.extracted_json if entry.extracted_json else [],
        extracted_images=entry.extracted_images or []
    )

@router.post("/delete/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(OCRData).filter(OCRData.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    try:
        # Delete associated files
        uploaded_file_path = os.path.join(settings.UPLOAD_DIR, entry.filename)
        if os.path.exists(uploaded_file_path):
            os.remove(uploaded_file_path)

        if entry.extracted_images:
            image_paths = entry.extracted_images
            for image_path in image_paths:
                full_image_path = os.path.join(settings.STATIC_DIR, image_path)
                if os.path.exists(full_image_path):
                    os.remove(full_image_path)

        # Delete from DB
        db.delete(entry)
        db.commit()
        return {"message": f"Entry {entry_id} deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting entry: {str(e)}")

@router.get("/download/{filename}/{filetype}")
def download_file(filename: str, filetype: str):
    if filetype not in ["text", "json"]:
        raise HTTPException(status_code=400, detail="Invalid file type for download")
    
    extension = '.txt' if filetype == 'text' else '.json'
    # This assumes an OUTPUT_FOLDER is defined in settings
    file_path = os.path.join(settings.OUTPUT_DIR, filename + extension)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=os.path.basename(file_path))

@router.get("/status/{task_id}")
async def get_processing_status(task_id: str):
    """Get the status of an async processing task"""
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return processing_status[task_id]

def _get_file_url(request: Request, file_path: str) -> str:
    """Construct a full URL for a static file."""
    if not file_path:
        return None
    # We need to get the relative path from the static dir
    static_dir = settings.STATIC_DIR
    try:
        relative_path = Path(file_path).relative_to(static_dir)
    except ValueError:
        # If the file_path is not in the static_dir, we can't build a URL
        # This might happen if paths are stored incorrectly. For now, we'll just return None.
        # A more robust solution might try to handle different base paths.
        return None

    # The URL should be relative to the server root, so we join it with 'static'
    # The path should use forward slashes for URLs
    url_path = f"static/{'/'.join(relative_path.parts)}"
    return str(request.base_url.join(url_path))

@router.get("/uploads", response_model=list[UploadResponse])
def get_uploads(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all uploads for the current user."""
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).order_by(Upload.created_at.desc()).all()
    response = []
    for upload in uploads:
        logger.info(f"Processing upload ID {upload.id} with json_export_path: {upload.json_export_path}")
        upload_data = UploadResponse.from_orm(upload)
        upload_data.html_url = _get_file_url(request, upload.html_path)
        upload_data.epub_url = _get_file_url(request, upload.epub_path)
        upload_data.mobi_url = _get_file_url(request, upload.mobi_path)
        upload_data.xml_url = _get_file_url(request, upload.xml_path)
        upload_data.json_export_url = _get_file_url(request, upload.json_export_path)
        upload_data.csv_export_url = _get_file_url(request, upload.csv_export_path)
        logger.info(f"Generated json_export_url: {upload_data.json_export_url}")
        response.append(upload_data)
    return response


@router.get("/uploads/{upload_id}", response_model=UploadResponse)
def get_upload(
    upload_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single upload by ID."""
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    upload_data = UploadResponse.from_orm(upload)
    upload_data.html_url = _get_file_url(request, upload.html_path)
    upload_data.epub_url = _get_file_url(request, upload.epub_path)
    upload_data.mobi_url = _get_file_url(request, upload.mobi_path)
    upload_data.xml_url = _get_file_url(request, upload.xml_path)
    upload_data.json_export_url = _get_file_url(request, upload.json_export_path)
    upload_data.csv_export_url = _get_file_url(request, upload.csv_export_path)

    return upload_data

@router.get("/uploads/{upload_id}/pdf")
def get_upload_pdf(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Serve the original PDF file for preview."""
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if not upload.file_path or not os.path.exists(upload.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        path=upload.file_path,
        filename=upload.file_name,
        media_type="application/pdf"
    )

@router.post("/export/{upload_id}")
def export_project(
    upload_id: int,
    format: str = Query(..., regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export project data to a file (JSON or CSV) and return the file URL."""
    logger.info(f"Export requested for upload_id: {upload_id} with format: {format}")
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        logger.error(f"Upload with id {upload_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Upload not found")

    export_data = {
        "id": upload.id,
        "file_name": upload.file_name,
        "status": upload.status.value,
        "created_at": upload.created_at.isoformat(),
        "file_type": upload.file_type,
        "file_size": upload.file_size,
        "page_count": upload.page_count,
        "image_count": upload.image_count,
        "formula_count": upload.formula_count,
        "processing_time": upload.processing_time,
        "error_message": upload.error_message,
    }

    if format == 'json':
        content = json.dumps(export_data, indent=2)
        file_extension = 'json'
        mime_type = 'application/json'
    else: # csv
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=export_data.keys())
        writer.writeheader()
        writer.writerow(export_data)
        content = output.getvalue()
        file_extension = 'csv'
        mime_type = 'text/csv'

    export_filename = f"{Path(upload.file_name).stem}_export.{file_extension}"
    export_path = os.path.join(settings.EXPORTS_DIR, export_filename)
    logger.info(f"Saving export file to: {export_path}")

    with open(export_path, 'w') as f:
        f.write(content)

    # Update the upload record with the new export path
    if format == 'json':
        upload.json_export_path = export_path
        logger.info(f"Updating upload.json_export_path to: {export_path}")
    else:
        upload.csv_export_path = export_path
        logger.info(f"Updating upload.csv_export_path to: {export_path}")
    
    try:
        db.commit()
        logger.info(f"Database commit successful for upload_id: {upload_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed for upload_id: {upload_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save export path.")

    return FileResponse(path=export_path, filename=export_filename, media_type=mime_type)

@router.get("/stats", response_model=Dict[str, int])
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get dashboard statistics for the current user.
    """
    total_projects = db.query(Upload).filter(Upload.user_id == current_user.id).count()
    completed_projects = db.query(Upload).filter(Upload.user_id == current_user.id, Upload.status == 'completed').count()
    processing_projects = db.query(Upload).filter(Upload.user_id == current_user.id, Upload.status == 'processing').count()
    failed_projects = db.query(Upload).filter(Upload.user_id == current_user.id, Upload.status == 'failed').count()
    
    return {
        "totalProjects": total_projects,
        "completedProjects": completed_projects,
        "processingProjects": processing_projects,
        "failedProjects": failed_projects,
    }

@router.post("/progress/{task_id}")
async def update_progress(
    task_id: str,
    progress_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update workflow progress for a task and save to database"""
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    new_progress = progress_data.get("progress", 0)
    frontend_status = progress_data.get("status", "processing")
    
    # Determine actual status based on progress
    if new_progress >= 100:
        actual_status = "completed"
    elif new_progress > 0:
        actual_status = "processing"
    else:
        actual_status = frontend_status
    
    # Update the processing status
    processing_status[task_id]["progress"] = new_progress
    processing_status[task_id]["status"] = actual_status
    
    # Find and update the database Upload record
    upload_record = None
    try:
        # First try to get upload_id from processing status result
        upload_id = processing_status[task_id].get("result", {}).get("id")
        if upload_id:
            upload_record = db.query(Upload).filter(Upload.id == upload_id).first()
        
        # If not found, try to find by user_id and recent uploads
        if not upload_record:
            # Find the most recent processing upload for this user
            upload_record = db.query(Upload).filter(
                Upload.user_id == current_user.id,
                Upload.status == ProcessingStatus.PROCESSING
            ).order_by(Upload.created_at.desc()).first()
        
        if upload_record:
            # Update upload record with current progress
            upload_record.progress = new_progress
            
            # Only update status based on progress, not frontend status
            if new_progress >= 100:
                upload_record.status = ProcessingStatus.COMPLETED
            elif new_progress > 0:
                upload_record.status = ProcessingStatus.PROCESSING
            # Keep existing status if progress is 0
            
            db.commit()
            logger.info(f"✅ Updated database record for upload {upload_record.id}: progress={new_progress}%, status={upload_record.status}")
        else:
            logger.warning(f"⚠️  No upload record found for task {task_id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to update database for task {task_id}: {e}")
        db.rollback()
        # Don't fail the request if database update fails
    
    logger.info(f"📊 Updated progress for task {task_id}: {new_progress}% - Status: {actual_status}")
    
    return {"message": "Progress updated", "progress": new_progress, "status": actual_status}

@router.post("/complete/{task_id}")
async def mark_completed(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark workflow as completed after successful export"""
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    processing_status[task_id]["status"] = "completed"
    processing_status[task_id]["progress"] = 100
    
    logger.info(f"Marked task {task_id} as completed")
    
    return {"message": "Task marked as completed", "status": "completed", "progress": 100}

@router.post("/fail/{task_id}")
async def mark_failed(
    task_id: str,
    error_message: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark workflow as failed due to error"""
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    processing_status[task_id]["status"] = "failed"
    processing_status[task_id]["error"] = error_message.get("error", "Unknown error")
    
    logger.error(f"Marked task {task_id} as failed: {error_message.get('error')}")
    
    return {"message": "Task marked as failed", "status": "failed", "error": error_message.get("error")}

@router.post("/validate-xml")
async def validate_xml(
    xml_file: UploadFile = File(...),
    dtd_file: Optional[UploadFile] = File(None),
    ent_file: Optional[UploadFile] = File(None) # Currently unused, but available for future extension
):
    """Validate XML file against DTD and ENT rules."""
    xml_content = await xml_file.read()

    try:
        # Basic well-formedness check
        parser = etree.XMLParser(resolve_entities=True)
        tree = etree.fromstring(xml_content, parser)

        if dtd_file:
            dtd_content = await dtd_file.read()
            dtd = etree.DTD(BytesIO(dtd_content))
            
            if not dtd.validate(tree):
                # Validation failed, provide detailed errors
                error_log = dtd.error_log.filter_from_errors()
                error_message = f"DTD Validation Failed: {error_log}"
                return JSONResponse(
                    status_code=200, 
                    content={"isValid": False, "message": error_message}
                )

        return JSONResponse(
            status_code=200,
            content={"isValid": True, "message": "XML is valid and well-formed"}
        )

    except etree.XMLSyntaxError as e:
        return JSONResponse(
            status_code=200,
            content={"isValid": False, "message": f"XML Syntax Error: {e}"}
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during XML validation: {e}")
        return JSONResponse(
            status_code=500,
            content={"isValid": False, "message": f"An unexpected server error occurred: {e}"}
        )
