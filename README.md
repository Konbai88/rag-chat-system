# 🧠 RAG 智能对话系统

> 基于 LangChain 的企业级检索增强生成（RAG）系统，支持文件知识库问答、多路召回、语义重排与对话记忆�?
## �?功能亮点

| 特�?| 说明 |
|------|------|
| **多格式文件支�?* | PDF / DOCX / TXT 文档自动解析入库 |
| **双路召回** | 向量语义搜索 + Elasticsearch 关键词搜索，RRF 算法融合 |
| **查询改写** | LLM 自动优化用户问题，提升检索命中率 |
| **语义重排** | DashScope gte-rerank 模型对召回结果精�?|
| **Parent Document 还原** | 检索到 chunk 后还原为完整原文段落 |
| **对话记忆** | 多轮对话历史持久化，支持上下文理�?|
| **多知识库隔离** | �?kb_id 隔离不同知识库数�?|
| **中文优化** | ES IK 分词 + 中文 embedding 模型 |

## 🏗�?系统架构

```
用户输入
    �?    ├─�?[查询改写] ──�?LLM 优化查询
    �?    ├─�?[双路召回]
    �?    ├─ ChromaDB（向量检索）
    �?    └─ Elasticsearch（关键词检索）
    �?    ├─�?[RRF 融合排序]
    �?    ├─�?[语义重排] ──�?gte-rerank 精排 + 置信度过�?    �?    ├─�?[Parent 还原] ──�?�?parent_store 还原完整段落
    �?    └─�?[LLM 生成] ──�?deepseek-r1 + 参考来源引�?```

> [!NOTE]
> 在线查看：https://github.com/Konbai88/rag-chat-system

## 🧰 技术栈

- **框架**: LangChain 1.2 · LangChain-Chroma · LangChain-Ollama
- **向量�?*: ChromaDB
- **搜索引擎**: Elasticsearch 7.x（IK 中文分词�?- **Embedding**: DashScope text-embedding-v4
- **重排模型**: DashScope gte-rerank-v2
- **大模�?*: deepseek-r1:7b（Ollama 本地部署�?- **前端**: Streamlit
- **文件解析**: PyMuPDF · python-docx

## 🚀 快速开�?
### 前置要求

- Python 3.10+
- [Ollama](https://ollama.com/) 已安装并运行 `deepseek-r1:7b` 模型
- Elasticsearch 7.x 服务（可选，不启动时降级为仅向量检索）
- DashScope API key（阿里云通义千问�?
### 安装

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd langchain_project

# 2. 创建虚拟环境
python -m venv .venv

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你�?DASHSCOPE_API_KEY
```

### 启动

```bash
# 启动 Ollama（确�?deepseek-r1:7b 已拉取）
ollama pull deepseek-r1:7b

# 启动 Elasticsearch（可选）
# docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:7.17.0

# 启动应用
streamlit run ui/app.py
```

### 使用流程

1. 在侧边栏输入「知识库 ID」（默认 `default`�?2. 上传 PDF / DOCX / TXT 文件
3. 点击「构建向量库」将文件入库
4. 在聊天框输入问题，系统自动检索并回答

## 📁 项目结构

```
langchain_project/
├── config/              # 配置文件
�?  └── config_data.py
├── api/                 # REST API 接口
�?  ├── app.py           # FastAPI 应用
�?  └── schemas.py       # 请求/响应模型
├── parser/              # 文件解析器（PDF / DOCX�?�?  ├── base.py          # 解析器抽象基�?�?  ├── factory.py       # 工厂模式
�?  ├── pdf_parser.py
�?  ├── docx_parser.py
�?  └── models.py        # 数据模型
├── retrieval/           # 检索模�?�?  ├── retrieval_service.py  # 双路召回 + 重排
�?  └── reranker.py           # 语义重排�?├── search/              # ES 搜索引擎
�?  ├── index_schema.py  # 索引映射定义
�?  ├── indexer.py       # ES 索引写入
�?  └── search_service.py     # ES 关键词检�?├── services/            # 业务服务�?�?  ├── knowledge_base.py # 知识库管�?�?  └── rag.py           # RAG 对话链路
├── memory/              # 对话记忆
�?  └── file_history_store.py
├── utils/               # 工具�?�?  ├── logger.py
�?  └── md5.py
├── evaluation/          # 检索评�?�?  └── evaluate.py
├── ui/                  # 前端界面
�?  └── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 🔧 主要特性详�?
### 双路召回（Hybrid Retrieval�?
| 召回方式 | 优势 | 技术实�?|
|---------|------|---------|
| **向量检�?* | 语义理解强，同义�?近义词匹�?| ChromaDB + DashScope embedding |
| **关键词检�?* | 精确匹配，专有名词命中率�?| Elasticsearch + IK 分词 |
| **融合** | 两者互补，提升召回�?| RRF（Reciprocal Rank Fusion）算�?|

### 安全降级策略

- **ES 不可�?* �?自动降级为纯向量检�?- **重排模型失败** �?使用粗排结果兜底
- **低分过滤** �?重排得分低于 0.05 的结果自动丢�?
## 📊 评估结果

�?Python 基础问答测试集上�?
- **召回率（Hit Rate�?*: 待补�?- 可通过 `python evaluation/evaluate.py` 自行评估

## 🎯 项目亮点（面试可用）

1. **企业�?RAG 架构**：查询改�?�?双路召回 �?RRF 融合 �?语义重排 �?Parent 还原的完整链�?2. **高可用设�?*：ES 故障降级、重排失败兜底、空结果处理
3. **防重复处�?*：MD5 文件指纹避免重复入库
4. **可扩展架�?*：工厂模式解析器、抽象基类、多知识库隔�?
## 📝 待办 / 改进方向

- [ ] 单元测试与集成测�?- [ ] Docker 容器化部�?- [ ] API 接口（FastAPI�?- [ ] 用户认证与权限管�?- [ ] 异步文件处理（大文件支持�?- [ ] Guardrails 防注�?
## 🌐 REST API

除了 Streamlit 前端，项目还提供了 FastAPI REST 接口，方便集成到其他系统。

### 启动 API 服务

```bash
# 方式一：直接运行
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# 方式二：Docker（会自动启动 API + Streamlit 两个端口）
docker compose up -d
```

API 文档（启动后浏览器打开）：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/chat` | RAG 对话 |
| `POST` | `/api/search` | 知识库检索（纯检索，不走 LLM） |
| `POST` | `/api/knowledge-bases/{kb_id}/upload` | 上传文件 |
| `DELETE` | `/api/knowledge-bases/{kb_id}` | 清空知识库 |
| `DELETE` | `/api/knowledge-bases/{kb_id}/files/{filename}` | 删除文件 |
| `GET` | `/api/knowledge-bases/{kb_id}` | 知识库状态 |

### 使用示例

```bash
# 对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Python 怎么打印？", "kb_id": "default"}'

# 上传文件
curl -X POST http://localhost:8000/api/knowledge-bases/default/upload \
  -F "file=@document.pdf"

# 搜索
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "变量定义", "top_k": 3}'
```

## 🤖 CI/CD

每次推送代码到 GitHub，自动执行：

| 步骤 | 内容 |
|------|------|
| **多版本测�?* | Python 3.10 / 3.11 / 3.12 三版并行 |
| **安装依赖** | `pip install -r requirements.txt` |
| **运行测试** | `pytest tests/ -v` |

> 推送后可在 GitHub 仓库�?Actions 页面查看运行结果�?> 当前项目徽章：[![CI](https://github.com/Konbai88/rag-chat-system/actions/workflows/ci.yml/badge.svg)](https://github.com/Konbai88/rag-chat-system/actions/workflows/ci.yml)

## 📄 许可�?
MIT
