# -*- coding: utf-8 -*-
"""CRUD layer that uses MongoDB when configured."""
from typing import List, Optional

from app import schemas
from app.config import settings
from app.mongo_crud_adapter import store


if settings.USE_MONGODB:
    # Mongo adapter: giữ đúng contract của router/crud.
    def list_groups(db):
        return store.list_groups()

    def get_group(db, group_id: int):
        return store.get_group(group_id)

    def get_groups_by_ids(db, ids: List[int]):
        return store.get_groups_by_ids(ids)

    def create_group(db, data: schemas.GroupCreate):
        return store.create_group(data)

    def update_group(db, group_id: int, data: schemas.GroupUpdate):
        return store.update_group(group_id, data)

    def delete_group(db, group_id: int):
        return store.delete_group(group_id)

    def list_topics(db):
        return store.list_topics()

    # user_contents (Mongo)
    # Implement tối thiểu để UI tạo lịch theo nội dung người dùng.
    def list_user_contents(db):
        return store.list_user_contents()

    def get_user_content(db, content_id: int):
        return store.get_user_content(content_id)

    def create_user_content(db, data: schemas.UserContentCreate):
        return store.create_user_content(data)

    def delete_user_content(db, content_id: int):
        return store.delete_user_content(content_id)



    def get_topic(db, topic_id: int):
        return store.get_topic(topic_id)

    def create_topic(db, data: schemas.TopicCreate):
        return store.create_topic(data)

    def update_topic(db, topic_id: int, data: schemas.TopicUpdate):
        return store.update_topic(topic_id, data)

    def delete_topic(db, topic_id: int):
        return store.delete_topic(topic_id)

    def list_post_schedules(db):
        return store.list_post_schedules()

    def get_post_schedule(db, schedule_id: int):
        return store.get_post_schedule(schedule_id)

    def create_post_schedule(db, data: schemas.PostScheduleCreate):
        obj = store.create_post_schedule(data)
        # debug-guard: nếu content_id được tạo mà không set được quan hệ, vẫn trả về obj
        return obj

    def update_post_schedule(db, schedule_id: int, data: schemas.PostScheduleUpdate):
        return store.update_post_schedule(schedule_id, data)

    def delete_post_schedule(db, schedule_id: int):
        return store.delete_post_schedule(schedule_id)

    def list_repost_schedules(db):
        return store.list_repost_schedules()

    def get_repost_schedule(db, schedule_id: int):
        return store.get_repost_schedule(schedule_id)

    def create_repost_schedule(db, data: schemas.RepostScheduleCreate):
        return store.create_repost_schedule(data)

    def update_repost_schedule(db, schedule_id: int, data: schemas.RepostScheduleUpdate):
        return store.update_repost_schedule(schedule_id, data)

    def delete_repost_schedule(db, schedule_id: int):
        return store.delete_repost_schedule(schedule_id)

    def list_interact_schedules(db):
        return store.list_interact_schedules()

    def get_interact_schedule(db, schedule_id: int):
        return store.get_interact_schedule(schedule_id)

    def create_interact_schedule(db, data: schemas.InteractScheduleCreate):
        return store.create_interact_schedule(data)

    def update_interact_schedule(db, schedule_id: int, data: schemas.InteractScheduleUpdate):
        return store.update_interact_schedule(schedule_id, data)

    def delete_interact_schedule(db, schedule_id: int):
        return store.delete_interact_schedule(schedule_id)

    def create_log(db, loai: str, schedule_id: Optional[int] = None):
        return store.create_log(loai, schedule_id)

    def finish_log(db, log_id: int, trang_thai: str, chi_tiet: Optional[str] = None):
        return store.finish_log(log_id, trang_thai, chi_tiet)

    def list_logs(db, limit: int = 100):
        return store.list_logs(limit)

    def get_log(db, log_id: int):
        return store.get_log(log_id)

    def get_settings(db) -> Optional[schemas.AppSettingsOut]:
        return store.get_settings()

    def ensure_settings(db, mac_dinh: dict):
        return store.ensure_settings(mac_dinh)

    def update_settings(db, data):
        return store.update_settings(data)
else:

    import datetime
    from sqlalchemy.orm import Session
    from app import models

    def list_groups(db: Session):
        return db.query(models.Group).order_by(models.Group.id).all()

    def get_group(db: Session, group_id: int):
        return db.query(models.Group).filter(models.Group.id == group_id).first()

    def get_groups_by_ids(db: Session, ids: List[int]):
        if not ids:
            return []
        return db.query(models.Group).filter(models.Group.id.in_(ids)).all()

    def create_group(db: Session, data: schemas.GroupCreate):
        obj = models.Group(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_group(db: Session, group_id: int, data: schemas.GroupUpdate):
        obj = get_group(db, group_id)
        if not obj:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_group(db: Session, group_id: int):
        obj = get_group(db, group_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def list_topics(db: Session):
        return db.query(models.Topic).order_by(models.Topic.id).all()

    def get_topic(db: Session, topic_id: int):
        return db.query(models.Topic).filter(models.Topic.id == topic_id).first()

    def create_topic(db: Session, data: schemas.TopicCreate):
        obj = models.Topic(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_topic(db: Session, topic_id: int, data: schemas.TopicUpdate):
        obj = get_topic(db, topic_id)
        if not obj:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_topic(db: Session, topic_id: int):
        obj = get_topic(db, topic_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def list_post_schedules(db: Session):
        return db.query(models.PostSchedule).order_by(models.PostSchedule.id).all()

    def get_post_schedule(db: Session, schedule_id: int):
        return db.query(models.PostSchedule).filter(models.PostSchedule.id == schedule_id).first()

    def create_post_schedule(db: Session, data: schemas.PostScheduleCreate):
        obj = models.PostSchedule(
            thu=data.thu, gio=data.gio, topic_id=data.topic_id,
            dang_kem_anh=data.dang_kem_anh, active=data.active,
            groups=get_groups_by_ids(db, data.group_ids),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_post_schedule(db: Session, schedule_id: int, data: schemas.PostScheduleUpdate):
        obj = get_post_schedule(db, schedule_id)
        if not obj:
            return None
        payload = data.model_dump(exclude_unset=True)
        if "group_ids" in payload:
            obj.groups = get_groups_by_ids(db, payload.pop("group_ids"))
        for k, v in payload.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_post_schedule(db: Session, schedule_id: int):
        obj = get_post_schedule(db, schedule_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def list_repost_schedules(db: Session):
        return db.query(models.RepostSchedule).order_by(models.RepostSchedule.id).all()

    def get_repost_schedule(db: Session, schedule_id: int):
        return db.query(models.RepostSchedule).filter(models.RepostSchedule.id == schedule_id).first()

    def create_repost_schedule(db: Session, data: schemas.RepostScheduleCreate):
        obj = models.RepostSchedule(
            thu=data.thu, gio=data.gio, so_bai=data.so_bai, active=data.active,
            nhom_nguon=get_groups_by_ids(db, data.nhom_nguon_ids),
            nhom_dich=get_groups_by_ids(db, data.nhom_dich_ids),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_repost_schedule(db: Session, schedule_id: int, data: schemas.RepostScheduleUpdate):
        obj = get_repost_schedule(db, schedule_id)
        if not obj:
            return None
        payload = data.model_dump(exclude_unset=True)
        if "nhom_nguon_ids" in payload:
            obj.nhom_nguon = get_groups_by_ids(db, payload.pop("nhom_nguon_ids"))
        if "nhom_dich_ids" in payload:
            obj.nhom_dich = get_groups_by_ids(db, payload.pop("nhom_dich_ids"))
        for k, v in payload.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_repost_schedule(db: Session, schedule_id: int):
        obj = get_repost_schedule(db, schedule_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def list_interact_schedules(db: Session):
        return db.query(models.InteractSchedule).order_by(models.InteractSchedule.id).all()

    def get_interact_schedule(db: Session, schedule_id: int):
        return db.query(models.InteractSchedule).filter(models.InteractSchedule.id == schedule_id).first()

    def create_interact_schedule(db: Session, data: schemas.InteractScheduleCreate):
        obj = models.InteractSchedule(
            thu=data.thu, gio=data.gio, active=data.active,
            groups=get_groups_by_ids(db, data.group_ids),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_interact_schedule(db: Session, schedule_id: int, data: schemas.InteractScheduleUpdate):
        obj = get_interact_schedule(db, schedule_id)
        if not obj:
            return None
        payload = data.model_dump(exclude_unset=True)
        if "group_ids" in payload:
            obj.groups = get_groups_by_ids(db, payload.pop("group_ids"))
        for k, v in payload.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_interact_schedule(db: Session, schedule_id: int):
        obj = get_interact_schedule(db, schedule_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def create_log(db: Session, loai: str, schedule_id: Optional[int] = None) -> models.ActivityLog:
        log = models.ActivityLog(loai=loai, schedule_id=schedule_id, trang_thai="running")
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def finish_log(db: Session, log_id: int, trang_thai: str, chi_tiet: Optional[str] = None):
        log = db.query(models.ActivityLog).filter(models.ActivityLog.id == log_id).first()
        if not log:
            return None
        log.trang_thai = trang_thai
        log.chi_tiet = chi_tiet
        log.ket_thuc = datetime.datetime.utcnow()
        db.commit()
        db.refresh(log)
        return log

    def list_logs(db: Session, limit: int = 100):
        return (
            db.query(models.ActivityLog)
            .order_by(models.ActivityLog.id.desc())
            .limit(limit)
            .all()
        )

    def get_log(db: Session, log_id: int):
        return db.query(models.ActivityLog).filter(models.ActivityLog.id == log_id).first()

    def get_settings(db: Session):
        return db.query(models.AppSettings).filter(models.AppSettings.id == 1).first()

    def ensure_settings(db: Session, mac_dinh: dict):
        obj = get_settings(db)
        if obj:
            return obj
        obj = models.AppSettings(id=1, **mac_dinh)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_settings(db: Session, data: schemas.AppSettingsUpdate):
        obj = get_settings(db)
        if not obj:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj