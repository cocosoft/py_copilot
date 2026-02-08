"""翻译历史模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TranslationHistory(Base):
    """翻译历史表"""
    __tablename__ = "translation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    model_name = Column(String(50), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    
    # 智能体和场景相关字段
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    scene = Column(String(20), nullable=True)
    
    # 知识库集成相关字段
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=True)
    use_knowledge_base = Column(Boolean, default=False)
    
    # 全局记忆集成相关字段
    use_memory_enhancement = Column(Boolean, default=False)
    
    # 术语一致性相关字段
    term_consistency = Column(Boolean, default=False)
    
    # 执行时间和性能指标
    execution_time_ms = Column(Integer, nullable=True)
    
    # 翻译质量评分
    quality_score = Column(Integer, nullable=True)  # 1-5分评分
    user_feedback = Column(String(500), nullable=True)  # 用户反馈
    
    # 元数据和统计信息
    additional_metadata = Column(JSON, nullable=True)  # 额外的元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 关联关系
    user = relationship("User", back_populates="translation_history")
    agent = relationship("Agent", back_populates="translation_history")
    knowledge_base = relationship("KnowledgeBase")
    
    def __repr__(self):
        return f"<TranslationHistory(id={self.id}, source_language={self.source_language}, target_language={self.target_language})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "source_text": self.source_text,
            "target_text": self.target_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "model_name": self.model_name,
            "tokens_used": self.tokens_used,
            "agent_id": self.agent_id,
            "scene": self.scene,
            "knowledge_base_id": self.knowledge_base_id,
            "use_knowledge_base": self.use_knowledge_base,
            "use_memory_enhancement": self.use_memory_enhancement,
            "term_consistency": self.term_consistency,
            "execution_time_ms": self.execution_time_ms,
            "quality_score": self.quality_score,
            "user_feedback": self.user_feedback,
            "additional_metadata": self.additional_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }