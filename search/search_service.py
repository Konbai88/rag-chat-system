from langchain_core.documents import Document
from elasticsearch import Elasticsearch,ElasticsearchException
from typing import List
from config.config_data import ES_INDEX_NAME
import config.config_data as config
from utils.logger import logger


class SearchService:

    def __init__(self, indexer,es_host=config.es_host):
        self.indexer = indexer
        try:
            self.es = Elasticsearch(es_host)
        except Exception as e:
            logger.error(f"ES检索客户端初始化失败：{str(e)}")
            self.es = None

    def keyword_search(self, query, kb_id,top_k=2)->List[Document]:
        if self.es is None:
            logger.warning("ES未连接，返回空结果")
            return []
        query_body={
            "size":top_k,
            "query":{
                "bool":{
                    "must":[{"match":{"content":query}}],
                    "filter":[{"term":{"kb_id":kb_id}}]
                }
            }
        }
        try:
            response=self.es.search(index=ES_INDEX_NAME,body=query_body)
            docs=[]
            for hit in response["hits"]["hits"]:
                source=hit["_source"]
                docs.append(Document(page_content=source["content"],metadata={
                    "kb_id":source["kb_id"],
                    "doc_id":source["doc_id"],
                    "parent_id":source["parent_id"],
                    "filename":source["filename"],
                    "page":source["page"],
                    "title":source["title"]}))
            return docs
        except ElasticsearchException as e:
            logger.error(f"ES检索失败：{str(e)}")
            return []
