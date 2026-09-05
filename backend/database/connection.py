"""
Database Connection & Session Initialization for AI-Sales-Analytics-Dashboard.
Uses SQLite by default with SQLAlchemy ORM and includes non-destructive schema migration.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base

DEFAULT_DB_URL = "sqlite:///./sales_analytics.db"

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DB_URL)

def create_db_engine(db_url: str = None):
    url = db_url or get_database_url()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(db_url: str = None):
    """
    Initializes the database schema without destroying existing data.
    Performs safe column additions if migrating from earlier schema versions.
    """
    global engine, SessionLocal
    if db_url:
        engine = create_db_engine(db_url)
        SessionLocal.configure(bind=engine)

    target_engine = engine
    Base.metadata.create_all(bind=target_engine)

    # Safe Schema Migration Check for datasets.user_id
    try:
        inspector = inspect(target_engine)
        if "datasets" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("datasets")]
            if "user_id" not in columns:
                with target_engine.begin() as conn:
                    conn.execute(text("ALTER TABLE datasets ADD COLUMN user_id VARCHAR(64)"))
    except Exception as e:
        # Log migration warning if any
        pass

@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
