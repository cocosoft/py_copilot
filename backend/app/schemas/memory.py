from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class MemoryBase(BaseModel):
    """记忆基础模型"""
    title: Optional[str] = None
    content: str
    memory_type: str  # SHORT_TERM, LONG_TERM, SEMANTIC, PROCEDURAL
    memory_category: Optional[str] = None  # CONVERSATION, KNOWLEDGE, PREFERENCE, CONTEXT
    summary: Optional[str] = None
    importance_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    memory_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    source_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class MemoryCreate(MemoryBase):
    """创建记忆请求模型"""
    # 与现有系统的关联字段
    source_type: Optional[str] = None  # CONVERSATION, KNOWLEDGE_BASE, DOCUMENT, USER_INPUT
    source_id: Optional[int] = None  # 对应现有系统中的记录ID
    source_reference: Optional[Dict[str, Any]] = None  # 额外引用信息


class MemoryUpdate(BaseModel):
    """更新记忆请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    memory_type: Optional[str] = None
    memory_category: Optional[str] = None
    summary: Optional[str] = None
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    memory_metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    source_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class MemoryResponse(MemoryBase):
    """记忆响应模型"""
    id: int
    user_id: int
    access_count: int
    last_accessed: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    embedding: Optional[List[float]] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_reference: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        exclude = {"_sa_instance_state"}  # 排除SQLAlchemy内部状态
        
    @validator("memory_metadata", pre=True)  # 在验证前处理memory_metadata
    def validate_memory_metadata(cls, v):
        if hasattr(v, "__class__") and v.__class__.__name__ == "MetaData":
            # 如果是Base.metadata对象，返回None或空字典
            return None
        return v


class MemorySearchRequest(BaseModel):
    """记忆搜索请求模型"""
    query: str
    memory_types: Optional[List[str]] = None
    memory_categories: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    session_id: Optional[str] = None
    context_ids: Optional[List[int]] = None


class MemoryStats(BaseModel):
    """记忆统计模型"""
    total_count: int
    by_type: Dict[str, int]
    by_category: Dict[str, int]
    active_count: int
    total_access_count: int
    average_importance: float
    time_range: str
    vector_db_count: Optional[int] = Field(default=0)


class MemoryStatsResponse(MemoryStats):
    """记忆统计响应模型"""
    class Config:
        from_attributes = True


class MemoryPatterns(BaseModel):
    """记忆模式模型"""
    temporal_patterns: Dict[str, Any]
    topic_patterns: List[Dict[str, Any]]
    access_patterns: Dict[str, Any]
    association_patterns: List[Dict[str, Any]]


class MemoryPatternsResponse(MemoryPatterns):
    """记忆模式响应模型"""
    class Config:
        from_attributes = True


class UserMemoryConfigBase(BaseModel):
    """用户记忆配置基础模型"""
    short_term_retention_days: Optional[int] = Field(default=7, ge=1)
    long_term_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    auto_cleanup_enabled: Optional[bool] = Field(default=True)
    privacy_level: Optional[str] = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH
    sync_enabled: Optional[bool] = Field(default=False)
    preferred_embedding_model: Optional[str] = Field(default="text-embedding-ada-002")


class UserMemoryConfigCreate(UserMemoryConfigBase):
    """创建用户记忆配置请求模型"""
    pass


class UserMemoryConfigUpdate(UserMemoryConfigBase):
    """更新用户记忆配置请求模型"""
    pass


class UserMemoryConfigResponse(UserMemoryConfigBase):
    """用户记忆配置响应模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnhancedSearchRequest(BaseModel):
    """增强搜索请求模型"""
    query: str
    knowledge_base_id: Optional[int] = None
    use_memory: bool = Field(default=True)
    limit: int = Field(default=10, ge=1, le=100)


class EnhancedSearchResponse(BaseModel):
    """增强搜索响应模型"""
    query: str
    results: List[Dict[str, Any]]
    memory_used: bool
    knowledge_base_used: bool = False
    total_results: int
    session_id: Optional[str] = None