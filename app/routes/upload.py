import os
import time
from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.upload import Upload, FileType, ProcessingStatus
from app.schemas.upload import Upload as UploadSchema, UploadWithDownloadUrls
from app.utils.dependencies import get_current_user, get_premium_user
from app.utils.file_utils import (
    save_upload_file, get_file_type, get_download_url
)
from app.services.enhanced_extraction import EnhancedDocumentExtractor
from app.services.xml_validation import XMLValidator
from app.services.conversion import EbookConverter
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()


def process_upload(
    upload_id: int, 
    file_path: str, 
    file_type: FileType, 
    db: Session
) -> None:
    """
    Background task to process an uploaded e-book file
    """
    upload = None
    try:
        # Get upload from database
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            logger.error(f"Upload with ID {upload_id} not found in database")
            return
        
        # Update status to processing
        upload.status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Extract content using enhanced extractor
        extractor = None
        try:
            logger.info(f"Starting enhanced extraction for {file_path}")
            extractor = EnhancedDocumentExtractor(file_path, file_type)
            xml_path = extractor.extract()
            
            if not os.path.exists(xml_path):
                raise FileNotFoundError(f"Generated XML file not found at {xml_path}")
                
            upload.xml_path = xml_path
            
            # Update metadata from enhanced extraction
            upload.page_count = extractor.metadata.get("page_count", 0)
            upload.image_count = extractor.metadata.get("image_count", 0)
            upload.formula_count = extractor.metadata.get("formula_count", 0)
            
            logger.info(f"Successfully extracted content from {file_path}")
            logger.info(f"Extraction metadata: {extractor.metadata}")
            
        except Exception as e:
            logger.error(f"Error during enhanced extraction: {str(e)}", exc_info=True)
            # Fall back to basic extraction if enhanced fails
            logger.info("Falling back to basic extraction")
            try:
                from app.services.extraction import EbookExtractor
                extractor = EbookExtractor(file_path, file_type)
                xml_path = extractor.extract()
                
                if not os.path.exists(xml_path):
                    raise FileNotFoundError(f"Generated XML file not found at {xml_path}")
                    
                upload.xml_path = xml_path
                upload.page_count = extractor.metadata.get("page_count", 0)
                upload.image_count = extractor.metadata.get("image_count", 0)
                upload.formula_count = extractor.metadata.get("formula_count", 0)
                logger.info("Basic extraction completed successfully")
            except Exception as basic_e:
                logger.error(f"Basic extraction also failed: {str(basic_e)}", exc_info=True)
                raise RuntimeError(f"Both enhanced and basic extraction failed: {str(basic_e)}")
        
        db.commit()
        
        # Validate XML
        logger.info("Validating generated XML")
        try:
            validator = XMLValidator(upload.xml_path)
            is_valid, message = validator.validate()
            upload.is_xml_valid = is_valid
            db.commit()
            
            if not is_valid:
                logger.warning(f"XML validation failed: {message}")
                upload.status = ProcessingStatus.FAILED
                upload.error_message = f"XML validation failed: {message}"
                db.commit()
                return
                
        except Exception as e:
            logger.error(f"Error during XML validation: {str(e)}", exc_info=True)
            upload.status = ProcessingStatus.FAILED
            upload.error_message = f"XML validation error: {str(e)}"
            db.commit()
            return
        
        # Convert to other formats
        logger.info("Starting format conversion")
        try:
            converter = EbookConverter(upload.xml_path)
            result_paths = converter.convert()
            
            # Update paths for successful conversions
            if result_paths.get("html"):
                upload.html_path = result_paths["html"]
                logger.info(f"HTML conversion successful: {upload.html_path}")
                
            if result_paths.get("epub"):
                upload.epub_path = result_paths["epub"]
                logger.info(f"EPUB conversion successful: {upload.epub_path}")
                
            if result_paths.get("mobi"):
                upload.mobi_path = result_paths["mobi"]
                logger.info(f"MOBI conversion successful: {upload.mobi_path}")
            
            # Update status to completed
            upload.status = ProcessingStatus.COMPLETED
            if extractor and "processing_time" in extractor.metadata:
                upload.processing_time = extractor.metadata["processing_time"]
                
            logger.info(f"Successfully processed upload {upload_id}")
            
        except Exception as e:
            logger.error(f"Error during format conversion: {str(e)}", exc_info=True)
            upload.status = ProcessingStatus.FAILED
            upload.error_message = f"Format conversion failed: {str(e)}"
            db.commit()
            return
            
        db.commit()
        
    except Exception as e:
        logger.error(f"Critical error in process_upload: {str(e)}", exc_info=True)
        if upload:
            upload.status = ProcessingStatus.FAILED
            upload.error_message = f"Processing failed: {str(e)}"
            try:
                db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update upload status in database: {str(db_error)}")
    finally:
        # Ensure database session is closed
        try:
            db.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")
        db.commit()

@router.post("", response_model=UploadWithDownloadUrls)
@router.post("/", response_model=UploadWithDownloadUrls)
async def create_upload(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
   
) -> Any:
    """
    Upload a new e-book file for processing and return JATS XML
    """
    logger.info(f"Starting file upload for user {current_user.id}")
    try:
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
        
        # Ensure upload directory exists
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path, file_name, file_size = save_upload_file(file, current_user.id)
        
        # Check file size limit
        max_size = (
            settings.MAX_UPLOAD_SIZE_PREMIUM
            if current_user.role in [UserRole.PREMIUM, UserRole.ADMIN]
            else settings.MAX_UPLOAD_SIZE_FREE
        )
        
        if file_size > max_size:
            # Remove the file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the limit ({max_size // 1024 // 1024}MB)"
            )
        
        # Get file type
        file_extension = file_name.split('.')[-1].lower()
        file_type = get_file_type(file_extension)
        
        # Process the file immediately to get JATS XML
        logger.info(f"Starting enhanced extraction for file: {file_path}")
        
        try:
            # Initialize the extractor
            extractor = EnhancedDocumentExtractor(file_path, file_type)
            logger.info("Extractor initialized successfully")
            
            # Extract content and generate JATS XML
            xml_path = extractor.extract()
            logger.info(f"Extraction completed. XML path: {xml_path}")
            
            if not os.path.exists(xml_path):
                raise FileNotFoundError(f"Generated XML file not found at {xml_path}")
            
            # Read the generated XML file
            with open(xml_path, 'r', encoding='utf-8') as f:
                jats_xml = f.read()
            
            logger.info(f"Successfully read JATS XML (length: {len(jats_xml)})")
            
            # Create upload record with JATS XML
            upload = Upload(
                user_id=current_user.id,
                file_name=file_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                status=ProcessingStatus.COMPLETED,
                xml_path=xml_path,
                is_xml_valid=True,
                page_count=extractor.metadata.get("processing_metadata", {}).get("page_count", 0),
                image_count=extractor.metadata.get("processing_metadata", {}).get("image_count", 0),
                formula_count=extractor.metadata.get("processing_metadata", {}).get("formula_count", 0),
                processing_time=extractor.metadata.get("processing_metadata", {}).get("processing_time", 0)
            )
            
            db.add(upload)
            db.commit()
            db.refresh(upload)
            
            # Create response with JATS XML
            response = UploadWithDownloadUrls.from_orm(upload)
            response.jats_xml = jats_xml  # Include JATS XML in response
            
            logger.info(f"Successfully processed file: {file_path}")
            return response
            
        except Exception as e:
            # Log the error and fall back to background processing
            logger.error(f"Error during immediate extraction: {str(e)}", exc_info=True)
            logger.info("Falling back to background processing")
            
            upload = Upload(
                user_id=current_user.id,
                file_name=file_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                status=ProcessingStatus.PENDING
            )
            db.add(upload)
            db.commit()
            db.refresh(upload)
            background_tasks.add_task(process_upload, upload.id, file_path, file_type, db)
            return upload
            
    except HTTPException as http_exc:
        # Log and re-raise HTTP exceptions
        logger.error(f"HTTP Exception in create_upload: {str(http_exc)}", exc_info=True)
        raise http_exc
        
    except Exception as e:
        # Log the full traceback for debugging
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected error in create_upload: {str(e)}\n{error_traceback}")
        
        # Return more detailed error information in development
        error_detail = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_traceback.split('\n') if settings.ENV == "development" else None
        }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
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