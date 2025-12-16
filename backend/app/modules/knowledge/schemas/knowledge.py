from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class KnowledgeDocumentBase(BaseModel):
    title: str
    file_type: str
    file_path: Optional[str] = None
    content: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None

class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None

class KnowledgeDocument(KnowledgeDocumentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    vector_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    id: str
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