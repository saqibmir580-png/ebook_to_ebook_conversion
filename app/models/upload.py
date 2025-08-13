from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.db.base_class import Base


class FileType(str, PyEnum):
    PDF = "pdf"
    DOCX = "docx"
    EPUB = "epub"


class ProcessingStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(Enum(FileType), nullable=False)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    # Extraction results
    xml_path = Column(String, nullable=True)
    is_xml_valid = Column(Boolean, nullable=True)
    html_path = Column(String, nullable=True)
    epub_path = Column(String, nullable=True)
    mobi_path = Column(String, nullable=True)
    
    # Metadata
    page_count = Column(Integer, nullable=True)
    image_count = Column(Integer, nullable=True)
    formula_count = Column(Integer, nullable=True)
    
    # Processing metrics
    processing_time = Column(Float, nullable=True)  # Time in seconds
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship with User
    user = relationship("User", back_populates="uploads")