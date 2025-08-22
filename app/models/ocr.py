from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
import datetime

from app.db.base_class import Base

class OCRData(Base):
    __tablename__ = 'ocr_data'
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True)
    extracted_text = Column(Text)
    extracted_json = Column(JSON)
    extracted_images = Column(JSON)  # Store JSON list of image paths
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
