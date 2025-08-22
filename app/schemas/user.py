from typing import Optional, Union
from pydantic import BaseModel, EmailStr, field_validator, FieldValidationInfo
from datetime import datetime

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name : Optional[str] = None
    email: EmailStr
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info: FieldValidationInfo) -> str:
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('passwords do not match')
        return v


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[Union[str, int]] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class RefreshToken(BaseModel):
    refresh_token: str