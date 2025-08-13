import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import List, Tuple

from app.core.config import settings
from app.models.upload import FileType


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split(".")[-1].lower()


def is_valid_file_type(file_extension: str) -> bool:
    """Check if file type is supported"""
    return file_extension in [e.value for e in FileType]


def get_file_type(file_extension: str) -> FileType:
    """Convert file extension to FileType enum"""
    if file_extension == "pdf":
        return FileType.PDF
    elif file_extension == "docx":
        return FileType.DOCX
    elif file_extension == "epub":
        return FileType.EPUB
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def save_upload_file(upload_file: UploadFile, user_id: int) -> Tuple[str, str, int]:
    """
    Save uploaded file and return file path, file name, and file size
    """
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Create user directory
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Get file extension and check if it's supported
    file_extension = get_file_extension(upload_file.filename)
    if not is_valid_file_type(file_extension):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: .{file_extension}. Supported types are: pdf, docx, epub"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(user_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return file_path, upload_file.filename, file_size


def get_download_url(file_path: str) -> str:
    """
    Generate a download URL for a file
    """
    if not file_path:
        return None
        
    # Get relative path to upload dir
    if file_path.startswith(settings.UPLOAD_DIR):
        relative_path = file_path[len(settings.UPLOAD_DIR):].lstrip('/')
        return f"/api/v1/downloads/{relative_path}"
    
    return None