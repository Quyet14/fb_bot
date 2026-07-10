# -*- coding: utf-8 -*-
"""
Diem khoi dong FastAPI app: dang ky router, tao bang DB,
khoi dong scheduler va nap lich tu database.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine
from app.config import settings
from app.scheduler import scheduler, nap_lai_toan_bo_lich
from app.routers import groups, topics, schedules, actions, logs, setting as settings_router, user_contents as user_contents_router
from app.routers.auth import router as auth_router
from app.routers.fanpage_schedules import router as fanpage_schedules_router
from app.routers.fb_accounts import router as fb_accounts_router


if settings.USE_MONGODB:
    from app.mongo_db import db as mongo_db

app = FastAPI(
    title="FB Bot Backend",
    description="API quan ly nhom, chu de, lich dang bai / repost / tuong tac cho bot Facebook.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(groups.router)
app.include_router(topics.router)
app.include_router(schedules.router)
app.include_router(fanpage_schedules_router)
app.include_router(fb_accounts_router)
app.include_router(actions.router)
app.include_router(logs.router)
app.include_router(settings_router.router)
app.include_router(user_contents_router.router)



@app.on_event("startup")
def khoi_dong():
    if not settings.USE_MONGODB:
        Base.metadata.create_all(bind=engine)
    # Tạo thư mục uploads nếu chưa có
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "images")
    os.makedirs(upload_dir, exist_ok=True)
    nap_lai_toan_bo_lich()
    scheduler.start()


# Serve uploaded images as static files
_upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "images")
os.makedirs(_upload_dir, exist_ok=True)
app.mount("/uploads/images", StaticFiles(directory=_upload_dir), name="uploads")


@app.on_event("shutdown")
def tat():
    scheduler.shutdown(wait=False)


@app.get("/", tags=["He thong"])
def trang_chu():
    return {"trang_thai": "OK", "thong_bao": "FB Bot Backend dang chay"}