from pydantic import BaseModel
from typing import Optional, List, Union
import datetime
import json

class OCRDataBase(BaseModel):
    filename: str
    extracted_text: Optional[str] = None
    extracted_json: Optional[str] = None
    extracted_images: Optional[str] = None

class OCRDataCreate(OCRDataBase):
    pass

class OCRDataUpdate(OCRDataBase):
    pass

class OCRDataInDBBase(OCRDataBase):
    id: int
    uploaded_at: datetime.datetime

    class Config:
        from_attributes = True

class OCRData(OCRDataInDBBase):
    pass

class OCRDataResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime.datetime
    extracted_text: Optional[str] = None
    extracted_json: Optional[Union[List[dict], dict]] = None  # Accept both list and dict
    extracted_images: Optional[List[str]] = None

    class Config:
        from_attributes = True