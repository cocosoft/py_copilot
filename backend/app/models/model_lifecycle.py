"""模型生命周期数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func, JSON, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class LifecycleStatus(str, enum.Enum):
    """生命周期状态枚举"""
    DRAFT = "draft"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelLifecycle(Base):
    """模型生命周期数据库模型"""
    __tablename__ = "model_lifecycles"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_status = Column(String(50), default=LifecycleStatus.DRAFT.value)
    previous_status = Column(String(50), nullable=True)
    status_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    status_changed_by = Column(String(100), nullable=True)
    version = Column(String(50), nullable=True)
    release_notes = Column(Text, nullable=True)
    migration_guide = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    model = relationship("ModelDB", back_populates="lifecycle")
    transitions = relationship("LifecycleTransition", back_populates="lifecycle", cascade="all, delete-orphan")
    approvals = relationship("LifecycleApproval", back_populates="lifecycle", cascade="all, delete-orphan")


class LifecycleTransition(Base):
    """生命周期状态流转记录"""
    __tablename__ = "lifecycle_transitions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    lifecycle_id = Column(Integer, ForeignKey("model_lifecycles.id", ondelete="CASCADE"), nullable=False)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    triggered_by = Column(String(100), nullable=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    lifecycle = relationship("ModelLifecycle", back_populates="transitions")


class LifecycleApproval(Base):
    """生命周期审批记录"""
    __tablename__ = "lifecycle_approvals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    lifecycle_id = Column(Integer, ForeignKey("model_lifecycles.id", ondelete="CASCADE"), nullable=False)
    transition_id = Column(Integer, ForeignKey("lifecycle_transitions.id", ondelete="CASCADE"), nullable=False)
    approver = Column(String(100), nullable=False)
    approval_status = Column(String(50), default='pending')
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    lifecycle = relationship("ModelLifecycle", back_populates="approvals")
    transition = relationship("LifecycleTransition")
