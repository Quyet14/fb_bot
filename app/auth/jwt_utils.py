# -*- coding: utf-8 -*-
"""JWT token creation and verification utilities."""
import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALGORITHM = "HS256"


def _secret() -> str:
    key = settings.JWT_SECRET_KEY
    if not key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    return key


def create_access_token(user_id: str, username: str, role: str) -> str:
    """Tạo JWT access token ngắn hạn."""
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.JWT_ACCESS_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Tạo JWT refresh token dài hạn."""
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        days=settings.JWT_REFRESH_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Xác minh token và trả về payload. Raise JWTError nếu không hợp lệ."""
    return jwt.decode(token, _secret(), algorithms=[ALGORITHM])


def get_current_user(token: str = Depends(oauth2_scheme)):
    """FastAPI Dependency: lấy user hiện tại từ Bearer token."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # Import ở đây để tránh circular import
    from app.auth.auth_crud import get_user_by_id
    from app.database import SessionLocal
    from app.config import settings as cfg

    if cfg.USE_MONGODB:
        user = get_user_by_id(None, user_id)
    else:
        db = SessionLocal()
        try:
            user = get_user_by_id(db, user_id)
        finally:
            db.close()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
