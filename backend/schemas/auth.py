from pydantic import BaseModel, EmailStr

class SignUp(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"