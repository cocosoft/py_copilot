"""LLM相关模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, func, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class LLMRequestHistory(Base):
    """LLM请求历史表模型"""
    __tablename__ = "llm_request_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    model_id = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    
    # 请求/响应统计
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # 状态信息
    status = Column(String(50), default="pending")  # pending, completed, error
    error_message = Column(Text, nullable=True)
    
    # 请求参数（存储为JSON）
    request_params = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系定义
    user = relationship("User", back_populates="llm_requests")
    
    def __repr__(self):
        return f"<LLMRequestHistory(id={self.id}, model='{self.model_id}', status='{self.status}')>"


class ModelConfiguration(Base):
    """LLM模型配置表模型"""
    __tablename__ = "model_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, nullable=False)
    provider = Column(String(50), nullable=False)  # openai, huggingface, etc.
    api_key_name = Column(String(100), nullable=True)  # 环境变量中的API密钥名称
    
    # 模型参数默认值
    default_temperature = Column(Float, default=0.7)
    default_max_tokens = Column(Integer, default=1000)
    default_top_p = Column(Float, default=1.0)
    default_frequency_penalty = Column(Float, default=0.0)
    default_presence_penalty = Column(Float, default=0.0)
    
    # 模型状态
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ModelConfiguration(id={self.id}, model='{self.model_id}', provider='{self.provider}')>"