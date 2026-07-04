# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(prefix="/topics", tags=["Chu de"])


@router.get("/", response_model=list[schemas.TopicOut])
def danh_sach_chu_de(db: Session = Depends(get_db)):
    return crud.list_topics(db)


@router.post("/", response_model=schemas.TopicOut, status_code=201)
def tao_chu_de(data: schemas.TopicCreate, db: Session = Depends(get_db)):
    return crud.create_topic(db, data)


@router.get("/{topic_id}", response_model=schemas.TopicOut)
def chi_tiet_chu_de(topic_id: int, db: Session = Depends(get_db)):
    obj = crud.get_topic(db, topic_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay chu de")
    return obj


@router.put("/{topic_id}", response_model=schemas.TopicOut)
def sua_chu_de(topic_id: int, data: schemas.TopicUpdate, db: Session = Depends(get_db)):
    obj = crud.update_topic(db, topic_id, data)
    if not obj:
        raise HTTPException(404, "Khong tim thay chu de")
    return obj


@router.delete("/{topic_id}", status_code=204)
def xoa_chu_de(topic_id: int, db: Session = Depends(get_db)):
    if not crud.delete_topic(db, topic_id):
        raise HTTPException(404, "Khong tim thay chu de")