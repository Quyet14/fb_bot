# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(prefix="/user-contents", tags=["Noi dung"])


@router.get("/", response_model=list[schemas.UserContentOut])
def danh_sach_noi_dung(db: Session = Depends(get_db)):
    return crud.list_user_contents(db)


@router.post("/", response_model=schemas.UserContentOut, status_code=201)
def tao_noi_dung(data: schemas.UserContentCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user_content(db, data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{content_id}", status_code=204)
def xoa_noi_dung(content_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_user_content(db, content_id)
    if not ok:
        raise HTTPException(404, "Khong tim thay noi dung")

