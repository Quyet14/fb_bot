# -*- coding: utf-8 -*-
"""
Endpoint chay thu cong ngay lap tuc (khong can doi lich), chay nen bang BackgroundTasks.
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db, SessionLocal
from app.scheduler import _lay_cau_hinh_hien_tai
from app.bot.dang_bai import thuc_thi_tien_trinh_dang
from app.bot.repost import thuc_thi_tien_trinh_repost
from app.bot.tuong_tac import thuc_thi_tien_trinh_tuong_tac

router = APIRouter(prefix="/actions", tags=["Chay thu cong"])


def _chay_dang_bai_nen(log_id: int, chu_de: str, nhom_urls: list, dang_kem_anh: bool):
    db = SessionLocal()
    try:
        cfg = _lay_cau_hinh_hien_tai(db)
        thanh_cong, chi_tiet = thuc_thi_tien_trinh_dang(
            chu_de, nhom_urls, dang_kem_anh, cfg.thu_muc_anh, cfg.thoi_gian_cho_giua_cac_nhom
        )
        crud.finish_log(db, log_id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


def _chay_repost_nen(log_id: int, nhom_nguon_urls: list, nhom_dich_urls: list, so_bai: int):
    db = SessionLocal()
    try:
        cfg = _lay_cau_hinh_hien_tai(db)
        thanh_cong, chi_tiet = thuc_thi_tien_trinh_repost(
            nhom_nguon_urls, nhom_dich_urls, so_bai, cfg.thu_muc_anh
        )
        crud.finish_log(db, log_id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


def _chay_tuong_tac_nen(log_id: int, nhom_urls: list):
    db = SessionLocal()
    try:
        cfg = _lay_cau_hinh_hien_tai(db)
        thanh_cong, chi_tiet = thuc_thi_tien_trinh_tuong_tac(
            nhom_urls, cfg.gioi_han_like, cfg.gioi_han_comment
        )
        crud.finish_log(db, log_id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


@router.post("/dang-bai/run-now", response_model=schemas.ActivityLogOut, status_code=202)
def chay_dang_bai_ngay(data: schemas.RunDangBaiNow, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    topic = crud.get_topic(db, data.topic_id)
    if not topic:
        raise HTTPException(404, "Khong tim thay chu de")
    groups = crud.get_groups_by_ids(db, data.group_ids)
    if not groups:
        raise HTTPException(400, "Danh sach nhom rong")

    log = crud.create_log(db, "dang_bai")
    chu_de = topic.ten + (f" - {topic.mo_ta}" if topic.mo_ta else "")
    background_tasks.add_task(_chay_dang_bai_nen, log.id, chu_de, [g.url for g in groups], data.dang_kem_anh)
    return log


@router.post("/repost/run-now", response_model=schemas.ActivityLogOut, status_code=202)
def chay_repost_ngay(data: schemas.RunRepostNow, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    nguon = crud.get_groups_by_ids(db, data.nhom_nguon_ids)
    dich = crud.get_groups_by_ids(db, data.nhom_dich_ids)
    if not nguon or not dich:
        raise HTTPException(400, "Can it nhat 1 nhom nguon va 1 nhom dich")

    log = crud.create_log(db, "repost")
    background_tasks.add_task(_chay_repost_nen, log.id, [g.url for g in nguon], [g.url for g in dich], data.so_bai)
    return log


@router.post("/tuong-tac/run-now", response_model=schemas.ActivityLogOut, status_code=202)
def chay_tuong_tac_ngay(data: schemas.RunTuongTacNow, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    groups = crud.get_groups_by_ids(db, data.group_ids)
    if not groups:
        raise HTTPException(400, "Danh sach nhom rong")

    log = crud.create_log(db, "tuong_tac")
    background_tasks.add_task(_chay_tuong_tac_nen, log.id, [g.url for g in groups])
    return log