"""聊天功能增强模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, BigInteger, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class StreamingResponse(Base):
    """流式响应记录表"""
    __tablename__ = "streaming_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content_chunk = Column(Text, nullable=False)
    is_final_chunk = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    message = relationship("Message", back_populates="streaming_chunks")
    
    def __repr__(self):
        return f"<StreamingResponse(id={self.id}, message_id={self.message_id}, chunk={self.chunk_index})>"


class UploadedFile(Base):
    """文件上传记录表"""
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    mime_type = Column(String(200), nullable=True)
    upload_status = Column(String(50), default='pending')  # pending, completed, failed
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    file_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="uploaded_files")
    conversation = relationship("Conversation", back_populates="uploaded_files")
    
    def __repr__(self):
        return f"<UploadedFile(id={self.id}, name='{self.file_name}', user_id={self.user_id})>"


class VoiceInput(Base):
    """语音输入记录表"""
    __tablename__ = "voice_inputs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    audio_file_path = Column(String(1000), nullable=False)
    transcribed_text = Column(Text, nullable=True)
    audio_duration = Column(Integer, nullable=True)  # 秒
    language = Column(String(50), default='zh-CN')
    transcription_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    confidence_score = Column(Float, nullable=True)
    voice_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="voice_inputs")
    conversation = relationship("Conversation", back_populates="voice_inputs")
    
    def __repr__(self):
        return f"<VoiceInput(id={self.id}, user_id={self.user_id}, status='{self.transcription_status}')>"


class ChainOfThought(Base):
    """思维链记录表"""
    __tablename__ = "chain_of_thoughts"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    chain_type = Column(String(50), nullable=False)  # step_by_step, tree, graph
    reasoning_steps = Column(JSON, nullable=False)
    final_answer = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    message = relationship("Message", back_populates="chain_of_thought")
    
    def __repr__(self):
        return f"<ChainOfThought(id={self.id}, message_id={self.message_id}, type='{self.chain_type}')>"


class SearchQuery(Base):
    """搜索记录表"""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    query_text = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False)  # web, knowledge, memory
    results_count = Column(Integer, nullable=True)
    search_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="search_queries")
    conversation = relationship("Conversation", back_populates="search_queries")
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, type='{self.search_type}', user_id={self.user_id})>"


class AnalyzedImage(Base):
    """图像分析记录表"""
    __tablename__ = "analyzed_images"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # general, text, face
    analysis_results = Column(Text, nullable=False)  # JSON字符串
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    confidence_score = Column(Float, nullable=True)
    analysis_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="analyzed_images")
    conversation = relationship("Conversation", back_populates="analyzed_images")
    
    def __repr__(self):
        return f"<AnalyzedImage(id={self.id}, image_id='{self.image_id}', type='{self.analysis_type}')>"