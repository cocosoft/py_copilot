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