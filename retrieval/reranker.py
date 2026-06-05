from typing import Optional
from dashscope import TextReRank
from config.config_data import rerank_model_name
from langchain_core.documents import Document


class DashScopeReranker:
    """基于 DashScope 的语义重排器"""

    def rerank(
        self, query: str, docs: list[Document], top_k: int = 3
    ) -> list[Document]:
        """对粗排结果进行语义重排，返回 top_k 个最高分文档"""
        if not docs:
            return []
        texts = [doc.page_content for doc in docs]
        response = TextReRank.call(
            model=rerank_model_name, query=query, documents=texts
        )
        reranked_docs: list[Document] = []
        for result in response.output.results:
            idx = result.index
            rel_score = result.relevance_score
            doc = docs[idx]
            doc.metadata["score"] = round(rel_score, 2)
            reranked_docs.append(doc)
        return reranked_docs[:top_k]
