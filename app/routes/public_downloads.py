import os
import base64
import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.db.session import get_db
from app.models.upload import Upload
from app.models.ocr import OCRData

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

# Map file extensions to content types
CONTENT_TYPES = {
    'html': 'text/html',
    'epub': 'application/epub+zip',
    'mobi': 'application/x-mobipocket-ebook',
    'xml': 'application/xml',
    'pdf': 'application/pdf'
}

def embed_images_in_html(html_content: str, upload_id: int, db: Session) -> str:
    """
    Embed images as Base64 data URIs in HTML content
    """
    try:
        # Get upload record first to get filename
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            logger.error(f"Upload not found with ID: {upload_id}")
            return html_content
        
        # Get OCR data using filename (not upload_id)
        ocr_data = db.query(OCRData).filter(OCRData.filename == upload.file_name).first()
        if not ocr_data:
            logger.info(f"No OCR data found for filename: {upload.file_name}")
            return html_content
        
        if not ocr_data.extracted_images:
            logger.info(f"No extracted images found for filename: {upload.file_name}")
            return html_content
        
        # Parse extracted images
        extracted_images = []
        if isinstance(ocr_data.extracted_images, str):
            try:
                extracted_images = json.loads(ocr_data.extracted_images)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse extracted_images JSON for filename: {upload.file_name}")
                return html_content
        elif isinstance(ocr_data.extracted_images, list):
            extracted_images = ocr_data.extracted_images
        else:
            logger.error(f"extracted_images is not a valid format for filename: {upload.file_name}")
            return html_content
        
        if not extracted_images:
            logger.info(f"No images in extracted_images for filename: {upload.file_name}")
            return html_content
        
        logger.info(f"Found {len(extracted_images)} images to embed for filename: {upload.file_name}")
        
        # Replace image paths with Base64 data URIs
        modified_html = html_content
        embedded_count = 0
        
        for image_path in extracted_images:
            if not image_path:
                continue
                
            # Try different possible image locations
            possible_paths = [
                os.path.join(settings.EXTRACTED_IMAGES_DIR, os.path.basename(image_path)),
                os.path.join(settings.STATIC_DIR, "extracted_images", os.path.basename(image_path)),
                os.path.join(os.getcwd(), settings.EXTRACTED_IMAGES_DIR, os.path.basename(image_path)),
                os.path.join(os.getcwd(), "static", "extracted_images", os.path.basename(image_path)),
                image_path
            ]
            
            image_found = False
            for full_path in possible_paths:
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'rb') as img_file:
                            img_data = img_file.read()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            
                            # Determine image format
                            img_format = 'png'
                            if full_path.lower().endswith(('.jpg', '.jpeg')):
                                img_format = 'jpeg'
                            elif full_path.lower().endswith('.gif'):
                                img_format = 'gif'
                            elif full_path.lower().endswith('.webp'):
                                img_format = 'webp'
                            
                            # Create data URI
                            data_uri = f"data:image/{img_format};base64,{img_base64}"
                            
                            # Replace all occurrences of this image path
                            image_basename = os.path.basename(image_path)
                            
                            # Try multiple replacement patterns
                            replacements = [
                                (f'src="{image_path}"', f'src="{data_uri}"'),
                                (f"src='{image_path}'", f"src='{data_uri}'"),
                                (f'src="{image_basename}"', f'src="{data_uri}"'),
                                (f"src='{image_basename}'", f"src='{data_uri}'"),
                                (f'src="static/extracted_images/{image_basename}"', f'src="{data_uri}"'),
                                (f"src='static/extracted_images/{image_basename}'", f"src='{data_uri}'"),
                                (f'src="../static/extracted_images/{image_basename}"', f'src="{data_uri}"'),
                                (f"src='../static/extracted_images/{image_basename}'", f"src='{data_uri}'")
                            ]
                            
                            for old_src, new_src in replacements:
                                if old_src in modified_html:
                                    modified_html = modified_html.replace(old_src, new_src)
                                    embedded_count += 1
                                    logger.info(f"Replaced {old_src} with embedded image")
                            
                            logger.info(f"Embedded image: {image_basename} from {full_path}")
                            image_found = True
                            break
                    except Exception as e:
                        logger.error(f"Error reading image {full_path}: {str(e)}")
                        continue
            
            if not image_found:
                logger.warning(f"Image not found in any location: {image_path}")
        
        logger.info(f"Successfully embedded {embedded_count} images in HTML")
        return modified_html
        
    except Exception as e:
        logger.error(f"Error embedding images: {str(e)}", exc_info=True)
        return html_content

@router.get("/export/{upload_id}")
@router.head("/export/{upload_id}")
async def public_export_ebook(
    request: Request,
    response: Response,
    upload_id: int,
    format: str,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to export converted ebooks without authentication
    Supported formats: html, epub, mobi, xml
    Supports both GET and HEAD methods
    """
    try:
        # Set CORS headers for public access
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        
        logger.info(f"Processing public export request - Upload ID: {upload_id}, Format: {format}, Method: {request.method}")
        
        # Get the upload record
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            error_msg = f"Upload not found with ID: {upload_id}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        logger.info(f"Found upload: {upload.file_name}, ID: {upload.id}")
        
        # Determine the file path based on format
        file_path = None
        content_type = "application/octet-stream"
        
        format = format.lower()
        
        # Map format to file path attribute and content type
        format_mapping = {
            'html': ('html_path', 'text/html'),
            'epub': ('epub_path', 'application/epub+zip'),
            'mobi': ('mobi_path', 'application/x-mobipocket-ebook'),
            'xml': ('xml_path', 'application/xml')
        }
        
        if format not in format_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}. Supported formats: html, epub, mobi, xml"
            )
        
        file_attr, content_type = format_mapping[format]
        
        if hasattr(upload, file_attr):
            file_path = getattr(upload, file_attr, None)
        
        if not file_path:
            error_msg = f"No {format.upper()} file available for this upload"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Convert to absolute path if it's a relative path
        if not os.path.isabs(file_path):
            # Try different base directories
            possible_paths = [
                os.path.join(os.getcwd(), file_path),
                os.path.join(settings.OUTPUT_DIR, file_path),
                os.path.join(settings.UPLOAD_DIR, file_path),
                file_path  # Try as is
            ]
            
            file_found = False
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    file_found = True
                    break
            
            if not file_found:
                logger.error(f"File not found in any of the expected locations: {possible_paths}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{format.upper()} file not found"
                )
        
        logger.info(f"Serving file: {file_path}")
        
        # For HEAD requests, just return headers without content
        if request.method == "HEAD":
            # Generate filename for headers
            original_name = getattr(upload, 'original_filename', upload.file_name)
            if original_name:
                filename_without_ext = os.path.splitext(original_name)[0]
                filename = f"{filename_without_ext}.{format}"
            else:
                filename = f"export_{upload_id}.{format}"
            
            return Response(
                status_code=200,
                headers={
                    "Content-Type": content_type,
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Access-Control-Expose-Headers": "Content-Disposition",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        
        # Special handling for HTML files - embed images as Base64
        if format == 'html':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Embed images as Base64 data URIs
                html_with_images = embed_images_in_html(html_content, upload_id, db)
                
                # Generate filename for download
                original_name = getattr(upload, 'original_filename', upload.file_name)
                if original_name:
                    filename_without_ext = os.path.splitext(original_name)[0]
                    filename = f"{filename_without_ext}.{format}"
                else:
                    filename = f"export_{upload_id}.{format}"
                
                # Return HTML content with embedded images
                return Response(
                    content=html_with_images,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "Access-Control-Expose-Headers": "Content-Disposition",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing HTML file: {str(e)}")
                # Fall back to regular file response
        
        # Generate filename for download
        original_name = getattr(upload, 'original_filename', upload.file_name)
        if original_name:
            filename_without_ext = os.path.splitext(original_name)[0]
            filename = f"{filename_without_ext}.{format}"
        else:
            filename = f"export_{upload_id}.{format}"
        
        # Set response headers
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Access-Control-Allow-Origin": "*"
        }
        
        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in public_export_ebook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.options("/export/{upload_id}")
async def options_export_ebook():
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600"  # 10 minutes
        }
    )
