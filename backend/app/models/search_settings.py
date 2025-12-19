"""搜索设置模型（仅联网搜索配置）"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class SearchSetting(Base):
    """搜索设置模型（仅联网搜索配置）"""
    __tablename__ = "search_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # nullable=True表示全局设置
    default_search_engine = Column(String(50), default="google")  # 可选：google, bing, baidu
    safe_search = Column(Boolean, default=True)  # 安全搜索开关
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
