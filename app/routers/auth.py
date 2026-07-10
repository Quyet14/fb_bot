# -*- coding: utf-8 -*-
"""Auth router: đăng ký, đăng nhập, social login, logout, refresh."""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from jose import JWTError

from app.config import settings
from app.database import get_db
from app.auth.schemas import (
    UserCreate, LoginRequest, TokenOut, RefreshRequest,
    UserOut, SocialLoginRequest, ProfileUpdate, ChangePasswordRequest,
)
from app.auth import auth_crud, jwt_utils, pwd_utils

router = APIRouter(prefix="/auth", tags=["Xác thực"])


UPLOAD_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "images")
AVATAR_SUBDIR = "avatars"
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _get_db_or_none():
    if settings.USE_MONGODB:
        return None
    db_gen = get_db()
    return next(db_gen)


# ── REGISTER ──────────────────────────────────────────────────
@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate):
    if not settings.ALLOW_REGISTER:
        raise HTTPException(status_code=403, detail="Đăng ký đã bị tắt")

    db = _get_db_or_none()
    try:
        if auth_crud.user_exists(db, data.username):
            raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại")

        if data.email and auth_crud.email_exists(db, data.email):
            raise HTTPException(status_code=409, detail="Email đã được sử dụng")

        hashed = pwd_utils.hash_password(data.password)
        return auth_crud.create_user(db, data, hashed)
    finally:
        if db is not None:
            db.close()


# ── LOGIN ──────────────────────────────────────────────────────
@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest):
    db = _get_db_or_none()
    try:
        user = auth_crud.get_user_by_login(db, data.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập/Email hoặc mật khẩu không đúng",
            )

        hashed = auth_crud.get_user_hashed_password(db, data.username)
        if not hashed or not pwd_utils.verify_password(data.password, hashed):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập/Email hoặc mật khẩu không đúng",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hoá",
            )

        access_token = jwt_utils.create_access_token(user.id, user.username, user.role)
        refresh_token = jwt_utils.create_refresh_token(user.id)

        return TokenOut(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            username=user.username,
            full_name=user.full_name,
            email=user.email,
        )
    finally:
        if db is not None:
            db.close()


# ── SOCIAL LOGIN (Google/Facebook) ────────────────────────────
@router.post("/social-login", response_model=TokenOut)
def social_login(data: SocialLoginRequest):
    """
    Đăng nhập qua Google hoặc Facebook.
    Frontend gọi API sau khi nhận được access_token từ Google/Facebook SDK.
    """
    # TODO: Xác minh access_token với Google/Facebook API
    # Đây là stub — bạn cần implement xác minh token thực tế

    if not data.email:
        raise HTTPException(status_code=400, detail="Email is required")

    db = _get_db_or_none()
    try:
        user = auth_crud.get_or_create_social_user(
            db, data.provider, data.email, data.full_name
        )

        access_token = jwt_utils.create_access_token(user.id, user.username, user.role)
        refresh_token = jwt_utils.create_refresh_token(user.id)

        return TokenOut(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            username=user.username,
            full_name=user.full_name,
            email=user.email,
        )
    finally:
        if db is not None:
            db.close()


# ── REFRESH ────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenOut)
def refresh_token(data: RefreshRequest):
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token không hợp lệ hoặc đã hết hạn",
    )
    try:
        payload = jwt_utils.verify_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exc
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    db = _get_db_or_none()
    try:
        user = auth_crud.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise credentials_exc

        new_access = jwt_utils.create_access_token(user.id, user.username, user.role)
        new_refresh = jwt_utils.create_refresh_token(user.id)

        return TokenOut(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            username=user.username,
            full_name=user.full_name,
            email=user.email,
        )
    finally:
        if db is not None:
            db.close()


# ── ME ─────────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut)
def me(current_user: UserOut = Depends(jwt_utils.get_current_user)):
    return current_user


# ── LOGOUT ─────────────────────────────────────────────────────
@router.post("/logout", status_code=204)
def logout(current_user: UserOut = Depends(jwt_utils.get_current_user)):
    return None


# ── CONFIG ─────────────────────────────────────────────────────
@router.get("/config")
def auth_config():
    return {"allow_register": settings.ALLOW_REGISTER}


# ── UPDATE PROFILE ─────────────────────────────────────────────
@router.put("/profile", response_model=UserOut)
def update_profile(
    data: ProfileUpdate,
    current_user: UserOut = Depends(jwt_utils.get_current_user),
):
    db = _get_db_or_none()
    try:
        payload = data.model_dump(exclude_unset=True)

        # Kiểm tra email trùng với user khác
        if payload.get("email"):
            existing = auth_crud.get_user_by_email(db, payload["email"])
            if existing and existing.id != current_user.id:
                raise HTTPException(status_code=409, detail="Email đã được sử dụng bởi tài khoản khác")

        updated = auth_crud.update_profile(db, current_user.id, payload)
        if not updated:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
        return updated
    finally:
        if db is not None:
            db.close()


# ── CHANGE PASSWORD ────────────────────────────────────────────
@router.post("/profile/avatar", response_model=UserOut)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user: UserOut = Depends(jwt_utils.get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Chi ho tro anh jpg, png, webp hoac gif")

    content_type = (file.content_type or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tai len phai la anh")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File anh rong")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Anh dai dien toi da 5MB")

    user_dir = os.path.join(UPLOAD_IMAGES_DIR, AVATAR_SUBDIR, current_user.id)
    os.makedirs(user_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/images/{AVATAR_SUBDIR}/{current_user.id}/{filename}"
    db = _get_db_or_none()
    try:
        updated = auth_crud.update_profile(db, current_user.id, {"avatar_url": avatar_url})
        if not updated:
            raise HTTPException(status_code=404, detail="Khong tim thay tai khoan")
        return updated
    finally:
        if db is not None:
            db.close()


@router.put("/change-password", status_code=204)
def change_password(
    data: ChangePasswordRequest,
    current_user: UserOut = Depends(jwt_utils.get_current_user),
):
    db = _get_db_or_none()
    try:
        hashed = auth_crud.get_hashed_password_by_id(db, current_user.id)
        if not hashed or not pwd_utils.verify_password(data.current_password, hashed):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng",
            )
        new_hashed = pwd_utils.hash_password(data.new_password)
        auth_crud.update_password(db, current_user.id, new_hashed)
        return None
    finally:
        if db is not None:
            db.close()
