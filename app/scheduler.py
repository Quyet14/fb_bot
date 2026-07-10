# -*- coding: utf-8 -*-
"""
APScheduler: doc lich tu database luc khoi dong va dang ky job.
Chi cho phep 1 job chay cung luc (dung 1 trinh duyet Chrome / 1 phien dang nhap).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
import os

from app import models, crud
from app.config import settings
from app.database import SessionLocal
from app.bot import browser as bot_browser
from app.bot.dang_bai import thuc_thi_tien_trinh_dang, thuc_thi_tien_trinh_dang_fanpage
from app.bot.repost import thuc_thi_tien_trinh_repost
from app.bot.tuong_tac import thuc_thi_tien_trinh_tuong_tac


def _sync_headless_from_db(cfg):
    """Scheduled jobs luôn chạy headless — không cần giao diện."""
    settings.HEADLESS_MODE = True

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


def _resolve_upload_path(p: str):
    if not p:
        return None
    try:
        if os.path.isabs(p):
            return p
        app_dir = os.path.dirname(os.path.abspath(__file__))
        if p.startswith('/uploads/images/') or p.startswith('uploads/images/'):
            relative = p.lstrip('/').replace('/', os.sep)
            prefix = os.path.join('uploads', 'images') + os.sep
            if relative.startswith(prefix):
                relative = relative[len(prefix):]
            return os.path.join(app_dir, 'uploads', 'images', relative)
        if '/' not in p and '\\' not in p and os.path.splitext(p)[1]:
            import glob
            pattern = os.path.join(app_dir, 'uploads', 'images', '**', p)
            matches = glob.glob(pattern, recursive=True)
            if matches:
                return matches[0]
        return p
    except Exception:
        return p


def _lay_cau_hinh_hien_tai(db, user_id=None):
    cfg = crud.ensure_settings(db, {
        "thu_muc_anh": settings.THU_MUC_ANH_MAC_DINH,
        "gioi_han_like": settings.GIOI_HAN_LIKE_MAC_DINH,
        "gioi_han_comment": settings.GIOI_HAN_COMMENT_MAC_DINH,
        "thoi_gian_cho_giua_cac_nhom": settings.THOI_GIAN_CHO_MAC_DINH,
        "ngon_ngu": "vi",
        "headless_mode": settings.HEADLESS_MODE,
    }, user_id=user_id)
    return cfg


def _get_user_id_from_schedule(db, collection_name: str, schedule_id: int):
    """Retrieve user_id from a schedule document. Returns None if not found."""
    if settings.USE_MONGODB:
        from app.mongo_db import get_collection
        doc = get_collection(collection_name).find_one({"id": schedule_id})
        return doc.get("user_id") if doc else None
    return None  # SQLAlchemy path doesn't need user_id for backward compat


# ============================================================
# CAC HAM JOB (chay trong luong nen)
# ============================================================
def job_dang_bai(schedule_id: int):
    db = SessionLocal()
    try:
        user_id = _get_user_id_from_schedule(db, "post_schedules", schedule_id)
        sch = crud.get_post_schedule(db, schedule_id, user_id=user_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db, user_id=user_id)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "dang_bai", schedule_id, user_id=user_id)
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

        # Xác định ảnh dựa trên image_mode
        image_mode = getattr(sch, "image_mode", "random") or "random"
        image_paths_saved = getattr(sch, "image_paths", None) or []
        anh_override = None
        def _resolve_upload_path(p: str):
            # Accept absolute paths, or convert upload URLs (/uploads/images/...) to filesystem paths.
            # Also support bare filenames by searching uploads/images/** for a match.
            import glob
            if not p:
                return None
            try:
                if os.path.isabs(p):
                    return p
                app_dir = os.path.dirname(os.path.abspath(__file__))
                # upload URL returned by upload endpoints: /uploads/images/... or uploads/images/...
                if p.startswith('/uploads/images/') or p.startswith('uploads/images/'):
                    relative = p.lstrip('/').replace('/', os.sep)
                    prefix = os.path.join('uploads', 'images') + os.sep
                    if relative.startswith(prefix):
                        relative = relative[len(prefix):]
                    return os.path.join(app_dir, 'uploads', 'images', relative)
                # If looks like a bare filename (no slashes) — search uploads folder
                if '/' not in p and '\\' not in p and os.path.splitext(p)[1]:
                    pattern = os.path.join(app_dir, 'uploads', 'images', '**', p)
                    matches = glob.glob(pattern, recursive=True)
                    if matches:
                        return matches[0]
                return p
            except Exception:
                return p

        if sch.dang_kem_anh:
            if image_mode == "manual":
                if not image_paths_saved:
                    crud.finish_log(db, log.id, "error", "Lich dang bai dang chon anh cu the nhung chua co image_paths.")
                    return
                # Normalize/resolve stored paths and filter to existing files
                resolved = [_resolve_upload_path(p) for p in image_paths_saved]
                valid = [p for p in resolved if p and os.path.exists(p)]
                print(f"[job_dang_bai] image_mode={image_mode}, saved_paths={image_paths_saved}, resolved_paths={resolved}, valid_paths={valid}")
                if not valid:
                    crud.finish_log(
                        db,
                        log.id,
                        "error",
                        f"Khong tim thay anh da chon cho lich dang bai #{schedule_id}: {image_paths_saved}",
                    )
                    return
                anh_override = valid
            # random → truyền None, hàm thuc_thi sẽ tự lay_anh_ngau_nhien

        thanh_cong, chi_tiet = thuc_thi_tien_trinh_dang(
            chu_de=chu_de,
            noi_dung_goc=noi_dung_goc,
            giu_nguyen_goc=getattr(sch, "giu_nguyen_goc", True),
            nhom_urls=[g.url for g in sch.groups],
            dang_kem_anh=sch.dang_kem_anh,
            thu_muc_anh=cfg.thu_muc_anh,
            thoi_gian_cho_giua_cac_nhom=cfg.thoi_gian_cho_giua_cac_nhom,
            anh_paths_override=anh_override,
        )

        crud.finish_log(db, log.id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


def job_repost(schedule_id: int):
    db = SessionLocal()
    try:
        user_id = _get_user_id_from_schedule(db, "repost_schedules", schedule_id)
        sch = crud.get_repost_schedule(db, schedule_id, user_id=user_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db, user_id=user_id)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "repost", schedule_id, user_id=user_id)
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
        user_id = _get_user_id_from_schedule(db, "interact_schedules", schedule_id)
        sch = crud.get_interact_schedule(db, schedule_id, user_id=user_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db, user_id=user_id)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "tuong_tac", schedule_id, user_id=user_id)
        thanh_cong, chi_tiet = thuc_thi_tien_trinh_tuong_tac(
            nhom_urls=[g.url for g in sch.groups],
            gioi_han_like=cfg.gioi_han_like,
            gioi_han_comment=cfg.gioi_han_comment,
        )
        crud.finish_log(db, log.id, "success" if thanh_cong else "error", chi_tiet)
    finally:
        db.close()


def job_fanpage(schedule_id: int):
    """Job đăng bài lên Fanpage theo lịch."""
    db = SessionLocal()
    try:
        user_id = _get_user_id_from_schedule(db, "fanpage_schedules", schedule_id)
        sch = crud.get_fanpage_schedule(db, schedule_id, user_id=user_id)
        if not sch or not sch.active:
            return
        cfg = _lay_cau_hinh_hien_tai(db, user_id=user_id)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "fanpage", schedule_id, user_id=user_id)

        if getattr(sch, "content", None):
            noi_dung_goc = sch.content.noi_dung
            chu_de = None
        elif getattr(sch, "topic", None):
            chu_de = sch.topic.ten + (f" - {sch.topic.mo_ta}" if getattr(sch.topic, "mo_ta", None) else "")
            noi_dung_goc = None
        else:
            crud.finish_log(db, log.id, "error", f"fanpage_schedule_id={schedule_id}: thiếu topic/content.")
            return

        thanh_cong, chi_tiet = thuc_thi_tien_trinh_dang_fanpage(
            chu_de=chu_de,
            noi_dung_goc=noi_dung_goc,
            giu_nguyen_goc=getattr(sch, "giu_nguyen_goc", True),
            fanpage_urls=[fp.url for fp in sch.fanpages],
            dang_kem_anh=sch.dang_kem_anh,
            thu_muc_anh=cfg.thu_muc_anh,
            thoi_gian_cho_giua_cac_nhom=cfg.thoi_gian_cho_giua_cac_nhom,
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
    gio_parts = _normalize_time(gio)
    if not gio_parts:
        return
    gio_h, gio_m = gio_parts

    import re
    if re.match(r'^\d{4}-\d{2}-\d{2}$', str(thu)):
        try:
            from datetime import date
            d = date.fromisoformat(thu)
            trigger = CronTrigger(
                year=d.year, month=d.month, day=d.day,
                hour=int(gio_h), minute=int(gio_m)
            )
        except ValueError:
            return
    else:
        ngay = _normalize_day(thu)
        if not ngay:
            return
        trigger = CronTrigger(day_of_week=ngay, hour=int(gio_h), minute=int(gio_m))

    ham = {"dang_bai": job_dang_bai, "repost": job_repost, "tuong_tac": job_tuong_tac, "fanpage": job_fanpage}[loai]
    scheduler.add_job(ham, trigger=trigger, args=[schedule_id], id=_job_key(loai, schedule_id), replace_existing=True)


def dang_ky_job_fanpage_v2(schedule_id: int, thu: str, gio: str):
    """Đăng ký job đăng fanpage v2.
    
    thu có thể là:
    - Tên thứ: "monday", "tuesday"... → chạy lặp lại hàng tuần
    - Ngày cụ thể: "2026-07-10" → chạy 1 lần đúng ngày đó
    """
    go_job("fanpage_v2", schedule_id)
    gio_parts = _normalize_time(gio)
    if not gio_parts:
        return
    gio_h, gio_m = gio_parts

    import re
    if re.match(r'^\d{4}-\d{2}-\d{2}$', str(thu)):
        # Ngày cụ thể — dùng CronTrigger với year/month/day
        try:
            from datetime import date
            d = date.fromisoformat(thu)
            trigger = CronTrigger(
                year=d.year, month=d.month, day=d.day,
                hour=gio_h, minute=gio_m
            )
        except ValueError:
            return
    else:
        # Tên thứ — chạy hàng tuần
        ngay = _normalize_day(thu)
        if not ngay:
            return
        trigger = CronTrigger(day_of_week=ngay, hour=gio_h, minute=gio_m)

    scheduler.add_job(
        job_fanpage_v2, trigger=trigger, args=[schedule_id],
        id=_job_key("fanpage_v2", schedule_id), replace_existing=True
    )


def job_fanpage_v2(schedule_id: int):
    """Job đăng bài lên Fanpage v2 — dùng tài khoản FB liên kết."""
    from app.mongo_db import get_collection
    from app.bot.dang_bai import thuc_thi_tien_trinh_dang_fanpage

    col = get_collection("fanpage_schedules_v2")
    doc = col.find_one({"id": schedule_id})
    if not doc or not doc.get("active"):
        return

    db = SessionLocal()
    try:
        user_id = doc.get("user_id")
        cfg = _lay_cau_hinh_hien_tai(db, user_id=user_id)
        _sync_headless_from_db(cfg)
        log = crud.create_log(db, "fanpage_v2", schedule_id, user_id=user_id)

        # Lấy URL fanpage từ tài khoản liên kết
        acc_col = get_collection("fb_accounts")
        acc = acc_col.find_one({"id": int(doc.get("fb_account_id", 0)), "user_id": user_id})
        if not acc:
            crud.finish_log(db, log.id, "error", "Không tìm thấy tài khoản Facebook")
            return

        page_ids = doc.get("page_ids") or []
        fp_map = {fp["page_id"]: fp for fp in (acc.get("fanpages") or [])}
        fanpage_urls = []
        for pid in page_ids:
            fp = fp_map.get(pid)
            if fp:
                raw_url = fp.get("url") or ""
                # Chuẩn hóa URL: bỏ đường dẫn admin, chỉ lấy slug/id
                # VD: facebook.com/bamoscafe24h.binhthanh (không phải trang admin)
                clean = raw_url.split("?")[0].rstrip("/")
                # Nếu URL chứa path admin (/pages_manager/, /pg/, ...) thì build lại từ page_id
                admin_paths = ["/pages_manager", "/pg/", "?ref=bookmarks", "business.facebook"]
                if any(p in clean for p in admin_paths) or not clean.startswith("http"):
                    clean = f"https://www.facebook.com/{pid}"
                fanpage_urls.append(clean)
            else:
                fanpage_urls.append(f"https://www.facebook.com/{pid}")

        if not fanpage_urls:
            crud.finish_log(db, log.id, "error", "Không có fanpage URL nào để đăng")
            return

        # Xác định nội dung
        chu_de = None
        noi_dung_goc = None
        if doc.get("content_text"):
            noi_dung_goc = doc["content_text"]
        elif doc.get("topic_id"):
            topics_col = get_collection("topics")
            t = topics_col.find_one({"id": int(doc["topic_id"]), "user_id": user_id})
            if t:
                chu_de = t["ten"] + (f" - {t['mo_ta']}" if t.get("mo_ta") else "")
            else:
                crud.finish_log(db, log.id, "error", "Không tìm thấy chủ đề")
                return
        else:
            crud.finish_log(db, log.id, "error", "Thiếu nội dung hoặc chủ đề")
            return

        # ── Ưu tiên Graph API nếu có page access token ──────────────
        from app.bot.graph_api import dang_bai_graph_api

        # Resolve nội dung cuối
        if noi_dung_goc:
            noi_dung_final = noi_dung_goc
        else:
            from app.bot.gemini import goi_gemini_viet_bai
            noi_dung_final = goi_gemini_viet_bai(chu_de) if chu_de else None
            if not noi_dung_final:
                crud.finish_log(db, log.id, "error", "Gemini không viết được bài")
                return

        # Kiểm tra fanpages có token chưa
        fp_map = {fp["page_id"]: fp for fp in (acc.get("fanpages") or [])}
        ket_qua_list = []
        co_token = any(fp_map.get(pid, {}).get("page_access_token") for pid in page_ids)
        anh_paths_final = None

        if doc.get("dang_kem_anh", False):
            image_mode = doc.get("image_mode", "random")
            image_paths = doc.get("image_paths") or []
            if image_mode == "manual":
                if not image_paths:
                    crud.finish_log(db, log.id, "error", "Lich fanpage dang chon anh cu the nhung chua co image_paths.")
                    return

                resolved = [_resolve_upload_path(p) for p in image_paths]
                anh_paths_final = [p for p in resolved if p and os.path.exists(p)]
                print(f"[job_fanpage_v2] image_mode={image_mode}, saved_paths={image_paths}, resolved_paths={resolved}, valid_paths={anh_paths_final}")
                if not anh_paths_final:
                    crud.finish_log(
                        db,
                        log.id,
                        "error",
                        f"Khong tim thay anh da chon cho lich fanpage #{schedule_id}: {image_paths}",
                    )
                    return
            else:
                from app.bot.browser import lay_anh_ngau_nhien
                anh_ngau_nhien = lay_anh_ngau_nhien(cfg.thu_muc_anh)
                anh_paths_final = [anh_ngau_nhien] if anh_ngau_nhien else None

        if co_token:
            # Đăng qua Graph API — nhanh, không Chrome, không hiện giao diện
            print(f"[job_fanpage_v2] Dung Graph API cho {len(page_ids)} fanpage")

            # Xác định danh sách ảnh cần đính kèm
            anh_paths_final = None
            if doc.get("dang_kem_anh", False):
                image_mode = doc.get("image_mode", "random")
                image_paths = doc.get("image_paths") or []
                if image_mode == "manual" and image_paths:
                    resolved = [_resolve_upload_path(p) for p in image_paths]
                    anh_paths_final = [p for p in resolved if p and os.path.exists(p)]
                    print(f"[job_fanpage_v2] image_mode={image_mode}, saved_paths={image_paths}, resolved_paths={resolved}, valid_paths={anh_paths_final}")
                else:
                    # Random: lấy ảnh ngẫu nhiên từ thư mục
                    from app.bot.browser import lay_anh_ngau_nhien
                    anh_ngau_nhien = lay_anh_ngau_nhien(cfg.thu_muc_anh)
                    anh_paths_final = [anh_ngau_nhien] if anh_ngau_nhien else None

            for pid in page_ids:
                fp = fp_map.get(pid, {})
                token = fp.get("page_access_token")
                if token:
                    ok, detail = dang_bai_graph_api(pid, noi_dung_final, token, anh_paths=anh_paths_final)
                    ket_qua_list.append(f"{fp.get('ten', pid)}: {detail}")
                else:
                    ket_qua_list.append(f"{fp.get('ten', pid)}: no_token_skip")
            chi_tiet = "\n".join(ket_qua_list)
            co_thanh_cong = any("SUCCESS" in r for r in ket_qua_list)
        else:
            # Fallback: Selenium (khi chưa có token)
            print(f"[job_fanpage_v2] Khong co token, dung Selenium")
            thanh_cong, chi_tiet = thuc_thi_tien_trinh_dang_fanpage(
                chu_de=chu_de,
                noi_dung_goc=noi_dung_goc,
                giu_nguyen_goc=doc.get("giu_nguyen_goc", True),
                fanpage_urls=fanpage_urls,
                dang_kem_anh=doc.get("dang_kem_anh", False),
                thu_muc_anh=cfg.thu_muc_anh,
                thoi_gian_cho_giua_cac_nhom=cfg.thoi_gian_cho_giua_cac_nhom,
                anh_paths_override=anh_paths_final,
            )
            co_thanh_cong = thanh_cong and ("SUCCESS" in (chi_tiet or "") or "PENDING" in (chi_tiet or ""))
        trang_thai_log = "success" if co_thanh_cong else "error"
        crud.finish_log(db, log.id, trang_thai_log, chi_tiet)

        # Nếu lịch chỉ chạy 1 lần (one_time=True) → tắt sau khi đăng xong
        if co_thanh_cong and doc.get("one_time", False):
            col.update_one({"id": schedule_id}, {"$set": {"active": False}})
            go_job("fanpage_v2", schedule_id)
            print(f"[job_fanpage_v2] one_time=True → đã tắt lịch #{schedule_id}")

    finally:
        db.close()


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
        for sch in crud.list_fanpage_schedules(None):
            if getattr(sch, "active", True):
                try:
                    dang_ky_job("fanpage", sch.id, sch.thu, sch.gio)
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
        for sch in db.query(models.FanpageSchedule).filter(models.FanpageSchedule.active.is_(True)).all():
            try:
                dang_ky_job("fanpage", sch.id, sch.thu, sch.gio)
            except Exception:
                pass
    finally:
        db.close()
