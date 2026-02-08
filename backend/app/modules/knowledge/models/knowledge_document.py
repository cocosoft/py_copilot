from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Table, Boolean, Float
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
    is_vectorized = Column(Integer, nullable=False, default=0)  # 0: 未向量化, 1: 已向量化
    version = Column(Integer, default=1)  # 文档版本
    is_current = Column(Boolean, nullable=False, default=True)  # 是否为当前版本 (True: 是, False: 历史版本)
    
    # 关系：一个文档属于一个知识库
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    # 关系：一个文档可以有多个标签
    tags = relationship("KnowledgeTag", secondary=document_tag_association, back_populates="documents")
    # 关系：一个文档包含多个实体
    entities = relationship("DocumentEntity", back_populates="document", cascade="all, delete-orphan")
    # 关系：一个文档包含多个向量片段
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
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


class DocumentEntity(Base):
    """文档实体模型"""
    __tablename__ = "document_entities"
    
    id = Column(Integer, primary_key=True, index=True)  # 实体ID
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)  # 所属文档ID
    entity_text = Column(String(200), nullable=False)  # 实体文本
    entity_type = Column(String(50), nullable=False)  # 实体类型 (如: PERSON, ORG, LOC)
    start_pos = Column(Integer, nullable=False)  # 实体在文档中的起始位置
    end_pos = Column(Integer, nullable=False)  # 实体在文档中的结束位置
    confidence = Column(Float, nullable=False, default=0.0)  # 识别置信度
    created_at = Column(DateTime, nullable=False, default=func.now())  # 创建时间
    
    # 关系：一个实体属于一个文档
    document = relationship("KnowledgeDocument", back_populates="entities")
    
    def __repr__(self):
        return f"<DocumentEntity(id={self.id}, entity_text='{self.entity_text}', entity_type='{self.entity_type}')>"


class EntityRelationship(Base):
    """实体关系模型"""
    __tablename__ = "entity_relationships"
    
    id = Column(Integer, primary_key=True, index=True)  # 关系ID
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)  # 所属文档ID
    source_id = Column(Integer, ForeignKey("document_entities.id"), nullable=False)  # 源实体ID
    target_id = Column(Integer, ForeignKey("document_entities.id"), nullable=False)  # 目标实体ID
    relationship_type = Column(String(100), nullable=False)  # 关系类型
    confidence = Column(Float, nullable=False, default=0.0)  # 识别置信度
    created_at = Column(DateTime, nullable=False, default=func.now())  # 创建时间
    
    # 关系：一个关系属于一个文档
    document = relationship("KnowledgeDocument")
    # 关系：源实体
    source_entity = relationship("DocumentEntity", foreign_keys=[source_id])
    # 关系：目标实体
    target_entity = relationship("DocumentEntity", foreign_keys=[target_id])
    
    def __repr__(self):
        return f"<EntityRelationship(id={self.id}, type='{self.relationship_type}')>"


class DocumentChunk(Base):
    """文档向量片段模型"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)  # 片段ID
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)  # 所属文档ID
    chunk_text = Column(Text, nullable=False)  # 片段内容
    chunk_index = Column(Integer, nullable=False)  # 片段索引
    total_chunks = Column(Integer, nullable=False)  # 总片段数
    chunk_metadata = Column(JSON, nullable=True)  # 片段元数据
    vector_id = Column(String(100), nullable=True)  # 向量索引ID
    created_at = Column(DateTime, nullable=False, default=func.now())  # 创建时间
    
    # 关系：一个片段属于一个文档
    document = relationship("KnowledgeDocument", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"