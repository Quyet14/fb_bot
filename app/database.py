# -*- coding: utf-8 -*-
"""Database layer that can use either SQLAlchemy/PostgreSQL or MongoDB."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

Base = declarative_base()

if settings.USE_MONGODB:
    class _DummySession:
        def close(self):
            pass

    engine = None
    SessionLocal = lambda: _DummySession()

    def get_db():
        db = _DummySession()
        try:
            yield db
        finally:
            db.close()
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db():
        """Dependency dung trong cac router FastAPI."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()