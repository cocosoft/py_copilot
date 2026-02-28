"""智能体数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Agent(Base):
    """智能体表模型"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    avatar = Column(String(50))
    prompt = Column(Text, nullable=False)
    knowledge_base = Column(String(100))
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="agents", foreign_keys=[user_id])
    
    is_public = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 与分类的关系
    category_id = Column(Integer, ForeignKey("agent_categories.id"), nullable=True)
    category = relationship("AgentCategory", back_populates="agents")
    
    # 默认模型字段
    default_model = Column(Integer, nullable=True)
    
    # 技能字段
    skills = Column(JSON, default=list)
    
    # 与对话的关系
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    
    # 与参数的关系
    parameters = relationship("AgentParameter", back_populates="agent", cascade="all, delete-orphan")
    
    # 与翻译历史的关系
    translation_history = relationship("TranslationHistory", back_populates="agent", cascade="all, delete-orphan")
    
    # 能力中心扩展字段 - 智能体分类
    agent_type = Column(String(50), default='single', index=True)  # single/composite
    primary_capability_id = Column(Integer, nullable=True)
    primary_capability_type = Column(String(50), nullable=True)  # skill/tool
    capability_orchestration = Column(JSON, default=dict)
    is_official = Column(Boolean, default=False, index=True)
    is_template = Column(Boolean, default=False, index=True)
    template_category = Column(String(50), nullable=True)
    
    # 关系
    skill_associations = relationship("AgentSkillAssociation", back_populates="agent", cascade="all, delete-orphan")
    tool_associations = relationship("AgentToolAssociation", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.agent_type}')>"