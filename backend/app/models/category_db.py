"""分类相关数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text
from app.models.base import Base

class ModelCategoryDB(Base):
    """模型分类数据库模型"""
    __tablename__ = "model_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    display_name = Column(String(200))
    description = Column(Text, nullable=True)
    category_type = Column(String(20), default="main")
    parent_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)