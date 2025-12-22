"""智能体分类数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgentCategory(Base):
    """智能体分类表模型"""
    __tablename__ = "agent_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    logo = Column(Text, nullable=True)  # SVG格式的logo数据
    is_system = Column(Boolean, default=False, nullable=False)
    parent_id = Column(Integer, ForeignKey("agent_categories.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 与智能体的关系
    agents = relationship("Agent", back_populates="category")
    
    # 树形结构关系
    parent = relationship("AgentCategory", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<AgentCategory(id={self.id}, name='{self.name}', is_system={self.is_system}, parent_id={self.parent_id})>"
    
    @property
    def is_root(self):
        """判断是否为根分类"""
        return self.parent_id is None
    
    @property
    def is_leaf(self):
        """判断是否为叶子分类（没有子分类）"""
        return len(self.children) == 0