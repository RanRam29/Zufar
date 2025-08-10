"""Authentication utilities for the casualty management application.

This module provides functions and dependencies to handle user
registration, login and JWT-based authentication. Passwords are
hashed using ``passlib``'s bcrypt implementation. Access tokens are
JSON Web Tokens signed with a secret key. The token contains the
user ID in the ``sub`` claim and expires after a configurable
duration.

FastAPI's dependency injection is used to provide the current user
to request handlers. The ``get_current_user`` dependency validates
the JWT and retrieves the corresponding user from the database.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlmodel import select

from .db import get_session
from .models import User

# Configurable settings. In production you should set a secure
# ``JWT_SECRET`` environment variable. The default secret is for
# development only and must not be used in production.
import os

JWT_SECRET = os.getenv("JWT_SECRET", "insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Password hashing context. Using bcrypt for secure password
# storage. The hash includes the salt, so you only need to store the
# hashed password.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction. Clients must send the JWT in
# the ``Authorization: Bearer <token>`` header when accessing
# protected endpoints. The token URL is set by the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Hash a plain-text password for storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    :param subject: The ``sub`` claim – typically the user ID as a string.
    :param expires_delta: Override default expiration time.
    :returns: Encoded JWT string
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token and return the payload.

    Raises an HTTP 401 error if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})


async def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password.

    Returns the User if the credentials are valid, else ``None``.
    """
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    """Dependency that resolves the currently authenticated user.

    Checks the JWT in the Authorization header and fetches the
    corresponding User from the database. Raises 401 if the token is
    invalid or the user no longer exists.
    """
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload", headers={"WWW-Authenticate": "Bearer"})
    user = session.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found", headers={"WWW-Authenticate": "Bearer"})
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the current user is active. Extend for account disabled flags."""
    # Placeholder for future account state checks.
    return current_user


async def get_current_active_dispatcher(current_user: User = Depends(get_current_active_user)) -> User:
    """Ensures the user has a dispatcher role."""
    if current_user.role != "dispatcher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation requires dispatcher role")
    return current_user