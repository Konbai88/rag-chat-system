"""memory/file_history_store 的单元测试"""
import os
import json
import tempfile
from memory.file_history_store import FileChatMessageHistory, get_history
from langchain_core.messages import HumanMessage, AIMessage


class TestFileChatMessageHistory:
    """测试文件型聊天历史存储"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.session_id = "test_session_001"
        self.history = FileChatMessageHistory(self.session_id, self.temp_dir)

    def teardown_method(self):
        # 清理临时文件
        file_path = os.path.join(self.temp_dir, self.session_id)
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(self.temp_dir)

    def test_empty_history(self):
        """新会话应返回空列表"""
        assert self.history.messages == []

    def test_add_and_retrieve_messages(self):
        msg1 = HumanMessage(content="你好")
        msg2 = AIMessage(content="你好！有什么可以帮助你的？")
        self.history.add_messages([msg1, msg2])
        messages = self.history.messages
        assert len(messages) == 2
        assert messages[0].content == "你好"
        assert isinstance(messages[0], HumanMessage)
        assert messages[1].content == "你好！有什么可以帮助你的？"
        assert isinstance(messages[1], AIMessage)

    def test_messages_persist_across_instances(self):
        """消息应持久化到文件，新建实例也能读取"""
        msg = HumanMessage(content="持久化测试")
        self.history.add_messages([msg])

        new_history = FileChatMessageHistory(self.session_id, self.temp_dir)
        messages = new_history.messages
        assert len(messages) == 1
        assert messages[0].content == "持久化测试"

    def test_clear_history(self):
        self.history.add_messages([HumanMessage(content="测试")])
        assert len(self.history.messages) == 1
        self.history.clear()
        assert self.history.messages == []

    def test_get_history_function(self):
        history = get_history("test_func_session")
        assert history is not None
        assert history.session_id == "test_func_session"
        # 清理
        file_path = os.path.join(r"./chat_memory", "test_func_session")
        if os.path.exists(file_path):
            os.remove(file_path)
