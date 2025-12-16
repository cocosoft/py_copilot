from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

# 文档和标签的多对多关系表
document_tag_association = Table(
    'document_tag_association',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('knowledge_documents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('knowledge_tags.id'), primary_key=True)
)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系：一个知识库包含多个文档
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}')>"

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    vector_id = Column(String(100), nullable=True)
    
    # 关系：一个文档属于一个知识库
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    # 关系：一个文档可以有多个标签
    tags = relationship("KnowledgeTag", secondary=document_tag_association, back_populates="documents")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', file_type='{self.file_type}')>"

class KnowledgeTag(Base):
    __tablename__ = "knowledge_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 关系：一个标签可以属于多个文档
    documents = relationship("KnowledgeDocument", secondary=document_tag_association, back_populates="tags")
    
    def __repr__(self):
        return f"<KnowledgeTag(id={self.id}, name='{self.name}')>"