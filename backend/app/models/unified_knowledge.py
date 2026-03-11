"""
一体化知识管理模型 - DB-001

定义统一知识单元、关联、处理流水线等核心数据模型

@task DB-001
@phase 数据库任务
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, Index, UniqueConstraint, JSON, Enum
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from .base import Base


class UnifiedKnowledgeUnit(Base):
    """
    统一知识单元模型
    
    整合文档、片段、实体、概念等多种知识表示形式
    """
    __tablename__ = 'unified_knowledge_units'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(String(64), unique=True, nullable=False, comment='全局唯一单元ID')
    
    # 外键关联
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(Integer, ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True)
    parent_unit_id = Column(String(64), ForeignKey('unified_knowledge_units.unit_id', ondelete='SET NULL'), nullable=True)
    
    # 单元类型和状态
    unit_type = Column(String(50), nullable=False, comment='单元类型: DOCUMENT/CHUNK/ENTITY/CONCEPT')
    status = Column(String(20), nullable=False, default='active', comment='状态: active/archived/deleted')
    
    # 内容信息
    title = Column(String(500), nullable=True, comment='单元标题')
    content = Column(Text, nullable=True, comment='单元内容')
    content_hash = Column(String(64), nullable=True, comment='内容哈希')
    
    # 向量化信息
    vector_id = Column(String(64), nullable=True, comment='向量存储ID')
    vector_status = Column(String(20), nullable=True, comment='向量化状态: pending/processing/completed/failed')
    vector_version = Column(Integer, nullable=False, default=1, comment='向量版本')
    
    # 质量评估
    quality_score = Column(Float, nullable=True, comment='质量分数 0-100')
    quality_dimensions = Column(JSON, nullable=True, comment='各维度质量评分')
    
    # 元数据
    metadata = Column(JSON, nullable=True, comment='扩展元数据')
    position = Column(JSON, nullable=True, comment='位置信息(起始/结束位置)')
    hierarchy_path = Column(String(500), nullable=True, comment='层级路径')
    depth = Column(Integer, nullable=False, default=0, comment='层级深度')
    
    # 统计信息
    child_count = Column(Integer, nullable=False, default=0, comment='子单元数量')
    association_count = Column(Integer, nullable=False, default=0, comment='关联数量')
    access_count = Column(Integer, nullable=False, default=0, comment='访问次数')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    vectorized_at = Column(DateTime, nullable=True, comment='向量化完成时间')
    last_accessed_at = Column(DateTime, nullable=True, comment='最后访问时间')
    
    # 关系定义
    knowledge_base = relationship('KnowledgeBase', back_populates='knowledge_units')
    document = relationship('KnowledgeDocument', back_populates='knowledge_units')
    parent = relationship('UnifiedKnowledgeUnit', remote_side=[unit_id], back_populates='children')
    children = relationship('UnifiedKnowledgeUnit', back_populates='parent', lazy='dynamic')
    
    # 关联关系
    outgoing_associations = relationship(
        'KnowledgeUnitAssociation',
        foreign_keys='KnowledgeUnitAssociation.source_unit_id',
        back_populates='source_unit',
        lazy='dynamic'
    )
    incoming_associations = relationship(
        'KnowledgeUnitAssociation',
        foreign_keys='KnowledgeUnitAssociation.target_unit_id',
        back_populates='target_unit',
        lazy='dynamic'
    )
    
    # 版本历史
    versions = relationship('KnowledgeUnitVersion', back_populates='unit', lazy='dynamic')
    
    # 向量元数据
    vector_metadata = relationship('VectorMetadata', back_populates='unit', uselist=False)
    
    # 索引定义
    __table_args__ = (
        Index('idx_uku_unit_id', 'unit_id', unique=True),
        Index('idx_uku_kb_id', 'knowledge_base_id'),
        Index('idx_uku_doc_id', 'document_id'),
        Index('idx_uku_parent_id', 'parent_unit_id'),
        Index('idx_uku_type', 'unit_type'),
        Index('idx_uku_status', 'status'),
        Index('idx_uku_vector_status', 'vector_status'),
        Index('idx_uku_quality', 'quality_score'),
        Index('idx_uku_created_at', 'created_at'),
        Index('idx_uku_kb_type', 'knowledge_base_id', 'unit_type'),
        Index('idx_uku_kb_status', 'knowledge_base_id', 'status'),
    )
    
    @validates('unit_type')
    def validate_unit_type(self, key, value):
        """验证单元类型"""
        valid_types = {'DOCUMENT', 'CHUNK', 'ENTITY', 'CONCEPT', 'RELATIONSHIP'}
        if value not in valid_types:
            raise ValueError(f'Invalid unit_type: {value}. Must be one of {valid_types}')
        return value
    
    @validates('status')
    def validate_status(self, key, value):
        """验证状态"""
        valid_statuses = {'active', 'archived', 'deleted'}
        if value not in valid_statuses:
            raise ValueError(f'Invalid status: {value}. Must be one of {valid_statuses}')
        return value
    
    @validates('vector_status')
    def validate_vector_status(self, key, value):
        """验证向量化状态"""
        if value is not None:
            valid_statuses = {'pending', 'processing', 'completed', 'failed'}
            if value not in valid_statuses:
                raise ValueError(f'Invalid vector_status: {value}. Must be one of {valid_statuses}')
        return value
    
    @validates('quality_score')
    def validate_quality_score(self, key, value):
        """验证质量分数"""
        if value is not None and not (0 <= value <= 100):
            raise ValueError('Quality score must be between 0 and 100')
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'knowledge_base_id': self.knowledge_base_id,
            'document_id': self.document_id,
            'parent_unit_id': self.parent_unit_id,
            'unit_type': self.unit_type,
            'status': self.status,
            'title': self.title,
            'content': self.content,
            'content_hash': self.content_hash,
            'vector_id': self.vector_id,
            'vector_status': self.vector_status,
            'vector_version': self.vector_version,
            'quality_score': self.quality_score,
            'quality_dimensions': self.quality_dimensions,
            'metadata': self.metadata,
            'position': self.position,
            'hierarchy_path': self.hierarchy_path,
            'depth': self.depth,
            'child_count': self.child_count,
            'association_count': self.association_count,
            'access_count': self.access_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'vectorized_at': self.vectorized_at.isoformat() if self.vectorized_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }
    
    def __repr__(self):
        return f'<UnifiedKnowledgeUnit(id={self.id}, unit_id={self.unit_id}, type={self.unit_type})>'


class KnowledgeUnitAssociation(Base):
    """
    知识单元关联模型
    
    表示知识单元之间的各种关联关系
    """
    __tablename__ = 'knowledge_unit_associations'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    association_id = Column(String(64), unique=True, nullable=False, comment='全局唯一关联ID')
    
    # 外键关联
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    source_unit_id = Column(String(64), ForeignKey('unified_knowledge_units.unit_id', ondelete='CASCADE'), nullable=False)
    target_unit_id = Column(String(64), ForeignKey('unified_knowledge_units.unit_id', ondelete='CASCADE'), nullable=False)
    
    # 关联属性
    association_type = Column(String(50), nullable=False, comment='关联类型')
    strength = Column(Float, nullable=False, default=1.0, comment='关联强度 0-1')
    bidirectional = Column(Boolean, nullable=False, default=False, comment='是否双向')
    
    # 关联元数据
    metadata = Column(JSON, nullable=True, comment='关联元数据')
    evidence = Column(Text, nullable=True, comment='关联证据/依据')
    confidence = Column(Float, nullable=True, comment='置信度 0-1')
    
    # 状态
    status = Column(String(20), nullable=False, default='active', comment='状态: active/inactive/deleted')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # 关系定义
    knowledge_base = relationship('KnowledgeBase')
    source_unit = relationship(
        'UnifiedKnowledgeUnit',
        foreign_keys=[source_unit_id],
        back_populates='outgoing_associations'
    )
    target_unit = relationship(
        'UnifiedKnowledgeUnit',
        foreign_keys=[target_unit_id],
        back_populates='incoming_associations'
    )
    
    # 索引定义
    __table_args__ = (
        UniqueConstraint('source_unit_id', 'target_unit_id', 'association_type', name='unique_association'),
        Index('idx_kua_association_id', 'association_id', unique=True),
        Index('idx_kua_kb_id', 'knowledge_base_id'),
        Index('idx_kua_source', 'source_unit_id'),
        Index('idx_kua_target', 'target_unit_id'),
        Index('idx_kua_type', 'association_type'),
        Index('idx_kua_strength', 'strength'),
        Index('idx_kua_status', 'status'),
        Index('idx_kua_kb_type', 'knowledge_base_id', 'association_type'),
    )
    
    @validates('association_type')
    def validate_association_type(self, key, value):
        """验证关联类型"""
        valid_types = {
            'CONTAINS', 'REFERENCES', 'SIMILAR_TO', 'RELATED_TO',
            'PART_OF', 'INSTANCE_OF', 'SUBCLASS_OF', 'MENTIONS'
        }
        if value not in valid_types:
            raise ValueError(f'Invalid association_type: {value}. Must be one of {valid_types}')
        return value
    
    @validates('strength')
    def validate_strength(self, key, value):
        """验证关联强度"""
        if not (0 <= value <= 1):
            raise ValueError('Strength must be between 0 and 1')
        return value
    
    @validates('confidence')
    def validate_confidence(self, key, value):
        """验证置信度"""
        if value is not None and not (0 <= value <= 1):
            raise ValueError('Confidence must be between 0 and 1')
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'association_id': self.association_id,
            'knowledge_base_id': self.knowledge_base_id,
            'source_unit_id': self.source_unit_id,
            'target_unit_id': self.target_unit_id,
            'association_type': self.association_type,
            'strength': self.strength,
            'bidirectional': self.bidirectional,
            'metadata': self.metadata,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<KnowledgeUnitAssociation(id={self.id}, type={self.association_type}, strength={self.strength})>'


class ProcessingPipelineRun(Base):
    """
    处理流水线运行记录模型
    
    记录文档处理、向量化、质量检查等任务的执行历史
    """
    __tablename__ = 'processing_pipeline_runs'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, comment='运行ID')
    
    # 外键关联
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    
    # 处理配置
    pipeline_type = Column(String(50), nullable=False, comment='流水线类型')
    trigger_type = Column(String(20), nullable=False, comment='触发类型: manual/scheduled/event')
    triggered_by = Column(Integer, nullable=True, comment='触发用户ID')
    
    # 处理范围
    target_unit_ids = Column(JSON, nullable=True, comment='目标单元ID列表')
    target_document_ids = Column(JSON, nullable=True, comment='目标文档ID列表')
    
    # 处理配置
    config = Column(JSON, nullable=True, comment='处理配置参数')
    processing_mode = Column(String(20), nullable=True, comment='处理模式: standard/high_quality/fast')
    
    # 状态
    status = Column(String(20), nullable=False, default='pending', 
                    comment='状态: pending/running/paused/completed/failed/cancelled')
    progress = Column(Float, nullable=False, default=0, comment='进度 0-100')
    
    # 统计信息
    total_items = Column(Integer, nullable=False, default=0, comment='总项目数')
    processed_items = Column(Integer, nullable=False, default=0, comment='已处理数')
    success_items = Column(Integer, nullable=False, default=0, comment='成功数')
    failed_items = Column(Integer, nullable=False, default=0, comment='失败数')
    skipped_items = Column(Integer, nullable=False, default=0, comment='跳过数')
    
    # 时间和性能
    started_at = Column(DateTime, nullable=True, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    estimated_duration = Column(Integer, nullable=True, comment='预估耗时(秒)')
    actual_duration = Column(Integer, nullable=True, comment='实际耗时(秒)')
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment='错误信息')
    error_details = Column(JSON, nullable=True, comment='错误详情')
    
    # 结果
    result_summary = Column(JSON, nullable=True, comment='结果摘要')
    output_log = Column(Text, nullable=True, comment='输出日志')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # 关系定义
    knowledge_base = relationship('KnowledgeBase')
    
    # 索引定义
    __table_args__ = (
        Index('idx_ppr_run_id', 'run_id', unique=True),
        Index('idx_ppr_kb_id', 'knowledge_base_id'),
        Index('idx_ppr_type', 'pipeline_type'),
        Index('idx_ppr_status', 'status'),
        Index('idx_ppr_triggered_by', 'triggered_by'),
        Index('idx_ppr_created_at', 'created_at'),
        Index('idx_ppr_kb_status', 'knowledge_base_id', 'status'),
    )
    
    @validates('pipeline_type')
    def validate_pipeline_type(self, key, value):
        """验证流水线类型"""
        valid_types = {
            'document_processing', 'vectorization', 'quality_check',
            'migration', 'reprocessing', 'association_extraction'
        }
        if value not in valid_types:
            raise ValueError(f'Invalid pipeline_type: {value}. Must be one of {valid_types}')
        return value
    
    @validates('trigger_type')
    def validate_trigger_type(self, key, value):
        """验证触发类型"""
        valid_types = {'manual', 'scheduled', 'event', 'api'}
        if value not in valid_types:
            raise ValueError(f'Invalid trigger_type: {value}. Must be one of {valid_types}')
        return value
    
    @validates('status')
    def validate_status(self, key, value):
        """验证状态"""
        valid_statuses = {'pending', 'running', 'paused', 'completed', 'failed', 'cancelled'}
        if value not in valid_statuses:
            raise ValueError(f'Invalid status: {value}. Must be one of {valid_statuses}')
        return value
    
    @validates('progress')
    def validate_progress(self, key, value):
        """验证进度"""
        if not (0 <= value <= 100):
            raise ValueError('Progress must be between 0 and 100')
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'run_id': self.run_id,
            'knowledge_base_id': self.knowledge_base_id,
            'pipeline_type': self.pipeline_type,
            'trigger_type': self.trigger_type,
            'triggered_by': self.triggered_by,
            'target_unit_ids': self.target_unit_ids,
            'target_document_ids': self.target_document_ids,
            'config': self.config,
            'processing_mode': self.processing_mode,
            'status': self.status,
            'progress': self.progress,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'success_items': self.success_items,
            'failed_items': self.failed_items,
            'skipped_items': self.skipped_items,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'result_summary': self.result_summary,
            'output_log': self.output_log,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<ProcessingPipelineRun(id={self.id}, run_id={self.run_id}, status={self.status})>'


class VectorMetadata(Base):
    """
    向量元数据模型
    
    存储向量的元数据信息，便于管理和追踪
    """
    __tablename__ = 'vector_metadata'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    vector_id = Column(String(64), unique=True, nullable=False, comment='向量ID')
    
    # 外键关联
    unit_id = Column(String(64), ForeignKey('unified_knowledge_units.unit_id', ondelete='CASCADE'), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    
    # 向量信息
    embedding_model = Column(String(100), nullable=True, comment='嵌入模型')
    vector_dimension = Column(Integer, nullable=True, comment='向量维度')
    vector_version = Column(Integer, nullable=False, default=1, comment='向量版本')
    
    # 存储信息
    storage_backend = Column(String(50), nullable=True, comment='存储后端: chromadb/faiss/milvus')
    storage_collection = Column(String(100), nullable=True, comment='存储集合名称')
    storage_metadata = Column(JSON, nullable=True, comment='存储相关元数据')
    
    # 状态
    status = Column(String(20), nullable=False, default='active', comment='状态: active/archived/deleted')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # 关系定义
    knowledge_base = relationship('KnowledgeBase')
    unit = relationship('UnifiedKnowledgeUnit', back_populates='vector_metadata')
    
    # 索引定义
    __table_args__ = (
        Index('idx_vm_vector_id', 'vector_id', unique=True),
        Index('idx_vm_unit_id', 'unit_id'),
        Index('idx_vm_kb_id', 'knowledge_base_id'),
        Index('idx_vm_model', 'embedding_model'),
        Index('idx_vm_status', 'status'),
        Index('idx_vm_kb_status', 'knowledge_base_id', 'status'),
    )
    
    @validates('storage_backend')
    def validate_storage_backend(self, key, value):
        """验证存储后端"""
        if value is not None:
            valid_backends = {'chromadb', 'faiss', 'milvus', 'pinecone', 'weaviate'}
            if value not in valid_backends:
                raise ValueError(f'Invalid storage_backend: {value}. Must be one of {valid_backends}')
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'vector_id': self.vector_id,
            'unit_id': self.unit_id,
            'knowledge_base_id': self.knowledge_base_id,
            'embedding_model': self.embedding_model,
            'vector_dimension': self.vector_dimension,
            'vector_version': self.vector_version,
            'storage_backend': self.storage_backend,
            'storage_collection': self.storage_collection,
            'storage_metadata': self.storage_metadata,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<VectorMetadata(id={self.id}, vector_id={self.vector_id}, backend={self.storage_backend})>'


class KnowledgeUnitVersion(Base):
    """
    知识单元版本模型
    
    记录知识单元的历史版本，支持版本回滚和审计
    """
    __tablename__ = 'knowledge_unit_versions'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(String(64), unique=True, nullable=False, comment='版本ID')
    
    # 外键关联
    unit_id = Column(String(64), ForeignKey('unified_knowledge_units.unit_id', ondelete='CASCADE'), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    parent_version_id = Column(String(64), ForeignKey('knowledge_unit_versions.version_id', ondelete='SET NULL'), nullable=True)
    
    # 版本信息
    version_number = Column(Integer, nullable=False, comment='版本号')
    version_type = Column(String(20), nullable=False, comment='版本类型: major/minor/patch')
    
    # 内容快照
    title = Column(String(500), nullable=True, comment='标题快照')
    content = Column(Text, nullable=True, comment='内容快照')
    content_hash = Column(String(64), nullable=True, comment='内容哈希')
    metadata_snapshot = Column(JSON, nullable=True, comment='元数据快照')
    
    # 变更信息
    change_summary = Column(Text, nullable=True, comment='变更摘要')
    change_type = Column(String(50), nullable=True, 
                         comment='变更类型: create/update/delete/merge/split')
    changed_fields = Column(JSON, nullable=True, comment='变更字段列表')
    
    # 版本关系
    merged_from_versions = Column(JSON, nullable=True, comment='合并来源版本')
    
    # 创建信息
    created_by = Column(Integer, nullable=True, comment='创建用户ID')
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    
    # 关系定义
    knowledge_base = relationship('KnowledgeBase')
    unit = relationship('UnifiedKnowledgeUnit', back_populates='versions')
    parent_version = relationship('KnowledgeUnitVersion', remote_side=[version_id])
    
    # 索引定义
    __table_args__ = (
        UniqueConstraint('unit_id', 'version_number', name='unique_unit_version'),
        Index('idx_kuv_version_id', 'version_id', unique=True),
        Index('idx_kuv_unit_id', 'unit_id'),
        Index('idx_kuv_kb_id', 'knowledge_base_id'),
        Index('idx_kuv_version_number', 'version_number'),
        Index('idx_kuv_created_at', 'created_at'),
        Index('idx_kuv_unit_version', 'unit_id', 'version_number'),
    )
    
    @validates('version_type')
    def validate_version_type(self, key, value):
        """验证版本类型"""
        valid_types = {'major', 'minor', 'patch'}
        if value not in valid_types:
            raise ValueError(f'Invalid version_type: {value}. Must be one of {valid_types}')
        return value
    
    @validates('change_type')
    def validate_change_type(self, key, value):
        """验证变更类型"""
        if value is not None:
            valid_types = {'create', 'update', 'delete', 'merge', 'split', 'rollback'}
            if value not in valid_types:
                raise ValueError(f'Invalid change_type: {value}. Must be one of {valid_types}')
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'unit_id': self.unit_id,
            'knowledge_base_id': self.knowledge_base_id,
            'version_number': self.version_number,
            'version_type': self.version_type,
            'title': self.title,
            'content': self.content,
            'content_hash': self.content_hash,
            'metadata_snapshot': self.metadata_snapshot,
            'change_summary': self.change_summary,
            'change_type': self.change_type,
            'changed_fields': self.changed_fields,
            'merged_from_versions': self.merged_from_versions,
            'parent_version_id': self.parent_version_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<KnowledgeUnitVersion(id={self.id}, unit_id={self.unit_id}, version={self.version_number})>'
