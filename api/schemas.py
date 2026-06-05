"""API 请求/响应数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., description="用户问题")
    kb_id: str = Field("default", description="知识库 ID")
    session_id: Optional[str] = Field(None, description="会话 ID，不传自动生成")


class SourceItem(BaseModel):
    """参考来源"""
    filename: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None
    content: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    sources: list[SourceItem]
    session_id: str


class SearchRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="检索关键词")
    kb_id: str = Field("default", description="知识库 ID")
    top_k: int = Field(5, description="返回结果数", ge=1, le=20)


class SearchResultItem(BaseModel):
    """检索结果项"""
    content: str
    filename: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None


class SearchResponse(BaseModel):
    """检索响应"""
    results: list[SearchResultItem]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
