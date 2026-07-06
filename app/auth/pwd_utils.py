# -*- coding: utf-8 -*-
"""Bcrypt password hashing — dùng thư viện bcrypt trực tiếp (tương thích bcrypt 5.x)."""
import bcrypt


def hash_password(plain: str) -> str:
    """Trả về bcrypt hash của plain-text password."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Kiểm tra plain-text password khớp với hash hay không."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
