# -*- coding: utf-8 -*-
"""MongoDB-backed CRUD helpers for the app."""
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from app import schemas
from app.mongo_db import get_collection


def _to_dict(data):
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    return data


def _to_obj(doc, model_cls):
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return model_cls.model_validate(doc)


class MongoStore:
    def __init__(self):
        self.groups = get_collection("groups")
        self.topics = get_collection("topics")
        self.post_schedules = get_collection("post_schedules")
        self.repost_schedules = get_collection("repost_schedules")
        self.interact_schedules = get_collection("interact_schedules")
        self.activity_logs = get_collection("activity_logs")
        self.app_settings = get_collection("app_settings")

    def list_groups(self):
        return [self._group_from_doc(doc) for doc in self.groups.find().sort("_id", 1)]

    def get_group(self, group_id: str):
        doc = self.groups.find_one({"_id": ObjectId(group_id)})
        return self._group_from_doc(doc)

    def get_groups_by_ids(self, ids: List[str]):
        if not ids:
            return []
        object_ids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
        return [self._group_from_doc(doc) for doc in self.groups.find({"_id": {"$in": object_ids}})]

    def create_group(self, data: schemas.GroupCreate):
        payload = data.model_dump()
        payload["tao_luc"] = datetime.now(timezone.utc)
        result = self.groups.insert_one(payload)
        doc = self.groups.find_one({"_id": result.inserted_id})
        return self._group_from_doc(doc)

    def update_group(self, group_id: str, data: schemas.GroupUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_group(group_id)
        self.groups.update_one({"_id": ObjectId(group_id)}, {"$set": payload})
        return self.get_group(group_id)

    def delete_group(self, group_id: str):
        result = self.groups.delete_one({"_id": ObjectId(group_id)})
        return result.deleted_count > 0

    def list_topics(self):
        return [self._topic_from_doc(doc) for doc in self.topics.find().sort("_id", 1)]

    def get_topic(self, topic_id: str):
        doc = self.topics.find_one({"_id": ObjectId(topic_id)})
        return self._topic_from_doc(doc)

    def create_topic(self, data: schemas.TopicCreate):
        payload = data.model_dump()
        payload["tao_luc"] = datetime.now(timezone.utc)
        result = self.topics.insert_one(payload)
        doc = self.topics.find_one({"_id": result.inserted_id})
        return self._topic_from_doc(doc)

    def update_topic(self, topic_id: str, data: schemas.TopicUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_topic(topic_id)
        self.topics.update_one({"_id": ObjectId(topic_id)}, {"$set": payload})
        return self.get_topic(topic_id)

    def delete_topic(self, topic_id: str):
        result = self.topics.delete_one({"_id": ObjectId(topic_id)})
        return result.deleted_count > 0

    def list_post_schedules(self):
        return [self._post_schedule_from_doc(doc) for doc in self.post_schedules.find().sort("_id", 1)]

    def get_post_schedule(self, schedule_id: str):
        doc = self.post_schedules.find_one({"_id": ObjectId(schedule_id)})
        return self._post_schedule_from_doc(doc)

    def create_post_schedule(self, data: schemas.PostScheduleCreate):
        payload = data.model_dump()
        payload["tao_luc"] = datetime.now(timezone.utc)
        result = self.post_schedules.insert_one(payload)
        doc = self.post_schedules.find_one({"_id": result.inserted_id})
        return self._post_schedule_from_doc(doc)

    def update_post_schedule(self, schedule_id: str, data: schemas.PostScheduleUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_post_schedule(schedule_id)
        self.post_schedules.update_one({"_id": ObjectId(schedule_id)}, {"$set": payload})
        return self.get_post_schedule(schedule_id)

    def delete_post_schedule(self, schedule_id: str):
        result = self.post_schedules.delete_one({"_id": ObjectId(schedule_id)})
        return result.deleted_count > 0

    def list_repost_schedules(self):
        return [self._repost_schedule_from_doc(doc) for doc in self.repost_schedules.find().sort("_id", 1)]

    def get_repost_schedule(self, schedule_id: str):
        doc = self.repost_schedules.find_one({"_id": ObjectId(schedule_id)})
        return self._repost_schedule_from_doc(doc)

    def create_repost_schedule(self, data: schemas.RepostScheduleCreate):
        payload = data.model_dump()
        payload["tao_luc"] = datetime.now(timezone.utc)
        result = self.repost_schedules.insert_one(payload)
        doc = self.repost_schedules.find_one({"_id": result.inserted_id})
        return self._repost_schedule_from_doc(doc)

    def update_repost_schedule(self, schedule_id: str, data: schemas.RepostScheduleUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_repost_schedule(schedule_id)
        self.repost_schedules.update_one({"_id": ObjectId(schedule_id)}, {"$set": payload})
        return self.get_repost_schedule(schedule_id)

    def delete_repost_schedule(self, schedule_id: str):
        result = self.repost_schedules.delete_one({"_id": ObjectId(schedule_id)})
        return result.deleted_count > 0

    def list_interact_schedules(self):
        return [self._interact_schedule_from_doc(doc) for doc in self.interact_schedules.find().sort("_id", 1)]

    def get_interact_schedule(self, schedule_id: str):
        doc = self.interact_schedules.find_one({"_id": ObjectId(schedule_id)})
        return self._interact_schedule_from_doc(doc)

    def create_interact_schedule(self, data: schemas.InteractScheduleCreate):
        payload = data.model_dump()
        payload["tao_luc"] = datetime.now(timezone.utc)
        result = self.interact_schedules.insert_one(payload)
        doc = self.interact_schedules.find_one({"_id": result.inserted_id})
        return self._interact_schedule_from_doc(doc)

    def update_interact_schedule(self, schedule_id: str, data: schemas.InteractScheduleUpdate):
        payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not payload:
            return self.get_interact_schedule(schedule_id)
        self.interact_schedules.update_one({"_id": ObjectId(schedule_id)}, {"$set": payload})
        return self.get_interact_schedule(schedule_id)

    def delete_interact_schedule(self, schedule_id: str):
        result = self.interact_schedules.delete_one({"_id": ObjectId(schedule_id)})
        return result.deleted_count > 0

    def create_log(self, loai: str, schedule_id: Optional[int] = None):
        payload = {"loai": loai, "schedule_id": schedule_id, "trang_thai": "running", "bat_dau": datetime.now(timezone.utc)}
        result = self.activity_logs.insert_one(payload)
        return {"id": str(result.inserted_id), **payload}

    def finish_log(self, log_id: str, trang_thai: str, chi_tiet: Optional[str] = None):
        payload = {"trang_thai": trang_thai, "chi_tiet": chi_tiet, "ket_thuc": datetime.now(timezone.utc)}
        self.activity_logs.update_one({"_id": ObjectId(log_id)}, {"$set": payload})
        return None

    def list_logs(self, limit: int = 100):
        return [self._log_from_doc(doc) for doc in self.activity_logs.find().sort("_id", -1).limit(limit)]

    def get_settings(self):
        doc = self.app_settings.find_one({"id": 1})
        return self._settings_from_doc(doc)

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

    def _group_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return schemas.GroupOut.model_validate(doc)

    def _topic_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return schemas.TopicOut.model_validate(doc)

    def _post_schedule_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return schemas.PostScheduleOut.model_validate(doc)

    def _repost_schedule_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return schemas.RepostScheduleOut.model_validate(doc)

    def _interact_schedule_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return schemas.InteractScheduleOut.model_validate(doc)

    def _log_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return schemas.ActivityLogOut.model_validate(doc)

    def _settings_from_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        return schemas.AppSettingsOut.model_validate(doc)


store = MongoStore()
