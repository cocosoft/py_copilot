"""分类模板相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoryTemplate(Base):
    """分类模板表模型"""
    __tablename__ = "category_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 模板名称
    display_name = Column(String(100), nullable=False)  # 显示名称
    description = Column(Text, nullable=True)  # 模板描述
    
    # 模板数据（包含分类结构、参数等）
    template_data = Column(JSON, nullable=False, default={})
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CategoryTemplate(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"