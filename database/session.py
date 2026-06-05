"""数据库连接管理（支持 MySQL + SQLite 回退）"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool
import config.config_data as cfg

_engine = None
_Session = None
_use_sqlite = False


def _build_url() -> str:
    """构建数据库连接 URL，MySQL 不可用时回退到 SQLite"""
    global _use_sqlite
    try:
        url = (
            f"mysql+pymysql://{cfg.MYSQL_USER}:{cfg.MYSQL_PASSWORD}"
            f"@{cfg.MYSQL_HOST}:{cfg.MYSQL_PORT}/{cfg.MYSQL_DATABASE}?charset=utf8mb4"
        )
        # 快速验证连接
        test_engine = create_engine(url, connect_args={"connect_timeout": 3})
        test_engine.connect().close()
        test_engine.dispose()
        _use_sqlite = False
        return url
    except Exception:
        _use_sqlite = True
        return "sqlite:///./rag.db?check_same_thread=False"


def get_engine():
    """获取数据库引擎（单例，自动检测 MySQL 可用性）"""
    global _engine
    if _engine is None:
        url = _build_url()
        if _use_sqlite:
            _engine = create_engine(
                url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False,
            )
        else:
            _engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                echo=False,
            )
    return _engine


def get_db():
    """获取数据库会话"""
    global _Session
    if _Session is None:
        _Session = scoped_session(sessionmaker(bind=get_engine()))
    return _Session()


def init_db():
    """初始化数据库表"""
    from database.models import Base
    Base.metadata.create_all(bind=get_engine())


def close_db():
    """关闭数据库连接"""
    global _engine, _Session
    if _Session is not None:
        _Session.remove()
        _Session = None
    if _engine is not None:
        _engine.dispose()
        _engine = None
