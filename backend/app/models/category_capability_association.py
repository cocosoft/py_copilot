"""分类与能力关联模型"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, Integer, DateTime, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoryCapabilityAssociation(Base):
    """模型分类和能力的多对多关联表"""
    __tablename__ = "category_capability_associations"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("model_categories.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(Integer, ForeignKey("model_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    # 是否为该分类的默认能力
    is_default = Column(Boolean, default=False)
    
    # 权重（用于能力优先级排序）
    weight = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    category = relationship("ModelCategory", backref="capability_associations")
    capability = relationship("ModelCapability", backref="category_associations")
    
    def __repr__(self):
        return f"<CategoryCapabilityAssociation(id={self.id}, category_id={self.category_id}, capability_id={self.capability_id})>"
