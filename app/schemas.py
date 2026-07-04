# -*- coding: utf-8 -*-
"""
Pydantic schemas dung cho request/response cua API.
"""
import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field



# ============================================================
# NHOM
# ============================================================
class GroupBase(BaseModel):
    ten: str
    url: str
    ghi_chu: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    ten: Optional[str] = None
    url: Optional[str] = None
    ghi_chu: Optional[str] = None


class GroupOut(GroupBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tao_luc: datetime.datetime


# ============================================================
# CHU DE
# ============================================================
class TopicBase(BaseModel):
    ten: str
    mo_ta: Optional[str] = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    ten: Optional[str] = None
    mo_ta: Optional[str] = None


class TopicOut(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tao_luc: datetime.datetime


# ============================================================
# LICH DANG BAI
# ============================================================
class UserContentBase(BaseModel):
    noi_dung: str


class UserContentCreate(UserContentBase):
    pass


class UserContentOut(UserContentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tao_luc: datetime.datetime


class PostScheduleBase(BaseModel):
    thu: str
    gio: str

    # Đăng bài theo topic HOẶC theo nội dung người dùng
    topic_id: Optional[int] = None
    content_id: Optional[int] = None
    giu_nguyen_goc: bool = True

    dang_kem_anh: bool = False
    active: bool = True
    group_ids: List[int] = Field(default_factory=list)



class PostScheduleCreate(PostScheduleBase):
    pass


class PostScheduleUpdate(BaseModel):
    thu: Optional[str] = None
    gio: Optional[str] = None

    topic_id: Optional[int] = None
    content_id: Optional[int] = None
    giu_nguyen_goc: Optional[bool] = None

    dang_kem_anh: Optional[bool] = None
    active: Optional[bool] = None
    group_ids: Optional[List[int]] = None


class PostScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thu: str
    gio: str
    dang_kem_anh: bool
    active: bool
    giu_nguyen_goc: bool = True

    topic: Optional[TopicOut] = None
    content: Optional[UserContentOut] = None
    groups: List[GroupOut]



# ============================================================
# LICH REPOST
# ============================================================
class RepostScheduleBase(BaseModel):
    thu: str
    gio: str
    so_bai: int = 1
    active: bool = True
    nhom_nguon_ids: List[int] = Field(default_factory=list)
    nhom_dich_ids: List[int] = Field(default_factory=list)



class RepostScheduleCreate(RepostScheduleBase):
    pass


class RepostScheduleUpdate(BaseModel):
    thu: Optional[str] = None
    gio: Optional[str] = None
    so_bai: Optional[int] = None
    active: Optional[bool] = None
    nhom_nguon_ids: Optional[List[int]] = None
    nhom_dich_ids: Optional[List[int]] = None


class RepostScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thu: str
    gio: str
    so_bai: int
    active: bool
    nhom_nguon: List[GroupOut]
    nhom_dich: List[GroupOut]


# ============================================================
# LICH TUONG TAC
# ============================================================
class InteractScheduleBase(BaseModel):
    thu: str
    gio: str
    active: bool = True
    group_ids: List[int] = Field(default_factory=list)



class InteractScheduleCreate(InteractScheduleBase):
    pass


class InteractScheduleUpdate(BaseModel):
    thu: Optional[str] = None
    gio: Optional[str] = None
    active: Optional[bool] = None
    group_ids: Optional[List[int]] = None


class InteractScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thu: str
    gio: str
    active: bool
    groups: List[GroupOut]


# ============================================================
# LOG HOAT DONG
# ============================================================
class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    loai: str
    schedule_id: Optional[int]
    trang_thai: str
    chi_tiet: Optional[str]
    bat_dau: datetime.datetime
    ket_thuc: Optional[datetime.datetime]


# ============================================================
# CAU HINH HE THONG
# ============================================================
class AppSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    thu_muc_anh: str
    gioi_han_like: int
    gioi_han_comment: int
    thoi_gian_cho_giua_cac_nhom: int


class AppSettingsUpdate(BaseModel):
    thu_muc_anh: Optional[str] = None
    gioi_han_like: Optional[int] = None
    gioi_han_comment: Optional[int] = None
    thoi_gian_cho_giua_cac_nhom: Optional[int] = None


# ============================================================
# CHAY THU CONG (khong can luu lich)
# ============================================================
class RunDangBaiNow(BaseModel):
    topic_id: int
    group_ids: List[int]
    dang_kem_anh: bool = False


class RunRepostNow(BaseModel):
    nhom_nguon_ids: List[int]
    nhom_dich_ids: List[int]
    so_bai: int = 1


class RunTuongTacNow(BaseModel):
    group_ids: List[int]