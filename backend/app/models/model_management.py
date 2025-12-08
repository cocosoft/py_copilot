"""模型管理相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, func, Boolean, Table
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelSupplier(Base):
    """模型供应商表模型"""
    __tablename__ = "suppliers"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    api_endpoint = Column(String(500))  # 数据库中存在的字段
    api_key_required = Column(Boolean, default=False)
    logo = Column(String(255))
    category = Column(String(100))
    website = Column(String(500))
    api_docs = Column(String(500))
    api_key = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # 定义关系
    models = relationship("Model", back_populates="supplier")
    
    def __repr__(self):
        return f"<ModelSupplier(id={self.id}, name='{self.name}')>"


class Model(Base):
    """模型表模型"""
    __tablename__ = "models"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(200))
    description = Column(Text)
    context_window = Column(Integer)
    max_tokens = Column(Integer)
    model_type = Column(String(50), default="chat", nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    logo = Column(String(255), nullable=True)  # 模型LOGO存储路径或URL
    
    # 添加关系定义
    supplier = relationship("ModelSupplier", back_populates="models")
    
    # 与模型分类的多对多关系 - 暂时注释，因为缺少model_category_associations中间表定义
    # categories = relationship(
    #     "ModelCategory",
    #     secondary="model_category_associations",
    #     backref="models"
    # )