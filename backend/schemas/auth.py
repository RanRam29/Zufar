from pydantic import BaseModel, EmailStr, Field

class SignUp(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=256)

class Login(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=256)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
