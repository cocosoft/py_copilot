"""对话模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
# 导入相关模型
from app.models.chat_enhancements import UploadedFile, VoiceInput, SearchQuery


class Conversation(Base):
    """对话表模型"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)  # 添加agent_id外键
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 新增字段
    current_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    topic_auto_detection = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    skill_sessions = relationship("SkillSession", back_populates="conversation", cascade="all, delete-orphan")
    memory_mappings = relationship("ConversationMemoryMapping", back_populates="conversation", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="conversation", foreign_keys="Topic.conversation_id", cascade="all, delete-orphan")
    current_topic = relationship("Topic", foreign_keys=[current_topic_id], post_update=True)
    uploaded_files = relationship("UploadedFile", back_populates="conversation", cascade="all, delete-orphan")
    voice_inputs = relationship("VoiceInput", back_populates="conversation", cascade="all, delete-orphan")
    search_queries = relationship("SearchQuery", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class Message(Base):
    """消息表模型"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    
    # 消息元数据
    model_used = Column(String(100), nullable=True)
    response_time = Column(Integer, nullable=True)  # 毫秒
    is_streaming = Column(Boolean, default=False)
    
    # 新增字段
    streaming_enabled = Column(Boolean, default=False)
    streaming_completed = Column(Boolean, default=False)
    chain_of_thought_enabled = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    conversation = relationship("Conversation", back_populates="messages")
    streaming_chunks = relationship("StreamingResponse", back_populates="message", cascade="all, delete-orphan")
    chain_of_thought = relationship("ChainOfThought", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"