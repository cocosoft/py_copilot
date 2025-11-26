"""供应商和模型数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SupplierDB(Base):
    """供应商数据库模型"""
    __tablename__ = "suppliers"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text, nullable=True)
    api_endpoint = Column(String(255), nullable=True)
    api_key_required = Column(Boolean, default=False)
    created_at = Column(String)
    updated_at = Column(String)
    # 新增字段
    logo = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    api_docs = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 添加关系定义
    models = relationship("ModelDB", back_populates="supplier")


class ModelDB(Base):
    """模型数据库模型"""
    __tablename__ = "models"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    display_name = Column(String(200))
    description = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    context_window = Column(Integer, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # 添加关系定义
    supplier = relationship("SupplierDB", back_populates="models")
