"""模型Webhook数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ModelWebhook(Base):
    """模型Webhook数据库模型"""
    __tablename__ = "model_webhooks"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)
    events = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_trigger_status = Column(String(50), nullable=True)
    
    # 关系
    model = relationship("ModelDB", back_populates="webhooks")
    supplier = relationship("SupplierDB", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    """Webhook投递记录"""
    __tablename__ = "webhook_deliveries"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("model_webhooks.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, default=dict)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    is_successful = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    webhook = relationship("ModelWebhook", back_populates="deliveries")
