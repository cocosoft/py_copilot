"""模型配置数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ModelConfig(Base):
    """模型配置数据库模型"""
    __tablename__ = "model_configs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(200), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default='string')
    description = Column(Text, nullable=True)
    environment = Column(String(50), default='production')
    is_encrypted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # 关系
    model = relationship("ModelDB", back_populates="configs")
    supplier = relationship("SupplierDB", back_populates="configs")
    
    # 版本历史
    versions = relationship("ModelConfigVersion", back_populates="config", cascade="all, delete-orphan")


class ModelConfigVersion(Base):
    """模型配置版本历史"""
    __tablename__ = "model_config_versions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("model_configs.id", ondelete="CASCADE"), nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default='string')
    changed_by = Column(String(100), nullable=True)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    config = relationship("ModelConfig", back_populates="versions")
