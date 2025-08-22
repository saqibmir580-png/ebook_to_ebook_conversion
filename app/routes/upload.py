import os
import time
import threading
import logging
from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.db.session import get_db, SessionLocal
from app.models.user import User, UserRole
from app.models.upload import Upload, FileType, ProcessingStatus
from app.schemas.upload import Upload as UploadSchema, UploadWithDownloadUrls
from app.utils.dependencies import get_current_user, get_premium_user
from app.utils.file_utils import (
    save_upload_file, get_file_type, get_download_url
)
from app.services.extraction import EbookExtractor
from app.services.xml_validation import XMLValidator
from app.services.conversion import EbookConverter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def process_upload(
    upload_id: int, 
    file_path: str, 
    file_type: FileType
) -> None:
    """
    Background task to process an uploaded e-book file with visible progress
    """
    logger.info(f"Starting background processing for upload {upload_id}")
    db = SessionLocal()
    
    try:
        # Get upload from database
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            logger.error(f"Upload {upload_id} not found")
            return
        
        logger.info(f"Setting upload {upload_id} to PROCESSING status")
        # Update status to processing
        upload.status = ProcessingStatus.PROCESSING
        upload.progress = 0
        db.commit()
        
        # Add longer delay to make progress visible
        logger.info(f"Upload {upload_id}: Starting with 5 second delay")
        time.sleep(5)
        
        # Step 1: Extract content (0-40%)
        logger.info(f"Upload {upload_id}: Progress 10%")
        upload.progress = 10
        db.commit()
        time.sleep(3)
        
        logger.info(f"Upload {upload_id}: Creating extractor")
        extractor = EbookExtractor(file_path, file_type)
        upload.progress = 20
        db.commit()
        time.sleep(3)
        
        logger.info(f"Upload {upload_id}: Extracting content")
        xml_path = extractor.extract()
        upload.xml_path = xml_path
        upload.page_count = extractor.metadata["page_count"]
        upload.image_count = extractor.metadata["image_count"]
        upload.formula_count = extractor.metadata["formula_count"]
        upload.progress = 40
        db.commit()
        time.sleep(3)
        
        # Step 2: Validate XML (40-50%)
        logger.info(f"Upload {upload_id}: Validating XML")
        validator = XMLValidator(xml_path)
        is_valid, message = validator.validate()
        upload.is_xml_valid = is_valid
        upload.progress = 50
        db.commit()
        time.sleep(2)
        
        if is_valid:
            # Step 3: Convert to other formats (50-90%)
            logger.info(f"Upload {upload_id}: Starting conversion")
            upload.progress = 60
            db.commit()
            time.sleep(3)
            
            converter = EbookConverter(xml_path)
            result_paths = converter.convert()
            
            logger.info(f"Upload {upload_id}: Conversion complete")
            upload.progress = 80
            db.commit()
            time.sleep(2)
            
            # Update paths
            if "html" in result_paths:
                upload.html_path = result_paths["html"]
            if "epub" in result_paths:
                upload.epub_path = result_paths["epub"]
            if "mobi" in result_paths:
                upload.mobi_path = result_paths["mobi"]
            
            upload.progress = 90
            db.commit()
            time.sleep(2)
            
            # Update status to completed
            logger.info(f"Upload {upload_id}: Setting to COMPLETED")
            upload.status = ProcessingStatus.COMPLETED
            upload.progress = 100  # Set progress to 100% when completed
            upload.processing_time = extractor.metadata["processing_time"]
        else:
            # Update status to failed
            logger.error(f"Upload {upload_id}: XML validation failed - {message}")
            upload.status = ProcessingStatus.FAILED
            upload.error_message = message
        
        db.commit()
        logger.info(f"Upload {upload_id}: Processing complete")
        
    except Exception as e:
        # Update status to failed
        logger.error(f"Upload {upload_id}: Processing failed - {str(e)}")
        upload.status = ProcessingStatus.FAILED
        upload.error_message = str(e)
        db.commit()
    finally:
        db.close()


@router.post("", response_model=UploadSchema)
async def create_upload(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
) -> Any:
    """
    Upload a new e-book file for processing
    """
    # Check daily upload limit
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    today_count = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.created_at >= today,
        Upload.created_at < tomorrow
    ).count()
    
    # Get upload limit based on user role
    upload_limit = (
        settings.PREMIUM_DAILY_CONVERSIONS
        if current_user.role in [UserRole.PREMIUM, UserRole.ADMIN]
        else settings.FREE_DAILY_CONVERSIONS
    )
    
    if today_count >= upload_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily upload limit reached ({upload_limit} uploads per day)"
        )
    
    try:
        # Save file
        file_path, file_name, file_size = await save_upload_file(file, current_user.id)
        
        # Check file size limit
        max_size = (
            settings.MAX_UPLOAD_SIZE_PREMIUM
            if current_user.role in [UserRole.PREMIUM, UserRole.ADMIN]
            else settings.MAX_UPLOAD_SIZE_FREE
        )
        
        if file_size > max_size:
            # Remove the file
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the limit ({max_size // 1024 // 1024}MB)"
            )
        
        # Get file type
        file_extension = file_name.split('.')[-1].lower()
        file_type = get_file_type(file_extension)
        
        # Create upload record
        upload = Upload(
            user_id=current_user.id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            status=ProcessingStatus.PENDING
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        # Start background processing
        background_tasks.add_task(process_upload, upload.id, file_path, file_type)
        
        return upload
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/public", response_model=List[UploadSchema])
def get_public_uploads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get demo uploads (public access for non-logged in users)
    """
    # Return empty list for non-authenticated users
    return []


@router.get("/public/{upload_id}", response_model=UploadWithDownloadUrls)
def get_public_upload(
    upload_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get demo upload (public access for non-logged in users)
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please login to view your projects"
    )


@router.get("", response_model=List[UploadSchema])
def get_uploads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all uploads for the current user
    """
    uploads = (
        db.query(Upload)
        .filter(Upload.user_id == current_user.id)
        .order_by(Upload.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return uploads


@router.get("/{upload_id}", response_model=UploadWithDownloadUrls)
def get_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific upload by ID
    """
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Check if user has permission to access this upload
    if upload.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Add download URLs
    result = UploadWithDownloadUrls.from_orm(upload)
    result.xml_url = get_download_url(upload.xml_path)
    result.html_url = get_download_url(upload.html_path)
    result.epub_url = get_download_url(upload.epub_path)
    result.mobi_url = get_download_url(upload.mobi_path)
    
    return result


@router.delete("/{upload_id}")
def delete_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a specific upload by ID
    """
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Check if user has permission to delete this upload
    if upload.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete associated files
    file_paths = [
        upload.file_path,
        upload.xml_path,
        upload.html_path,
        upload.epub_path,
        upload.mobi_path
    ]
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    
    # Delete upload from database
    db.delete(upload)
    db.commit()
    
    return {"message": "Upload deleted successfully"}