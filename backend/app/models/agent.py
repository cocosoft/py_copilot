"""智能体数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Agent(Base):
    """智能体表模型"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    avatar = Column(String(50))
    prompt = Column(Text, nullable=False)
    knowledge_base = Column(String(100))
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="agents")
    
    is_public = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 与对话的关系
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"