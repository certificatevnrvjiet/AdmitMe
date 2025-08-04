from typing import Optional
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    dept: str
    rights: str
    password: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    dept: str
    rights: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    dept: Optional[str] = None
    rights: Optional[str] = None
    password: Optional[str] = None

class PasswordChange(BaseModel):
    new_password: str
    confirm_password: str 