import os
from io import IOBase
from typing import Optional

from sqlalchemy.orm import Session as DbSession

import config.config_data as config
from utils.md5 import check_md5, save_md5, get_string_md5, delete_md5
from utils.logger import logger
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from search.index_schema import create_index
from search.indexer import SearchIndexer
from database.session import get_db, init_db
from database.models import ParentStore, FileRecord


class KnowledgeBaseService:
    """知识库服务：管理文件上传、向量存储、ES 索引（MySQL 持久化）"""

    def __init__(self, kb_id: str = "default") -> None:
        self.kb_id = kb_id
        init_db()  # 确保表已创建

        self.search_indexer = SearchIndexer()
        create_index(self.search_indexer.es)
        self.collection_name = f"{config.collection_name}_{kb_id}"

        # Chroma 本地存储目录
        os.makedirs(config.persist_directory, exist_ok=True)
        self.persist_directory = os.path.join(config.persist_directory, kb_id)
        os.makedirs(self.persist_directory, exist_ok=True)

        # parent_store 从 MySQL 加载到内存（提高检索时读取性能）
        self.parent_store: dict[str, dict] = self._load_parent_store()

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

    # ── Parent Store (MySQL) ──────────────────────────────────

    def _load_parent_store(self) -> dict[str, dict]:
        """从 MySQL 加载当前知识库的全部 parent_store 到内存"""
        store: dict[str, dict] = {}
        db: DbSession = get_db()
        try:
            rows = (
                db.query(ParentStore)
                .filter(ParentStore.kb_id == self.kb_id)
                .all()
            )
            for row in rows:
                store[row.parent_id] = {
                    "content": row.content,
                    "page": row.page,
                    "filename": row.filename,
                    "title": row.title or "",
                    "doc_id": row.doc_id,
                }
            logger.info(f"从 MySQL 加载 parent_store：{len(rows)} 条")
            return store
        finally:
            db.close()

    def _insert_parent(self, parent_id: str, data: dict) -> None:
        """插入一条 parent 记录到 MySQL"""
        db: DbSession = get_db()
        try:
            record = ParentStore(
                kb_id=self.kb_id,
                parent_id=parent_id,
                content=data["content"],
                page=data["page"],
                filename=data["filename"],
                title=data.get("title", ""),
                doc_id=data["doc_id"],
            )
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _delete_parents_by_ids(self, parent_ids: list[str]) -> None:
        """根据 parent_id 列表删除 MySQL 记录"""
        db: DbSession = get_db()
        try:
            db.query(ParentStore).filter(
                ParentStore.kb_id == self.kb_id,
                ParentStore.parent_id.in_(parent_ids),
            ).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _delete_all_parents(self) -> None:
        """删除当前知识库的所有 parent 记录"""
        db: DbSession = get_db()
        try:
            db.query(ParentStore).filter(
                ParentStore.kb_id == self.kb_id
            ).delete()
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── 文件记录 (MySQL, 替代 md5.text) ──────────────────────

    def _save_file_record(self, md5: str, filename: str) -> None:
        """记录已入库的文件"""
        db: DbSession = get_db()
        try:
            record = FileRecord(kb_id=self.kb_id, md5=md5, filename=filename)
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def _check_file_record(self, md5: str) -> bool:
        """检查文件是否已入库"""
        db: DbSession = get_db()
        try:
            return (
                db.query(FileRecord)
                .filter(FileRecord.kb_id == self.kb_id, FileRecord.md5 == md5)
                .first()
                is not None
            )
        finally:
            db.close()

    def _delete_file_record(self, md5: str) -> None:
        """删除文件入库记录"""
        db: DbSession = get_db()
        try:
            db.query(FileRecord).filter(
                FileRecord.kb_id == self.kb_id, FileRecord.md5 == md5
            ).delete()
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    # ── 公共方法 ──────────────────────────────────────────────

    def get_retriever(self):
        """获取 Chroma 向量检索器"""
        return self.chroma.as_retriever(search_kwargs={"k": 2})

    def upload_file(self, uploaded_file: IOBase) -> str:
        """上传文件，解析入库"""
        from parser.factory import ParserFactory

        parser = ParserFactory.get_parser(uploaded_file)
        parsed_doc = parser.parse(uploaded_file)

        doc_md5 = parsed_doc.doc_id
        if self._check_file_record(doc_md5):
            return "skip,completion."

        documents: list[Document] = []
        for section in parsed_doc.sections:
            parent_id = f"{parsed_doc.doc_id}_{section.page}"
            parent_data = {
                "content": section.content,
                "page": section.page,
                "filename": parsed_doc.filename,
                "title": section.title,
                "doc_id": parsed_doc.doc_id,
            }
            # 写入内存 + MySQL
            self.parent_store[parent_id] = parent_data
            self._insert_parent(parent_id, parent_data)

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

        self._save_file_record(doc_md5, parsed_doc.filename)
        return "ok,already."

    def clear_kb(self) -> bool:
        """清空当前知识库（Chroma + ES + MySQL + md5.text）"""
        try:
            self.chroma.delete(where={"kb_id": self.kb_id})
            self.search_indexer.clear_by_kb_id(self.kb_id)
            self.parent_store = {}
            self._delete_all_parents()
            open(config.md5_path, "w", encoding="utf-8").close()
            logger.info(f"知识库 {self.kb_id} 已完全清空")
            return True
        except Exception as e:
            logger.error(f"清空失败 {str(e)}")
            return False

    def delete_file(self, filename: str) -> bool:
        """根据文件名从知识库删除"""
        try:
            # 找到该文件的所有 parent_id
            parent_ids_to_del = [
                pid for pid, info in self.parent_store.items()
                if info.get("filename") == filename
            ]
            if not parent_ids_to_del:
                logger.warning(f"未找到文件：{filename}")
                return False

            for pid in parent_ids_to_del:
                self.chroma.delete(where={"parent_id": pid})
            self.search_indexer.delete_by_filename(self.kb_id, filename)

            # 从内存和 MySQL 删除
            for pid in parent_ids_to_del:
                self.parent_store.pop(pid, None)
            self._delete_parents_by_ids(parent_ids_to_del)

            md5_str = get_string_md5(filename)
            self._delete_file_record(md5_str)
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
