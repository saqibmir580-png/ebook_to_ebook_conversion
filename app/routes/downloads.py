import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.upload import Upload
from app.utils.dependencies import get_current_user


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
    
    return FileResponse(
        file_path,
        media_type=content_type,
        filename=os.path.basename(filename)
    )