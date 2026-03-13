"""
统一数据模型使用示例 - 向量化管理模块优化

展示如何使用 UnifiedKnowledgeUnit 和相关服务。

任务编号: BE-009
阶段: Phase 3 - 一体化建设期
"""

import logging
from typing import List, Dict, Any

from app.modules.knowledge.models.unified_knowledge_unit import (
    UnifiedKnowledgeUnit,
    KnowledgeUnitAssociation,
    ProcessingPipelineRun,
    KnowledgeUnitType,
    KnowledgeUnitStatus,
    AssociationType
)
from app.services.knowledge.unified_knowledge_service import (
    UnifiedKnowledgeService,
    create_knowledge_unit,
    get_knowledge_unit,
    search_knowledge_units
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 创建知识单元 ====================

def example_create_units():
    """创建知识单元示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 创建知识单元")
    logger.info("=" * 60)
    
    service = UnifiedKnowledgeService()
    
    # 示例：创建文档单元
    doc_unit = create_knowledge_unit(
        unit_type=KnowledgeUnitType.DOCUMENT,
        knowledge_base_id=1,
        content="人工智能（AI）是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。",
        metadata={
            "title": "人工智能简介",
            "author": "张三",
            "tags": ["AI", "人工智能", "计算机科学"]
        },
        source_type="document",
        source_id="doc_001",
        source_location="/docs/ai_intro.pdf"
    )
    
    logger.info(f"创建文档单元: id={doc_unit.id}, type={doc_unit.unit_type.value}")
    
    # 示例：创建片段单元
    chunk_unit = create_knowledge_unit(
        unit_type=KnowledgeUnitType.CHUNK,
        knowledge_base_id=1,
        content="机器学习是人工智能的核心技术之一。",
        metadata={
            "chunk_index": 0,
            "parent_document_id": "doc_001"
        },
        source_type="chunk",
        source_id="chunk_001"
    )
    
    logger.info(f"创建片段单元: id={chunk_unit.id}, type={chunk_unit.unit_type.value}")
    
    # 示例：创建实体单元
    entity_unit = create_knowledge_unit(
        unit_type=KnowledgeUnitType.ENTITY,
        knowledge_base_id=1,
        content="机器学习",
        metadata={
            "entity_type": "CONCEPT",
            "aliases": ["Machine Learning", "ML"]
        },
        source_type="entity",
        source_id="entity_001"
    )
    
    logger.info(f"创建实体单元: id={entity_unit.id}, type={entity_unit.unit_type.value}")


# ==================== 示例 2: 关联管理 ====================

def example_association_management():
    """关联管理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 关联管理")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        # 创建两个知识单元
        doc_unit = service.create_knowledge_unit(
            db=db,
            unit_type=KnowledgeUnitType.DOCUMENT,
            knowledge_base_id=1,
            content="深度学习文档",
            source_type="document",
            source_id="doc_assoc_001"
        )
        
        chunk_unit = service.create_knowledge_unit(
            db=db,
            unit_type=KnowledgeUnitType.CHUNK,
            knowledge_base_id=1,
            content="深度学习是机器学习的一个子集",
            source_type="chunk",
            source_id="chunk_assoc_001"
        )
        
        # 创建关联（文档包含片段）
        association = service.create_association(
            db=db,
            source_unit_id=doc_unit.id,
            target_unit_id=chunk_unit.id,
            association_type=AssociationType.CONTAINS,
            weight=1.0,
            properties={"chunk_index": 0}
        )
        
        logger.info(f"创建关联: {doc_unit.id} -> {chunk_unit.id}, type={association.association_type.value}")
        
        # 查询相关单元
        related = service.get_related_units(
            db=db,
            unit_id=doc_unit.id,
            association_type=AssociationType.CONTAINS
        )
        
        logger.info(f"找到 {len(related)} 个相关单元")
        for item in related:
            logger.info(f"  - {item['unit']['id']}: {item['unit']['content'][:30]}...")


# ==================== 示例 3: 版本控制 ====================

def example_version_control():
    """版本控制示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 版本控制")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        # 创建初始版本
        unit_v1 = service.create_knowledge_unit(
            db=db,
            unit_type=KnowledgeUnitType.DOCUMENT,
            knowledge_base_id=1,
            content="这是第一版内容",
            source_type="document",
            source_id="doc_version_001"
        )
        
        logger.info(f"创建 V1: id={unit_v1.id}, version={unit_v1.version}, is_current={unit_v1.is_current}")
        
        # 创建新版本
        unit_v2 = service.update_knowledge_unit(
            db=db,
            unit_id=unit_v1.id,
            updates={"content": "这是第二版内容，更新了部分信息"},
            create_version=True
        )
        
        logger.info(f"创建 V2: id={unit_v2.id}, version={unit_v2.version}, is_current={unit_v2.is_current}")
        
        # 检查旧版本状态
        db.refresh(unit_v1)
        logger.info(f"V1 状态: is_current={unit_v1.is_current}")
        
        # 获取所有版本
        versions = unit_v2.child_units if hasattr(unit_v2, 'child_units') else []
        logger.info(f"版本链: V2 的父单元是 V1 (id={unit_v2.parent_unit_id})")


# ==================== 示例 4: 搜索查询 ====================

def example_search():
    """搜索查询示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 搜索查询")
    logger.info("=" * 60)
    
    # 搜索知识单元
    units, total = search_knowledge_units(
        knowledge_base_id=1,
        unit_type=KnowledgeUnitType.DOCUMENT,
        status=KnowledgeUnitStatus.ACTIVE,
        limit=10
    )
    
    logger.info(f"搜索到 {total} 个文档单元")
    for unit in units[:5]:
        logger.info(f"  - ID: {unit.id}, Content: {unit.content[:50] if unit.content else 'N/A'}...")


# ==================== 示例 5: 去重检测 ====================

def example_deduplication():
    """去重检测示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 去重检测")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        # 创建重复内容
        content = "这是重复的内容示例"
        
        unit1 = service.create_knowledge_unit(
            db=db,
            unit_type=KnowledgeUnitType.DOCUMENT,
            knowledge_base_id=1,
            content=content,
            source_type="document",
            source_id="dup_001"
        )
        
        # 尝试创建重复内容（应该检测到）
        existing = service.find_by_content_hash(
            db=db,
            content_hash=unit1.content_hash,
            knowledge_base_id=1
        )
        
        if existing:
            logger.info(f"检测到重复内容: 已存在单元 id={existing.id}")
        
        # 查找所有重复
        duplicates = service.find_duplicates(db, knowledge_base_id=1)
        logger.info(f"发现 {len(duplicates)} 组重复内容")


# ==================== 示例 6: 流水线运行记录 ====================

def example_pipeline_run():
    """流水线运行记录示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 流水线运行记录")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        # 创建知识单元
        unit = service.create_knowledge_unit(
            db=db,
            unit_type=KnowledgeUnitType.DOCUMENT,
            knowledge_base_id=1,
            content="待处理文档",
            source_type="document",
            source_id="pipeline_doc_001"
        )
        
        # 创建流水线运行记录
        run = service.create_pipeline_run(
            db=db,
            knowledge_unit_id=unit.id,
            pipeline_name="document_processing",
            pipeline_version="1.0.0"
        )
        
        logger.info(f"创建流水线记录: id={run.id}, status={run.status}")
        
        # 更新阶段
        service.update_pipeline_run_status(
            db=db,
            run_id=run.id,
            status="running",
            current_stage="text_extraction"
        )
        
        logger.info(f"更新阶段: text_extraction")
        
        # 完成
        service.update_pipeline_run_status(
            db=db,
            run_id=run.id,
            status="completed",
            current_stage="vectorization"
        )
        
        logger.info(f"流水线完成")


# ==================== 示例 7: 批量操作 ====================

def example_batch_operations():
    """批量操作示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 批量操作")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        # 批量创建
        units_data = [
            {
                "unit_type": KnowledgeUnitType.CHUNK,
                "knowledge_base_id": 1,
                "content": f"批量创建的片段 {i}",
                "source_type": "chunk",
                "source_id": f"batch_chunk_{i}"
            }
            for i in range(5)
        ]
        
        created, failed = service.batch_create_units(db, units_data)
        
        logger.info(f"批量创建: {len(created)} 成功, {len(failed)} 失败")
        
        # 批量更新状态
        unit_ids = [unit.id for unit in created]
        updated_count = service.batch_update_status(
            db=db,
            unit_ids=unit_ids,
            new_status=KnowledgeUnitStatus.ACTIVE
        )
        
        logger.info(f"批量更新状态: {updated_count} 个单元")


# ==================== 示例 8: 统计信息 ====================

def example_statistics():
    """统计信息示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 统计信息")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        stats = service.get_statistics(db, knowledge_base_id=1)
        
        logger.info("知识库统计:")
        logger.info(f"  总单元数: {stats['total_count']}")
        logger.info(f"  按类型统计: {stats['type_counts']}")
        logger.info(f"  按状态统计: {stats['status_counts']}")
        logger.info(f"  有向量的单元: {stats['vector_count']}")
        logger.info(f"  向量化率: {stats['vector_rate']:.1%}")


# ==================== 示例 9: 复杂查询 ====================

def example_complex_query():
    """复杂查询示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 复杂查询")
    logger.info("=" * 60)
    
    from app.core.database import get_db_pool
    
    service = UnifiedKnowledgeService()
    db_pool = get_db_pool()
    
    with db_pool.get_db_session() as db:
        # 多条件搜索
        units, total = service.search_knowledge_units(
            db=db,
            knowledge_base_id=1,
            unit_type=KnowledgeUnitType.DOCUMENT,
            status=KnowledgeUnitStatus.ACTIVE,
            content_query="人工智能",
            metadata_filters={"author": "张三"},
            limit=10
        )
        
        logger.info(f"复杂查询: 找到 {total} 个结果")


# ==================== 示例 10: 数据模型转换 ====================

def example_model_conversion():
    """数据模型转换示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 数据模型转换")
    logger.info("=" * 60)
    
    # 模拟从旧模型转换
    old_document = {
        "id": 123,
        "title": "旧文档标题",
        "content": "旧文档内容",
        "file_type": "pdf",
        "knowledge_base_id": 1,
        "is_vectorized": True,
        "vector_id": "vec_123"
    }
    
    # 转换为统一模型
    new_unit_data = {
        "unit_type": KnowledgeUnitType.DOCUMENT,
        "knowledge_base_id": old_document["knowledge_base_id"],
        "content": old_document["content"],
        "metadata": {
            "title": old_document["title"],
            "file_type": old_document["file_type"],
            "original_id": old_document["id"]
        },
        "source_type": "document",
        "source_id": str(old_document["id"]),
        "status": KnowledgeUnitStatus.ACTIVE if old_document["is_vectorized"] else KnowledgeUnitStatus.PENDING
    }
    
    logger.info("模型转换:")
    logger.info(f"  旧模型: {old_document}")
    logger.info(f"  新模型: {new_unit_data}")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("统一数据模型使用示例")
    logger.info("=" * 70)
    
    try:
        example_create_units()
        example_association_management()
        example_version_control()
        example_search()
        example_deduplication()
        example_pipeline_run()
        example_batch_operations()
        example_statistics()
        example_complex_query()
        example_model_conversion()
        
        logger.info("\n" + "=" * 70)
        logger.info("所有示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
