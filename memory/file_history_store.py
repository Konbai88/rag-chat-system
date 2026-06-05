import os
import json
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


def get_history(session_id: str) -> "FileChatMessageHistory":
    """获取指定会话的消息历史对象"""
    return FileChatMessageHistory(session_id, r"./chat_memory")


class FileChatMessageHistory(BaseChatMessageHistory):
    """基于文件存储的聊天历史"""

    def __init__(self, session_id: str, storage_path: str) -> None:
        self.session_id = session_id
        self.storage_path = storage_path
        self.file_path = os.path.join(self.storage_path, self.session_id)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    @property
    def messages(self) -> list[BaseMessage]:
        """从文件加载消息历史"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def add_messages(self, messages: list[BaseMessage]) -> None:
        """追加消息到历史"""
        all_messages = self.messages
        all_messages.extend(messages)
        new_messages = [message_to_dict(msg) for msg in all_messages]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(new_messages, f)

    def clear(self) -> None:
        """清空消息历史"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
