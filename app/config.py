# -*- coding: utf-8 -*-
"""
Cau hinh he thong, doc tu bien moi truong (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://fb_bot_user:matkhau@localhost:5432/fb_bot_db"
    )
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "fb_bot_backend")
    USE_MONGODB: bool = os.getenv("USE_MONGODB", "true").lower() in {"1", "true", "yes", "y", "on"}
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    CORS_ORIGINS: list = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    ]

    # Gia tri mac dinh khi khoi tao bang app_settings lan dau (sau do sua qua API)
    THU_MUC_ANH_MAC_DINH: str = os.getenv("THU_MUC_ANH", "C:/fb_images")
    GIOI_HAN_LIKE_MAC_DINH: int = int(os.getenv("GIOI_HAN_LIKE", 5))
    GIOI_HAN_COMMENT_MAC_DINH: int = int(os.getenv("GIOI_HAN_COMMENT", 3))
    THOI_GIAN_CHO_MAC_DINH: int = int(os.getenv("THOI_GIAN_CHO_GIUA_CAC_NHOM", 150))


settings = Settings()