# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db
from app.dependencies import get_user_id

router = APIRouter(prefix="/logs", tags=["Log hoat dong"])


@router.get("/", response_model=list[schemas.ActivityLogOut])
def danh_sach_log(limit: int = Query(100, le=500), db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_logs(db, limit, user_id=user_id)


@router.get("/{log_id}", response_model=schemas.ActivityLogOut)
def chi_tiet_log(log_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.get_log(db, log_id, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay log")
    return obj