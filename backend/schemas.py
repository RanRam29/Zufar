from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

class LoginJSON(BaseModel):
    identifier: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
