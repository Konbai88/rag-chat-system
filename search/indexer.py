from config.config_data import ES_INDEX_NAME
from elasticsearch import Elasticsearch,helpers,ElasticsearchException
from langchain_core.documents import Document
from typing import Dict
from search.index_schema import create_index
import config.config_data as config
from utils.logger import logger


class SearchIndexer:

    def __init__(self,es_host=config.es_host):
        try:
            self.es = Elasticsearch(es_host)
            if not self.es.ping():
                raise ConnectionError("ES服务连接失败，请检查服务是否启动")
        except Exception as e:
            logger.error(f"ES客户端初始化失败：{str(e)}")
            self.es = None

    def add_documents(self,kb_id:str,documents: list[Document]):
        if self.es is None:
            logger.warning("ES未连接，跳过ES索引写入")
            return
        actions=[]
        for doc in documents:
            meta=doc.metadata
            action={
                "_index":ES_INDEX_NAME,
                "_id":f"{meta.get("doc_id"," ")}_{meta.get("parent_id"," ")}",
                "_source":{
                    "kb_id":kb_id,
                    "doc_id":meta.get("doc_id"," "),
                    "parent_id":meta.get("parent_id"," "),
                    "filename":meta.get("filename"," "),
                    "page":meta.get("page",0),
                    "title":meta.get("title"," "),
                    "content":doc.page_content
                }
            }
            actions.append(action)
        try:
            if actions:
                helpers.bulk(self.es,actions)
                logger.info(f"成功写入 {len(actions)} 条数据到ES")
        except ElasticsearchException as e:
            logger.error(f"ES批量写入失败：{str(e)}")

    def clear_by_kb_id(self, kb_id):
        if self.es is None:
            logger.warning("ES未连接，跳过清空")
            return
        try:
            self.es.delete_by_query(
                index=ES_INDEX_NAME,
                body={"query": {"term": {"kb_id": kb_id}}}
            )
        except ElasticsearchException as e:
            logger.error(f"ES清空失败：{str(e)}")

    def delete_by_filename(self, kb_id, filename):
        if self.es is None:
            logger.warning("ES未连接，跳过删除")
            return
        try:
            self.es.delete_by_query(
                index=ES_INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"kb_id": kb_id}},
                                {"term": {"filename": filename}}
                            ]
                        }
                    }
                }
            )
        except ElasticsearchException as e:
            logger.error(f"ES删除文件失败：{str(e)}")

    def rebuild_index(self):
        if self.es is None:
            logger.warning("ES未连接，跳过重建索引")
            return
        try:
            if self.es.indices.exists(index=ES_INDEX_NAME):
                self.es.indices.delete(index=ES_INDEX_NAME)
            create_index(self.es)
        except ElasticsearchException as e:
            logger.error(f"ES重建索引失败：{str(e)}")
