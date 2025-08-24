# backend/security_simple.py
from __future__ import annotations
import base64, hmac, hashlib, os, time
from dataclasses import dataclass
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from bcrypt import hashpw, gensalt, checkpw

# Pull secret from env (or default to a dev key); keep it stable across restarts in prod
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "change-me-in-prod"
TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

bearer = HTTPBearer(auto_error=False)

def hash_password(plain: str) -> str:
    return hashpw(plain.encode("utf-8"), gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    exp = int(time.time()) + (expires_minutes or TOKEN_EXPIRE_MINUTES) * 60
    msg = f"{subject}:{exp}".encode("utf-8")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    token_bytes = f"{subject}:{exp}:{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(token_bytes).decode("utf-8")

def decode_access_token(token: str) -> Tuple[str, int]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        subject, exp_str, sig = raw.split(":", 2)
        exp = int(exp_str)
        msg = f"{subject}:{exp}".encode("utf-8")
        expected = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise ValueError("Invalid signature")
        if int(time.time()) > exp:
            raise ValueError("Token expired")
        return subject, exp
    except Exception as e:
        raise ValueError("Invalid token") from e

# Dependency for routes
def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        sub, _ = decode_access_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        return int(sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")
