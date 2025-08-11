from fastapi import APIRouter

# Import מתוקן
from ..schemas import SignUp, Login, Token

router = APIRouter()

@router.get("/ping")
def ping():
    return {"msg": "pong"}
