# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db
from app.dependencies import get_user_id

router = APIRouter(prefix="/topics", tags=["Chu de"])


@router.get("/", response_model=list[schemas.TopicOut])
def danh_sach_chu_de(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_topics(db, user_id=user_id)


@router.post("/", response_model=schemas.TopicOut, status_code=201)
def tao_chu_de(data: schemas.TopicCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.create_topic(db, data, user_id=user_id)


@router.get("/{topic_id}", response_model=schemas.TopicOut)
def chi_tiet_chu_de(topic_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.get_topic(db, topic_id, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay chu de")
    return obj


@router.put("/{topic_id}", response_model=schemas.TopicOut)
def sua_chu_de(topic_id: int, data: schemas.TopicUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    obj = crud.update_topic(db, topic_id, data, user_id=user_id)
    if not obj:
        raise HTTPException(404, "Khong tim thay chu de")
    return obj


@router.delete("/{topic_id}", status_code=204)
def xoa_chu_de(topic_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    if not crud.delete_topic(db, topic_id, user_id=user_id):
        raise HTTPException(404, "Khong tim thay chu de")