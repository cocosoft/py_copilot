"""模型分类相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelCategory(Base):
    """模型分类表模型"""
    __tablename__ = "model_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 分类名称，如 task_type, size
    display_name = Column(String(100), nullable=False)  # 显示名称，如 任务类型, 规模
    description = Column(Text, nullable=True)  # 分类描述
    
    # 分类类型：main（主要分类）, secondary（次要分类）
    category_type = Column(String(20), default="main", nullable=False)
    
    # 父分类ID，支持层级分类
    parent_id = Column(Integer, ForeignKey("model_categories.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    # 自引用关系，用于层级分类
    parent = relationship("ModelCategory", remote_side=[id], backref="children")
    
    # 与模型的多对多关系将在后续的关联表中定义
    
    def __repr__(self):
        return f"<ModelCategory(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


# 创建模型和分类之间的多对多关联表
class ModelCategoryAssociation(Base):
    """模型和分类的多对多关联表"""
    __tablename__ = "model_category_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("model_categories.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())