# -*- coding: utf-8 -*-
"""MongoDB connection helpers for the FastAPI backend."""
from pymongo import MongoClient
from app.config import settings


client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[settings.MONGODB_DB_NAME]


def get_collection(name: str):
    return db[name]
