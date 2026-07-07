# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud, scheduler as sch_module
from app.database import get_db
from app.dependencies import get_user_id

router = APIRouter(prefix="/schedules", tags=["Lich"])


# ============================================================
# LICH DANG BAI
# ============================================================
@router.get("/dang-bai", response_model=list[schemas.PostScheduleOut])
def ds_lich_dang_bai(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_post_schedules(db, user_id=user_id)


@router.post("/dang-bai", response_model=schemas.PostScheduleOut, status_code=201)
def tao_lich_dang_bai(data: schemas.PostScheduleCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.create_post_schedule(db, data, user_id=user_id)
    if obj.active:
        sch_module.dang_ky_job("dang_bai", obj.id, obj.thu, obj.gio)
    return obj


@router.put("/dang-bai/{schedule_id}", response_model=schemas.PostScheduleOut)
def sua_lich_dang_bai(schedule_id: int, data: schemas.PostScheduleUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
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