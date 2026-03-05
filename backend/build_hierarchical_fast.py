"""
分层知识图谱快速构建脚本

使用优化的算法：
1. 基于精确匹配的快速去重
2. 简化的相似度计算
3. 批量处理
"""

import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import time
from collections import defaultdict
from difflib import SequenceMatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

engine = create_engine('sqlite:///py_copilot.db')
Session = sessionmaker(bind=engine)


def fast_text_similarity(text1: str, text2: str) -> float:
    """快速文本相似度计算"""
    if not text1 or not text2:
        return 0.0
    
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    
    if t1 == t2:
        return 1.0
    
    # 使用SequenceMatcher快速计算
    return SequenceMatcher(None, t1, t2).ratio()


def build_kb_level_fast(knowledge_base_id: int, db) -> dict:
    """
    快速构建知识库级实体
    
    策略：
    1. 精确匹配分组（完全相同文本）
    2. 高相似度合并（>0.85）
    """
    from app.modules.knowledge.models.knowledge_document import (
        DocumentEntity, KBEntity, KnowledgeDocument
    )
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📚 快速构建知识库 {knowledge_base_id}")
    logger.info(f"{'='*70}")
    
    start_time = time.time()
    
    # 1. 获取所有文档实体
    entities = db.query(DocumentEntity).join(
        KnowledgeDocument
    ).filter(
        KnowledgeDocument.knowledge_base_id == knowledge_base_id
    ).all()
    
    if not entities:
        return {'success': True, 'kb_entities_created': 0, 'entities_aligned': 0}
    
    logger.info(f"获取到 {len(entities)} 个文档实体")
    
    # 2. 按类型分组
    type_groups = defaultdict(list)
    for entity in entities:
        type_groups[entity.entity_type].append(entity)
    
    logger.info(f"实体类型分布: {dict((k, len(v)) for k, v in type_groups.items())}")
    
    total_kb_entities = 0
    total_aligned = 0
    
    # 3. 对每个类型组进行快速对齐
    for entity_type, type_entities in type_groups.items():
        logger.info(f"\n处理类型 '{entity_type}': {len(type_entities)} 个实体")
        
        # 使用精确匹配 + 高相似度合并
        clusters = []
        used = set()
        
        for i, entity in enumerate(type_entities):
            if i in used:
                continue
            
            # 创建新簇
            cluster = [entity]
            used.add(i)
            
            # 查找相似实体
            for j in range(i + 1, len(type_entities)):
                if j in used:
                    continue
                
                other = type_entities[j]
                sim = fast_text_similarity(entity.entity_text, other.entity_text)
                
                if sim >= 0.85:  # 高相似度阈值
                    cluster.append(other)
                    used.add(j)
            
            clusters.append(cluster)
        
        logger.info(f"  聚类完成: {len(clusters)} 个簇")
        
        # 4. 创建KB实体
        for cluster in clusters:
            # 选择最频繁的名称作为规范名称
            name_counts = defaultdict(int)
            for e in cluster:
                name_counts[e.entity_text] += 1
            
            canonical_name = max(name_counts.keys(), key=lambda x: name_counts[x])
            aliases = list(set(e.entity_text for e in cluster if e.entity_text != canonical_name))
            
            # 统计
            doc_ids = set(e.document_id for e in cluster)
            
            # 创建KB实体
            kb_entity = KBEntity(
                knowledge_base_id=knowledge_base_id,
                canonical_name=canonical_name,
                entity_type=entity_type,
                aliases=aliases,
                document_count=len(doc_ids),
                occurrence_count=len(cluster)
            )
            db.add(kb_entity)
            db.flush()
            
            # 关联文档实体
            for e in cluster:
                e.kb_entity_id = kb_entity.id
            
            total_kb_entities += 1
            total_aligned += len(cluster)
        
        # 每类型提交一次
        db.commit()
        logger.info(f"  创建 {len(clusters)} 个KB实体，关联 {len(used)} 个文档实体")
    
    elapsed = time.time() - start_time
    logger.info(f"\n✅ 知识库级构建完成: {total_kb_entities} 个KB实体, {total_aligned} 个对齐, 耗时 {elapsed:.2f}秒")
    
    return {
        'success': True,
        'kb_entities_created': total_kb_entities,
        'entities_aligned': total_aligned
    }


def build_global_level_fast(db) -> dict:
    """快速构建全局级实体"""
    from app.modules.knowledge.models.knowledge_document import (
        KBEntity, GlobalEntity
    )
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🌍 快速构建全局级")
    logger.info(f"{'='*70}")
    
    start_time = time.time()
    
    # 1. 获取所有KB实体
    kb_entities = db.query(KBEntity).all()
    
    if not kb_entities:
        return {'success': True, 'global_entities_created': 0, 'kb_entities_linked': 0}
    
    logger.info(f"获取到 {len(kb_entities)} 个KB实体")
    
    # 2. 按类型分组
    type_groups = defaultdict(list)
    for entity in kb_entities:
        type_groups[entity.entity_type].append(entity)
    
    total_global = 0
    total_linked = 0
    
    # 3. 对每个类型组进行链接
    for entity_type, type_entities in type_groups.items():
        logger.info(f"\n处理类型 '{entity_type}': {len(type_entities)} 个实体")
        
        # 使用精确匹配 + 高相似度合并
        clusters = []
        used = set()
        
        for i, entity in enumerate(type_entities):
            if i in used:
                continue
            
            cluster = [entity]
            used.add(i)
            
            for j in range(i + 1, len(type_entities)):
                if j in used:
                    continue
                
                other = type_entities[j]
                
                # 检查规范名称和别名
                names1 = set([entity.canonical_name] + (entity.aliases or []))
                names2 = set([other.canonical_name] + (other.aliases or []))
                
                # 是否有重叠
                if names1 & names2:
                    cluster.append(other)
                    used.add(j)
                    continue
                
                # 相似度检查
                sim = fast_text_similarity(entity.canonical_name, other.canonical_name)
                if sim >= 0.80:
                    cluster.append(other)
                    used.add(j)
            
            clusters.append(cluster)
        
        logger.info(f"  聚类完成: {len(clusters)} 个簇")
        
        # 4. 创建全局实体
        for cluster in clusters:
            # 选择全局名称
            name_counts = defaultdict(int)
            for e in cluster:
                name_counts[e.canonical_name] += e.occurrence_count
            
            global_name = max(name_counts.keys(), key=lambda x: name_counts[x])
            
            # 收集所有别名
            all_aliases = set()
            for e in cluster:
                all_aliases.add(e.canonical_name)
                all_aliases.update(e.aliases or [])
            all_aliases.discard(global_name)
            
            # 统计
            kb_ids = set(e.knowledge_base_id for e in cluster)
            doc_count = sum(e.document_count for e in cluster)
            
            # 创建全局实体
            global_entity = GlobalEntity(
                global_name=global_name,
                entity_type=entity_type,
                all_aliases=list(all_aliases),
                kb_count=len(kb_ids),
                document_count=doc_count
            )
            db.add(global_entity)
            db.flush()
            
            # 关联KB实体
            for e in cluster:
                e.global_entity_id = global_entity.id
                # 同时更新文档实体
                for doc_entity in e.document_entities:
                    doc_entity.global_entity_id = global_entity.id
            
            total_global += 1
            total_linked += len(cluster)
        
        db.commit()
        logger.info(f"  创建 {len(clusters)} 个全局实体，链接 {len(used)} 个KB实体")
    
    elapsed = time.time() - start_time
    logger.info(f"\n✅ 全局级构建完成: {total_global} 个全局实体, {total_linked} 个链接, 耗时 {elapsed:.2f}秒")
    
    return {
        'success': True,
        'global_entities_created': total_global,
        'kb_entities_linked': total_linked
    }


def main():
    """主函数"""
    db = Session()
    
    try:
        from app.modules.knowledge.models.knowledge_document import KnowledgeBase
        
        # 获取知识库
        knowledge_bases = db.query(KnowledgeBase).all()
        logger.info(f"发现 {len(knowledge_bases)} 个知识库")
        
        # Phase 1: 知识库级
        logger.info(f"\n{'#'*70}")
        logger.info(f"# Phase 1: 知识库级快速构建")
        logger.info(f"{'#'*70}")
        
        for kb in knowledge_bases:
            result = build_kb_level_fast(kb.id, db)
            if not result.get('success'):
                logger.error(f"知识库 {kb.id} 构建失败: {result.get('error')}")
        
        # Phase 2: 全局级
        logger.info(f"\n{'#'*70}")
        logger.info(f"# Phase 2: 全局级快速构建")
        logger.info(f"{'#'*70}")
        
        result = build_global_level_fast(db)
        if not result.get('success'):
            logger.error(f"全局级构建失败: {result.get('error')}")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 分层知识图谱快速构建完成!")
        logger.info(f"{'='*70}")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
