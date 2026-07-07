# -*- coding: utf-8 -*-
"""MongoDB-backed CRUD adapter that preserves the existing API contract.

user_id is optional in all methods:
- When provided (router context): queries are scoped to that user.
- When None (scheduler background context): no user filter — safe because
  the scheduler always uses a specific numeric schedule_id.
"""
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
        self.fanpage_schedules = get_collection("fanpage_schedules")
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

    @staticmethod
    def _user_filter(base: dict, user_id: Optional[str]) -> dict:
        """Merge user_id into a query dict when user_id is provided."""
        if user_id is not None:
            return {**base, "user_id": user_id}
        return base

    def _group_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        data.setdefault("loai", "group")  # backward compat: bản cũ không có loai
        return schemas.GroupOut.model_validate(data)

    def _topic_from_doc(self, doc):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        return schemas.TopicOut.model_validate(data)

    def _group_or_placeholder(self, gid, user_id: Optional[str] = None):
        """Lookup a group by id, scoped to user_id when provided."""
        q = self._user_filter({"id": int(gid)}, user_id)
        existing = self._group_from_doc(self.groups.find_one(q))
        if existing is not None:
            return existing
        # Fallback placeholder — group may have been deleted or belong to different user
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

    def _topic_or_placeholder(self, topic_id, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(topic_id)}, user_id)
        return self._topic_from_doc(self.topics.find_one(q))

    def _content_or_placeholder(self, content_id, user_id: Optional[str] = None):
        if content_id is None:
            return None
        q = self._user_filter({"id": int(content_id)}, user_id)
        return self._user_content_from_doc(self.user_contents.find_one(q))

    def _post_schedule_from_doc(self, doc, user_id: Optional[str] = None):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))

        topic_id = data.get("topic_id")
        content_id = data.get("content_id")
        group_ids = (
            data.get("group_ids")
            or data.get("groups_ids")
            or data.get("groupIds")
            or data.get("groups")
            or []
        )
        if isinstance(group_ids, list) and group_ids and isinstance(group_ids[0], dict):
            group_ids = [g.get("id") for g in group_ids if g.get("id") is not None]

        if "thu" not in data:
            data["thu"] = data.get("thứ") or data.get("thu_moi") or data.get("ngay") or data.get("day_of_week")
        if "gio" not in data:
            data["gio"] = data.get("gio") or data.get("time") or data.get("hour") or data.get("minute")

        data["topic"] = self._topic_or_placeholder(topic_id, user_id) if topic_id is not None else None
        data["content"] = self._content_or_placeholder(content_id, user_id)
        data["groups"] = [self._group_or_placeholder(gid, user_id) for gid in group_ids]
        return schemas.PostScheduleOut.model_validate(data)

    def _repost_schedule_from_doc(self, doc, user_id: Optional[str] = None):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        data["nhom_nguon"] = [self._group_or_placeholder(gid, user_id) for gid in data.get("nhom_nguon_ids", [])]
        data["nhom_dich"] = [self._group_or_placeholder(gid, user_id) for gid in data.get("nhom_dich_ids", [])]
        return schemas.RepostScheduleOut.model_validate(data)

    def _interact_schedule_from_doc(self, doc, user_id: Optional[str] = None):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        data["groups"] = [self._group_or_placeholder(gid, user_id) for gid in data.get("group_ids", [])]
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

    # ── Groups ────────────────────────────────────────────────

    def list_groups(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._group_from_doc(doc) for doc in self.groups.find(q).sort("id", 1)]

    def get_group(self, group_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(group_id)}, user_id)
        return self._group_from_doc(self.groups.find_one(q))

    def get_groups_by_ids(self, ids: List[int], user_id: Optional[str] = None):
        if not ids:
            return []
        q = self._user_filter({"id": {"$in": [int(i) for i in ids]}}, user_id)
        return [self._group_from_doc(doc) for doc in self.groups.find(q)]

    def create_group(self, data: schemas.GroupCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("groups")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.groups.insert_one(payload)
        return self._group_from_doc(payload)

    def update_group(self, group_id: int, data: schemas.GroupUpdate, user_id: Optional[str] = None):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_group(group_id, user_id)
        q = self._user_filter({"id": int(group_id)}, user_id)
        self.groups.update_one(q, {"$set": payload})
        return self.get_group(group_id, user_id)

    def delete_group(self, group_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(group_id)}, user_id)
        result = self.groups.delete_one(q)
        return result.deleted_count > 0

    # ── Topics ────────────────────────────────────────────────

    def list_topics(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._topic_from_doc(doc) for doc in self.topics.find(q).sort("id", 1)]

    def get_topic(self, topic_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(topic_id)}, user_id)
        return self._topic_from_doc(self.topics.find_one(q))

    def create_topic(self, data: schemas.TopicCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("topics")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.topics.insert_one(payload)
        return self._topic_from_doc(payload)

    def update_topic(self, topic_id: int, data: schemas.TopicUpdate, user_id: Optional[str] = None):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_topic(topic_id, user_id)
        q = self._user_filter({"id": int(topic_id)}, user_id)
        self.topics.update_one(q, {"$set": payload})
        return self.get_topic(topic_id, user_id)

    def delete_topic(self, topic_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(topic_id)}, user_id)
        result = self.topics.delete_one(q)
        return result.deleted_count > 0

    # ── User Contents ─────────────────────────────────────────

    def list_user_contents(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._user_content_from_doc(doc) for doc in self.user_contents.find(q).sort("id", 1)]

    def get_user_content(self, content_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(content_id)}, user_id)
        return self._user_content_from_doc(self.user_contents.find_one(q))

    def create_user_content(self, data: schemas.UserContentCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("user_contents")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.user_contents.insert_one(payload)
        return self._user_content_from_doc(payload)

    def delete_user_content(self, content_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(content_id)}, user_id)
        result = self.user_contents.delete_one(q)
        return result.deleted_count > 0

    # ── Post Schedules ────────────────────────────────────────

    def list_post_schedules(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._post_schedule_from_doc(doc, user_id) for doc in self.post_schedules.find(q).sort("id", 1)]

    def get_post_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        return self._post_schedule_from_doc(self.post_schedules.find_one(q), user_id)

    def create_post_schedule(self, data: schemas.PostScheduleCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("post_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.post_schedules.insert_one(payload)
        return self._post_schedule_from_doc(payload, user_id)

    def update_post_schedule(self, schedule_id: int, data: schemas.PostScheduleUpdate, user_id: Optional[str] = None):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self.get_post_schedule(schedule_id, user_id)
        set_fields = {k: v for k, v in payload.items() if v is not None}
        unset_fields = {k: "" for k, v in payload.items() if v is None}
        update_op = {}
        if set_fields:
            update_op["$set"] = set_fields
        if unset_fields:
            update_op["$unset"] = unset_fields
        if update_op:
            q = self._user_filter({"id": int(schedule_id)}, user_id)
            self.post_schedules.update_one(q, update_op)
        return self.get_post_schedule(schedule_id, user_id)

    def delete_post_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        result = self.post_schedules.delete_one(q)
        return result.deleted_count > 0

    # ── Repost Schedules ──────────────────────────────────────

    def list_repost_schedules(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._repost_schedule_from_doc(doc, user_id) for doc in self.repost_schedules.find(q).sort("id", 1)]

    def get_repost_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        return self._repost_schedule_from_doc(self.repost_schedules.find_one(q), user_id)

    def create_repost_schedule(self, data: schemas.RepostScheduleCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("repost_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.repost_schedules.insert_one(payload)
        return self._repost_schedule_from_doc(payload, user_id)

    def update_repost_schedule(self, schedule_id: int, data: schemas.RepostScheduleUpdate, user_id: Optional[str] = None):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_repost_schedule(schedule_id, user_id)
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        self.repost_schedules.update_one(q, {"$set": payload})
        return self.get_repost_schedule(schedule_id, user_id)

    def delete_repost_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        result = self.repost_schedules.delete_one(q)
        return result.deleted_count > 0

    # ── Interact Schedules ────────────────────────────────────

    def list_interact_schedules(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._interact_schedule_from_doc(doc, user_id) for doc in self.interact_schedules.find(q).sort("id", 1)]

    def get_interact_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        return self._interact_schedule_from_doc(self.interact_schedules.find_one(q), user_id)

    def create_interact_schedule(self, data: schemas.InteractScheduleCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("interact_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.interact_schedules.insert_one(payload)
        return self._interact_schedule_from_doc(payload, user_id)

    def update_interact_schedule(self, schedule_id: int, data: schemas.InteractScheduleUpdate, user_id: Optional[str] = None):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_interact_schedule(schedule_id, user_id)
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        self.interact_schedules.update_one(q, {"$set": payload})
        return self.get_interact_schedule(schedule_id, user_id)

    def delete_interact_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        result = self.interact_schedules.delete_one(q)
        return result.deleted_count > 0

    # ── Activity Logs ─────────────────────────────────────────

    def create_log(self, loai: str, schedule_id: Optional[int] = None, user_id: Optional[str] = None):
        payload = {
            "id": self._next_id("activity_logs"),
            "loai": loai,
            "schedule_id": schedule_id,
            "trang_thai": "running",
            "bat_dau": datetime.now(timezone.utc),
        }
        if user_id is not None:
            payload["user_id"] = user_id
        self.activity_logs.insert_one(payload)
        return SimpleNamespace(**payload)

    def finish_log(self, log_id: int, trang_thai: str, chi_tiet: Optional[str] = None):
        self.activity_logs.update_one(
            {"id": int(log_id)},
            {"$set": {"trang_thai": trang_thai, "chi_tiet": chi_tiet, "ket_thuc": datetime.now(timezone.utc)}}
        )
        return None

    def list_logs(self, limit: int = 100, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._log_from_doc(doc) for doc in self.activity_logs.find(q).sort("id", -1).limit(limit)]

    def get_log(self, log_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(log_id)}, user_id)
        return self._log_from_doc(self.activity_logs.find_one(q))

    # ── App Settings ──────────────────────────────────────────

    def _settings_key(self, user_id: Optional[str]) -> dict:
        """Each user gets their own settings document keyed by user_id.
        Falls back to legacy {"id": 1} key when no user_id (scheduler/internal)."""
        if user_id is not None:
            return {"user_id": user_id}
        return {"id": 1}

    def get_settings(self, user_id: Optional[str] = None):
        return self._settings_from_doc(self.app_settings.find_one(self._settings_key(user_id)))

    def ensure_settings(self, mac_dinh: dict, user_id: Optional[str] = None):
        key = self._settings_key(user_id)
        doc = self.app_settings.find_one(key)
        if doc:
            return self._settings_from_doc(doc)
        payload = {**key, **mac_dinh}
        self.app_settings.insert_one(payload)
        return self._settings_from_doc(payload)

    def update_settings(self, data, user_id: Optional[str] = None):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        key = self._settings_key(user_id)
        self.app_settings.update_one(key, {"$set": payload}, upsert=True)
        return self.get_settings(user_id)

    # ── Fanpage Schedules (legacy collection) ─────────────────

    def _fanpage_schedule_from_doc(self, doc, user_id: Optional[str] = None):
        if not doc:
            return None
        data = dict(doc)
        data["id"] = int(data.get("id", 0))
        topic_id = data.get("topic_id")
        content_id = data.get("content_id")
        fanpage_ids = (
            data.get("fanpage_ids")
            or data.get("fanpages")
            or []
        )
        if isinstance(fanpage_ids, list) and fanpage_ids and isinstance(fanpage_ids[0], dict):
            fanpage_ids = [g.get("id") for g in fanpage_ids if g.get("id") is not None]
        data["topic"] = self._topic_or_placeholder(topic_id, user_id) if topic_id is not None else None
        data["content"] = self._content_or_placeholder(content_id, user_id)
        data["fanpages"] = [self._group_or_placeholder(fid, user_id) for fid in fanpage_ids]
        return schemas.FanpageScheduleOut.model_validate(data)

    def list_fanpage_schedules(self, user_id: Optional[str] = None):
        q = self._user_filter({}, user_id)
        return [self._fanpage_schedule_from_doc(doc, user_id) for doc in self.fanpage_schedules.find(q).sort("id", 1)]

    def get_fanpage_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        return self._fanpage_schedule_from_doc(self.fanpage_schedules.find_one(q), user_id)

    def create_fanpage_schedule(self, data: schemas.FanpageScheduleCreate, user_id: Optional[str] = None):
        payload = data.model_dump()
        payload["id"] = self._next_id("fanpage_schedules")
        payload["tao_luc"] = datetime.now(timezone.utc)
        if user_id is not None:
            payload["user_id"] = user_id
        self.fanpage_schedules.insert_one(payload)
        return self._fanpage_schedule_from_doc(payload, user_id)

    def update_fanpage_schedule(self, schedule_id: int, data: schemas.FanpageScheduleUpdate, user_id: Optional[str] = None):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self.get_fanpage_schedule(schedule_id, user_id)
        set_fields = {k: v for k, v in payload.items() if v is not None}
        unset_fields = {k: "" for k, v in payload.items() if v is None}
        update_op = {}
        if set_fields:
            update_op["$set"] = set_fields
        if unset_fields:
            update_op["$unset"] = unset_fields
        if update_op:
            q = self._user_filter({"id": int(schedule_id)}, user_id)
            self.fanpage_schedules.update_one(q, update_op)
        return self.get_fanpage_schedule(schedule_id, user_id)

    def delete_fanpage_schedule(self, schedule_id: int, user_id: Optional[str] = None):
        q = self._user_filter({"id": int(schedule_id)}, user_id)
        result = self.fanpage_schedules.delete_one(q)
        return result.deleted_count > 0

    def list_fanpages(self, user_id: Optional[str] = None):
        """Trả về danh sách group có loai='fanpage'."""
        q = self._user_filter({"loai": "fanpage"}, user_id)
        return [self._group_from_doc(doc) for doc in self.groups.find(q).sort("id", 1)]


store = MongoCrudAdapter()
