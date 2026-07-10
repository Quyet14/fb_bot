# -*- coding: utf-8 -*-
"""
Router quản lý lịch đăng bài cho Fanpage.
Fanpage được chọn từ tài khoản FB đã liên kết (không dùng URL thủ công).
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
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
    image_mode: str = "random"          # "random" | "manual"
    image_paths: List[str] = Field(default_factory=list)         # list đường dẫn ảnh cụ thể (khi image_mode="manual")
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
    image_mode: Optional[str] = None
    image_paths: Optional[List[str]] = None
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
    image_mode: str = "random"
    image_paths: List[str] = Field(default_factory=list)
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
        image_mode=doc.get("image_mode", "random"),
        image_paths=doc.get("image_paths") or [],
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

    if data.dang_kem_anh and data.image_mode == "manual" and not data.image_paths:
        raise HTTPException(400, "Phai chon it nhat 1 anh hoac chuyen sang Random")

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
    if (
        payload.get("dang_kem_anh", doc.get("dang_kem_anh", False))
        and payload.get("image_mode", doc.get("image_mode", "random")) == "manual"
        and not payload.get("image_paths", doc.get("image_paths") or [])
    ):
        raise HTTPException(400, "Phai chon it nhat 1 anh hoac chuyen sang Random")
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


# ── Upload ảnh ─────────────────────────────────────────────────
import os, shutil, uuid
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "images")
FANPAGE_UPLOAD_SUBDIR = "fanpage"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def _fanpage_user_dir(user_id: str) -> str:
    return os.path.join(UPLOAD_DIR, FANPAGE_UPLOAD_SUBDIR, user_id)

def _fanpage_image_url(user_id: str, filename: str) -> str:
    return f"/uploads/images/{FANPAGE_UPLOAD_SUBDIR}/{user_id}/{filename}"

@router.post("/upload-image", status_code=201)
async def upload_anh(file: UploadFile = File(...), user_id: str = Depends(get_user_id)):
    """Upload 1 ảnh lên server. Trả về đường dẫn tuyệt đối để lưu vào image_paths."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"Định dạng không hỗ trợ: {ext}. Chỉ chấp nhận: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    user_dir = _fanpage_user_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(user_dir, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": filepath, "filename": filename, "url": _fanpage_image_url(user_id, filename)}


@router.get("/uploaded-images")
def danh_sach_anh(
    include_used: bool = Query(False),
    user_id: str = Depends(get_user_id),
):
    """Lấy danh sách ảnh đã upload của user."""
    user_dir = _fanpage_user_dir(user_id)
    if not os.path.exists(user_dir):
        return []
    used_filenames = set()
    if not include_used:
        docs = _col().find({
            "user_id": user_id,
            "dang_kem_anh": True,
            "image_mode": "manual",
        }, {"image_paths": 1})
        for doc in docs:
            for path in doc.get("image_paths") or []:
                name = os.path.basename(str(path).replace("\\", "/"))
                if name:
                    used_filenames.add(name)
    files = []
    for fname in sorted(os.listdir(user_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            if fname in used_filenames:
                continue
            fpath = os.path.join(user_dir, fname)
            files.append({
                "filename": fname,
                "path": fpath,
                "url": _fanpage_image_url(user_id, fname),
                "size": os.path.getsize(fpath),
            })
    return files


@router.delete("/uploaded-images/{filename}", status_code=204)
def xoa_anh(filename: str, user_id: str = Depends(get_user_id)):
    """Xóa ảnh đã upload."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Tên file không hợp lệ")
    filepath = os.path.join(_fanpage_user_dir(user_id), filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Không tìm thấy file")
    normalized = os.path.abspath(filepath)
    variants = {
        normalized,
        normalized.replace("\\", "/"),
        _fanpage_image_url(user_id, filename),
        _fanpage_image_url(user_id, filename).lstrip("/"),
    }
    in_use = _col().find_one({
        "user_id": user_id,
        "image_paths": {"$in": list(variants)},
    })
    if in_use:
        raise HTTPException(409, f"Ảnh đang được dùng trong lịch fanpage #{in_use.get('id')}, không thể xóa file.")
    os.remove(filepath)
