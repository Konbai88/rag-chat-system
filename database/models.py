"""SQLAlchemy ORM 数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class ChatHistory(Base):
    """对话历史表"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False, comment="user / assistant")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_session_time", "session_id", "created_at"),
    )


class ParentStore(Base):
    """父文档存储表（chunk -> 原文段落映射）"""
    __tablename__ = "parent_store"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(String(64), nullable=False, index=True)
    parent_id = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    page = Column(Integer, default=0)
    filename = Column(String(255), default="")
    title = Column(String(255), default="", nullable=True)
    doc_id = Column(String(128), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("kb_id", "parent_id", name="uq_kb_parent"),
        Index("idx_kb_filename", "kb_id", "filename"),
    )


class FileRecord(Base):
    """已入库文件记录（替代 md5.text）"""
    __tablename__ = "file_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(String(64), nullable=False, index=True)
    md5 = Column(String(32), nullable=False)
    filename = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("kb_id", "md5", name="uq_kb_md5"),
    )
