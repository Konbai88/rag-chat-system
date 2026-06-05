"""基于 MySQL 的聊天历史存储"""
import json
from datetime import datetime

from sqlalchemy.orm import Session as DbSession
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from database.session import get_db, init_db
from database.models import ChatHistory


def get_history(session_id: str) -> "DbChatMessageHistory":
    """获取指定会话的消息历史对象"""
    init_db()
    return DbChatMessageHistory(session_id)


class DbChatMessageHistory(BaseChatMessageHistory):
    """基于 MySQL 的聊天历史（替代原来的 JSON 文件存储）"""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    @property
    def messages(self) -> list[BaseMessage]:
        """从 MySQL 加载消息历史"""
        db: DbSession = get_db()
        try:
            rows = (
                db.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .order_by(ChatHistory.id.asc())
                .all()
            )
            raw = [json.loads(r.content) for r in rows]
            return messages_from_dict(raw)
        finally:
            db.close()

    def add_messages(self, messages: list[BaseMessage]) -> None:
        """追加消息到 MySQL"""
        db: DbSession = get_db()
        try:
            for msg in messages:
                msg_dict = message_to_dict(msg)
                record = ChatHistory(
                    session_id=self.session_id,
                    role=msg_dict["type"],
                    content=json.dumps(msg_dict, ensure_ascii=False),
                    created_at=datetime.utcnow(),
                )
                db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def clear(self) -> None:
        """清空该会话的所有消息"""
        db: DbSession = get_db()
        try:
            db.query(ChatHistory).filter(
                ChatHistory.session_id == self.session_id
            ).delete()
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
