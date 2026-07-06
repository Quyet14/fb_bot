# -*- coding: utf-8 -*-
"""
APScheduler: doc lich tu database luc khoi dong va dang ky job.
Chi cho phep 1 job chay cung luc (dung 1 trinh duyet Chrome / 1 phien dang nhap).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from app import models, crud
from app.config import settings
from app.database import SessionLocal
from app.bot import browser as bot_browser
from app.bot.dang_bai import thuc_thi_tien_trinh_dang
from app.bot.repost import thuc_thi_tien_trinh_repost
from app.bot.tuong_tac import thuc_thi_tien_trinh_tuong_tac


def _sync_headless_from_db(cfg):
    """Cập nhật HEADLESS_MODE từ DB settings trước khi chạy job."""
    headless = getattr(cfg, 'headless_mode', settings.HEADLESS_MODE)
    settings.HEADLESS_MODE = headless

THU_SANG_SO = {
    "monday": "mon", "tuesday": "tue", "wednesday": "wed",
    "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun",
    "mon": "mon", "tue": "tue", "wed": "wed", "thu": "thu", "fri": "fri", "sat": "sat", "sun": "sun",
    "thứ 2": "mon", "thứ hai": "mon", "thứ2": "mon", "thu2": "mon", "thu hai": "mon",
    "thứ 3": "tue", "thứ ba": "tue", "thứ3": "tue", "thu3": "tue", "thu ba": "tue",
    "thứ 4": "wed", "thứ tư": "wed", "thứ4": "wed", "thu4": "wed", "thu tu": "wed",
    "thứ 5": "thu", "thứ năm": "thu", "thứ5": "thu", "thu5": "thu", "thu nam": "thu",
    "thứ 6": "fri", "thứ sáu": "fri", "thứ6": "fri", "thu6": "fri", "thu sau": "fri",
    "thứ 7": "sat", "thứ bảy": "sat", "thứ7": "sat", "thu7": "sat", "thu bay": "sat",
    "chủ nhật": "sun", "chủnhật": "sun", "cn": "sun", "sun": "sun",
    "2": "mon", "3": "tue", "4": "wed", "5": "thu", "6": "fri", "7": "sat", "8": "sun",
}

scheduler = BackgroundScheduler(
    executors={"default": ThreadPoolExecutor(max_workers=1)},
    job_defaults={"max_instances": 1, "coalesce": True, "misfire_grace_time": 3600},
)


def _lay_cau_hinh_hien_tai(db):
    cfg = crud.ensure_settings(db, {
        "thu_muc_anh": settings.THU_MUC_ANH_MAC_DINH,
        "gioi_han_like": settings.GIOI_HAN_LIKE_MAC_DINH,
        "gioi_han_comment": settings.GIOI_HAN_COMMENT_MAC_DINH,
        "thoi_gian_cho_giua_cac_nhom": settings.THOI_GIAN_CHO_MAC_DINH,
        "ngon_ngu": "vi",
        "headless_mode": settings.HEADLESS_MODE,
    })
    return cfg


# ============================================================
# CAC HAM JOB (chay trong luong nen)
# ============================================================
def job_dang_bai(schedule_id: int):
    db = SessionLocal()
    try:
        sch = crud.get_post_schedule(db, schedule_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "dang_bai", schedule_id)
        # Chế độ đăng bài:
        # - Nếu có content (đã resolve): dùng nội dung người dùng (giữ nguyên hoặc nhờ Gemini viết lại)
        # - Ngược lại: fallback theo topic
        if getattr(sch, "content", None):
            noi_dung_goc = sch.content.noi_dung
            chu_de = None
        elif getattr(sch, "topic", None):
            chu_de = sch.topic.ten + (f" - {sch.topic.mo_ta}" if getattr(sch.topic, "mo_ta", None) else "")
            noi_dung_goc = None
        else:
            # Không có cả topic lẫn content — lấy topic_id/content_id từ DB doc gốc nếu có
            chi_tiet = (
                f"schedule_id={schedule_id} invalid: topic missing "
                f"(topic_id={getattr(sch, 'topic_id', None)}, content_id={getattr(sch, 'content_id', None)})."
            )
            crud.finish_log(db, log.id, "error", chi_tiet)
            return

        thanh_cong, chi_tiet = thuc_thi_tien_trinh_dang(
            chu_de=chu_de,
            noi_dung_goc=noi_dung_goc,
            giu_nguyen_goc=getattr(sch, "giu_nguyen_goc", True),
            nhom_urls=[g.url for g in sch.groups],
            dang_kem_anh=sch.dang_kem_anh,
            thu_muc_anh=cfg.thu_muc_anh,
            thoi_gian_cho_giua_cac_nhom=cfg.thoi_gian_cho_giua_cac_nhom,
        )

        crud.finish_log(db, log.id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


def job_repost(schedule_id: int):
    db = SessionLocal()
    try:
        sch = crud.get_repost_schedule(db, schedule_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "repost", schedule_id)
        thanh_cong, chi_tiet = thuc_thi_tien_trinh_repost(
            nhom_nguon_urls=[g.url for g in sch.nhom_nguon],
            nhom_dich_urls=[g.url for g in sch.nhom_dich],
            so_bai=sch.so_bai,
            thu_muc_anh=cfg.thu_muc_anh,
        )
        crud.finish_log(db, log.id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


def job_tuong_tac(schedule_id: int):
    db = SessionLocal()
    try:
        sch = crud.get_interact_schedule(db, schedule_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "tuong_tac", schedule_id)
        thanh_cong, chi_tiet = thuc_thi_tien_trinh_tuong_tac(
            nhom_urls=[g.url for g in sch.groups],
            gioi_han_like=cfg.gioi_han_like,
            gioi_han_comment=cfg.gioi_han_comment,
        )
        crud.finish_log(db, log.id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


# ============================================================
# DANG KY / GO JOB THEO ID (dung khi tao/sua/xoa lich qua API)
# ============================================================
def _job_key(loai: str, schedule_id: int) -> str:
    return f"{loai}_{schedule_id}"


def _normalize_day(thu: str):
    if not thu:
        return None
    value = str(thu).strip().lower().replace(" ", "")
    return THU_SANG_SO.get(value)


def _normalize_time(gio: str):
    if not gio:
        return None
    value = str(gio).strip()
    parts = value.split(":")
    if len(parts) != 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def dang_ky_job(loai: str, schedule_id: int, thu: str, gio: str):
    go_job(loai, schedule_id)
    ngay = _normalize_day(thu)
    gio_parts = _normalize_time(gio)
    if not ngay or not gio_parts:
        return
    gio_h, gio_m = gio_parts
    trigger = CronTrigger(day_of_week=ngay, hour=int(gio_h), minute=int(gio_m))
    ham = {"dang_bai": job_dang_bai, "repost": job_repost, "tuong_tac": job_tuong_tac}[loai]
    scheduler.add_job(ham, trigger=trigger, args=[schedule_id], id=_job_key(loai, schedule_id), replace_existing=True)


def go_job(loai: str, schedule_id: int):
    try:
        scheduler.remove_job(_job_key(loai, schedule_id))
    except Exception:
        pass


def nap_lai_toan_bo_lich():
    """Goi luc app khoi dong: doc het lich active trong DB va dang ky vao scheduler."""
    if settings.USE_MONGODB:
        for sch in crud.list_post_schedules(None):
            if getattr(sch, "active", True):
                try:
                    dang_ky_job("dang_bai", sch.id, sch.thu, sch.gio)
                except Exception:
                    pass
        for sch in crud.list_repost_schedules(None):
            if getattr(sch, "active", True):
                try:
                    dang_ky_job("repost", sch.id, sch.thu, sch.gio)
                except Exception:
                    pass
        for sch in crud.list_interact_schedules(None):
            if getattr(sch, "active", True):
                try:
                    dang_ky_job("tuong_tac", sch.id, sch.thu, sch.gio)
                except Exception:
                    pass
        return

    db = SessionLocal()
    try:
        for sch in db.query(models.PostSchedule).filter(models.PostSchedule.active.is_(True)).all():
            try:
                dang_ky_job("dang_bai", sch.id, sch.thu, sch.gio)
            except Exception:
                pass
        for sch in db.query(models.RepostSchedule).filter(models.RepostSchedule.active.is_(True)).all():
            try:
                dang_ky_job("repost", sch.id, sch.thu, sch.gio)
            except Exception:
                pass
        for sch in db.query(models.InteractSchedule).filter(models.InteractSchedule.active.is_(True)).all():
            try:
                dang_ky_job("tuong_tac", sch.id, sch.thu, sch.gio)
            except Exception:
                pass
    finally:
        db.close()