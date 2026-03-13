"""
统一知识单元模型 - 向量化管理模块优化

设计并实现统一知识数据模型，整合向量、实体、图谱数据。

任务编号: BE-009
阶段: Phase 3 - 一体化建设期
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, JSON, ForeignKey, 
    Table, Boolean, Float, Enum, Index, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from enum import Enum as PyEnum
from typing import Dict, Any, List, Optional

from app.core.database import Base


class KnowledgeUnitType(PyEnum):
    """知识单元类型"""
    DOCUMENT = "document"           # 文档
    CHUNK = "chunk"                 # 文档片段
    ENTITY = "entity"               # 实体
    RELATIONSHIP = "relationship"   # 关系
    CONCEPT = "concept"             # 概念
    FACT = "fact"                   # 事实


class KnowledgeUnitStatus(PyEnum):
    """知识单元状态"""
    ACTIVE = "active"               # 活跃
    INACTIVE = "inactive"           # 非活跃
    DEPRECATED = "deprecated"       # 已弃用
    PENDING = "pending"             # 待处理
    PROCESSING = "processing"       # 处理中
    FAILED = "failed"               # 失败


class AssociationType(PyEnum):
    """关联类型"""
    CONTAINS = "contains"           # 包含关系 (文档-片段)
    REFERENCES = "references"       # 引用关系
    SIMILAR_TO = "similar_to"       # 相似关系
    RELATED_TO = "related_to"       # 相关关系
    PART_OF = "part_of"             # 组成部分
    INSTANCE_OF = "instance_of"     # 实例关系
    SUBCLASS_OF = "subclass_of"     # 子类关系
    MENTIONS = "mentions"           # 提及关系


class UnifiedKnowledgeUnit(Base):
    """
    统一知识单元表
    
    整合向量、实体、图谱数据的统一数据模型。
    支持多种知识表示形式的存储和关联。
    
    字段说明：
    - id: 唯一标识符
    - unit_type: 知识单元类型
    - status: 状态
    - knowledge_base_id: 所属知识库
    - content: 内容（文本、JSON等）
    - vector_embedding: 向量嵌入（可选）
    - metadata: 元数据
    - source_info: 来源信息
    - version: 版本号
    - created_at/updated_at: 时间戳
    """
    
    __tablename__ = "unified_knowledge_units"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 知识单元类型
    unit_type = Column(
        Enum(KnowledgeUnitType),
        nullable=False,
        index=True,
        comment="知识单元类型: document/chunk/entity/relationship/concept/fact"
    )
    
    # 状态
    status = Column(
        Enum(KnowledgeUnitStatus),
        nullable=False,
        default=KnowledgeUnitStatus.PENDING,
        index=True,
        comment="状态: active/inactive/deprecated/pending/processing/failed"
    )
    
    # 所属知识库
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属知识库ID"
    )
    
    # 内容
    content = Column(Text, nullable=True, comment="内容文本")
    content_hash = Column(String(64), nullable=True, index=True, comment="内容哈希，用于去重")
    
    # 向量嵌入（以JSON格式存储，支持不同维度）
    vector_embedding = Column(JSON, nullable=True, comment="向量嵌入数据")
    vector_id = Column(String(100), nullable=True, index=True, comment="向量存储中的ID")
    vector_dimension = Column(Integer, nullable=True, comment="向量维度")
    
    # 元数据（使用 meta_data 避免与 SQLAlchemy 保留字冲突）
    meta_data = Column(JSON, nullable=True, comment="元数据")
    
    # 来源信息
    source_type = Column(String(50), nullable=True, comment="来源类型: document/entity/graph")
    source_id = Column(String(100), nullable=True, index=True, comment="来源ID")
    source_location = Column(String(500), nullable=True, comment="来源位置（如文件路径）")
    
    # 版本控制
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    is_current = Column(Boolean, nullable=False, default=True, comment="是否为当前版本")
    parent_unit_id = Column(
        Integer,
        ForeignKey("unified_knowledge_units.id"),
        nullable=True,
        comment="父单元ID（用于版本链）"
    )
    
    # 统计信息
    access_count = Column(Integer, default=0, comment="访问次数")
    relevance_score = Column(Float, nullable=True, comment="相关性分数")
    confidence = Column(Float, nullable=True, default=1.0, comment="置信度")
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=True, onupdate=func.now(), comment="更新时间")
    processed_at = Column(DateTime, nullable=True, comment="处理完成时间")
    
    # 关系
    # knowledge_base = relationship("KnowledgeBase", back_populates="knowledge_units")
    
    # 父单元关系
    parent_unit = relationship(
        "UnifiedKnowledgeUnit",
        remote_side=[id],
        back_populates="child_units"
    )
    child_units = relationship(
        "UnifiedKnowledgeUnit",
        back_populates="parent_unit"
    )
    
    # 关联关系（通过关联表）
    outgoing_associations = relationship(
        "KnowledgeUnitAssociation",
        foreign_keys="KnowledgeUnitAssociation.source_unit_id",
        back_populates="source_unit",
        cascade="all, delete-orphan"
    )
    incoming_associations = relationship(
        "KnowledgeUnitAssociation",
        foreign_keys="KnowledgeUnitAssociation.target_unit_id",
        back_populates="target_unit",
        cascade="all, delete-orphan"
    )
    
    # 流水线运行记录
    pipeline_runs = relationship(
        "ProcessingPipelineRun",
        back_populates="knowledge_unit",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_unit_kb_type', 'knowledge_base_id', 'unit_type'),
        Index('idx_unit_status_type', 'status', 'unit_type'),
        Index('idx_unit_source', 'source_type', 'source_id'),
        Index('idx_unit_current', 'is_current', 'knowledge_base_id'),
        Index('idx_unit_content_hash', 'content_hash'),
        UniqueConstraint('knowledge_base_id', 'content_hash', name='uq_unit_content_hash'),
    )
    
    def __repr__(self):
        return f"<UnifiedKnowledgeUnit(id={self.id}, type={self.unit_type.value}, status={self.status.value})>"
    
    @validates('vector_embedding')
    def validate_vector_embedding(self, key, value):
        """验证向量嵌入数据"""
        if value is not None:
            if not isinstance(value, list):
                raise ValueError("向量嵌入必须是列表")
            if len(value) > 0 and not all(isinstance(x, (int, float)) for x in value):
                raise ValueError("向量嵌入元素必须是数字")
            self.vector_dimension = len(value)
        return value
    
    def to_dict(self, include_vector: bool = False) -> Dict[str, Any]:
        """
        转换为字典
        
        Args:
            include_vector: 是否包含向量数据
            
        Returns:
            字典表示
        """
        result = {
            "id": self.id,
            "unit_type": self.unit_type.value,
            "status": self.status.value,
            "knowledge_base_id": self.knowledge_base_id,
            "content": self.content,
            "content_hash": self.content_hash,
            "metadata": self.meta_data,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_location": self.source_location,
            "version": self.version,
            "is_current": self.is_current,
            "parent_unit_id": self.parent_unit_id,
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
        
        if include_vector and self.vector_embedding:
            result["vector_embedding"] = self.vector_embedding
            result["vector_dimension"] = self.vector_dimension
            result["vector_id"] = self.vector_id
        
        return result
    
    def get_associated_units(
        self,
        association_type: Optional[AssociationType] = None,
        direction: str = "both"
    ) -> List["KnowledgeUnitAssociation"]:
        """
        获取关联的知识单元
        
        Args:
            association_type: 关联类型过滤
            direction: 方向，"outgoing"/"incoming"/"both"
            
        Returns:
            关联列表
        """
        associations = []
        
        if direction in ["outgoing", "both"]:
            for assoc in self.outgoing_associations:
                if association_type is None or assoc.association_type == association_type:
                    associations.append(assoc)
        
        if direction in ["incoming", "both"]:
            for assoc in self.incoming_associations:
                if association_type is None or assoc.association_type == association_type:
                    associations.append(assoc)
        
        return associations


class KnowledgeUnitAssociation(Base):
    """
    知识单元关联表
    
    存储知识单元之间的各种关联关系。
    支持多种关联类型和权重。
    """
    
    __tablename__ = "knowledge_unit_associations"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联类型
    association_type = Column(
        Enum(AssociationType),
        nullable=False,
        index=True,
        comment="关联类型"
    )
    
    # 源单元
    source_unit_id = Column(
        Integer,
        ForeignKey("unified_knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="源单元ID"
    )
    
    # 目标单元
    target_unit_id = Column(
        Integer,
        ForeignKey("unified_knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="目标单元ID"
    )
    
    # 关联权重（0-1）
    weight = Column(Float, nullable=True, default=1.0, comment="关联权重")
    
    # 关联属性
    properties = Column(JSON, nullable=True, comment="关联属性")
    
    # 双向标记
    is_bidirectional = Column(Boolean, default=False, comment="是否双向关联")
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=True, onupdate=func.now(), comment="更新时间")
    
    # 关系
    source_unit = relationship(
        "UnifiedKnowledgeUnit",
        foreign_keys=[source_unit_id],
        back_populates="outgoing_associations"
    )
    target_unit = relationship(
        "UnifiedKnowledgeUnit",
        foreign_keys=[target_unit_id],
        back_populates="incoming_associations"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_assoc_type', 'association_type'),
        Index('idx_assoc_source', 'source_unit_id', 'association_type'),
        Index('idx_assoc_target', 'target_unit_id', 'association_type'),
        Index('idx_assoc_pair', 'source_unit_id', 'target_unit_id'),
        UniqueConstraint(
            'source_unit_id', 'target_unit_id', 'association_type',
            name='uq_assoc_pair_type'
        ),
    )
    
    def __repr__(self):
        return f"<KnowledgeUnitAssociation({self.source_unit_id} -> {self.target_unit_id}, {self.association_type.value})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "association_type": self.association_type.value,
            "source_unit_id": self.source_unit_id,
            "target_unit_id": self.target_unit_id,
            "weight": self.weight,
            "properties": self.properties,
            "is_bidirectional": self.is_bidirectional,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProcessingPipelineRun(Base):
    """
    处理流水线运行记录表
    
    记录知识单元在流水线中的处理历史。
    """
    
    __tablename__ = "processing_pipeline_runs"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的知识单元
    knowledge_unit_id = Column(
        Integer,
        ForeignKey("unified_knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="知识单元ID"
    )
    
    # 流水线信息
    pipeline_name = Column(String(100), nullable=False, comment="流水线名称")
    pipeline_version = Column(String(20), nullable=True, comment="流水线版本")
    
    # 运行状态
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="状态: pending/running/completed/failed"
    )
    
    # 阶段信息
    current_stage = Column(String(50), nullable=True, comment="当前阶段")
    completed_stages = Column(JSON, nullable=True, default=list, comment="已完成阶段")
    
    # 处理统计
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    duration_ms = Column(Integer, nullable=True, comment="耗时（毫秒）")
    
    # 输入输出
    input_data_hash = Column(String(64), nullable=True, comment="输入数据哈希")
    output_data_hash = Column(String(64), nullable=True, comment="输出数据哈希")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_stage = Column(String(50), nullable=True, comment="错误发生的阶段")
    
    # 元数据（使用 meta_data 避免与 SQLAlchemy 保留字冲突）
    meta_data = Column(JSON, nullable=True, comment="运行元数据")
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=True, onupdate=func.now(), comment="更新时间")
    
    # 关系
    knowledge_unit = relationship(
        "UnifiedKnowledgeUnit",
        back_populates="pipeline_runs"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_pipeline_unit_status', 'knowledge_unit_id', 'status'),
        Index('idx_pipeline_name_status', 'pipeline_name', 'status'),
        Index('idx_pipeline_time', 'started_at', 'completed_at'),
    )
    
    def __repr__(self):
        return f"<ProcessingPipelineRun(id={self.id}, unit={self.knowledge_unit_id}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "knowledge_unit_id": self.knowledge_unit_id,
            "pipeline_name": self.pipeline_name,
            "pipeline_version": self.pipeline_version,
            "status": self.status,
            "current_stage": self.current_stage,
            "completed_stages": self.completed_stages,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "error_stage": self.error_stage,
            "metadata": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def mark_stage_complete(self, stage_name: str):
        """标记阶段完成"""
        if self.completed_stages is None:
            self.completed_stages = []
        if stage_name not in self.completed_stages:
            self.completed_stages.append(stage_name)
    
    def calculate_duration(self):
        """计算运行时长"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class KnowledgeUnitIndex(Base):
    """
    知识单元索引表
    
    用于优化查询性能的辅助索引。
    """
    
    __tablename__ = "knowledge_unit_indices"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 知识单元ID
    knowledge_unit_id = Column(
        Integer,
        ForeignKey("unified_knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # 索引字段
    keywords = Column(JSON, nullable=True, comment="关键词列表")
    categories = Column(JSON, nullable=True, comment="分类列表")
    tags = Column(JSON, nullable=True, comment="标签列表")
    
    # 搜索优化
    search_text = Column(Text, nullable=True, comment="搜索文本（分词后）")
    search_vector = Column(JSON, nullable=True, comment="搜索向量")
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    knowledge_unit = relationship("UnifiedKnowledgeUnit")
    
    def __repr__(self):
        return f"<KnowledgeUnitIndex(unit_id={self.knowledge_unit_id})>"


# 更新 KnowledgeBase 模型，添加反向关系
# 注意：这需要在 knowledge_document.py 中更新
# KnowledgeBase.knowledge_units = relationship(
#     "UnifiedKnowledgeUnit",
#     back_populates="knowledge_base",
#     cascade="all, delete-orphan"
# )
