from typing import Optional
from langchain_core.documents import Document
from retrieval.reranker import DashScopeReranker
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from services.knowledge_base import KnowledgeBaseService
from search.search_service import SearchService
from utils.logger import logger
from config.config_data import ollama_base_url, ollama_model


class RetrievalService:
    """检索服务：查询改写 -> 双路召回 -> RRF 融合 -> 语义重排 -> Parent 还原"""

    def __init__(self, knowledge_base: KnowledgeBaseService) -> None:
        self.knowledge_base = knowledge_base
        self.search_service = SearchService(self.knowledge_base.search_indexer)
        self.reranker = DashScopeReranker()
        self.retriever = knowledge_base.get_retriever()
        self.rewrite_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个查询改写助手，只需要改写用户的提问，不要回答用户的问题。"
                    "请将用户问题改写成更适合知识库检索的查询。"
                    "要求："
                    "1. 保持原始语义"
                    "2. 补充可能的专业表达"
                    "3. 输出简洁"
                    "4. 不要回答问题",
                ),
                ("user", "{query}"),
            ]
        )
        self.chat_model = ChatOllama(model=ollama_model, base_url=ollama_base_url)
        self.rewrite_chain = self.rewrite_prompt | self.chat_model | StrOutputParser()

    def rewrite_query(self, query: str) -> str:
        """LLM 改写用户查询，提升检索效果"""
        return self.rewrite_chain.invoke({"query": query})

    def retrieve_and_rerank(self, query: str) -> list[Document]:
        """完整检索链路：改写 -> 双路召回 -> RRF 融合 -> 重排 -> Parent 还原"""
        logger.info("====进入正式检索函数====")
        parent_docs: list[Document] = []
        seen_parent_ids: set[str] = set()

        re_query = self.rewrite_query(query)
        logger.info(f"rewrite query: {re_query}")

        # 向量检索
        try:
            vector_docs = self.retriever.invoke(re_query)
        except Exception:
            vector_docs = []

        # ES 关键词检索
        try:
            search_docs = self.search_service.keyword_search(
                re_query, self.knowledge_base.kb_id, top_k=2
            )
        except Exception:
            search_docs = []

        def rrf_score(rank: int) -> float:
            return 1 / (rank + 60)

        score_map: dict[str, float] = {}
        for i, doc in enumerate(vector_docs):
            pid = doc.metadata.get("parent_id")
            score_map[pid] = score_map.get(pid, 0) + rrf_score(i)

        for i, doc in enumerate(search_docs):
            pid = doc.metadata.get("parent_id")
            score_map[pid] = score_map.get(pid, 0) + rrf_score(i)

        # 按融合分排序 + 去重
        all_docs = vector_docs + search_docs
        all_docs.sort(
            key=lambda x: score_map.get(x.metadata.get("parent_id"), 0), reverse=True
        )

        unique_docs: list[Document] = []
        seen_chunks: set[tuple[Optional[str], str]] = set()
        for doc in all_docs:
            chunk_key = (doc.metadata.get("parent_id"), doc.page_content)
            if chunk_key in seen_chunks:
                continue
            seen_chunks.add(chunk_key)
            unique_docs.append(doc)

        logger.info(f"粗召回总数：{len(unique_docs)}")
        unique_docs = unique_docs[:16]

        # 语义重排
        try:
            reranked_docs = self.reranker.rerank(re_query, unique_docs)
            min_score = 0.05
            reranked_docs = [
                d for d in reranked_docs if d.metadata.get("score", 0) > min_score
            ]
            logger.info(f"重排后剩余：{len(reranked_docs)}")
        except Exception as e:
            logger.warning(f"重排失败，使用兜底：{str(e)}")
            reranked_docs = unique_docs[:5]

        # Parent 还原
        for doc in reranked_docs[:5]:
            parent_id = doc.metadata.get("parent_id")
            if parent_id in seen_parent_ids:
                continue
            seen_parent_ids.add(parent_id)
            parent = self.knowledge_base.parent_store[parent_id]
            document = Document(
                page_content=parent["content"],
                metadata={
                    "parent_id": parent_id,
                    "page": parent["page"],
                    "title": parent["title"],
                    "doc_id": parent["doc_id"],
                    "filename": parent["filename"],
                    "score": doc.metadata.get("score", 0.0),
                },
            )
            parent_docs.append(document)
        return parent_docs
