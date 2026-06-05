"""FastAPI 应用：REST API 接口"""
import uuid
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ChatRequest, ChatResponse, SourceItem,
    SearchRequest, SearchResponse, SearchResultItem,
    HealthResponse,
)
from services.knowledge_base import KnowledgeBaseService
from services.rag import RagService

# ===================== 应用初始化 =====================

app = FastAPI(
    title="RAG API",
    description="基于 LangChain 的 RAG 智能对话系统 REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 服务实例缓存 =====================

_kb_services: dict[str, KnowledgeBaseService] = {}
_rag_services: dict[str, RagService] = {}


def _get_services(kb_id: str):
    """获取或创建知识库和 RAG 服务实例"""
    if kb_id not in _kb_services:
        _kb_services[kb_id] = KnowledgeBaseService(kb_id)
        _rag_services[kb_id] = RagService(_kb_services[kb_id])
    return _kb_services[kb_id], _rag_services[kb_id]


# ===================== 健康检查 =====================


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """服务健康检查"""
    return HealthResponse(status="ok", version="1.0.0")


# ===================== 聊天 =====================


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """RAG 对话：检索知识库 + LLM 生成回答"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    kb, rag = _get_services(request.kb_id)
    session_id = request.session_id or str(uuid.uuid4())

    config = {"configurable": {"session_id": session_id}}
    answer, docs = rag.chat(request.query, config=config)

    sources = [
        SourceItem(
            filename=d.metadata.get("filename"),
            page=d.metadata.get("page"),
            score=d.metadata.get("score"),
            content=d.page_content,
        )
        for d in docs
    ]

    return ChatResponse(answer=answer, sources=sources, session_id=session_id)


# ===================== 知识库检索（纯检索，不走 LLM） =====================


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """知识库检索：双路召回 + 重排，返回原文片段"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    kb, rag = _get_services(request.kb_id)
    docs = rag.retrieve_and_rerank(request.query)

    results = [
        SearchResultItem(
            content=d.page_content,
            filename=d.metadata.get("filename"),
            page=d.metadata.get("page"),
            score=d.metadata.get("score"),
        )
        for d in docs[:request.top_k]
    ]

    return SearchResponse(results=results)


# ===================== 文件上传 =====================


@app.post("/api/knowledge-bases/{kb_id}/upload")
def upload_file(kb_id: str, file: UploadFile = File(...)):
    """上传文件到指定知识库（PDF / DOCX / TXT）"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    allowed = (".pdf", ".docx", ".txt")
    if not any(file.filename.lower().endswith(ext) for ext in allowed):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持 {', '.join(allowed)}",
        )

    kb, _ = _get_services(kb_id)
    try:
        result = kb.upload_file(file.file)
        return {"result": result, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== 知识库管理 =====================


@app.delete("/api/knowledge-bases/{kb_id}")
def clear_knowledge_base(kb_id: str):
    """清空指定知识库的所有数据"""
    kb, _ = _get_services(kb_id)
    ok = kb.clear_kb()
    if not ok:
        raise HTTPException(status_code=500, detail="清空失败")
    return {"result": True, "kb_id": kb_id}


@app.delete("/api/knowledge-bases/{kb_id}/files/{filename:path}")
def delete_file(kb_id: str, filename: str):
    """从知识库中删除指定文件"""
    kb, _ = _get_services(kb_id)
    ok = kb.delete_file(filename)
    if not ok:
        raise HTTPException(status_code=404, detail=f"文件 {filename} 未找到")
    return {"result": True, "filename": filename}


@app.get("/api/knowledge-bases/{kb_id}")
def get_knowledge_base(kb_id: str):
    """获取知识库状态"""
    kb, _ = _get_services(kb_id)
    file_count = len(kb.parent_store)
    return {
        "kb_id": kb_id,
        "status": "active",
        "total_documents": file_count,
    }
