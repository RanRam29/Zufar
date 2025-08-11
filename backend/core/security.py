"""
Security utilities for the application.

This module implements minimal password hashing and token creation without
introducing heavy external dependencies.  Passwords are hashed using
PBKDF2‑HMAC with SHA‑256 and a random salt.  Access tokens are signed
using HMAC and encoded with URL‑safe base64.  The tokens include the
subject (user ID), an expiry timestamp and a signature.  See
``create_access_token`` for the format.
"""

import base64
import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from ..models.user import User


def get_password_hash(password: str) -> str:
    """Create a salted PBKDF2 hash of the given password.

    The returned string contains the hex‑encoded salt and hash separated
    by a colon.  A relatively high iteration count is used to slow
    down brute‑force attacks.
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}:{dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against the stored salted hash."""
    try:
        salt_hex, hash_hex = hashed_password.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, 100_000)
    return hmac.compare_digest(dk, expected)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    """Generate a simple HMAC‑signed access token.

    The token structure is ``base64url(subject:expiry:signature)`` where
    ``expiry`` is a Unix timestamp in seconds and ``signature`` is
    ``HMAC_SHA256(secret, subject:expiry)`` in hex.  The token must be
    presented as a Bearer token by the client.  The default expiry
    duration is read from the configuration.
    """
    expiry = int(time.time()) + ((expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES) * 60)
    message = f"{subject}:{expiry}".encode()
    signature = hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()
    token_str = f"{subject}:{expiry}:{signature}"
    return base64.urlsafe_b64encode(token_str.encode()).decode()


def _decode_token(token: str) -> Tuple[str, int]:
    """Decode and verify an access token.

    Returns the subject and expiry on success.  Raises ``ValueError`` on
    signature mismatch or expiry.
    """
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        subject, expiry_str, signature = decoded.split(":", 2)
        expiry = int(expiry_str)
    except Exception as exc:
        raise ValueError("Malformed token") from exc
    message = f"{subject}:{expiry}".encode()
    expected_sig = hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        raise ValueError("Invalid signature")
    if expiry < int(time.time()):
        raise ValueError("Token expired")
    return subject, expiry


http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Retrieve the currently authenticated user from a Bearer token.

    Raises a 401 error if authentication fails for any reason.
    """
    if cred is None or cred.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = cred.credentials
    try:
        subject, _expiry = _decode_token(token)
        user_id = int(subject)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
