"""
统一数据模型迁移脚本 - 向量化管理模块优化

将现有数据迁移到统一知识单元模型。

任务编号: BE-009
阶段: Phase 3 - 一体化建设期

使用方法:
    python -m backend.app.services.knowledge.unified_model_migration
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    AssociationType,
    ProcessingPipelineRun
)
from app.services.knowledge.unified_knowledge_service import UnifiedKnowledgeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedModelMigration:
    """
    统一数据模型迁移工具
    
    将现有知识库数据迁移到统一知识单元模型。
    
    迁移内容：
    - KnowledgeDocument -> UnifiedKnowledgeUnit (DOCUMENT)
    - DocumentChunk -> UnifiedKnowledgeUnit (CHUNK)
    - DocumentEntity -> UnifiedKnowledgeUnit (ENTITY)
    - EntityRelationship -> KnowledgeUnitAssociation
    """
    
    def __init__(self):
        """初始化迁移工具"""
        self.service = UnifiedKnowledgeService()
        self.stats = {
            "documents_migrated": 0,
            "chunks_migrated": 0,
            "entities_migrated": 0,
            "relationships_migrated": 0,
            "errors": []
        }
        logger.info("统一数据模型迁移工具初始化完成")
    
    def migrate_all(
        self,
        knowledge_base_id: Optional[int] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        执行完整迁移
        
        Args:
            knowledge_base_id: 指定知识库ID，None则迁移所有
            dry_run: 是否仅模拟运行
            
        Returns:
            迁移统计信息
        """
        logger.info(f"开始数据迁移: knowledge_base_id={knowledge_base_id}, dry_run={dry_run}")
        
        db_pool = get_db_pool()
        
        with db_pool.get_db_session() as db:
            try:
                # 1. 迁移文档
                self._migrate_documents(db, knowledge_base_id, dry_run)
                
                # 2. 迁移片段
                self._migrate_chunks(db, knowledge_base_id, dry_run)
                
                # 3. 迁移实体
                self._migrate_entities(db, knowledge_base_id, dry_run)
                
                # 4. 迁移关系
                self._migrate_relationships(db, knowledge_base_id, dry_run)
                
                # 5. 创建关联
                self._create_associations(db, knowledge_base_id, dry_run)
                
                if dry_run:
                    logger.info("模拟运行完成，不提交更改")
                    db.rollback()
                else:
                    logger.info("迁移完成，提交更改")
                
            except Exception as e:
                logger.error(f"迁移过程中出错: {e}")
                self.stats["errors"].append(str(e))
                db.rollback()
                raise
        
        return self.stats
    
    def _migrate_documents(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """迁移文档"""
        logger.info("开始迁移文档...")
        
        query = db.query(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        documents = query.all()
        
        migrated_count = 0
        for doc in documents:
            try:
                # 检查是否已存在
                existing = db.query(UnifiedKnowledgeUnit).filter(
                    UnifiedKnowledgeUnit.source_type == "document",
                    UnifiedKnowledgeUnit.source_id == str(doc.id)
                ).first()
                
                if existing:
                    logger.debug(f"文档 {doc.id} 已存在，跳过")
                    continue
                
                if not dry_run:
                    # 创建知识单元
                    unit = self.service.create_knowledge_unit(
                        db=db,
                        unit_type=KnowledgeUnitType.DOCUMENT,
                        knowledge_base_id=doc.knowledge_base_id,
                        content=doc.content,
                        metadata={
                            "title": doc.title,
                            "file_type": doc.file_type,
                            "file_path": doc.file_path,
                            "document_metadata": doc.document_metadata,
                            "version": doc.version,
                            "file_hash": doc.file_hash
                        },
                        source_type="document",
                        source_id=str(doc.id),
                        source_location=doc.file_path,
                        status=KnowledgeUnitStatus.ACTIVE if (doc.document_metadata or {}).get('processing_status') == 'completed' else KnowledgeUnitStatus.PENDING
                    )
                    
                    # 如果有向量ID，记录
                    if doc.vector_id:
                        unit.vector_id = doc.vector_id
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移文档 {doc.id} 失败: {e}")
                self.stats["errors"].append(f"Document {doc.id}: {str(e)}")
        
        self.stats["documents_migrated"] = migrated_count
        logger.info(f"文档迁移完成: {migrated_count} 个")
    
    def _migrate_chunks(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """迁移文档片段"""
        logger.info("开始迁移文档片段...")
        
        query = db.query(DocumentChunk).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        chunks = query.all()
        
        migrated_count = 0
        for chunk in chunks:
            try:
                # 检查是否已存在
                existing = db.query(UnifiedKnowledgeUnit).filter(
                    UnifiedKnowledgeUnit.source_type == "chunk",
                    UnifiedKnowledgeUnit.source_id == str(chunk.id)
                ).first()
                
                if existing:
                    continue
                
                if not dry_run:
                    # 查找对应的文档单元
                    doc_unit = db.query(UnifiedKnowledgeUnit).filter(
                        UnifiedKnowledgeUnit.source_type == "document",
                        UnifiedKnowledgeUnit.source_id == str(chunk.document_id)
                    ).first()
                    
                    # 创建片段单元
                    unit = self.service.create_knowledge_unit(
                        db=db,
                        unit_type=KnowledgeUnitType.CHUNK,
                        knowledge_base_id=chunk.document.knowledge_base_id if chunk.document else 0,
                        content=chunk.chunk_text,
                        metadata={
                            "chunk_index": chunk.chunk_index,
                            "total_chunks": chunk.total_chunks,
                            "chunk_metadata": chunk.chunk_metadata,
                            "document_id": chunk.document_id
                        },
                        source_type="chunk",
                        source_id=str(chunk.id),
                        status=KnowledgeUnitStatus.ACTIVE if chunk.vector_id else KnowledgeUnitStatus.PENDING
                    )
                    
                    if chunk.vector_id:
                        unit.vector_id = chunk.vector_id
                    
                    # 创建与文档的关联
                    if doc_unit:
                        self.service.create_association(
                            db=db,
                            source_unit_id=doc_unit.id,
                            target_unit_id=unit.id,
                            association_type=AssociationType.CONTAINS,
                            properties={"chunk_index": chunk.chunk_index}
                        )
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移片段 {chunk.id} 失败: {e}")
                self.stats["errors"].append(f"Chunk {chunk.id}: {str(e)}")
        
        self.stats["chunks_migrated"] = migrated_count
        logger.info(f"片段迁移完成: {migrated_count} 个")
    
    def _migrate_entities(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """迁移实体"""
        logger.info("开始迁移实体...")
        
        query = db.query(DocumentEntity).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        entities = query.all()
        
        migrated_count = 0
        for entity in entities:
            try:
                # 检查是否已存在
                existing = db.query(UnifiedKnowledgeUnit).filter(
                    UnifiedKnowledgeUnit.source_type == "entity",
                    UnifiedKnowledgeUnit.source_id == str(entity.id)
                ).first()
                
                if existing:
                    continue
                
                if not dry_run:
                    # 创建实体单元
                    unit = self.service.create_knowledge_unit(
                        db=db,
                        unit_type=KnowledgeUnitType.ENTITY,
                        knowledge_base_id=entity.document.knowledge_base_id if entity.document else 0,
                        content=entity.entity_text,
                        metadata={
                            "entity_type": entity.entity_type,
                            "start_pos": entity.start_pos,
                            "end_pos": entity.end_pos,
                            "confidence": entity.confidence,
                            "document_id": entity.document_id,
                            "kb_entity_id": entity.kb_entity_id,
                            "global_entity_id": entity.global_entity_id
                        },
                        source_type="entity",
                        source_id=str(entity.id),
                        status=KnowledgeUnitStatus.ACTIVE
                    )
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移实体 {entity.id} 失败: {e}")
                self.stats["errors"].append(f"Entity {entity.id}: {str(e)}")
        
        self.stats["entities_migrated"] = migrated_count
        logger.info(f"实体迁移完成: {migrated_count} 个")
    
    def _migrate_relationships(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """迁移关系"""
        logger.info("开始迁移关系...")
        
        query = db.query(EntityRelationship).join(KnowledgeDocument)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        relationships = query.all()
        
        migrated_count = 0
        for rel in relationships:
            try:
                if not dry_run:
                    # 查找源实体和目标实体对应的单元
                    source_unit = db.query(UnifiedKnowledgeUnit).filter(
                        UnifiedKnowledgeUnit.source_type == "entity",
                        UnifiedKnowledgeUnit.source_id == str(rel.source_id)
                    ).first()
                    
                    target_unit = db.query(UnifiedKnowledgeUnit).filter(
                        UnifiedKnowledgeUnit.source_type == "entity",
                        UnifiedKnowledgeUnit.source_id == str(rel.target_id)
                    ).first()
                    
                    if source_unit and target_unit:
                        # 创建关系关联
                        self.service.create_association(
                            db=db,
                            source_unit_id=source_unit.id,
                            target_unit_id=target_unit.id,
                            association_type=AssociationType.RELATED_TO,
                            weight=rel.confidence,
                            properties={
                                "relationship_type": rel.relationship_type,
                                "original_id": rel.id,
                                "document_id": rel.document_id
                            }
                        )
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移关系 {rel.id} 失败: {e}")
                self.stats["errors"].append(f"Relationship {rel.id}: {str(e)}")
        
        self.stats["relationships_migrated"] = migrated_count
        logger.info(f"关系迁移完成: {migrated_count} 个")
    
    def _create_associations(
        self,
        db: Session,
        knowledge_base_id: Optional[int],
        dry_run: bool
    ):
        """创建额外的关联"""
        logger.info("创建额外关联...")
        
        if dry_run:
            return
        
        # 创建实体与文档的 MENTIONS 关联
        entity_units = db.query(UnifiedKnowledgeUnit).filter(
            UnifiedKnowledgeUnit.unit_type == KnowledgeUnitType.ENTITY,
            UnifiedKnowledgeUnit.source_type == "entity"
        )
        
        if knowledge_base_id:
            entity_units = entity_units.filter(
                UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id
            )
        
        for entity_unit in entity_units:
            try:
                document_id = entity_unit.metadata.get("document_id")
                if document_id:
                    doc_unit = db.query(UnifiedKnowledgeUnit).filter(
                        UnifiedKnowledgeUnit.source_type == "document",
                        UnifiedKnowledgeUnit.source_id == str(document_id)
                    ).first()
                    
                    if doc_unit:
                        # 检查关联是否已存在
                        existing = db.query(KnowledgeUnitAssociation).filter(
                            KnowledgeUnitAssociation.source_unit_id == doc_unit.id,
                            KnowledgeUnitAssociation.target_unit_id == entity_unit.id,
                            KnowledgeUnitAssociation.association_type == AssociationType.MENTIONS
                        ).first()
                        
                        if not existing:
                            self.service.create_association(
                                db=db,
                                source_unit_id=doc_unit.id,
                                target_unit_id=entity_unit.id,
                                association_type=AssociationType.MENTIONS,
                                properties={
                                    "entity_type": entity_unit.metadata.get("entity_type"),
                                    "confidence": entity_unit.metadata.get("confidence")
                                }
                            )
            except Exception as e:
                logger.error(f"创建关联失败: {e}")
    
    def verify_migration(
        self,
        knowledge_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        验证迁移结果
        
        Args:
            knowledge_base_id: 知识库ID过滤
            
        Returns:
            验证结果
        """
        logger.info("验证迁移结果...")
        
        db_pool = get_db_pool()
        
        with db_pool.get_db_session() as db:
            # 统计源数据
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
            
            source_stats = {
                "documents": doc_query.count(),
                "chunks": chunk_query.count(),
                "entities": entity_query.count()
            }
            
            # 统计目标数据
            unit_query = db.query(UnifiedKnowledgeUnit)
            if knowledge_base_id:
                unit_query = unit_query.filter(
                    UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id
                )
            
            target_stats = {
                "total_units": unit_query.count(),
                "documents": unit_query.filter(
                    UnifiedKnowledgeUnit.unit_type == KnowledgeUnitType.DOCUMENT
                ).count(),
                "chunks": unit_query.filter(
                    UnifiedKnowledgeUnit.unit_type == KnowledgeUnitType.CHUNK
                ).count(),
                "entities": unit_query.filter(
                    UnifiedKnowledgeUnit.unit_type == KnowledgeUnitType.ENTITY
                ).count(),
            }
            
            # 检查一致性
            consistency = {
                "documents_match": source_stats["documents"] == target_stats["documents"],
                "chunks_match": source_stats["chunks"] == target_stats["chunks"],
                "entities_match": source_stats["entities"] == target_stats["entities"]
            }
            
            return {
                "source_stats": source_stats,
                "target_stats": target_stats,
                "consistency": consistency,
                "all_consistent": all(consistency.values())
            }
    
    def rollback_migration(
        self,
        knowledge_base_id: Optional[int] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        回滚迁移
        
        删除所有迁移创建的统一知识单元。
        
        Args:
            knowledge_base_id: 知识库ID过滤
            dry_run: 是否仅模拟运行
            
        Returns:
            回滚统计
        """
        logger.info(f"回滚迁移: knowledge_base_id={knowledge_base_id}, dry_run={dry_run}")
        
        db_pool = get_db_pool()
        
        stats = {
            "units_deleted": 0,
            "associations_deleted": 0,
            "pipeline_runs_deleted": 0
        }
        
        with db_pool.get_db_session() as db:
            try:
                # 删除关联
                assoc_query = db.query(KnowledgeUnitAssociation).join(
                    UnifiedKnowledgeUnit,
                    KnowledgeUnitAssociation.source_unit_id == UnifiedKnowledgeUnit.id
                )
                
                if knowledge_base_id:
                    assoc_query = assoc_query.filter(
                        UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id
                    )
                
                stats["associations_deleted"] = assoc_query.count()
                
                if not dry_run:
                    assoc_query.delete(synchronize_session=False)
                
                # 删除流水线记录
                run_query = db.query(ProcessingPipelineRun).join(
                    UnifiedKnowledgeUnit
                )
                
                if knowledge_base_id:
                    run_query = run_query.filter(
                        UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id
                    )
                
                stats["pipeline_runs_deleted"] = run_query.count()
                
                if not dry_run:
                    run_query.delete(synchronize_session=False)
                
                # 删除知识单元
                unit_query = db.query(UnifiedKnowledgeUnit)
                
                if knowledge_base_id:
                    unit_query = unit_query.filter(
                        UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id
                    )
                
                stats["units_deleted"] = unit_query.count()
                
                if not dry_run:
                    unit_query.delete(synchronize_session=False)
                
                if dry_run:
                    logger.info("模拟回滚完成，不提交更改")
                    db.rollback()
                else:
                    logger.info("回滚完成，提交更改")
                
            except Exception as e:
                logger.error(f"回滚过程中出错: {e}")
                db.rollback()
                raise
        
        return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一数据模型迁移工具")
    parser.add_argument(
        "--knowledge-base-id",
        type=int,
        help="指定知识库ID，不指定则迁移所有"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，不实际修改数据"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="仅验证迁移结果"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="回滚迁移"
    )
    
    args = parser.parse_args()
    
    migration = UnifiedModelMigration()
    
    if args.verify:
        result = migration.verify_migration(args.knowledge_base_id)
        print("\n验证结果:")
        print(f"  源数据统计: {result['source_stats']}")
        print(f"  目标数据统计: {result['target_stats']}")
        print(f"  一致性检查: {result['consistency']}")
        print(f"  全部一致: {result['all_consistent']}")
    
    elif args.rollback:
        result = migration.rollback_migration(args.knowledge_base_id, args.dry_run)
        print("\n回滚结果:")
        print(f"  删除单元数: {result['units_deleted']}")
        print(f"  删除关联数: {result['associations_deleted']}")
        print(f"  删除流水线记录: {result['pipeline_runs_deleted']}")
    
    else:
        result = migration.migrate_all(args.knowledge_base_id, args.dry_run)
        print("\n迁移结果:")
        print(f"  文档迁移: {result['documents_migrated']}")
        print(f"  片段迁移: {result['chunks_migrated']}")
        print(f"  实体迁移: {result['entities_migrated']}")
        print(f"  关系迁移: {result['relationships_migrated']}")
        if result['errors']:
            print(f"  错误数: {len(result['errors'])}")


if __name__ == "__main__":
    main()
