from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

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
    created_at: datetime
    updated_at: Optional[datetime] = None
    vector_id: Optional[str] = None
    is_vectorized: int
    
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