# -*- coding: utf-8 -*-
"""Shared dependencies for FastAPI endpoints."""
from fastapi import Depends

from app.auth.jwt_utils import get_current_user
from app.auth.schemas import UserOut


def get_user_id(current_user: UserOut = Depends(get_current_user)) -> str:
    """Extract user_id from the authenticated user for multi-tenant isolation."""
    return current_user.id
