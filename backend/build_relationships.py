"""
关系聚合构建脚本

将文档级关系聚合到知识库级和全局级
"""

import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import time
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

engine = create_engine('sqlite:///py_copilot.db')
Session = sessionmaker(bind=engine)


def aggregate_kb_relationships(knowledge_base_id: int, db) -> dict:
    """
    聚合知识库级关系
    """
    from app.modules.knowledge.models.knowledge_document import (
        EntityRelationship, KBRelationship, DocumentEntity, KnowledgeDocument
    )
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📚 聚合知识库 {knowledge_base_id} 的关系")
    logger.info(f"{'='*70}")
    
    start_time = time.time()
    
    # 1. 获取知识库内所有文档关系
    doc_relationships = db.query(EntityRelationship).join(
        DocumentEntity, EntityRelationship.source_id == DocumentEntity.id
    ).join(
        KnowledgeDocument, DocumentEntity.document_id == KnowledgeDocument.id
    ).filter(
        KnowledgeDocument.knowledge_base_id == knowledge_base_id
    ).all()
    
    if not doc_relationships:
        logger.info("没有文档关系需要聚合")
        return {'success': True, 'kb_relationships_created': 0}
    
    logger.info(f"获取到 {len(doc_relationships)} 个文档关系")
    
    # 2. 按KB实体对和关系类型分组
    rel_groups = defaultdict(list)
    
    for rel in doc_relationships:
        source_kb_id = rel.source_entity.kb_entity_id if rel.source_entity else None
        target_kb_id = rel.target_entity.kb_entity_id if rel.target_entity else None
        
        if source_kb_id and target_kb_id:
            key = (source_kb_id, target_kb_id, rel.relationship_type)
            rel_groups[key].append(rel)
    
    logger.info(f"分组完成: {len(rel_groups)} 个关系组")
    
    # 3. 创建KB级关系
    count = 0
    for (source_kb_id, target_kb_id, rel_type), rels in rel_groups.items():
        # 检查是否已存在
        existing = db.query(KBRelationship).filter(
            KBRelationship.knowledge_base_id == knowledge_base_id,
            KBRelationship.source_kb_entity_id == source_kb_id,
            KBRelationship.target_kb_entity_id == target_kb_id,
            KBRelationship.relationship_type == rel_type
        ).first()
        
        source_rel_ids = [rel.id for rel in rels]
        
        if existing:
            # 更新现有关系
            existing.aggregated_count = len(rels)
            existing.source_relationships = source_rel_ids
        else:
            # 创建新关系
            kb_rel = KBRelationship(
                knowledge_base_id=knowledge_base_id,
                source_kb_entity_id=source_kb_id,
                target_kb_entity_id=target_kb_id,
                relationship_type=rel_type,
                aggregated_count=len(rels),
                source_relationships=source_rel_ids
            )
            db.add(kb_rel)
            count += 1
    
    db.commit()
    
    elapsed = time.time() - start_time
    logger.info(f"✅ 知识库级关系聚合完成: {count} 个新关系, 耗时 {elapsed:.2f}秒")
    
    return {
        'success': True,
        'kb_relationships_created': count
    }


def aggregate_global_relationships(db) -> dict:
    """
    聚合全局级关系
    """
    from app.modules.knowledge.models.knowledge_document import (
        KBRelationship, GlobalRelationship
    )
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🌍 聚合全局级关系")
    logger.info(f"{'='*70}")
    
    start_time = time.time()
    
    # 1. 获取所有KB关系
    kb_relationships = db.query(KBRelationship).all()
    
    if not kb_relationships:
        logger.info("没有KB关系需要聚合")
        return {'success': True, 'global_relationships_created': 0}
    
    logger.info(f"获取到 {len(kb_relationships)} 个KB关系")
    
    # 2. 按全局实体对和关系类型分组
    rel_groups = defaultdict(list)
    
    for rel in kb_relationships:
        source = db.query(KBRelationship).get(rel.id).source_kb_entity if hasattr(rel, 'source_kb_entity') else None
        target = db.query(KBRelationship).get(rel.id).target_kb_entity if hasattr(rel, 'target_kb_entity') else None
        
        # 直接从KB实体获取全局ID
        from app.modules.knowledge.models.knowledge_document import KBEntity
        source_kb = db.query(KBEntity).get(rel.source_kb_entity_id)
        target_kb = db.query(KBEntity).get(rel.target_kb_entity_id)
        
        source_global_id = source_kb.global_entity_id if source_kb else None
        target_global_id = target_kb.global_entity_id if target_kb else None
        
        if source_global_id and target_global_id:
            key = (source_global_id, target_global_id, rel.relationship_type)
            rel_groups[key].append(rel)
    
    logger.info(f"分组完成: {len(rel_groups)} 个关系组")
    
    # 3. 创建全局关系
    count = 0
    for (source_global_id, target_global_id, rel_type), rels in rel_groups.items():
        # 检查是否已存在
        existing = db.query(GlobalRelationship).filter(
            GlobalRelationship.source_global_entity_id == source_global_id,
            GlobalRelationship.target_global_entity_id == target_global_id,
            GlobalRelationship.relationship_type == rel_type
        ).first()
        
        source_kb_ids = [rel.id for rel in rels]
        total_count = sum(rel.aggregated_count for rel in rels)
        
        # 收集来源知识库ID
        kb_ids = list(set(rel.knowledge_base_id for rel in rels))
        
        if existing:
            # 更新现有关系
            existing.aggregated_count = total_count
            existing.source_kbs = kb_ids
        else:
            # 创建新关系
            global_rel = GlobalRelationship(
                source_global_entity_id=source_global_id,
                target_global_entity_id=target_global_id,
                relationship_type=rel_type,
                aggregated_count=total_count,
                source_kbs=kb_ids
            )
            db.add(global_rel)
            count += 1
    
    db.commit()
    
    elapsed = time.time() - start_time
    logger.info(f"✅ 全局级关系聚合完成: {count} 个新关系, 耗时 {elapsed:.2f}秒")
    
    return {
        'success': True,
        'global_relationships_created': count
    }


def main():
    """主函数"""
    db = Session()
    
    try:
        from app.modules.knowledge.models.knowledge_document import KnowledgeBase
        
        # 获取知识库
        knowledge_bases = db.query(KnowledgeBase).all()
        logger.info(f"发现 {len(knowledge_bases)} 个知识库")
        
        # Phase 1: 聚合知识库级关系
        logger.info(f"\n{'#'*70}")
        logger.info(f"# Phase 1: 知识库级关系聚合")
        logger.info(f"{'#'*70}")
        
        for kb in knowledge_bases:
            result = aggregate_kb_relationships(kb.id, db)
            if not result.get('success'):
                logger.error(f"知识库 {kb.id} 关系聚合失败: {result.get('error')}")
        
        # Phase 2: 聚合全局级关系
        logger.info(f"\n{'#'*70}")
        logger.info(f"# Phase 2: 全局级关系聚合")
        logger.info(f"{'#'*70}")
        
        result = aggregate_global_relationships(db)
        if not result.get('success'):
            logger.error(f"全局级关系聚合失败: {result.get('error')}")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 关系聚合完成!")
        logger.info(f"{'='*70}")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
