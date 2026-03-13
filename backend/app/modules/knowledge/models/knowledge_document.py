from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Table, Boolean, Float, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

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
    # 关系：一个知识库包含多个KB级实体
    kb_entities = relationship("KBEntity", back_populates="knowledge_base", cascade="all, delete-orphan")
    # 关系：一个知识库包含多个KB级关系
    kb_relationships = relationship("KBRelationship", back_populates="knowledge_base", cascade="all, delete-orphan")
    # 关系：一个知识库有一个模型配置
    model_configs = relationship("KnowledgeBaseModelConfig", back_populates="knowledge_base", cascade="all, delete-orphan", uselist=False)
    # 关系：一个知识库包含多个权限记录
    permissions = relationship("KnowledgeBasePermission", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}')>"

def generate_uuid():
    """生成文档UUID"""
    return f"doc-{uuid.uuid4()}"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(40), nullable=False, unique=True, index=True, default=generate_uuid)  # 全局唯一UUID，对外暴露
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    vector_id = Column(String(100), nullable=True)  # 向量ID，使用uuid格式
    is_vectorized = Column(Integer, nullable=False, default=0)  # 0: 未向量化, 1: 已向量化
    version = Column(Integer, default=1)  # 文档版本
    is_current = Column(Boolean, nullable=False, default=True)  # 是否为当前版本 (True: 是, False: 历史版本)
    file_hash = Column(String(64), nullable=True, index=True)  # 文件SHA256哈希值，用于去重检测

    # 添加唯一约束：同一知识库内file_hash唯一
    __table_args__ = (
        UniqueConstraint('knowledge_base_id', 'file_hash', name='uix_kb_file_hash'),
    )
    
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
    
    # 层级关联：关联到KB级实体
    kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=True, index=True)
    # 层级关联：关联到全局级实体
    global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=True, index=True)
    
    # 关系：一个实体属于一个文档
    document = relationship("KnowledgeDocument", back_populates="entities")
    # 关系：关联到KB级实体
    kb_entity = relationship("KBEntity", back_populates="document_entities")
    # 关系：关联到全局级实体
    global_entity = relationship("GlobalEntity")
    # 关系：作为源实体的关系
    source_relationships = relationship("EntityRelationship", foreign_keys="EntityRelationship.source_id", cascade="all, delete-orphan")
    # 关系：作为目标实体的关系
    target_relationships = relationship("EntityRelationship", foreign_keys="EntityRelationship.target_id", cascade="all, delete-orphan")
    
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


class KBEntity(Base):
    """
    知识库级实体 - 跨文档整合
    
    用于聚合同一知识库内不同文档中的相同实体
    """
    __tablename__ = "kb_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    # 实体信息
    canonical_name = Column(String(200), nullable=False)  # 规范名称
    entity_type = Column(String(50), nullable=False, index=True)  # 实体类型
    aliases = Column(JSON, default=list)  # 别名列表 ["别名1", "别名2"]
    
    # 统计信息
    document_count = Column(Integer, default=0)  # 出现文档数
    occurrence_count = Column(Integer, default=0)  # 总出现次数
    
    # 层级关联
    global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=True, index=True)
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="kb_entities")
    global_entity = relationship("GlobalEntity", back_populates="kb_entities")
    document_entities = relationship("DocumentEntity", back_populates="kb_entity")
    
    def __repr__(self):
        return f"<KBEntity(id={self.id}, name='{self.canonical_name}', type='{self.entity_type}')>"


class GlobalEntity(Base):
    """
    全局级实体 - 跨知识库统一
    
    用于聚合不同知识库中的相同实体，提供全局视角
    """
    __tablename__ = "global_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 实体信息
    global_name = Column(String(200), nullable=False)  # 全局规范名称
    entity_type = Column(String(50), nullable=False, index=True)  # 实体类型
    all_aliases = Column(JSON, default=list)  # 所有别名（跨知识库）
    
    # 统计信息
    kb_count = Column(Integer, default=0)  # 出现知识库数
    document_count = Column(Integer, default=0)  # 出现文档数
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    kb_entities = relationship("KBEntity", back_populates="global_entity")
    
    def __repr__(self):
        return f"<GlobalEntity(id={self.id}, name='{self.global_name}', type='{self.entity_type}')>"


class KBRelationship(Base):
    """
    知识库级关系 - 跨文档聚合
    
    聚合同一知识库内不同文档中的相同关系
    """
    __tablename__ = "kb_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    # 关联的KB级实体
    source_kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=False, index=True)
    target_kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=False, index=True)
    
    # 关系信息
    relationship_type = Column(String(100), nullable=False)  # 关系类型
    aggregated_count = Column(Integer, default=0)  # 聚合的关系数量
    
    # 来源文档关系ID列表
    source_relationships = Column(JSON, default=list)  # [doc_rel_id1, doc_rel_id2, ...]
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="kb_relationships")
    source_entity = relationship("KBEntity", foreign_keys=[source_kb_entity_id])
    target_entity = relationship("KBEntity", foreign_keys=[target_kb_entity_id])
    
    def __repr__(self):
        return f"<KBRelationship(id={self.id}, type='{self.relationship_type}')>"


class GlobalRelationship(Base):
    """
    全局级关系 - 跨知识库发现
    
    发现不同知识库中实体间的关联关系
    """
    __tablename__ = "global_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的全局实体
    source_global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=False, index=True)
    target_global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=False, index=True)
    
    # 关系信息
    relationship_type = Column(String(100), nullable=False)  # 关系类型
    aggregated_count = Column(Integer, default=0)  # 聚合的关系数量
    
    # 来源知识库ID列表
    source_kbs = Column(JSON, default=list)  # [kb_id1, kb_id2, ...]
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    source_entity = relationship("GlobalEntity", foreign_keys=[source_global_entity_id])
    target_entity = relationship("GlobalEntity", foreign_keys=[target_global_entity_id])
    
    def __repr__(self):
        return f"<GlobalRelationship(id={self.id}, type='{self.relationship_type}')>"


class KnowledgeBasePermission(Base):
    """
    知识库权限模型
    
    用于管理用户对知识库的访问权限
    """
    __tablename__ = "knowledge_base_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")  # admin, editor, viewer
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="permissions")

    def __repr__(self):
        return f"<KnowledgeBasePermission(id={self.id}, user_id={self.user_id}, role='{self.role}')>"