# -*- coding: utf-8 -*-
import re
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db
from app.dependencies import get_user_id
from app.config import settings

router = APIRouter(prefix="/logs", tags=["Log hoat dong"])


def _post_id_from_detail(detail: Optional[str]) -> Optional[str]:
    m = re.search(r"\bpost_id=([0-9]+(?:_[0-9]+)?)\b", detail or "")
    return m.group(1) if m else None


def _page_id_from_post_id(post_id: str) -> Optional[str]:
    if "_" in post_id:
        return post_id.split("_", 1)[0]
    return None


def _page_token_for_post(user_id: str, post_id: str) -> Optional[str]:
    if not settings.USE_MONGODB:
        return None
    page_id = _page_id_from_post_id(post_id)
    if not page_id:
        return None
    from app.mongo_db import get_collection
    doc = get_collection("fb_accounts").find_one(
        {"user_id": user_id, "fanpages.page_id": page_id},
        {"fanpages.$": 1},
    )
    fanpages = (doc or {}).get("fanpages") or []
    return fanpages[0].get("page_access_token") if fanpages else None


def _mark_post_deleted_if_needed(log: schemas.ActivityLogOut, user_id: str) -> schemas.ActivityLogOut:
    if log.trang_thai != "success" or not log.chi_tiet:
        return log
    if "POST_DELETED" in log.chi_tiet:
        return log
    post_id = _post_id_from_detail(log.chi_tiet)
    if not post_id:
        return log
    token = _page_token_for_post(user_id, post_id)
    if not token:
        return log
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{post_id}",
            params={"fields": "id,permalink_url", "access_token": token},
            timeout=5,
        )
        data = resp.json()
        detail = log.chi_tiet
        if resp.ok and data.get("permalink_url"):
            if "post_url=" not in detail:
                detail = f"{detail} post_url={data['permalink_url']}"
        elif not resp.ok:
            err = data.get("error", {})
            err_text = str(err).lower()
            if err.get("code") == 100 or "does not exist" in err_text or "cannot be loaded" in err_text:
                detail = re.sub(r"\s+post_url=https?:\/\/[^\s|]+", "", detail)
                detail = f"{detail} POST_DELETED"
        if detail != log.chi_tiet:
            if settings.USE_MONGODB:
                from app.mongo_db import get_collection
                get_collection("activity_logs").update_one(
                    {"id": int(log.id), "user_id": user_id},
                    {"$set": {"chi_tiet": detail, "post_checked_at": datetime.now(timezone.utc)}},
                )
            return log.model_copy(update={"chi_tiet": detail})
    except Exception:
        return log
    return log


@router.get("/", response_model=list[schemas.ActivityLogOut])
def danh_sach_log(limit: int = Query(100, le=500), db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    logs = crud.list_logs(db, limit, user_id=user_id)
    return [_mark_post_deleted_if_needed(log, user_id) for log in logs]


@router.get("/{log_id}", response_model=schemas.ActivityLogOut)
def chi_tiet_log(log_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.get_log(db, log_id, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay log")
    return _mark_post_deleted_if_needed(obj, user_id)
