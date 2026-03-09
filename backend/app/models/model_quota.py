"""模型配额数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class QuotaPeriod(str, enum.Enum):
    """配额周期枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class ModelQuota(Base):
    """模型配额数据库模型"""
    __tablename__ = "model_quotas"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String(100), nullable=True)
    api_key_id = Column(String(100), nullable=True)
    
    # 配额限制
    max_requests = Column(Integer, default=1000)
    max_tokens = Column(Integer, default=1000000)
    max_cost = Column(Float, default=100.0)
    
    # 当前使用量
    current_requests = Column(Integer, default=0)
    current_tokens = Column(Integer, default=0)
    current_cost = Column(Float, default=0.0)
    
    # 配额周期
    period = Column(String(50), default=QuotaPeriod.DAILY.value)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # 预警阈值
    warning_threshold = Column(Float, default=0.8)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_exceeded = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # 关系
    model = relationship("ModelDB", back_populates="quotas")
    supplier = relationship("SupplierDB", back_populates="quotas")
    usages = relationship("QuotaUsage", back_populates="quota", cascade="all, delete-orphan")


class QuotaUsage(Base):
    """配额使用记录"""
    __tablename__ = "quota_usages"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    quota_id = Column(Integer, ForeignKey("model_quotas.id", ondelete="CASCADE"), nullable=False)
    requests_used = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    cost_incurred = Column(Float, default=0.0)
    usage_date = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(JSON, default=dict)
    
    # 关系
    quota = relationship("ModelQuota", back_populates="usages")
