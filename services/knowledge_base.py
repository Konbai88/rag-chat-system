import json
import os
from io import IOBase
from typing import Optional

import config.config_data as config
from utils.md5 import check_md5, save_md5, get_string_md5, delete_md5
from utils.logger import logger
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from search.index_schema import create_index
from search.indexer import SearchIndexer


class KnowledgeBaseService:
    """知识库服务：管理文件上传、向量存储、ES 索引"""

    def __init__(self, kb_id: str = "default") -> None:
        self.kb_id = kb_id
        self.search_indexer = SearchIndexer()
        create_index(self.search_indexer.es)
        self.collection_name = f"{config.collection_name}_{kb_id}"

        os.makedirs(config.persist_directory, exist_ok=True)
        self.persist_directory = os.path.join(config.persist_directory, kb_id)
        os.makedirs(self.persist_directory, exist_ok=True)

        self.parent_store_path = os.path.join(
            config.persist_directory, kb_id, "parent_store.json"
        )
        self.parent_store = self._load_parent_store()

        self.chroma = Chroma(
            collection_name=self.collection_name,
            embedding_function=DashScopeEmbeddings(model=config.embedding_model_name),
            persist_directory=self.persist_directory,
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

    def _load_parent_store(self) -> dict[str, dict]:
        """从磁盘加载 parent_store"""
        if os.path.exists(self.parent_store_path):
            with open(self.parent_store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_parent_store(self) -> None:
        """保存 parent_store 到磁盘"""
        with open(self.parent_store_path, "w", encoding="utf-8") as f:
            json.dump(self.parent_store, f, ensure_ascii=False, indent=2)

    def get_retriever(self):
        """获取 Chroma 向量检索器"""
        return self.chroma.as_retriever(search_kwargs={"k": 2})

    def upload_file(self, uploaded_file: IOBase) -> str:
        """上传文件，解析入库"""
        from parser.factory import ParserFactory

        parser = ParserFactory.get_parser(uploaded_file)
        parsed_doc = parser.parse(uploaded_file)

        if check_md5(parsed_doc.doc_id):
            return "skip,completion."

        documents: list[Document] = []
        for section in parsed_doc.sections:
            parent_id = f"{parsed_doc.doc_id}_{section.page}"
            self.parent_store[parent_id] = {
                "content": section.content,
                "page": section.page,
                "filename": parsed_doc.filename,
                "title": section.title,
                "doc_id": parsed_doc.doc_id,
            }
            doc = Document(
                page_content=section.content,
                metadata={
                    "parent_id": parent_id,
                    "page": section.page,
                    "title": section.title,
                    "doc_id": parsed_doc.doc_id,
                    "filename": parsed_doc.filename,
                    "kb_id": self.kb_id,
                },
            )
            documents.append(doc)

        if not documents:
            return "empty document"

        knowledge_chunk = self.spliter.split_documents(documents)
        self.chroma.add_documents(knowledge_chunk)
        self.search_indexer.add_documents(self.kb_id, knowledge_chunk)

        self._save_parent_store()
        save_md5(parsed_doc.doc_id)
        return "ok,already."

    def clear_kb(self) -> bool:
        """清空当前知识库（Chroma + ES + parent_store + md5）"""
        try:
            self.chroma.delete(where={"kb_id": self.kb_id})
            self.search_indexer.clear_by_kb_id(self.kb_id)
            self.parent_store = {}
            self._save_parent_store()
            open(config.md5_path, "w", encoding="utf-8").close()
            logger.info(f"知识库 {self.kb_id} 已完全清空")
            return True
        except Exception as e:
            logger.error(f"清空失败 {str(e)}")
            return False

    def delete_file(self, filename: str) -> bool:
        """根据文件名从知识库删除"""
        try:
            parent_ids_to_del: list[str] = []
            parent_store = self._load_parent_store()
            for pid, info in parent_store.items():
                if info.get("filename") == filename:
                    parent_ids_to_del.append(pid)
            if not parent_ids_to_del:
                logger.warning(f"未找到文件：{filename}")
                return False
            for pid in parent_ids_to_del:
                self.chroma.delete(where={"parent_id": pid})
            self.search_indexer.delete_by_filename(self.kb_id, filename)
            for pid in parent_ids_to_del:
                self.parent_store.pop(pid, None)
            self._save_parent_store()

            md5_str = get_string_md5(filename)
            delete_md5(md5_str)

            logger.info(f"文件 {filename} 已从知识库 {self.kb_id} 中删除")
            return True
        except Exception as e:
            logger.error(f"删除文件失败 {str(e)}")
            return False

    def rebuild_es_index(self) -> None:
        """重建 ES 索引"""
        self.search_indexer.rebuild_index()
        logger.info("es 索引已重建")
