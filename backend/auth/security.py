"""
Password hashing and JWT token creation/verification.
Uses the bcrypt library directly (not passlib, which has known
compatibility issues with recent bcrypt versions).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

# bcrypt has a hard 72-byte limit on the input password — truncate
# safely rather than letting it raise an error for long passwords.
MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password for storage. Never store the raw password."""
    password_bytes = plain_password.encode("utf-8")[:MAX_PASSWORD_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")[:MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        logger.warning("Malformed password hash encountered during verification.")
        return False


def create_access_token(username: str) -> str:
    """Create a signed JWT encoding the username and an expiry time."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """
    Verify a JWT's signature and expiry, returning the username it
    encodes — or None if the token is invalid/expired/tampered with.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        logger.warning("Invalid or expired JWT presented.")
        return None