# -*- coding: utf-8 -*-
"""MongoDB-backed CRUD adapter that preserves the existing API contract."""
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import List, Optional

from app import schemas
from app.mongo_db import get_collection


class MongoCrudAdapter:
    def __init__(self):
        self.groups = get_collection("groups")
        self.topics = get_collection("topics")
        self.user_contents = get_collection("user_contents")
        self.post_schedules = get_collection("post_schedules")
        self.repost_schedules = get_collection("repost_schedules")
        self.interact_schedules = get_collection("interact_schedules")
        self.activity_logs = get_collection("activity_logs")
        self.app_settings = get_collection("app_settings")
        self.counters = get_collection("counters")

    def _next_id(self, name: str) -> int:
        doc = self.counters.find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        return int(doc.get("seq", 0))

    def _group_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        return schemas.GroupOut.model_validate(data)

    def _topic_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        return schemas.TopicOut.model_validate(data)

    def _group_or_placeholder(self, gid):
        existing = self._group_from_doc(self.groups.find_one({"id": int(gid)}))
        if existing is not None:
            return existing
        return schemas.GroupOut(
            id=int(gid),
            ten=f"Nhóm {gid}",
            url="",
            ghi_chu=None,
            tao_luc=datetime.now(timezone.utc),
        )

    def _user_content_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        return schemas.UserContentOut.model_validate(data)

    def _topic_or_placeholder(self, topic_id):
        return self._topic_from_doc(self.topics.find_one({"id": int(topic_id)}))

    def _content_or_placeholder(self, content_id):
        if content_id is None:
            return None
        existing = self._user_content_from_doc(self.user_contents.find_one({"id": int(content_id)}))
        return existing

    def _post_schedule_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))

        topic_id = data.get("topic_id")
        content_id = data.get("content_id")
        # group_ids có thể lưu với nhiều key tuỳ dữ liệu cũ mới
        group_ids = (
            data.get("group_ids")
            or data.get("groups_ids")
            or data.get("groupIds")
            or data.get("groups")
            or []
        )
        # Nếu "groups" đã là list object thì cố gắng rút id
        if isinstance(group_ids, list) and group_ids and isinstance(group_ids[0], dict):
            group_ids = [g.get("id") for g in group_ids if g.get("id") is not None]

        # Normalize thu/gio from possible legacy keys
        # Legacy variants observed from UI/DB: may store as "thu"/"gio" or "thứ"/"ngày".
        # The UI/backend expects: thu in monday..sunday and gio in HH:MM.
        if "thu" not in data:
            data["thu"] = data.get("thứ") or data.get("thu_moi") or data.get("ngay") or data.get("day_of_week")
        if "gio" not in data:
            data["gio"] = data.get("gio") or data.get("time") or data.get("hour") or data.get("minute")

        data["topic"] = self._topic_or_placeholder(topic_id) if topic_id is not None else None
        data["content"] = self._content_or_placeholder(content_id)
        data["groups"] = [self._group_or_placeholder(gid) for gid in group_ids]
        return schemas.PostScheduleOut.model_validate(data)


    def _repost_schedule_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        data["nhom_nguon"] = [self._group_or_placeholder(gid) for gid in data.get("nhom_nguon_ids", [])]
        data["nhom_dich"] = [self._group_or_placeholder(gid) for gid in data.get("nhom_dich_ids", [])]
        return schemas.RepostScheduleOut.model_validate(data)

    def _interact_schedule_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        data["groups"] = [self._group_or_placeholder(gid) for gid in data.get("group_ids", [])]
        return schemas.InteractScheduleOut.model_validate(data)

    def _log_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        data["chi_tiet"] = data.get("chi_tiet")
        data["ket_thuc"] = data.get("ket_thuc")
        data.pop("_id", None)
        return schemas.ActivityLogOut.model_validate(data)

    def _settings_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data.pop("_id", None)
        return schemas.AppSettingsOut.model_validate(data)

    def list_groups(self):
        return [self._group_from_doc(doc) for doc in self.groups.find().sort("id", 1)]

    def get_group(self, group_id: int):
        return self._group_from_doc(self.groups.find_one({"id": int(group_id)}))

    def get_groups_by_ids(self, ids: List[int]):
        if not ids:
            return []
        return [self._group_from_doc(doc) for doc in self.groups.find({"id": {"$in": [int(i) for i in ids]}})]

    def create_group(self, data: schemas.GroupCreate):
        payload = data.model_dump()
        payload["id"] = self._next_id("groups")
        payload["tao_luc"] = datetime.now(timezone.utc)
        self.groups.insert_one(payload)
        return self._group_from_doc(payload)

    def update_group(self, group_id: int, data: schemas.GroupUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_group(group_id)
        self.groups.update_one({"id": int(group_id)}, {"$set": payload})
        return self.get_group(group_id)

    def delete_group(self, group_id: int):
        result = self.groups.delete_one({"id": int(group_id)})
        return result.deleted_count > 0

    def list_topics(self):
        return [self._topic_from_doc(doc) for doc in self.topics.find().sort("id", 1)]

    def get_topic(self, topic_id: int):
        return self._topic_from_doc(self.topics.find_one({"id": int(topic_id)}))

    def create_topic(self, data: schemas.TopicCreate):
        payload = data.model_dump()
        payload["id"] = self._next_id("topics")
        payload["tao_luc"] = datetime.now(timezone.utc)
        self.topics.insert_one(payload)
        return self._topic_from_doc(payload)

    def list_user_contents(self):
        return [self._user_content_from_doc(doc) for doc in self.user_contents.find().sort("id", 1)]

    def get_user_content(self, content_id: int):
        return self._user_content_from_doc(self.user_contents.find_one({"id": int(content_id)}))

    def create_user_content(self, data: schemas.UserContentCreate):
        payload = data.model_dump()
        payload["id"] = self._next_id("user_contents")
        payload["tao_luc"] = datetime.now(timezone.utc)
        self.user_contents.insert_one(payload)
        return self._user_content_from_doc(payload)

    def delete_user_content(self, content_id: int):
        result = self.user_contents.delete_one({"id": int(content_id)})
        return result.deleted_count > 0

    def update_topic(self, topic_id: int, data: schemas.TopicUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_topic(topic_id)
        self.topics.update_one({"id": int(topic_id)}, {"$set": payload})
        return self.get_topic(topic_id)

    def delete_topic(self, topic_id: int):
        result = self.topics.delete_one({"id": int(topic_id)})
        return result.deleted_count > 0

    def list_post_schedules(self):
        return [self._post_schedule_from_doc(doc) for doc in self.post_schedules.find().sort("id", 1)]

    def get_post_schedule(self, schedule_id: int):
        return self._post_schedule_from_doc(self.post_schedules.find_one({"id": int(schedule_id)}))

    def create_post_schedule(self, data: schemas.PostScheduleCreate):
        payload = data.model_dump()
        payload["id"] = self._next_id("post_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        self.post_schedules.insert_one(payload)
        return self._post_schedule_from_doc(payload)

    def update_post_schedule(self, schedule_id: int, data: schemas.PostScheduleUpdate):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self.get_post_schedule(schedule_id)
        # Tách các field null (cần $unset) và field có giá trị (cần $set)
        set_fields = {k: v for k, v in payload.items() if v is not None}
        unset_fields = {k: "" for k, v in payload.items() if v is None}
        update_op = {}
        if set_fields:
            update_op["$set"] = set_fields
        if unset_fields:
            update_op["$unset"] = unset_fields
        if update_op:
            self.post_schedules.update_one({"id": int(schedule_id)}, update_op)
        return self.get_post_schedule(schedule_id)

    def delete_post_schedule(self, schedule_id: int):
        result = self.post_schedules.delete_one({"id": int(schedule_id)})
        return result.deleted_count > 0

    def list_repost_schedules(self):
        return [self._repost_schedule_from_doc(doc) for doc in self.repost_schedules.find().sort("id", 1)]

    def get_repost_schedule(self, schedule_id: int):
        return self._repost_schedule_from_doc(self.repost_schedules.find_one({"id": int(schedule_id)}))

    def create_repost_schedule(self, data: schemas.RepostScheduleCreate):
        payload = data.model_dump()
        payload["id"] = self._next_id("repost_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        self.repost_schedules.insert_one(payload)
        return self._repost_schedule_from_doc(payload)

    def update_repost_schedule(self, schedule_id: int, data: schemas.RepostScheduleUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_repost_schedule(schedule_id)
        self.repost_schedules.update_one({"id": int(schedule_id)}, {"$set": payload})
        return self.get_repost_schedule(schedule_id)

    def delete_repost_schedule(self, schedule_id: int):
        result = self.repost_schedules.delete_one({"id": int(schedule_id)})
        return result.deleted_count > 0

    def list_interact_schedules(self):
        return [self._interact_schedule_from_doc(doc) for doc in self.interact_schedules.find().sort("id", 1)]

    def get_interact_schedule(self, schedule_id: int):
        return self._interact_schedule_from_doc(self.interact_schedules.find_one({"id": int(schedule_id)}))

    def create_interact_schedule(self, data: schemas.InteractScheduleCreate):
        payload = data.model_dump()
        payload["id"] = self._next_id("interact_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        self.interact_schedules.insert_one(payload)
        return self._interact_schedule_from_doc(payload)

    def update_interact_schedule(self, schedule_id: int, data: schemas.InteractScheduleUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_interact_schedule(schedule_id)
        self.interact_schedules.update_one({"id": int(schedule_id)}, {"$set": payload})
        return self.get_interact_schedule(schedule_id)

    def delete_interact_schedule(self, schedule_id: int):
        result = self.interact_schedules.delete_one({"id": int(schedule_id)})
        return result.deleted_count > 0

    def create_log(self, loai: str, schedule_id: Optional[int] = None):
        payload = {"id": self._next_id("activity_logs"), "loai": loai, "schedule_id": schedule_id, "trang_thai": "running", "bat_dau": datetime.now(timezone.utc)}
        self.activity_logs.insert_one(payload)
        return SimpleNamespace(**payload)

    def finish_log(self, log_id: int, trang_thai: str, chi_tiet: Optional[str] = None):
        self.activity_logs.update_one({"id": int(log_id)}, {"$set": {"trang_thai": trang_thai, "chi_tiet": chi_tiet, "ket_thuc": datetime.now(timezone.utc)}})
        return None

    def list_logs(self, limit: int = 100):
        return [self._log_from_doc(doc) for doc in self.activity_logs.find().sort("id", -1).limit(limit)]

    def get_log(self, log_id: int):
        return self._log_from_doc(self.activity_logs.find_one({"id": int(log_id)}))

    def get_settings(self):
        return self._settings_from_doc(self.app_settings.find_one({"id": 1}))

    def ensure_settings(self, mac_dinh: dict):
        doc = self.app_settings.find_one({"id": 1})
        if doc:
            return self._settings_from_doc(doc)
        payload = {"id": 1, **mac_dinh}
        self.app_settings.insert_one(payload)
        return self._settings_from_doc(payload)

    def update_settings(self, data):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        self.app_settings.update_one({"id": 1}, {"$set": payload}, upsert=True)
        return self.get_settings()


store = MongoCrudAdapter()
