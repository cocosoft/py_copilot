"""术语库数据模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Terminology(Base):
    """术语库条目表"""
    __tablename__ = "terminology"
    
    id = Column(Integer, primary_key=True, index=True)
    source_term = Column(String(500), nullable=False, index=True)  # 源术语
    target_term = Column(String(500), nullable=False)  # 目标术语
    source_language = Column(String(10), nullable=False, index=True)  # 源语言代码
    target_language = Column(String(10), nullable=False, index=True)  # 目标语言代码
    
    # 术语属性
    domain = Column(String(50), nullable=True, index=True)  # 领域：general, business, technical, medical等
    description = Column(Text, nullable=True)  # 术语描述
    tags = Column(String(200), nullable=True)  # 标签，逗号分隔
    
    # 术语质量指标
    confidence_score = Column(Integer, default=80)  # 置信度分数 0-100
    usage_count = Column(Integer, default=0)  # 使用次数
    approval_status = Column(String(20), default="pending")  # 审核状态：pending, approved, rejected
    
    # 用户和来源信息
    user_id = Column(Integer, nullable=True)  # 创建用户ID
    source = Column(String(50), default="manual")  # 来源：manual, import, auto_extract
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        # 确保同一语言对中术语唯一
        {'sqlite_autoincrement': True},
    )


class TerminologyHistory(Base):
    """术语使用历史表"""
    __tablename__ = "terminology_history"
    
    id = Column(Integer, primary_key=True, index=True)
    terminology_id = Column(Integer, nullable=False, index=True)  # 移除外键约束
    translation_id = Column(Integer, nullable=True, index=True)  # 移除外键约束
    
    # 使用上下文
    source_text = Column(Text, nullable=True)  # 使用时的源文本
    target_text = Column(Text, nullable=True)  # 使用时的目标文本
    
    # 使用统计
    match_type = Column(String(20), default="exact")  # 匹配类型：exact, partial, fuzzy
    match_score = Column(Integer, default=100)  # 匹配分数 0-100
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 索引
    __table_args__ = (
        # 按术语和翻译记录索引
        {'sqlite_autoincrement': True},
    )