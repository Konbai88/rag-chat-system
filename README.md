# 🧠 RAG 智能对话系统

> 基于 LangChain 的企业级检索增强生成（RAG）系统，支持文件知识库问答、多路召回、语义重排与对话记忆。

## ✨ 功能亮点

| 特性 | 说明 |
|------|------|
| **多格式文件支持** | PDF / DOCX / TXT 文档自动解析入库 |
| **双路召回** | 向量语义搜索 + Elasticsearch 关键词搜索，RRF 算法融合 |
| **查询改写** | LLM 自动优化用户问题，提升检索命中率 |
| **语义重排** | DashScope gte-rerank 模型对召回结果精排 |
| **Parent Document 还原** | 检索到 chunk 后还原为完整原文段落 |
| **对话记忆** | 多轮对话历史持久化，支持上下文理解 |
| **多知识库隔离** | 按 kb_id 隔离不同知识库数据 |
| **中文优化** | ES IK 分词 + 中文 embedding 模型 |

## 🏗️ 系统架构

```
用户输入
    │
    ├─→ [查询改写] ──→ LLM 优化查询
    │
    ├─→ [双路召回]
    │     ├─ ChromaDB（向量检索）
    │     └─ Elasticsearch（关键词检索）
    │
    ├─→ [RRF 融合排序]
    │
    ├─→ [语义重排] ──→ gte-rerank 精排 + 置信度过滤
    │
    ├─→ [Parent 还原] ──→ 从 parent_store 还原完整段落
    │
    └─→ [LLM 生成] ──→ deepseek-r1 + 参考来源引用
```

## 🧰 技术栈

- **框架**: LangChain 1.2 · LangChain-Chroma · LangChain-Ollama
- **向量库**: ChromaDB
- **搜索引擎**: Elasticsearch 7.x（IK 中文分词）
- **Embedding**: DashScope text-embedding-v4
- **重排模型**: DashScope gte-rerank-v2
- **大模型**: deepseek-r1:7b（Ollama 本地部署）
- **前端**: Streamlit
- **文件解析**: PyMuPDF · python-docx

## 🚀 快速开始

### 前置要求

- Python 3.10+
- [Ollama](https://ollama.com/) 已安装并运行 `deepseek-r1:7b` 模型
- Elasticsearch 7.x 服务（可选，不启动时降级为仅向量检索）
- DashScope API key（阿里云通义千问）

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
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 启动

```bash
# 启动 Ollama（确保 deepseek-r1:7b 已拉取）
ollama pull deepseek-r1:7b

# 启动 Elasticsearch（可选）
# docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:7.17.0

# 启动应用
streamlit run ui/app.py
```

### 使用流程

1. 在侧边栏输入「知识库 ID」（默认 `default`）
2. 上传 PDF / DOCX / TXT 文件
3. 点击「构建向量库」将文件入库
4. 在聊天框输入问题，系统自动检索并回答

## 📁 项目结构

```
langchain_project/
├── config/              # 配置文件
│   └── config_data.py
├── parser/              # 文件解析器（PDF / DOCX）
│   ├── base.py          # 解析器抽象基类
│   ├── factory.py       # 工厂模式
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   └── models.py        # 数据模型
├── retrieval/           # 检索模块
│   ├── retrieval_service.py  # 双路召回 + 重排
│   └── reranker.py           # 语义重排器
├── search/              # ES 搜索引擎
│   ├── index_schema.py  # 索引映射定义
│   ├── indexer.py       # ES 索引写入
│   └── search_service.py     # ES 关键词检索
├── services/            # 业务服务层
│   ├── knowlege_base.py # 知识库管理
│   └── rag.py           # RAG 对话链路
├── memory/              # 对话记忆
│   └── file_history_store.py
├── utils/               # 工具类
│   ├── logger.py
│   └── md5.py
├── evaluation/          # 检索评估
│   └── evaluate.py
├── ui/                  # 前端界面
│   └── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 🔧 主要特性详解

### 双路召回（Hybrid Retrieval）

| 召回方式 | 优势 | 技术实现 |
|---------|------|---------|
| **向量检索** | 语义理解强，同义词/近义词匹配 | ChromaDB + DashScope embedding |
| **关键词检索** | 精确匹配，专有名词命中率高 | Elasticsearch + IK 分词 |
| **融合** | 两者互补，提升召回率 | RRF（Reciprocal Rank Fusion）算法 |

### 安全降级策略

- **ES 不可用** → 自动降级为纯向量检索
- **重排模型失败** → 使用粗排结果兜底
- **低分过滤** → 重排得分低于 0.05 的结果自动丢弃

## 📊 评估结果

在 Python 基础问答测试集上：

- **召回率（Hit Rate）**: 待补充
- 可通过 `python evaluation/evaluate.py` 自行评估

## 🎯 项目亮点（面试可用）

1. **企业级 RAG 架构**：查询改写 → 双路召回 → RRF 融合 → 语义重排 → Parent 还原的完整链路
2. **高可用设计**：ES 故障降级、重排失败兜底、空结果处理
3. **防重复处理**：MD5 文件指纹避免重复入库
4. **可扩展架构**：工厂模式解析器、抽象基类、多知识库隔离

## 📝 待办 / 改进方向

- [ ] 单元测试与集成测试
- [ ] Docker 容器化部署
- [ ] API 接口（FastAPI）
- [ ] 用户认证与权限管理
- [ ] 异步文件处理（大文件支持）
- [ ] Guardrails 防注入

## 🤖 CI/CD

每次推送代码到 GitHub，自动执行：

| 步骤 | 内容 |
|------|------|
| **多版本测试** | Python 3.10 / 3.11 / 3.12 三版并行 |
| **安装依赖** | `pip install -r requirements.txt` |
| **运行测试** | `pytest tests/ -v` |

> 推送后可在 GitHub 仓库的 Actions 页面查看运行结果。
> 把下面这行加到 README 顶部即可显示徽章（替换 `<OWNER>/<REPO>`）：
> `[![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml)`

## 📄 许可证

MIT
