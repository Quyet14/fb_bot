# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.scheduler import _lay_cau_hinh_hien_tai
from app.crud import update_settings

router = APIRouter(prefix="/settings", tags=["Cau hinh"])


@router.get("/", response_model=schemas.AppSettingsOut)
def xem_cau_hinh(db: Session = Depends(get_db)):
    return _lay_cau_hinh_hien_tai(db)


@router.put("/", response_model=schemas.AppSettingsOut)
def sua_cau_hinh(data: schemas.AppSettingsUpdate, db: Session = Depends(get_db)):
    _lay_cau_hinh_hien_tai(db)  # dam bao da co dong cau hinh
    return update_settings(db, data)