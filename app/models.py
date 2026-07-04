# -*- coding: utf-8 -*-
"""
Cac model SQLAlchemy: nhom, chu de, lich dang bai / repost / tuong tac,
log hoat dong, va cau hinh he thong luu trong DB.
"""
import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship

from app.database import Base

# ============================================================
# BANG TRUNG GIAN (many-to-many)
# ============================================================
post_schedule_groups = Table(
    "post_schedule_groups", Base.metadata,
    Column("post_schedule_id", Integer, ForeignKey("post_schedules.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

repost_schedule_source_groups = Table(
    "repost_schedule_source_groups", Base.metadata,
    Column("repost_schedule_id", Integer, ForeignKey("repost_schedules.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

repost_schedule_dest_groups = Table(
    "repost_schedule_dest_groups", Base.metadata,
    Column("repost_schedule_id", Integer, ForeignKey("repost_schedules.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

interact_schedule_groups = Table(
    "interact_schedule_groups", Base.metadata,
    Column("interact_schedule_id", Integer, ForeignKey("interact_schedules.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)


# ============================================================
# NHOM & CHU DE
# ============================================================
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    ten = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    ghi_chu = Column(String(500), nullable=True)
    tao_luc = Column(DateTime, default=datetime.datetime.utcnow)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    ten = Column(String(255), nullable=False)
    mo_ta = Column(Text, nullable=True)
    tao_luc = Column(DateTime, default=datetime.datetime.utcnow)


# ============================================================
# LICH DANG BAI
# ============================================================
class UserContent(Base):
    __tablename__ = "user_contents"

    id = Column(Integer, primary_key=True, index=True)
    noi_dung = Column(Text, nullable=False)
    tao_luc = Column(DateTime, default=datetime.datetime.utcnow)


class PostSchedule(Base):
    __tablename__ = "post_schedules"

    id = Column(Integer, primary_key=True, index=True)
    thu = Column(String(20), nullable=False)     # monday..sunday
    gio = Column(String(5), nullable=False)      # "HH:MM"

    # Có 2 chế độ cho "Đăng bài":
    # 1) Theo topic (topic_id != NULL)
    # 2) Theo nội dung người dùng (content_id != NULL)
    # Validation logic sẽ nằm ở crud/router.
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    content_id = Column(Integer, ForeignKey("user_contents.id"), nullable=True)
    giu_nguyen_goc = Column(Boolean, default=True)

    dang_kem_anh = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    tao_luc = Column(DateTime, default=datetime.datetime.utcnow)

    topic = relationship("Topic")
    content = relationship("UserContent")
    groups = relationship("Group", secondary=post_schedule_groups)



# ============================================================
# LICH REPOST
# ============================================================
class RepostSchedule(Base):
    __tablename__ = "repost_schedules"

    id = Column(Integer, primary_key=True, index=True)
    thu = Column(String(20), nullable=False)
    gio = Column(String(5), nullable=False)
    so_bai = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    tao_luc = Column(DateTime, default=datetime.datetime.utcnow)

    nhom_nguon = relationship("Group", secondary=repost_schedule_source_groups)
    nhom_dich = relationship("Group", secondary=repost_schedule_dest_groups)


# ============================================================
# LICH TUONG TAC
# ============================================================
class InteractSchedule(Base):
    __tablename__ = "interact_schedules"

    id = Column(Integer, primary_key=True, index=True)
    thu = Column(String(20), nullable=False)
    gio = Column(String(5), nullable=False)
    active = Column(Boolean, default=True)
    tao_luc = Column(DateTime, default=datetime.datetime.utcnow)

    groups = relationship("Group", secondary=interact_schedule_groups)


# ============================================================
# LOG HOAT DONG
# ============================================================
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    loai = Column(String(30), nullable=False)          # dang_bai | repost | tuong_tac
    schedule_id = Column(Integer, nullable=True)
    trang_thai = Column(String(20), default="running")  # running | success | error | pending
    chi_tiet = Column(Text, nullable=True)
    bat_dau = Column(DateTime, default=datetime.datetime.utcnow)
    ket_thuc = Column(DateTime, nullable=True)


# ============================================================
# CAU HINH HE THONG (1 dong duy nhat, id=1)
# ============================================================
class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    thu_muc_anh = Column(String(500), nullable=False)
    gioi_han_like = Column(Integer, default=5)
    gioi_han_comment = Column(Integer, default=3)
    thoi_gian_cho_giua_cac_nhom = Column(Integer, default=150)