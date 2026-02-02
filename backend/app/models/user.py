"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.core.database import Base
# 导入相关模型
from app.models.chat_enhancements import UploadedFile, VoiceInput, SearchQuery, AnalyzedImage


class User(Base):
    """用户表模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # 用户状态
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # 关系定义 - 使用字符串引用避免循环导入
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    llm_requests = relationship("LLMRequestHistory", back_populates="user", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    skill_sessions = relationship("SkillSession", back_populates="user", cascade="all, delete-orphan")
    global_memories = relationship("GlobalMemory", back_populates="user", cascade="all, delete-orphan")
    memory_access_logs = relationship("MemoryAccessLog", back_populates="user", cascade="all, delete-orphan")
    memory_config = relationship("UserMemoryConfig", back_populates="user", cascade="all, delete-orphan", uselist=False)
    uploaded_files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")
    voice_inputs = relationship("VoiceInput", back_populates="user", cascade="all, delete-orphan")
    search_queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan")
    analyzed_images = relationship("AnalyzedImage", back_populates="user", cascade="all, delete-orphan")
    translation_history = relationship("TranslationHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"