from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Document Processing Status Enum
class DocumentProcessingStatus(str, Enum):
    """文档处理状态枚举"""
    # 核心状态
    IDLE = "idle"  # 待处理
    PROCESSING = "processing"  # 处理中
    TEXT_EXTRACTED = "text_extracted"  # 文本提取完成
    CHUNKED = "chunked"  # 切片完成
    ENTITY_EXTRACTED = "entity_extracted"  # 实体提取完成
    VECTORIZED = "vectorized"  # 向量化完成
    GRAPH_BUILT = "graph_built"  # 知识图谱构建完成
    COMPLETED = "completed"  # 处理完成
    FAILED = "failed"  # 处理失败
    
    # 失败状态细分
    TEXT_EXTRACTION_FAILED = "text_extraction_failed"  # 文本提取失败
    CHUNKING_FAILED = "chunking_failed"  # 切片失败
    ENTITY_EXTRACTION_FAILED = "entity_extraction_failed"  # 实体提取失败
    VECTORIZATION_FAILED = "vectorization_failed"  # 向量化失败
    GRAPH_BUILDING_FAILED = "graph_building_failed"  # 知识图谱构建失败


# Document Processing Stage Enum
class ProcessingStage(str, Enum):
    """处理阶段枚举"""
    TEXT_EXTRACTED = "text_extracted"
    CHUNKED = "chunked"
    ENTITY_EXTRACTED = "entity_extracted"
    VECTORIZED = "vectorized"
    GRAPH_BUILT = "graph_built"

# Knowledge Base Schemas
class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class KnowledgeBase(KnowledgeBaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Knowledge Document Schemas
class KnowledgeDocumentBase(BaseModel):
    title: str
    file_type: str
    knowledge_base_id: int
    file_path: Optional[str] = None
    content: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None

class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None
    knowledge_base_id: Optional[int] = None

class KnowledgeDocument(KnowledgeDocumentBase):
    id: int
    uuid: Optional[str] = None  # 文档全局唯一UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    vector_id: Optional[str] = None
    # is_vectorized 已移除，使用 document_metadata['processing_status'] 替代
    file_hash: Optional[str] = None  # 文件内容哈希，用于去重

    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    id: Union[int, str]
    title: str
    content: str
    score: float
    
    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    count: int

class DocumentListResponse(BaseModel):
    documents: List[KnowledgeDocument]
    skip: int
    limit: int
    total: int

# Knowledge Tag Schemas
class KnowledgeTagBase(BaseModel):
    name: str

class KnowledgeTagCreate(KnowledgeTagBase):
    pass

class KnowledgeTag(KnowledgeTagBase):
    id: int
    created_at: datetime
    document_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class KnowledgeTagWithCount(KnowledgeTag):
    document_count: int

class TagListResponse(BaseModel):
    tags: List[KnowledgeTag]
    total: int

class DocumentTagRequest(BaseModel):
    tag_name: str

class DocumentTagsResponse(BaseModel):
    document_id: int
    tags: List[KnowledgeTag]

# Advanced Search Schemas
class AdvancedSearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 10
    knowledge_base_id: Optional[int] = None
    tags: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = "relevance"
    entity_filter: Optional[Dict[str, Any]] = None

class HybridSearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 10
    keyword_weight: Optional[float] = 0.3
    vector_weight: Optional[float] = 0.7
    knowledge_base_id: Optional[int] = None
    tags: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = "relevance"

class AdvancedSearchResult(BaseModel):
    id: Union[int, str]
    title: str
    content: str
    score: float
    keyword_score: Optional[float] = None
    vector_score: Optional[float] = None
    knowledge_base_id: Optional[int] = None
    file_type: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class AdvancedSearchResponse(BaseModel):
    query: str
    results: List[AdvancedSearchResult]
    count: int
    search_type: str

# Semantic Search Schemas
class SemanticSearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 10
    knowledge_base_id: Optional[int] = None
    use_entities: Optional[bool] = True
    use_synonyms: Optional[bool] = True
    boost_recent: Optional[bool] = True
    semantic_boost: Optional[float] = 0.3

class SearchSuggestionRequest(BaseModel):
    query: str
    n_suggestions: Optional[int] = 5
    knowledge_base_id: Optional[int] = None

class SearchSuggestion(BaseModel):
    suggestion: str
    score: float
    type: str  # "synonym", "expansion", "correction"

class SearchSuggestionResponse(BaseModel):
    query: str
    suggestions: List[SearchSuggestion]
    count: int

class SearchAnalysis(BaseModel):
    query_complexity: str  # "simple", "medium", "complex"
    entity_usage: bool
    synonym_usage: bool
    semantic_boost: float
    result_quality: str  # "high", "medium", "low"
    suggestions: List[str]

class SearchAnalysisResponse(BaseModel):
    query: str
    analysis: SearchAnalysis
    recommendations: List[str]

# Document Processing Status Schemas
class DocumentProcessingStages(BaseModel):
    """文档处理阶段状态"""
    text_extracted: bool = False
    chunked: bool = False
    entity_extracted: bool = False
    vectorized: bool = False
    graph_built: bool = False


class DocumentProcessingTimestamps(BaseModel):
    """文档处理时间戳"""
    uploaded_at: Optional[datetime] = None
    text_extracted_at: Optional[datetime] = None
    chunked_at: Optional[datetime] = None
    entity_extracted_at: Optional[datetime] = None
    vectorized_at: Optional[datetime] = None
    graph_built_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class DocumentProcessingStats(BaseModel):
    """文档处理统计信息"""
    chunks_count: Optional[int] = 0
    entities_count: Optional[int] = 0
    relationships_count: Optional[int] = 0
    vectorization_rate: Optional[float] = 0.0
    graph_nodes: Optional[int] = 0
    graph_edges: Optional[int] = 0


class DocumentProcessingStatusResponse(BaseModel):
    """文档处理状态响应"""
    document_id: int
    processing_status: DocumentProcessingStatus
    stages: DocumentProcessingStages
    timestamps: Optional[DocumentProcessingTimestamps] = None
    stats: Optional[DocumentProcessingStats] = None
    error_info: Optional[str] = None
    message: Optional[str] = None


# Knowledge Document Chunk Schemas
class KnowledgeDocumentChunk(BaseModel):
    id: int
    document_id: int
    chunk_text: str
    chunk_index: int
    total_chunks: int
    chunk_metadata: Optional[Dict[str, Any]] = None
    vector_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Knowledge Graph API Schemas
class EntityExtractionRequest(BaseModel):
    text: str
    language: Optional[str] = "zh"

class EntityExtractionResponse(BaseModel):
    entities: List[Dict[str, Any]]

class KeywordExtractionRequest(BaseModel):
    text: str
    language: Optional[str] = "zh"
    max_keywords: Optional[int] = 10

class KeywordExtractionResponse(BaseModel):
    keywords: List[Dict[str, Any]]

class TextSimilarityRequest(BaseModel):
    text1: str
    text2: str

class TextSimilarityResponse(BaseModel):
    similarity: float

class TextProcessingRequest(BaseModel):
    text: str
    operation: str  # "clean", "chunk", "entities", "keywords"
    language: Optional[str] = "zh"

class TextProcessingResponse(BaseModel):
    result: Union[str, List[str], List[Dict[str, Any]]]
    operation: str



class DocumentChunkRequest(BaseModel):
    document_id: int
    chunk_size: Optional[int] = 1000

class DocumentChunkResponse(BaseModel):
    document_id: int
    chunks: List[str]
    total_chunks: int

# Knowledge Document Chunk Schemas
class KnowledgeDocumentChunk(BaseModel):
    """知识库文档向量片段模型"""
    id: str
    title: str
    content: str
    chunk_index: int
    total_chunks: int
    
    class Config:
        from_attributes = True


# Knowledge Base Permission Schemas
class KnowledgeBasePermissionBase(BaseModel):
    """知识库权限基础模型"""
    user_id: int
    role: str  # admin, editor, viewer


class KnowledgeBasePermissionCreate(BaseModel):
    """创建知识库权限请求模型"""
    user_id: int
    role: str = "viewer"  # admin, editor, viewer


class KnowledgeBasePermissionUpdate(BaseModel):
    """更新知识库权限请求模型"""
    role: str


class KnowledgeBasePermission(KnowledgeBasePermissionBase):
    """知识库权限响应模型"""
    id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class KnowledgeBasePermissionListResponse(BaseModel):
    """知识库权限列表响应模型"""
    permissions: List[KnowledgeBasePermission]
    total: int


class KnowledgeBasePermissionsUpdateRequest(BaseModel):
    """批量更新知识库权限请求模型"""
    permissions: List[KnowledgeBasePermissionCreate]