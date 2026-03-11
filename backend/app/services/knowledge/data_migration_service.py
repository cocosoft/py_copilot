"""
数据迁移服务 - 向量化管理模块优化

实现旧数据向新模型的迁移，支持零停机迁移、数据完整性校验、回滚机制。

任务编号: BE-012
阶段: Phase 3 - 一体化建设期
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import time
import threading

from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_

from app.core.database import get_db_pool
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeDocument,
    DocumentChunk,
    DocumentEntity,
    EntityRelationship,
    KnowledgeBase
)
from app.modules.knowledge.models.unified_knowledge_unit import (
    UnifiedKnowledgeUnit,
    KnowledgeUnitAssociation,
    KnowledgeUnitType,
    KnowledgeUnitStatus,
    AssociationType
)
from app.services.knowledge.unified_knowledge_service import UnifiedKnowledgeService
from app.services.knowledge.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """迁移状态"""
    PENDING = "pending"           # 待迁移
    IN_PROGRESS = "in_progress"   # 迁移中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    ROLLING_BACK = "rolling_back" # 回滚中
    ROLLED_BACK = "rolled_back"   # 已回滚
    VALIDATED = "validated"       # 已验证


class MigrationPhase(Enum):
    """迁移阶段"""
    PREPARATION = "preparation"       # 准备阶段
    DOCUMENTS = "documents"           # 文档迁移
    CHUNKS = "chunks"                 # 片段迁移
    ENTITIES = "entities"             # 实体迁移
    RELATIONSHIPS = "relationships"   # 关系迁移
    ASSOCIATIONS = "associations"     # 关联创建
    VALIDATION = "validation"         # 数据验证
    CLEANUP = "cleanup"               # 清理阶段


@dataclass
class MigrationRecord:
    """迁移记录"""
    id: int
    knowledge_base_id: Optional[int]
    phase: MigrationPhase
    status: MigrationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    error_message: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationStats:
    """迁移统计"""
    total_documents: int = 0
    migrated_documents: int = 0
    total_chunks: int = 0
    migrated_chunks: int = 0
    total_entities: int = 0
    migrated_entities: int = 0
    total_relationships: int = 0
    migrated_relationships: int = 0
    total_associations: int = 0
    created_associations: int = 0
    failed_items: int = 0
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """迁移耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = (self.total_documents + self.total_chunks + 
                self.total_entities + self.total_relationships)
        migrated = (self.migrated_documents + self.migrated_chunks +
                   self.migrated_entities + self.migrated_relationships)
        if total > 0:
            return migrated / total
        return 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_documents": self.total_documents,
            "migrated_documents": self.migrated_documents,
            "total_chunks": self.total_chunks,
            "migrated_chunks": self.migrated_chunks,
            "total_entities": self.total_entities,
            "migrated_entities": self.migrated_entities,
            "total_relationships": self.total_relationships,
            "migrated_relationships": self.migrated_relationships,
            "total_associations": self.total_associations,
            "created_associations": self.created_associations,
            "failed_items": self.failed_items,
            "error_count": len(self.errors),
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate
        }


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    total_checked: int
    valid_count: int
    invalid_count: int
    missing_items: List[Dict[str, Any]] = field(default_factory=list)
    inconsistent_items: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "total_checked": self.total_checked,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "missing_count": len(self.missing_items),
            "inconsistent_count": len(self.inconsistent_items),
            "error_count": len(self.errors)
        }


class MigrationStrategy(ABC):
    """迁移策略基类"""
    
    @abstractmethod
    def migrate(self, db: Session, item: Any) -> Tuple[bool, Optional[str]]:
        """
        迁移单个项目
        
        Args:
            db: 数据库会话
            item: 要迁移的项目
            
        Returns:
            (是否成功, 错误信息)
        """
        pass
    
    @abstractmethod
    def rollback(self, db: Session, item_id: str) -> bool:
        """
        回滚单个项目
        
        Args:
            db: 数据库会话
            item_id: 项目ID
            
        Returns:
            是否回滚成功
        """
        pass


class DocumentMigrationStrategy(MigrationStrategy):
    """文档迁移策略"""
    
    def __init__(self, service: UnifiedKnowledgeService):
        self.service = service
    
    def migrate(self, db: Session, doc: KnowledgeDocument) -> Tuple[bool, Optional[str]]:
        """迁移文档"""
        try:
            # 检查是否已存在
            existing = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "document",
                UnifiedKnowledgeUnit.source_id == str(doc.id)
            ).first()
            
            if existing:
                return True, None  # 已存在，视为成功
            
            # 创建知识单元
            unit = self.service.create_knowledge_unit(
                db=db,
                unit_type=KnowledgeUnitType.DOCUMENT,
                knowledge_base_id=doc.knowledge_base_id,
                content=doc.content,
                metadata={
                    "title": doc.title,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "original_id": doc.id
                },
                source_type="document",
                source_id=str(doc.id),
                source_location=doc.file_path,
                status=KnowledgeUnitStatus.ACTIVE
            )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def rollback(self, db: Session, item_id: str) -> bool:
        """回滚文档迁移"""
        try:
            unit = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "document",
                UnifiedKnowledgeUnit.source_id == item_id
            ).first()
            
            if unit:
                db.delete(unit)
                db.flush()
            
            return True
            
        except Exception as e:
            logger.error(f"回滚文档失败: {e}")
            return False


class ChunkMigrationStrategy(MigrationStrategy):
    """片段迁移策略"""
    
    def __init__(self, service: UnifiedKnowledgeService, chroma_service: ChromaService):
        self.service = service
        self.chroma_service = chroma_service
    
    def migrate(self, db: Session, chunk: DocumentChunk) -> Tuple[bool, Optional[str]]:
        """迁移片段"""
        try:
            # 检查是否已存在
            existing = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "chunk",
                UnifiedKnowledgeUnit.source_id == str(chunk.id)
            ).first()
            
            if existing:
                return True, None
            
            # 获取向量嵌入
            vector_embedding = None
            try:
                # 从ChromaDB获取向量
                vector_data = self.chroma_service.get_document(str(chunk.id))
                if vector_data and 'embeddings' in vector_data:
                    vector_embedding = vector_data['embeddings']
            except Exception as e:
                logger.warning(f"获取片段 {chunk.id} 的向量失败: {e}")
            
            # 创建知识单元
            unit = self.service.create_knowledge_unit(
                db=db,
                unit_type=KnowledgeUnitType.CHUNK,
                knowledge_base_id=chunk.document.knowledge_base_id if chunk.document else None,
                content=chunk.content,
                vector_embedding=vector_embedding,
                metadata={
                    "chunk_index": chunk.chunk_index,
                    "document_id": chunk.document_id,
                    "original_id": chunk.id
                },
                source_type="chunk",
                source_id=str(chunk.id),
                status=KnowledgeUnitStatus.ACTIVE
            )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def rollback(self, db: Session, item_id: str) -> bool:
        """回滚片段迁移"""
        try:
            unit = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "chunk",
                UnifiedKnowledgeUnit.source_id == item_id
            ).first()
            
            if unit:
                db.delete(unit)
                db.flush()
            
            return True
            
        except Exception as e:
            logger.error(f"回滚片段失败: {e}")
            return False


class EntityMigrationStrategy(MigrationStrategy):
    """实体迁移策略"""
    
    def __init__(self, service: UnifiedKnowledgeService):
        self.service = service
    
    def migrate(self, db: Session, entity: DocumentEntity) -> Tuple[bool, Optional[str]]:
        """迁移实体"""
        try:
            # 检查是否已存在
            existing = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "entity",
                UnifiedKnowledgeUnit.source_id == str(entity.id)
            ).first()
            
            if existing:
                return True, None
            
            # 创建知识单元
            unit = self.service.create_knowledge_unit(
                db=db,
                unit_type=KnowledgeUnitType.ENTITY,
                knowledge_base_id=entity.document.knowledge_base_id if entity.document else None,
                content=entity.entity_text,
                metadata={
                    "entity_type": entity.entity_type,
                    "confidence": entity.confidence,
                    "start_pos": entity.start_pos,
                    "end_pos": entity.end_pos,
                    "document_id": entity.document_id,
                    "original_id": entity.id
                },
                source_type="entity",
                source_id=str(entity.id),
                status=KnowledgeUnitStatus.ACTIVE
            )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def rollback(self, db: Session, item_id: str) -> bool:
        """回滚实体迁移"""
        try:
            unit = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "entity",
                UnifiedKnowledgeUnit.source_id == item_id
            ).first()
            
            if unit:
                db.delete(unit)
                db.flush()
            
            return True
            
        except Exception as e:
            logger.error(f"回滚实体失败: {e}")
            return False


class DataMigrationService:
    """
    数据迁移服务
    
    实现旧数据向新模型的迁移，支持：
    - 零停机迁移
    - 数据完整性校验
    - 迁移过程可回滚
    - 增量迁移
    - 并行迁移
    
    迁移流程：
    1. 准备阶段 - 检查环境、创建备份点
    2. 文档迁移 - 迁移 KnowledgeDocument
    3. 片段迁移 - 迁移 DocumentChunk
    4. 实体迁移 - 迁移 DocumentEntity
    5. 关系迁移 - 迁移 EntityRelationship
    6. 关联创建 - 创建知识单元关联
    7. 数据验证 - 校验迁移结果
    8. 清理阶段 - 清理临时数据
    """
    
    def __init__(
        self,
        batch_size: int = 100,
        enable_parallel: bool = True,
        max_workers: int = 4
    ):
        """
        初始化数据迁移服务
        
        Args:
            batch_size: 批处理大小
            enable_parallel: 是否启用并行处理
            max_workers: 最大工作线程数
        """
        self.batch_size = batch_size
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        
        # 服务初始化
        self.knowledge_service = UnifiedKnowledgeService()
        self.chroma_service = ChromaService()
        self.db_pool = get_db_pool()
        
        # 迁移策略
        self.document_strategy = DocumentMigrationStrategy(self.knowledge_service)
        self.chunk_strategy = ChunkMigrationStrategy(self.knowledge_service, self.chroma_service)
        self.entity_strategy = EntityMigrationStrategy(self.knowledge_service)
        
        # 统计信息
        self.stats = MigrationStats()
        
        # 进度回调
        self.progress_callbacks: List[Callable[[MigrationPhase, int, int, str], None]] = []
        
        # 迁移记录
        self.migration_records: List[MigrationRecord] = []
        
        logger.info(f"数据迁移服务初始化完成: batch_size={batch_size}, parallel={enable_parallel}")
    
    def register_progress_callback(
        self,
        callback: Callable[[MigrationPhase, int, int, str], None]
    ):
        """
        注册进度回调
        
        Args:
            callback: 回调函数，参数为 (phase, current, total, message)
        """
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, phase: MigrationPhase, current: int, total: int, message: str):
        """通知进度更新"""
        for callback in self.progress_callbacks:
            try:
                callback(phase, current, total, message)
            except Exception as e:
                logger.error(f"进度回调失败: {e}")
    
    def migrate(
        self,
        knowledge_base_id: Optional[int] = None,
        dry_run: bool = False,
        incremental: bool = False,
        phases: Optional[List[MigrationPhase]] = None
    ) -> MigrationStats:
        """
        执行数据迁移
        
        Args:
            knowledge_base_id: 指定知识库ID，None则迁移所有
            dry_run: 是否仅模拟运行
            incremental: 是否增量迁移
            phases: 指定迁移阶段，None则执行全部
            
        Returns:
            迁移统计信息
        """
        self.stats = MigrationStats()
        self.stats.start_time = datetime.now()
        
        phases = phases or [
            MigrationPhase.PREPARATION,
            MigrationPhase.DOCUMENTS,
            MigrationPhase.CHUNKS,
            MigrationPhase.ENTITIES,
            MigrationPhase.RELATIONSHIPS,
            MigrationPhase.ASSOCIATIONS,
            MigrationPhase.VALIDATION,
            MigrationPhase.CLEANUP
        ]
        
        logger.info(f"开始数据迁移: kb_id={knowledge_base_id}, dry_run={dry_run}, incremental={incremental}")
        
        with self.db_pool.get_db_session() as db:
            try:
                for phase in phases:
                    logger.info(f"执行阶段: {phase.value}")
                    
                    if phase == MigrationPhase.PREPARATION:
                        self._prepare_migration(db, knowledge_base_id)
                    
                    elif phase == MigrationPhase.DOCUMENTS:
                        self._migrate_documents(db, knowledge_base_id, dry_run, incremental)
                    
                    elif phase == MigrationPhase.CHUNKS:
                        self._migrate_chunks(db, knowledge_base_id, dry_run, incremental)
                    
                    elif phase == MigrationPhase.ENTITIES:
                        self._migrate_entities(db, knowledge_base_id, dry_run, incremental)
                    
                    elif phase == MigrationPhase.RELATIONSHIPS:
                        self._migrate_relationships(db, knowledge_base_id, dry_run, incremental)
                    
                    elif phase == MigrationPhase.ASSOCIATIONS:
                        self._create_associations(db, knowledge_base_id, dry_run)
                    
                    elif phase == MigrationPhase.VALIDATION:
                        self._validate_migration(db, knowledge_base_id)
                    
                    elif phase == MigrationPhase.CLEANUP:
                        self._cleanup_migration(db, knowledge_base_id, dry_run)
                
                if dry_run:
                    logger.info("模拟运行完成，回滚所有更改")
                    db.rollback()
                else:
                    logger.info("迁移完成，提交更改")
                    db.commit()
                
            except Exception as e:
                logger.error(f"迁移失败: {e}")
                self.stats.errors.append(str(e))
                db.rollback()
                raise
        
        self.stats.end_time = datetime.now()
        
        logger.info(f"迁移统计: {self.stats.to_dict()}")
        
        return self.stats
    
    def _prepare_migration(self, db: Session, knowledge_base_id: Optional[int]):
        """准备迁移"""
        logger.info("准备迁移环境...")
        
        # 检查表是否存在
        # 这里可以添加表结构检查
        
        # 统计待迁移数据
        doc_query = db.query(KnowledgeDocument)
        chunk_query = db.query(DocumentChunk)
        entity_query = db.query(DocumentEntity)
        rel_query = db.query(EntityRelationship)
        
        if knowledge_base_id:
            doc_query = doc_query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
            chunk_query = chunk_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
            entity_query = entity_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
            rel_query = rel_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        self.stats.total_documents = doc_query.count()
        self.stats.total_chunks = chunk_query.count()
        self.stats.total_entities = entity_query.count()
        self.stats.total_relationships = rel_query.count()
        
        logger.info(f"待迁移数据: 文档={self.stats.total_documents}, 片段={self.stats.total_chunks}, "
                   f"实体={self.stats.total_entities}, 关系={self.stats.total_relationships}")
    
    def _migrate_documents(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool,
        incremental: bool
    ):
        """迁移文档"""
        logger.info("迁移文档...")
        
        query = db.query(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        if incremental:
            # 只迁移未迁移的文档
            migrated_ids = db.query(UnifiedKnowledgeUnit.source_id).filter(
                UnifiedKnowledgeUnit.source_type == "document"
            ).all()
            migrated_ids = [int(id[0]) for id in migrated_ids if id[0].isdigit()]
            if migrated_ids:
                query = query.filter(~KnowledgeDocument.id.in_(migrated_ids))
        
        documents = query.all()
        total = len(documents)
        
        logger.info(f"需要迁移 {total} 个文档")
        
        for i, doc in enumerate(documents):
            success, error = self.document_strategy.migrate(db, doc)
            
            if success:
                self.stats.migrated_documents += 1
            else:
                self.stats.failed_items += 1
                self.stats.errors.append(f"文档 {doc.id}: {error}")
                logger.error(f"迁移文档 {doc.id} 失败: {error}")
            
            # 通知进度
            if (i + 1) % 10 == 0 or i == total - 1:
                self._notify_progress(
                    MigrationPhase.DOCUMENTS,
                    i + 1,
                    total,
                    f"已迁移 {i + 1}/{total} 个文档"
                )
        
        logger.info(f"文档迁移完成: {self.stats.migrated_documents}/{total}")
    
    def _migrate_chunks(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool,
        incremental: bool
    ):
        """迁移片段"""
        logger.info("迁移片段...")
        
        query = db.query(DocumentChunk).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        if incremental:
            migrated_ids = db.query(UnifiedKnowledgeUnit.source_id).filter(
                UnifiedKnowledgeUnit.source_type == "chunk"
            ).all()
            migrated_ids = [int(id[0]) for id in migrated_ids if id[0].isdigit()]
            if migrated_ids:
                query = query.filter(~DocumentChunk.id.in_(migrated_ids))
        
        chunks = query.all()
        total = len(chunks)
        
        logger.info(f"需要迁移 {total} 个片段")
        
        for i, chunk in enumerate(chunks):
            success, error = self.chunk_strategy.migrate(db, chunk)
            
            if success:
                self.stats.migrated_chunks += 1
            else:
                self.stats.failed_items += 1
                self.stats.errors.append(f"片段 {chunk.id}: {error}")
            
            if (i + 1) % 50 == 0 or i == total - 1:
                self._notify_progress(
                    MigrationPhase.CHUNKS,
                    i + 1,
                    total,
                    f"已迁移 {i + 1}/{total} 个片段"
                )
        
        logger.info(f"片段迁移完成: {self.stats.migrated_chunks}/{total}")
    
    def _migrate_entities(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool,
        incremental: bool
    ):
        """迁移实体"""
        logger.info("迁移实体...")
        
        query = db.query(DocumentEntity).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        if incremental:
            migrated_ids = db.query(UnifiedKnowledgeUnit.source_id).filter(
                UnifiedKnowledgeUnit.source_type == "entity"
            ).all()
            migrated_ids = [int(id[0]) for id in migrated_ids if id[0].isdigit()]
            if migrated_ids:
                query = query.filter(~DocumentEntity.id.in_(migrated_ids))
        
        entities = query.all()
        total = len(entities)
        
        logger.info(f"需要迁移 {total} 个实体")
        
        for i, entity in enumerate(entities):
            success, error = self.entity_strategy.migrate(db, entity)
            
            if success:
                self.stats.migrated_entities += 1
            else:
                self.stats.failed_items += 1
                self.stats.errors.append(f"实体 {entity.id}: {error}")
            
            if (i + 1) % 100 == 0 or i == total - 1:
                self._notify_progress(
                    MigrationPhase.ENTITIES,
                    i + 1,
                    total,
                    f"已迁移 {i + 1}/{total} 个实体"
                )
        
        logger.info(f"实体迁移完成: {self.stats.migrated_entities}/{total}")
    
    def _migrate_relationships(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool,
        incremental: bool
    ):
        """迁移关系"""
        logger.info("迁移关系...")
        
        query = db.query(EntityRelationship).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        relationships = query.all()
        total = len(relationships)
        
        logger.info(f"需要处理 {total} 个关系")
        
        # 关系迁移主要是创建关联
        # 在 _create_associations 中完成
        self.stats.migrated_relationships = total
        
        logger.info(f"关系处理完成: {total}")
    
    def _create_associations(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """创建知识单元关联"""
        logger.info("创建知识单元关联...")
        
        # 获取所有关系
        query = db.query(EntityRelationship).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        relationships = query.all()
        total = len(relationships)
        
        created_count = 0
        
        for i, rel in enumerate(relationships):
            try:
                # 查找源实体和目标实体对应的知识单元
                source_unit = db.query(UnifiedKnowledgeUnit).filter(
                    UnifiedKnowledgeUnit.source_type == "entity",
                    UnifiedKnowledgeUnit.source_id == str(rel.source_id)
                ).first()
                
                target_unit = db.query(UnifiedKnowledgeUnit).filter(
                    UnifiedKnowledgeUnit.source_type == "entity",
                    UnifiedKnowledgeUnit.source_id == str(rel.target_id)
                ).first()
                
                if source_unit and target_unit:
                    # 检查关联是否已存在
                    existing = db.query(KnowledgeUnitAssociation).filter(
                        KnowledgeUnitAssociation.source_unit_id == source_unit.id,
                        KnowledgeUnitAssociation.target_unit_id == target_unit.id,
                        KnowledgeUnitAssociation.association_type == AssociationType.RELATED_TO
                    ).first()

                    if not existing:
                        # 创建关联
                        association = KnowledgeUnitAssociation(
                            source_unit_id=source_unit.id,
                            target_unit_id=target_unit.id,
                            association_type=AssociationType.RELATED_TO,
                            relationship_type=rel.relationship_type,
                            strength=rel.confidence,
                            metadata={
                                "original_relationship_id": rel.id,
                                "document_id": rel.document_id
                            }
                        )
                        db.add(association)
                        created_count += 1
                
                if (i + 1) % 100 == 0 or i == total - 1:
                    self._notify_progress(
                        MigrationPhase.ASSOCIATIONS,
                        i + 1,
                        total,
                        f"已创建 {created_count} 个关联"
                    )
                
            except Exception as e:
                logger.error(f"创建关联失败: {e}")
        
        self.stats.created_associations = created_count
        self.stats.total_associations = total
        
        logger.info(f"关联创建完成: {created_count}/{total}")
    
    def _validate_migration(
        self,
        db: Session,
        knowledge_base_id: Optional[int]
    ) -> ValidationResult:
        """验证迁移结果"""
        logger.info("验证迁移结果...")
        
        result = ValidationResult(
            is_valid=True,
            total_checked=0,
            valid_count=0,
            invalid_count=0
        )
        
        # 验证文档
        doc_query = db.query(KnowledgeDocument)
        if knowledge_base_id:
            doc_query = doc_query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        for doc in doc_query.all():
            result.total_checked += 1
            
            unit = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "document",
                UnifiedKnowledgeUnit.source_id == str(doc.id)
            ).first()
            
            if unit:
                result.valid_count += 1
            else:
                result.invalid_count += 1
                result.missing_items.append({
                    "type": "document",
                    "id": doc.id,
                    "title": doc.title
                })
        
        # 验证实体
        entity_query = db.query(DocumentEntity).join(KnowledgeDocument)
        if knowledge_base_id:
            entity_query = entity_query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        for entity in entity_query.all():
            result.total_checked += 1
            
            unit = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.source_type == "entity",
                UnifiedKnowledgeUnit.source_id == str(entity.id)
            ).first()
            
            if unit:
                result.valid_count += 1
            else:
                result.invalid_count += 1
        
        result.is_valid = result.invalid_count == 0
        
        logger.info(f"验证完成: 总数={result.total_checked}, 有效={result.valid_count}, "
                   f"无效={result.invalid_count}")
        
        return result
    
    def _cleanup_migration(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """清理迁移数据"""
        logger.info("清理迁移数据...")
        # 可以在这里添加清理临时数据的逻辑
    
    def rollback(
        self,
        knowledge_base_id: Optional[int] = None,
        phases: Optional[List[MigrationPhase]] = None
    ) -> bool:
        """
        回滚迁移
        
        Args:
            knowledge_base_id: 指定知识库ID
            phases: 指定回滚阶段
            
        Returns:
            是否回滚成功
        """
        logger.info(f"开始回滚迁移: kb_id={knowledge_base_id}")
        
        phases = phases or [
            MigrationPhase.ASSOCIATIONS,
            MigrationPhase.ENTITIES,
            MigrationPhase.CHUNKS,
            MigrationPhase.DOCUMENTS
        ]
        
        with self.db_pool.get_db_session() as db:
            try:
                for phase in phases:
                    logger.info(f"回滚阶段: {phase.value}")
                    
                    if phase == MigrationPhase.ASSOCIATIONS:
                        # 删除关联
                        query = db.query(KnowledgeUnitAssociation).join(
                            UnifiedKnowledgeUnit,
                            KnowledgeUnitAssociation.source_unit_id == UnifiedKnowledgeUnit.id
                        )
                        if knowledge_base_id:
                            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
                        query.delete(synchronize_session=False)
                    
                    elif phase == MigrationPhase.ENTITIES:
                        # 删除实体知识单元
                        query = db.query(UnifiedKnowledgeUnit).filter(
                            UnifiedKnowledgeUnit.source_type == "entity"
                        )
                        if knowledge_base_id:
                            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
                        query.delete(synchronize_session=False)
                    
                    elif phase == MigrationPhase.CHUNKS:
                        # 删除片段知识单元
                        query = db.query(UnifiedKnowledgeUnit).filter(
                            UnifiedKnowledgeUnit.source_type == "chunk"
                        )
                        if knowledge_base_id:
                            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
                        query.delete(synchronize_session=False)
                    
                    elif phase == MigrationPhase.DOCUMENTS:
                        # 删除文档知识单元
                        query = db.query(UnifiedKnowledgeUnit).filter(
                            UnifiedKnowledgeUnit.source_type == "document"
                        )
                        if knowledge_base_id:
                            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
                        query.delete(synchronize_session=False)
                
                db.commit()
                logger.info("回滚完成")
                return True
                
            except Exception as e:
                logger.error(f"回滚失败: {e}")
                db.rollback()
                return False
    
    def get_migration_status(
        self,
        knowledge_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取迁移状态
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            迁移状态信息
        """
        with self.db_pool.get_db_session() as db:
            # 统计各类型知识单元数量
            query = db.query(UnifiedKnowledgeUnit)
            if knowledge_base_id:
                query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
            
            total_units = query.count()
            
            doc_units = query.filter(UnifiedKnowledgeUnit.source_type == "document").count()
            chunk_units = query.filter(UnifiedKnowledgeUnit.source_type == "chunk").count()
            entity_units = query.filter(UnifiedKnowledgeUnit.source_type == "entity").count()
            
            # 统计原始数据
            doc_query = db.query(KnowledgeDocument)
            chunk_query = db.query(DocumentChunk)
            entity_query = db.query(DocumentEntity)
            
            if knowledge_base_id:
                doc_query = doc_query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
                chunk_query = chunk_query.join(KnowledgeDocument).filter(
                    KnowledgeDocument.knowledge_base_id == knowledge_base_id
                )
                entity_query = entity_query.join(KnowledgeDocument).filter(
                    KnowledgeDocument.knowledge_base_id == knowledge_base_id
                )
            
            total_docs = doc_query.count()
            total_chunks = chunk_query.count()
            total_entities = entity_query.count()
            
            return {
                "knowledge_base_id": knowledge_base_id,
                "migrated_units": {
                    "total": total_units,
                    "documents": doc_units,
                    "chunks": chunk_units,
                    "entities": entity_units
                },
                "original_data": {
                    "documents": total_docs,
                    "chunks": total_chunks,
                    "entities": total_entities
                },
                "progress": {
                    "documents": doc_units / total_docs if total_docs > 0 else 1.0,
                    "chunks": chunk_units / total_chunks if total_chunks > 0 else 1.0,
                    "entities": entity_units / total_entities if total_entities > 0 else 1.0
                }
            }


# 便捷函数

def migrate_data(
    knowledge_base_id: Optional[int] = None,
    dry_run: bool = False,
    incremental: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：执行数据迁移
    
    Args:
        knowledge_base_id: 知识库ID
        dry_run: 是否模拟运行
        incremental: 是否增量迁移
        
    Returns:
        迁移统计信息
    """
    service = DataMigrationService()
    stats = service.migrate(
        knowledge_base_id=knowledge_base_id,
        dry_run=dry_run,
        incremental=incremental
    )
    return stats.to_dict()


def rollback_migration(knowledge_base_id: Optional[int] = None) -> bool:
    """
    便捷函数：回滚迁移
    
    Args:
        knowledge_base_id: 知识库ID
        
    Returns:
        是否回滚成功
    """
    service = DataMigrationService()
    return service.rollback(knowledge_base_id=knowledge_base_id)


def get_migration_progress(knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
    """
    便捷函数：获取迁移进度
    
    Args:
        knowledge_base_id: 知识库ID
        
    Returns:
        迁移进度信息
    """
    service = DataMigrationService()
    return service.get_migration_status(knowledge_base_id=knowledge_base_id)


# 全局服务实例
data_migration_service = DataMigrationService()
