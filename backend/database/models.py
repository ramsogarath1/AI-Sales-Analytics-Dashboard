"""
SQLAlchemy Models for AI-Sales-Analytics-Dashboard.
Defines schema for User accounts, Dataset metadata, and Cache records.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserRecord(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "user_id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }

class DatasetRecord(Base):
    __tablename__ = "datasets"

    dataset_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    dataset_hash = Column(String(64), nullable=False, index=True)
    processing_status = Column(String(20), default="processed", nullable=False)
    error_message = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    def to_dict(self):
        return {
            "dataset_id": self.dataset_id,
            "user_id": self.user_id,
            "filename": self.original_filename,
            "upload_time": self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "rows": self.row_count,
            "columns": self.column_count,
            "dataset_hash": self.dataset_hash,
            "processing_status": self.processing_status,
            "error_message": self.error_message,
            "is_active": self.is_active,
        }

class CacheRecord(Base):
    __tablename__ = "caches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(64), index=True, nullable=False)
    dataset_hash = Column(String(64), index=True, nullable=False)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    cache_type = Column(String(30), nullable=False) # analytics, insights, ai_summary, ai_ask
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
