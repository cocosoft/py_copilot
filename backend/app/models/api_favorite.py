"""API文档收藏模型"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class ApiFavorite(Base):
    """API文档收藏表"""
    __tablename__ = "api_favorites"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True, comment="用户ID")
    api_path = Column(String(500), nullable=False, comment="API路径")
    api_method = Column(String(10), nullable=False, comment="API方法")
    api_summary = Column(String(500), nullable=True, comment="API摘要")
    api_module = Column(String(100), nullable=True, comment="API模块")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 唯一约束：同一用户不能重复收藏同一个API
    __table_args__ = (
        {'extend_existing': True},
    )
