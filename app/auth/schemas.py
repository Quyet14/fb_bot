# -*- coding: utf-8 -*-
"""Pydantic schemas for authentication."""
import datetime
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ hoa")
    if not re.search(r"[a-z]", v):
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ thường")
    if not re.search(r"\d", v):
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ số")
    return v


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    password: str = Field(..., min_length=8)
    confirm_password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("email")
    @classmethod
    def email_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Email không hợp lệ")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self


class LoginRequest(BaseModel):
    username: str = Field(..., description="Tên đăng nhập hoặc email")
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime.datetime


class SocialLoginRequest(BaseModel):
    provider: str
    access_token: str
    email: Optional[str] = None
    full_name: Optional[str] = None


# ── Profile update ────────────────────────────────────────────
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=300)
    avatar_url: Optional[str] = Field(None, max_length=500)

    @field_validator("email")
    @classmethod
    def email_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Email không hợp lệ")
        return v


# ── Change password ───────────────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self
