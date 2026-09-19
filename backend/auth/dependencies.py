"""
FastAPI dependency that extracts and verifies the current user
from the Authorization header, for use on any protected endpoint.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.auth.security import decode_access_token

# tokenUrl is just for the /docs "Authorize" button — points at our login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_username(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decode the bearer token from the request and return the
    username it belongs to, or raise 401 if it's missing/invalid.
    """
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username