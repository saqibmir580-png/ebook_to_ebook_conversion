from typing import Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from app.models.upload import FileType, ProcessingStatus


class UploadBase(BaseModel):
    file_name: str
    file_type: FileType


class UploadCreate(UploadBase):
    pass


class UploadUpdate(UploadBase):
    status: Optional[ProcessingStatus] = None
    progress: Optional[int] = None
    xml_path: Optional[str] = None
    is_xml_valid: Optional[bool] = None
    html_path: Optional[str] = None
    epub_path: Optional[str] = None
    mobi_path: Optional[str] = None
    page_count: Optional[int] = None
    image_count: Optional[int] = None
    formula_count: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


class UploadInDBBase(UploadBase):
    id: int
    user_id: int
    file_path: str
    file_size: int
    status: ProcessingStatus
    progress: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Upload(UploadInDBBase):
    xml_path: Optional[str] = None
    is_xml_valid: Optional[bool] = None
    html_path: Optional[str] = None
    epub_path: Optional[str] = None
    mobi_path: Optional[str] = None
    page_count: Optional[int] = None
    image_count: Optional[int] = None
    formula_count: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    download_urls: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True


class UploadWithDownloadUrls(Upload):
    xml_url: Optional[str] = None
    html_url: Optional[str] = None
    epub_url: Optional[str] = None
    mobi_url: Optional[str] = None


class UploadResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    file_size: int
    file_type: FileType
    status: ProcessingStatus
    progress: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    xml_path: Optional[str] = None
    is_xml_valid: Optional[bool] = None
    html_path: Optional[str] = None
    epub_path: Optional[str] = None
    mobi_path: Optional[str] = None
    json_export_path: Optional[str] = None
    csv_export_path: Optional[str] = None
    page_count: Optional[int] = None
    image_count: Optional[int] = None
    formula_count: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

    # URLs will be constructed in the route
    xml_url: Optional[str] = None
    html_url: Optional[str] = None
    epub_url: Optional[str] = None
    mobi_url: Optional[str] = None
    json_export_url: Optional[str] = None
    csv_export_url: Optional[str] = None

    class Config:
        from_attributes = True


class UploadStatistics(BaseModel):
    total_uploads: int
    completed: int
    in_progress: int
    failed: int
    
    class Config:
        from_attributes = True