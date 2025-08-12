from pydantic import BaseModel, EmailStr

class SignUp(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
