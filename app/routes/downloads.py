import os
import base64
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Path, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.upload import Upload
from app.models.ocr import OCRData
from app.utils.dependencies import get_current_user, oauth2_scheme

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{user_id}/{filename:path}")
def download_file(
    user_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Download a file from uploads directory
    """
    # Check if user has permission to download this file
    if str(current_user.id) != str(user_id) and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Construct file path
    file_path = os.path.join(settings.UPLOAD_DIR, str(user_id), filename)
    
    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Get file extension for content type
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Determine content type
    content_type = "application/octet-stream"  # Default
    if file_ext == ".pdf":
        content_type = "application/pdf"
    elif file_ext == ".docx":
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_ext == ".epub":
        content_type = "application/epub+zip"
    elif file_ext == ".mobi":
        content_type = "application/x-mobipocket-ebook"
    elif file_ext == ".html":
        content_type = "text/html"
    elif file_ext == ".xml":
        content_type = "application/xml"
    
    logger.debug(f"File download requested for file: {filename}")
    
    return FileResponse(
        file_path,
        media_type=content_type,
        filename=os.path.basename(filename)
    )


@router.get("/test-auth")
async def test_auth(
    current_user: User = Depends(get_current_user)
):
    """Test endpoint to verify authentication is working"""
    return {"user_id": current_user.id, "email": current_user.email, "status": "authenticated"}


@router.get("/html-download/{upload_id}")
async def download_html_new(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download HTML file with embedded Base64 images from database"""
    try:
        logger.info(f"HTML download requested for upload_id: {upload_id} by user: {current_user.id}")
        
        # Get upload record with user permission check
        upload = db.query(Upload).filter(
            Upload.id == upload_id,
            Upload.user_id == current_user.id
        ).first()
        
        if not upload:
            logger.error(f"Upload not found or access denied for id: {upload_id}, user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Upload not found or access denied")
        
        logger.info(f"Found upload: {upload.file_name}, html_path: {upload.html_path}")
        
        if not upload.html_path or not os.path.exists(upload.html_path):
            logger.error(f"HTML file not available for upload: {upload_id}")
            raise HTTPException(status_code=404, detail="HTML file not available")
        
        # Get OCR data with images
        ocr_data = db.query(OCRData).filter(OCRData.filename == upload.file_name).first()
        
        # Read the original HTML file
        with open(upload.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info(f"Read HTML file, length: {len(html_content)} characters")
        
        # Process images if OCR data exists
        images_html = []
        embedded_count = 0
        extracted_images = []
        
        if ocr_data and ocr_data.extracted_images:
            if isinstance(ocr_data.extracted_images, list):
                extracted_images = ocr_data.extracted_images
            else:
                try:
                    import json
                    extracted_images = json.loads(ocr_data.extracted_images)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted_images JSON")
        
        # Embed images as Base64 if they exist
        if extracted_images:
            logger.info(f"Processing {len(extracted_images)} extracted images")
            
            for i, img_path in enumerate(extracted_images):
                if not img_path:
                    continue
                    
                logger.info(f"Processing image {i+1}: {img_path}")
                
                # Try multiple path constructions
                abs_image_path = None
                
                # Get the base filename
                img_filename = os.path.basename(img_path)
                
                # Get current working directory and project structure
                current_dir = os.getcwd()
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                project_root = os.path.dirname(backend_dir)
                
                # Clean the image path - remove any leading path separators
                clean_img_path = img_path.strip().lstrip('/\\')
                
                # List of paths to try (ordered by most likely to least likely)
                potential_paths = [
                    # Path 1: Direct absolute path if provided
                    img_path if os.path.isabs(img_path) else None,
                    
                    # Path 2: Project root + static + extracted_images + filename (most common)
                    os.path.join(project_root, "static", "extracted_images", img_filename),
                    
                    # Path 3: Current working directory + static + extracted_images + filename
                    os.path.join(current_dir, "static", "extracted_images", img_filename),
                    
                    # Path 4: Backend directory + static + extracted_images + filename
                    os.path.join(backend_dir, "static", "extracted_images", img_filename),
                    
                    # Path 5: Using settings EXTRACTED_IMAGES_DIR + filename
                    os.path.join(project_root, settings.EXTRACTED_IMAGES_DIR, img_filename) if hasattr(settings, 'EXTRACTED_IMAGES_DIR') else None,
                    
                    # Path 6: If img_path already contains extracted_images, use it directly from project root
                    os.path.join(project_root, "static", clean_img_path) if "extracted_images" in clean_img_path else None,
                    
                    # Path 7: If img_path starts with static/, use it from project root
                    os.path.join(project_root, clean_img_path) if clean_img_path.startswith("static") else None,
                    
                    # Path 8: Try relative to current directory
                    os.path.join(current_dir, clean_img_path),
                    
                    # Path 9: Legacy paths for backward compatibility
                    os.path.join(project_root, "extracted_images", img_filename),
                    os.path.join(current_dir, "extracted_images", img_filename),
                ]
                
                # Filter out None values and duplicates
                potential_paths = list(dict.fromkeys([p for p in potential_paths if p is not None]))
                
                logger.debug(f"Trying {len(potential_paths)} potential paths for image: {img_filename}")
                
                for j, path in enumerate(potential_paths):
                    logger.debug(f"  Path {j+1}: {path}")
                    if os.path.exists(path) and os.path.isfile(path):
                        abs_image_path = path
                        logger.info(f"✓ Found image at path {j+1}: {abs_image_path}")
                        break
                
                if abs_image_path and os.path.exists(abs_image_path):
                    # Read and encode image as Base64
                    try:
                        logger.info(f"Reading and encoding image: {abs_image_path}")
                        with open(abs_image_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            
                            # Determine image format
                            ext = os.path.splitext(abs_image_path)[1].lower().lstrip('.')
                            if ext == 'jpg':
                                ext = 'jpeg'
                            elif ext not in ['png', 'jpeg', 'gif', 'webp', 'svg']:
                                ext = 'png'  # Default fallback
                            
                            data_uri = f"data:image/{ext};base64,{encoded_string}"
                            images_html.append(f'''
                                <div style="margin: 15px 0; text-align: center;">
                                    <img src="{data_uri}" 
                                         alt="Extracted Image {i+1}" 
                                         style="max-width: 100%; max-height: 600px; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <p style="font-size: 12px; color: #666; margin-top: 5px;">Image {i+1}: {img_filename}</p>
                                </div>
                            ''')
                            embedded_count += 1
                            logger.info(f"✓ Successfully embedded image {i+1}: {img_filename} (size: {len(encoded_string)} chars)")
                    except Exception as e:
                        logger.error(f"Error reading image file {abs_image_path}: {str(e)}")
                        images_html.append(f'''
                            <div style="margin: 15px 0; padding: 20px; border: 1px dashed #ccc; text-align: center; color: #666;">
                                <p>❌ Error loading Image {i+1}: {img_filename}</p>
                                <p style="font-size: 10px;">Error: {str(e)}</p>
                            </div>
                        ''')
                else:
                    logger.warning(f"❌ Image not found in any location: {img_filename}")
                    logger.warning(f"Original path: {img_path}")
                    logger.warning(f"Searched {len(potential_paths)} locations")
                    
                    # List existing files in the expected directory for debugging
                    expected_dir = os.path.join(project_root, "static", "extracted_images")
                    if os.path.exists(expected_dir):
                        existing_files = os.listdir(expected_dir)
                        logger.warning(f"Files in {expected_dir}: {existing_files[:10]}...")  # Show first 10 files
                    
                    images_html.append(f'''
                        <div style="margin: 15px 0; padding: 20px; border: 1px dashed #ccc; text-align: center; color: #666;">
                            <p>❌ Image {i+1} not found: {img_filename}</p>
                            <p style="font-size: 10px;">Original path: {img_path}</p>
                            <p style="font-size: 10px;">Searched {len(potential_paths)} locations</p>
                        </div>
                    ''')
            
            # Insert images into HTML
            if images_html:
                images_section = f'''
                    <div style="margin: 30px 0; padding: 20px; background-color: #f9f9f9; border-radius: 8px;">
                        <h2 style="color: #333; margin-bottom: 20px; text-align: center;">Extracted Images</h2>
                        {''.join(images_html)}
                    </div>
                '''
                
                # Insert before closing body tag
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'{images_section}</body>')
                else:
                    html_content += images_section
            
            logger.info(f"Successfully embedded {embedded_count} out of {len(extracted_images)} images into HTML")
        
        # Return HTML with embedded images
        response = Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={upload.file_name}.html"
            }
        )
        logger.info(f"Returning HTML response, content length: {len(html_content)}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in HTML download: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/public/export/{upload_id}")
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
    """
    try:
        # Set CORS headers for public access
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        
        logger.info(f"Processing public export request - Upload ID: {upload_id}, Format: {format}")
        
        # Get the upload record
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            error_msg = f"Upload not found with ID: {upload_id}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        logger.info(f"Found upload: {upload.filename}, ID: {upload.id}")
        
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
                os.path.join(settings.BASE_DIR, file_path),
                os.path.join(settings.OUTPUT_DIR, file_path),
                os.path.join(os.getcwd(), file_path),
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
        
        # Generate filename for download
        original_name = getattr(upload, 'original_filename', upload.filename)
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


@router.options("/public/export/{upload_id}")
async def options_export_ebook():
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600"  # 10 minutes
        }
    )


@router.get("/test-token-validation", response_model=dict)
async def test_token_validation(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to validate JWT token and return token details
    """
    try:
        # Try to get current user to test token validation
        user = get_current_user(db, token)
        
        # If we get here, token is valid
        return {
            "status": "valid",
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active
        }
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return {
                "status": "invalid",
                "error": "Invalid or expired token",
                "detail": str(e.detail) if hasattr(e, 'detail') else "No details"
            }
        return {
            "status": "error",
            "error": "Validation error",
            "detail": str(e.detail) if hasattr(e, 'detail') else str(e)
        }