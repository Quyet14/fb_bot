# -*- coding: utf-8 -*-
"""
Auth CRUD layer — hỗ trợ cả MongoDB và SQLAlchemy.
Bổ sung các trường: full_name, email, social provider.
"""
import datetime
import uuid
from typing import Optional

from app.config import settings
from app.auth.schemas import UserCreate, UserOut


if settings.USE_MONGODB:
    # ── MongoDB branch ──────────────────────────────────────
    from app.mongo_db import get_collection

    def _col():
        return get_collection("users")

    def _ensure_indexes():
        _col().create_index("username", unique=True)
        _col().create_index("email", sparse=True)  # email có thể null

    def _to_user_out(doc) -> Optional[UserOut]:
        if not doc:
            return None
        return UserOut(
            id=str(doc.get("id") or doc.get("_id")),
            username=doc["username"],
            full_name=doc.get("full_name"),
            email=doc.get("email"),
            role=doc.get("role", "admin"),
            is_active=doc.get("is_active", True),
            created_at=doc.get("created_at", datetime.datetime.utcnow()),
        )

    def get_user_by_username(db, username: str) -> Optional[UserOut]:
        doc = _col().find_one({"username": username})
        return _to_user_out(doc)

    def get_user_by_email(db, email: str) -> Optional[UserOut]:
        doc = _col().find_one({"email": email})
        return _to_user_out(doc)

    def get_user_by_id(db, user_id: str) -> Optional[UserOut]:
        doc = _col().find_one({"id": user_id})
        return _to_user_out(doc)

    def get_user_hashed_password(db, username: str) -> Optional[str]:
        # Cho phép đăng nhập bằng username hoặc email
        query = {"$or": [{"username": username}, {"email": username}]}
        doc = _col().find_one(query, {"hashed_password": 1, "id": 1, "username": 1})
        return doc.get("hashed_password") if doc else None

    def get_user_by_login(db, login: str) -> Optional[UserOut]:
        """Tìm user bằng username hoặc email."""
        query = {"$or": [{"username": login}, {"email": login}]}
        doc = _col().find_one(query)
        return _to_user_out(doc)

    def user_exists(db, username: str) -> bool:
        return _col().count_documents({"username": username}, limit=1) > 0

    def email_exists(db, email: str) -> bool:
        if not email:
            return False
        return _col().count_documents({"email": email}, limit=1) > 0

    def create_user(db, data: UserCreate, hashed_password: str) -> UserOut:
        _ensure_indexes()
        uid = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        doc = {
            "id": uid,
            "username": data.username,
            "full_name": data.full_name,
            "email": data.email,
            "hashed_password": hashed_password,
            "role": "admin",
            "is_active": True,
            "provider": "local",
            "created_at": now,
        }
        _col().insert_one(doc)
        return UserOut(
            id=uid,
            username=data.username,
            full_name=data.full_name,
            email=data.email,
            role="admin",
            is_active=True,
            created_at=now,
        )

    def get_or_create_social_user(db, provider: str, email: str,
                                   full_name: Optional[str] = None) -> UserOut:
        """Tạo hoặc lấy user từ social login (Google/Facebook)."""
        _ensure_indexes()
        doc = _col().find_one({"email": email})
        if doc:
            return _to_user_out(doc)

        uid = str(uuid.uuid4())
        # Tạo username từ email
        base = email.split("@")[0].replace(".", "_").lower()
        username = base
        counter = 1
        while _col().count_documents({"username": username}, limit=1) > 0:
            username = f"{base}{counter}"
            counter += 1

        now = datetime.datetime.utcnow()
        doc = {
            "id": uid,
            "username": username,
            "full_name": full_name or username,
            "email": email,
            "hashed_password": "",  # social user không có password
            "role": "admin",
            "is_active": True,
            "provider": provider,
            "created_at": now,
        }
        _col().insert_one(doc)
        return UserOut(
            id=uid, username=username, full_name=full_name,
            email=email, role="admin", is_active=True, created_at=now,
        )

else:
    # ── SQLAlchemy branch ────────────────────────────────────
    import datetime as _dt
    from sqlalchemy.orm import Session
    from app.models import User  # type: ignore

    def get_user_by_username(db: Session, username: str) -> Optional[UserOut]:
        obj = db.query(User).filter(User.username == username).first()
        return UserOut.model_validate(obj) if obj else None

    def get_user_by_email(db: Session, email: str) -> Optional[UserOut]:
        obj = db.query(User).filter(User.email == email).first()
        return UserOut.model_validate(obj) if obj else None

    def get_user_by_id(db: Session, user_id: str) -> Optional[UserOut]:
        obj = db.query(User).filter(User.id == user_id).first()
        return UserOut.model_validate(obj) if obj else None

    def get_user_hashed_password(db: Session, login: str) -> Optional[str]:
        from sqlalchemy import or_
        obj = db.query(User).filter(
            or_(User.username == login, User.email == login)
        ).first()
        return obj.hashed_password if obj else None

    def get_user_by_login(db: Session, login: str) -> Optional[UserOut]:
        from sqlalchemy import or_
        obj = db.query(User).filter(
            or_(User.username == login, User.email == login)
        ).first()
        return UserOut.model_validate(obj) if obj else None

    def user_exists(db: Session, username: str) -> bool:
        return db.query(User.id).filter(User.username == username).first() is not None

    def email_exists(db: Session, email: str) -> bool:
        if not email:
            return False
        return db.query(User.id).filter(User.email == email).first() is not None

    def create_user(db: Session, data: UserCreate, hashed_password: str) -> UserOut:
        uid = str(uuid.uuid4())
        obj = User(
            id=uid,
            username=data.username,
            full_name=data.full_name,
            email=data.email,
            hashed_password=hashed_password,
            role="admin",
            is_active=True,
            created_at=_dt.datetime.utcnow(),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return UserOut.model_validate(obj)

    def get_or_create_social_user(db: Session, provider: str, email: str,
                                   full_name: Optional[str] = None) -> UserOut:
        obj = db.query(User).filter(User.email == email).first()
        if obj:
            return UserOut.model_validate(obj)
        import re
        base = email.split("@")[0].replace(".", "_").lower()
        username = base
        counter = 1
        while db.query(User.id).filter(User.username == username).first():
            username = f"{base}{counter}"
            counter += 1
        uid = str(uuid.uuid4())
        obj = User(
            id=uid, username=username, full_name=full_name or username,
            email=email, hashed_password="", role="admin",
            is_active=True, created_at=_dt.datetime.utcnow(),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return UserOut.model_validate(obj)


# ── Update profile & change password (cả hai DB branch) ──────

if settings.USE_MONGODB:
    def update_profile(db, user_id: str, data: dict) -> Optional[UserOut]:
        _col().update_one({"id": user_id}, {"$set": data})
        return get_user_by_id(db, user_id)

    def update_password(db, user_id: str, new_hashed: str) -> bool:
        result = _col().update_one(
            {"id": user_id}, {"$set": {"hashed_password": new_hashed}}
        )
        return result.modified_count > 0

    def get_hashed_password_by_id(db, user_id: str) -> Optional[str]:
        doc = _col().find_one({"id": user_id}, {"hashed_password": 1})
        return doc.get("hashed_password") if doc else None

else:
    from sqlalchemy.orm import Session as _Session
    from app.models import User as _User  # type: ignore

    def update_profile(db: _Session, user_id: str, data: dict) -> Optional[UserOut]:
        obj = db.query(_User).filter(_User.id == user_id).first()
        if not obj:
            return None
        for k, v in data.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return UserOut.model_validate(obj)

    def update_password(db: _Session, user_id: str, new_hashed: str) -> bool:
        obj = db.query(_User).filter(_User.id == user_id).first()
        if not obj:
            return False
        obj.hashed_password = new_hashed
        db.commit()
        return True

    def get_hashed_password_by_id(db: _Session, user_id: str) -> Optional[str]:
        obj = db.query(_User).filter(_User.id == user_id).first()
        return obj.hashed_password if obj else None
