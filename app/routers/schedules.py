# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import os, shutil, uuid

from app import schemas, crud, scheduler as sch_module
from app.database import get_db
from app.dependencies import get_user_id

router = APIRouter(prefix="/schedules", tags=["Lich"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "images")
SCHEDULE_UPLOAD_SUBDIR = "schedules"

def _schedule_user_dir(user_id: str) -> str:
    return os.path.join(UPLOAD_DIR, SCHEDULE_UPLOAD_SUBDIR, user_id)

def _schedule_image_url(user_id: str, filename: str) -> str:
    return f"/uploads/images/{SCHEDULE_UPLOAD_SUBDIR}/{user_id}/{filename}"


# ============================================================
# LICH DANG BAI
# ============================================================
@router.get("/dang-bai", response_model=list[schemas.PostScheduleOut])
def ds_lich_dang_bai(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_post_schedules(db, user_id=user_id)


@router.post("/dang-bai", response_model=schemas.PostScheduleOut, status_code=201)
def tao_lich_dang_bai(data: schemas.PostScheduleCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    if data.dang_kem_anh and data.image_mode == "manual" and not data.image_paths:
        raise HTTPException(400, "Da chon anh cu the nhung chua co anh nao")
    obj = crud.create_post_schedule(db, data, user_id=user_id)
    if obj.active:
        sch_module.dang_ky_job("dang_bai", obj.id, obj.thu, obj.gio)
    return obj


@router.put("/dang-bai/{schedule_id}", response_model=schemas.PostScheduleOut)
def sua_lich_dang_bai(schedule_id: int, data: schemas.PostScheduleUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    current = crud.get_post_schedule(db, schedule_id, user_id=user_id)
    if not current:
        raise HTTPException(404, "Khong tim thay lich")
    dang_kem_anh = data.dang_kem_anh if data.dang_kem_anh is not None else current.dang_kem_anh
    image_mode = data.image_mode if data.image_mode is not None else current.image_mode
    image_paths = data.image_paths if data.image_paths is not None else current.image_paths
    if dang_kem_anh and image_mode == "manual" and not image_paths:
        raise HTTPException(400, "Da chon anh cu the nhung chua co anh nao")
    obj = crud.update_post_schedule(db, schedule_id, data, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay lich")
    if obj.active:
        sch_module.dang_ky_job("dang_bai", obj.id, obj.thu, obj.gio)
    else:
        sch_module.go_job("dang_bai", obj.id)
    return obj


@router.delete("/dang-bai/{schedule_id}", status_code=204)
def xoa_lich_dang_bai(schedule_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    if not crud.delete_post_schedule(db, schedule_id, user_id=user_id):
        raise HTTPException(404, "Khong tim thay lich")
    sch_module.go_job("dang_bai", schedule_id)

# ============================================================
# IMAGE UPLOAD CHO LICH NHOM
# ============================================================

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

@router.post("/upload-image", status_code=201)
async def upload_sched_image(file: UploadFile = File(...), user_id: str = Depends(get_user_id)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"Dinh dang khong ho tro: {ext}. Chi chap nhan: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    user_dir = _schedule_user_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(user_dir, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": filepath, "filename": filename, "url": _schedule_image_url(user_id, filename)}


@router.get("/uploaded-images")
def list_sched_images(
    include_used: bool = Query(False),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    user_dir = _schedule_user_dir(user_id)
    if not os.path.exists(user_dir):
        return []
    used_filenames = set()
    if not include_used:
        for schedule in crud.list_post_schedules(db, user_id=user_id):
            if not getattr(schedule, "dang_kem_anh", False):
                continue
            if getattr(schedule, "image_mode", "random") != "manual":
                continue
            for path in getattr(schedule, "image_paths", None) or []:
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
                "url": _schedule_image_url(user_id, fname),
                "size": os.path.getsize(fpath),
            })
    return files


@router.delete("/uploaded-images/{filename}", status_code=204)
def delete_sched_image(filename: str, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Ten file khong hop le")
    filepath = os.path.join(_schedule_user_dir(user_id), filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Khong tim thay file")
    for schedule in crud.list_post_schedules(db, user_id=user_id):
        for path in getattr(schedule, "image_paths", None) or []:
            if os.path.basename(str(path).replace("\\", "/")) == filename:
                raise HTTPException(409, "Anh nay dang duoc dung trong lich, khong the xoa")
    os.remove(filepath)

# ============================================================
# LICH REPOST
# ============================================================
@router.get("/repost", response_model=list[schemas.RepostScheduleOut])
def ds_lich_repost(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_repost_schedules(db, user_id=user_id)


@router.post("/repost", response_model=schemas.RepostScheduleOut, status_code=201)
def tao_lich_repost(data: schemas.RepostScheduleCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.create_repost_schedule(db, data, user_id=user_id)
    if obj.active:
        sch_module.dang_ky_job("repost", obj.id, obj.thu, obj.gio)
    return obj


@router.put("/repost/{schedule_id}", response_model=schemas.RepostScheduleOut)
def sua_lich_repost(schedule_id: int, data: schemas.RepostScheduleUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.update_repost_schedule(db, schedule_id, data, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay lich")
    if obj.active:
        sch_module.dang_ky_job("repost", obj.id, obj.thu, obj.gio)
    else:
        sch_module.go_job("repost", obj.id)
    return obj


@router.delete("/repost/{schedule_id}", status_code=204)
def xoa_lich_repost(schedule_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    if not crud.delete_repost_schedule(db, schedule_id, user_id=user_id):
        raise HTTPException(404, "Khong tim thay lich")
    sch_module.go_job("repost", schedule_id)


# ============================================================
# LICH TUONG TAC
# ============================================================
@router.get("/tuong-tac", response_model=list[schemas.InteractScheduleOut])
def ds_lich_tuong_tac(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_interact_schedules(db, user_id=user_id)


@router.post("/tuong-tac", response_model=schemas.InteractScheduleOut, status_code=201)
def tao_lich_tuong_tac(data: schemas.InteractScheduleCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.create_interact_schedule(db, data, user_id=user_id)
    if obj.active:
        sch_module.dang_ky_job("tuong_tac", obj.id, obj.thu, obj.gio)
    return obj


@router.put("/tuong-tac/{schedule_id}", response_model=schemas.InteractScheduleOut)
def sua_lich_tuong_tac(schedule_id: int, data: schemas.InteractScheduleUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.update_interact_schedule(db, schedule_id, data, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay lich")
    if obj.active:
        sch_module.dang_ky_job("tuong_tac", obj.id, obj.thu, obj.gio)
    else:
        sch_module.go_job("tuong_tac", obj.id)
    return obj


@router.delete("/tuong-tac/{schedule_id}", status_code=204)
def xoa_lich_tuong_tac(schedule_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    if not crud.delete_interact_schedule(db, schedule_id, user_id=user_id):
        raise HTTPException(404, "Khong tim thay lich")
    sch_module.go_job("tuong_tac", schedule_id)
