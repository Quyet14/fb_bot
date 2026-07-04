# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(prefix="/groups", tags=["Nhom"])


@router.get("/", response_model=list[schemas.GroupOut])
def danh_sach_nhom(db: Session = Depends(get_db)):
    return crud.list_groups(db)


@router.post("/", response_model=schemas.GroupOut, status_code=201)
def tao_nhom(data: schemas.GroupCreate, db: Session = Depends(get_db)):
    return crud.create_group(db, data)


@router.get("/{group_id}", response_model=schemas.GroupOut)
def chi_tiet_nhom(group_id: int, db: Session = Depends(get_db)):
    obj = crud.get_group(db, group_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay nhom")
    return obj


@router.put("/{group_id}", response_model=schemas.GroupOut)
def sua_nhom(group_id: int, data: schemas.GroupUpdate, db: Session = Depends(get_db)):
    obj = crud.update_group(db, group_id, data)
    if not obj:
        raise HTTPException(404, "Khong tim thay nhom")
    return obj


@router.delete("/{group_id}", status_code=204)
def xoa_nhom(group_id: int, db: Session = Depends(get_db)):
    if not crud.delete_group(db, group_id):
        raise HTTPException(404, "Khong tim thay nhom")