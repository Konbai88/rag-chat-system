from typing import Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory
from memory.file_history_store import get_history
from services.knowlege_base import KnowledgeBaseService
from retrieval.retrieval_service import RetrievalService
from langchain_core.documents import Document


class RagService:
    """RAG 对话服务：检索 + 生成"""

    def __init__(self, knowledge_base: KnowledgeBaseService) -> None:
        self.retrieval_service = RetrievalService(knowledge_base)
        self.retrieve_and_rerank = self.retrieval_service.retrieve_and_rerank
        self.chat_model = self.retrieval_service.chat_model
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "严格依据参考资料回答。要求："
                    "1. 若资料中存在明确答案，优先引用对应页码。"
                    "2. 若资料不足以回答，明确说明'参考资料未提供足够信息'。"
                    "3. 不要编造参考资料中不存在的信息。"
                    "参考资料：{content}",
                ),
                ("system", "并且结合以下的聊天历史回答用户问题："),
                MessagesPlaceholder("chat_history"),
                ("user", "{input}"),
            ]
        )

        base_chain = self.prompt_template | self.chat_model | StrOutputParser()

        self.conversation_chain = RunnableWithMessageHistory(
            base_chain,
            get_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    @staticmethod
    def format_document(docs: list[Document]) -> str:
        """将检索到的文档列表格式化为字符串"""
        if not docs:
            return "not document."
        res = ""
        for doc in docs:
            res += (
                f"来源：{doc.metadata.get('filename')}\n"
                f"页码：{doc.metadata.get('page')}\n"
                f"内容：{doc.page_content}\n\n"
            )
        return res

    def chat(self, user_input: str, config: dict[str, Any]) -> tuple[str, list[Document]]:
        """接收用户输入，检索 + 生成回答"""
        docs = self.retrieve_and_rerank(user_input)
        content = self.format_document(docs)
        ans = self.conversation_chain.invoke(
            {"input": user_input, "content": content},
            config=config,
        )
        return ans, docs
