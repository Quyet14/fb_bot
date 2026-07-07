# -*- coding: utf-8 -*-
"""
Router quản lý lịch đăng bài cho Fanpage.
Fanpage được chọn từ tài khoản FB đã liên kết (không dùng URL thủ công).
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.mongo_db import get_collection
from app import scheduler as sch_module
from app.dependencies import get_user_id

router = APIRouter(prefix="/fanpage-schedules", tags=["Lich Fanpage"])


def _col():
    return get_collection("fanpage_schedules_v2")

def _counters():
    return get_collection("counters")

def _next_id(name: str) -> int:
    doc = _counters().find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return int(doc.get("seq", 0))

def _accounts_col():
    return get_collection("fb_accounts")


# ── Schemas ──────────────────────────────────────────────────
class FanpageScheduleV2Create(BaseModel):
    thu: str
    gio: str
    fb_account_id: int
    page_ids: List[str]
    topic_id: Optional[int] = None
    content_text: Optional[str] = None
    giu_nguyen_goc: bool = True
    dang_kem_anh: bool = False
    active: bool = True
    one_time: bool = False   # True = chỉ chạy 1 lần rồi tự tắt

class FanpageScheduleV2Update(BaseModel):
    thu: Optional[str] = None
    gio: Optional[str] = None
    page_ids: Optional[List[str]] = None
    topic_id: Optional[int] = None
    content_text: Optional[str] = None
    giu_nguyen_goc: Optional[bool] = None
    dang_kem_anh: Optional[bool] = None
    active: Optional[bool] = None
    one_time: Optional[bool] = None

class FanpageScheduleV2Out(BaseModel):
    id: int
    thu: str
    gio: str
    fb_account_id: int
    fb_account_name: str
    page_ids: List[str]
    page_names: List[str]           # tên fanpage để hiển thị
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    content_text: Optional[str] = None
    giu_nguyen_goc: bool
    dang_kem_anh: bool
    active: bool
    one_time: bool = False
    tao_luc: datetime


def _build_out(doc, user_id: str) -> FanpageScheduleV2Out:
    if not doc:
        return None
    acc = _accounts_col().find_one({"id": int(doc.get("fb_account_id", 0)), "user_id": user_id})
    acc_name = acc["ten_hien_thi"] if acc else f"Account #{doc.get('fb_account_id')}"
    page_ids = doc.get("page_ids") or []
    page_names = []
    if acc:
        fp_map = {fp["page_id"]: fp["ten"] for fp in (acc.get("fanpages") or [])}
        page_names = [fp_map.get(pid, pid) for pid in page_ids]

    # Lấy topic name nếu có
    topic_name = None
    if doc.get("topic_id"):
        from app.mongo_db import get_collection as gc
        t = gc("topics").find_one({"id": int(doc["topic_id"]), "user_id": user_id})
        if t:
            topic_name = t.get("ten")

    return FanpageScheduleV2Out(
        id=int(doc["id"]),
        thu=doc.get("thu", ""),
        gio=doc.get("gio", ""),
        fb_account_id=int(doc.get("fb_account_id", 0)),
        fb_account_name=acc_name,
        page_ids=page_ids,
        page_names=page_names,
        topic_id=doc.get("topic_id"),
        topic_name=topic_name,
        content_text=doc.get("content_text"),
        giu_nguyen_goc=doc.get("giu_nguyen_goc", True),
        dang_kem_anh=doc.get("dang_kem_anh", False),
        active=doc.get("active", True),
        one_time=doc.get("one_time", False),
        tao_luc=doc.get("tao_luc", datetime.now(timezone.utc)),
    )


# ── Endpoints ─────────────────────────────────────────────────
@router.get("/", response_model=List[FanpageScheduleV2Out])
def ds_lich(user_id: str = Depends(get_user_id)):
    docs = list(_col().find({"user_id": user_id}).sort("id", 1))
    return [_build_out(d, user_id) for d in docs]


@router.post("/", response_model=FanpageScheduleV2Out, status_code=201)
def tao_lich(data: FanpageScheduleV2Create, user_id: str = Depends(get_user_id)):
    if not data.topic_id and not data.content_text:
        raise HTTPException(400, "Phải chọn chủ đề hoặc nhập nội dung")
    if not data.page_ids:
        raise HTTPException(400, "Phải chọn ít nhất một Fanpage")

    acc = _accounts_col().find_one({"id": data.fb_account_id, "user_id": user_id})
    if not acc:
        raise HTTPException(404, "Không tìm thấy tài khoản Facebook")

    payload = {
        **data.model_dump(),
        "id": _next_id("fanpage_schedules_v2"),
        "user_id": user_id,
        "tao_luc": datetime.now(timezone.utc),
    }
    _col().insert_one(payload)
    obj = _build_out(payload, user_id)
    if obj.active:
        sch_module.dang_ky_job_fanpage_v2(obj.id, obj.thu, obj.gio)
    return obj


@router.put("/{schedule_id}", response_model=FanpageScheduleV2Out)
def sua_lich(schedule_id: int, data: FanpageScheduleV2Update, user_id: str = Depends(get_user_id)):
    doc = _col().find_one({"id": schedule_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy lịch fanpage")
    # Dùng exclude_unset=True để chỉ cập nhật field được gửi lên
    # KHÔNG lọc None — cho phép reset topic_id/content_text về null
    payload = data.model_dump(exclude_unset=True)
    if payload:
        _col().update_one({"id": schedule_id, "user_id": user_id}, {"$set": payload})
    doc = _col().find_one({"id": schedule_id, "user_id": user_id})
    obj = _build_out(doc, user_id)
    if obj.active:
        sch_module.dang_ky_job_fanpage_v2(obj.id, obj.thu, obj.gio)
    else:
        sch_module.go_job("fanpage_v2", obj.id)
    return obj


@router.delete("/{schedule_id}", status_code=204)
def xoa_lich(schedule_id: int, user_id: str = Depends(get_user_id)):
    result = _col().delete_one({"id": schedule_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Không tìm thấy lịch fanpage")
    sch_module.go_job("fanpage_v2", schedule_id)
