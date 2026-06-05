import os

# ========== 路径 ==========
md5_path = os.getenv("MD5_PATH", "./md5.text")
persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# ========== 向量库 ==========
collection_name = "rag"
chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
separators = ['\n\n','\n','.','!','?','。','！','？',' ','']
top_k = int(os.getenv("TOP_K", "2"))

# ========== 模型 ==========
embedding_model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
rerank_model_name = os.getenv("RERANK_MODEL", "gte-rerank-v2")

# ========== LLM（Ollama） ==========
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")

# ========== 搜索引擎 ==========
es_host = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX_NAME = "knowlege_index"

# ========== MySQL 数据库 ==========
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "rag")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "rag_password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rag_db")
