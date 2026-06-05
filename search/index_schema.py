from dataclasses import dataclass
from elasticsearch import Elasticsearch,ElasticsearchException
from config.config_data import ES_INDEX_NAME
from utils.logger import logger


def create_index(es:Elasticsearch):
    if es is None:
        logger.warning("ES未连接，跳过索引创建")
        return
    mapping={
        "settings":{
            "number_of_shards":1,
            "number_of_replicas": 0,
            "analysis":{
                "analyzer": {
                    "ik_analyzer":{
                        "type":"custom",
                        "tokenizer":"ik_max_word"
                    }
                }
            }
        },
        "mappings":{
            "properties":{
                "kb_id":{"type":"keyword"},
                "parent_id":{"type": "keyword"},
                "filename":{"type": "keyword"},
                "page":{"type":"integer"},
                "title":{"type": "text","analyzer":"ik_analyzer"},
                "content":{"type": "text","analyzer":"ik_analyzer"}
            }
        }
    }
    try:
        if not es.indices.exists(index=ES_INDEX_NAME):
            es.indices.create(index=ES_INDEX_NAME, body=mapping)
            logger.info(f"索引 {ES_INDEX_NAME} 创建成功")
        else:
            logger.info(f"索引 {ES_INDEX_NAME} 已存在")
    except ElasticsearchException as e:
        logger.error(f"ES索引创建失败：{str(e)}")
