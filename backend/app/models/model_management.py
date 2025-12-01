"""模型管理相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, func, Boolean, Table
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelSupplier(Base):
    """模型供应商表模型"""
    __tablename__ = "suppliers"
    
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
    
    # 暂时不定义关系，避免初始化错误
    
    def __repr__(self):
        return f"<ModelSupplier(id={self.id}, name='{self.name}')>"


class Model(Base):
    """模型表模型"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    context_window = Column(Integer)
    max_tokens = Column(Integer)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)