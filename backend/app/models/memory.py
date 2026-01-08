from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Table, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

# 导入KnowledgeBase模型
from app.modules.knowledge.models.knowledge_document import KnowledgeBase, KnowledgeDocument


class GlobalMemory(Base):
    """全局记忆主表"""
    __tablename__ = "global_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), index=True)
    memory_type = Column(String(50), nullable=False, index=True)  # SHORT_TERM, LONG_TERM, SEMANTIC, PROCEDURAL
    memory_category = Column(String(100))  # CONVERSATION, KNOWLEDGE, PREFERENCE, CONTEXT
    title = Column(String(500))
    content = Column(Text, nullable=False)
    summary = Column(Text)
    importance_score = Column(Float, default=0.0, index=True)  # 0.0-1.0重要性评分
    relevance_score = Column(Float, default=0.0)  # 0.0-1.0相关性评分
    access_count = Column(Integer, default=0)  # 访问次数
    last_accessed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # 过期时间
    is_active = Column(Boolean, default=True, index=True)
    memory_metadata = Column(JSON, nullable=True)  # 额外的元数据
    embedding = Column(Text, nullable=True)  # 向量嵌入 (JSON格式存储)
    tags = Column(JSON, nullable=True)  # 标签数组 (JSON格式存储)
    source_info = Column(JSON, nullable=True)  # 来源信息
    
    # 与现有系统的关联字段
    source_type = Column(String(50), index=True)  # CONVERSATION, KNOWLEDGE_BASE, DOCUMENT, USER_INPUT
    source_id = Column(Integer, index=True)  # 对应现有系统中的记录ID
    source_reference = Column(JSON, nullable=True)  # 额外引用信息，如Message ID, Document路径等
    
    # 关系定义
    user = relationship("User", back_populates="global_memories")
    conversation_mappings = relationship("ConversationMemoryMapping", back_populates="memory", cascade="all, delete-orphan")
    knowledge_mappings = relationship("KnowledgeMemoryMapping", back_populates="memory", cascade="all, delete-orphan")
    source_associations = relationship("MemoryAssociation", foreign_keys="MemoryAssociation.source_memory_id", back_populates="source_memory", cascade="all, delete-orphan")
    target_associations = relationship("MemoryAssociation", foreign_keys="MemoryAssociation.target_memory_id", back_populates="target_memory", cascade="all, delete-orphan")
    access_logs = relationship("MemoryAccessLog", back_populates="memory", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GlobalMemory(id={self.id}, title='{self.title}', memory_type='{self.memory_type}')>"


class ConversationMemoryMapping(Base):
    """对话记忆映射表"""
    __tablename__ = "conversation_memory_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    memory_id = Column(Integer, ForeignKey("global_memories.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    conversation = relationship("Conversation", back_populates="memory_mappings")
    message = relationship("Message")
    memory = relationship("GlobalMemory", back_populates="conversation_mappings")
    
    def __repr__(self):
        return f"<ConversationMemoryMapping(id={self.id}, conversation_id={self.conversation_id}, memory_id={self.memory_id})>"


class KnowledgeMemoryMapping(Base):
    """知识库记忆映射表"""
    __tablename__ = "knowledge_memory_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=True)
    memory_id = Column(Integer, ForeignKey("global_memories.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    knowledge_base = relationship("KnowledgeBase")
    document = relationship("KnowledgeDocument")
    memory = relationship("GlobalMemory", back_populates="knowledge_mappings")
    
    def __repr__(self):
        return f"<KnowledgeMemoryMapping(id={self.id}, knowledge_base_id={self.knowledge_base_id}, memory_id={self.memory_id})>"


class MemoryAssociation(Base):
    """记忆关联表"""
    __tablename__ = "memory_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    source_memory_id = Column(Integer, ForeignKey("global_memories.id"), nullable=False)
    target_memory_id = Column(Integer, ForeignKey("global_memories.id"), nullable=False)
    association_type = Column(String(100), nullable=False)  # SEMANTIC, CAUSAL, TEMPORAL, CONTEXTUAL
    strength = Column(Float, default=0.0)  # 0.0-1.0关联强度
    bidirectional = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    source_memory = relationship("GlobalMemory", foreign_keys=[source_memory_id], back_populates="source_associations")
    target_memory = relationship("GlobalMemory", foreign_keys=[target_memory_id], back_populates="target_associations")
    
    def __repr__(self):
        return f"<MemoryAssociation(id={self.id}, type='{self.association_type}', strength={self.strength})>"


class MemoryAccessLog(Base):
    """记忆访问日志表"""
    __tablename__ = "memory_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("global_memories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_type = Column(String(50), nullable=False)  # READ, WRITE, UPDATE, DELETE
    context_info = Column(JSON, nullable=True)  # 访问上下文
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    memory = relationship("GlobalMemory", back_populates="access_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<MemoryAccessLog(id={self.id}, memory_id={self.memory_id}, access_type='{self.access_type}')>"


class UserMemoryConfig(Base):
    """用户记忆配置表"""
    __tablename__ = "user_memory_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    short_term_retention_days = Column(Integer, default=7)
    long_term_threshold = Column(Float, default=0.7)
    auto_cleanup_enabled = Column(Boolean, default=True)
    privacy_level = Column(String(50), default='MEDIUM')  # LOW, MEDIUM, HIGH
    sync_enabled = Column(Boolean, default=False)
    preferred_embedding_model = Column(String(100), default='text-embedding-ada-002')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="memory_config")
    
    def __repr__(self):
        return f"<UserMemoryConfig(id={self.id}, user_id={self.user_id}, privacy_level='{self.privacy_level}')>"