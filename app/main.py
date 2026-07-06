# -*- coding: utf-8 -*-
"""
Diem khoi dong FastAPI app: dang ky router, tao bang DB,
khoi dong scheduler va nap lich tu database.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.scheduler import scheduler, nap_lai_toan_bo_lich
from app.routers import groups, topics, schedules, actions, logs, setting as settings_router, user_contents as user_contents_router
from app.routers.auth import router as auth_router


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
app.include_router(actions.router)
app.include_router(logs.router)
app.include_router(settings_router.router)
app.include_router(user_contents_router.router)



@app.on_event("startup")
def khoi_dong():
    if not settings.USE_MONGODB:
        Base.metadata.create_all(bind=engine)
    nap_lai_toan_bo_lich()
    scheduler.start()


@app.on_event("shutdown")
def tat():
    scheduler.shutdown(wait=False)


@app.get("/", tags=["He thong"])
def trang_chu():
    return {"trang_thai": "OK", "thong_bao": "FB Bot Backend dang chay"}