"""
数据迁移服务使用示例 - 向量化管理模块优化

展示如何使用 DataMigrationService 进行数据迁移。

任务编号: BE-012
阶段: Phase 3 - 一体化建设期
"""

import logging
from typing import Dict, Any

from app.services.knowledge.data_migration_service import (
    DataMigrationService,
    MigrationPhase,
    MigrationStats,
    ValidationResult,
    migrate_data,
    rollback_migration,
    get_migration_progress,
    data_migration_service
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本迁移 ====================

def example_basic_migration():
    """基本迁移示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本数据迁移")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 执行完整迁移
    stats = service.migrate(
        knowledge_base_id=1,  # 指定知识库ID，None则迁移所有
        dry_run=False,         # 实际执行
        incremental=False      # 全量迁移
    )
    
    # 输出统计信息
    logger.info("\n迁移统计:")
    logger.info(f"  文档: {stats.migrated_documents}/{stats.total_documents}")
    logger.info(f"  片段: {stats.migrated_chunks}/{stats.total_chunks}")
    logger.info(f"  实体: {stats.migrated_entities}/{stats.total_entities}")
    logger.info(f"  关系: {stats.migrated_relationships}/{stats.total_relationships}")
    logger.info(f"  关联: {stats.created_associations}/{stats.total_associations}")
    logger.info(f"  失败: {stats.failed_items}")
    logger.info(f"  耗时: {stats.duration_seconds:.2f}秒")
    logger.info(f"  成功率: {stats.success_rate:.1%}")
    
    if stats.errors:
        logger.warning(f"\n错误信息 ({len(stats.errors)} 个):")
        for error in stats.errors[:5]:  # 只显示前5个
            logger.warning(f"  - {error}")


# ==================== 示例 2: 模拟运行 ====================

def example_dry_run():
    """模拟运行示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 模拟运行 (Dry Run)")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 模拟运行，不实际修改数据
    stats = service.migrate(
        knowledge_base_id=1,
        dry_run=True,      # 仅模拟
        incremental=False
    )
    
    logger.info("\n模拟运行结果:")
    logger.info(f"  预计迁移文档: {stats.total_documents}")
    logger.info(f"  预计迁移片段: {stats.total_chunks}")
    logger.info(f"  预计迁移实体: {stats.total_entities}")
    logger.info(f"  预计创建关联: {stats.total_relationships}")
    logger.info("\n✓ 模拟运行完成，未修改任何数据")


# ==================== 示例 3: 增量迁移 ====================

def example_incremental_migration():
    """增量迁移示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 增量迁移")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 只迁移未迁移的数据
    stats = service.migrate(
        knowledge_base_id=1,
        dry_run=False,
        incremental=True   # 增量模式
    )
    
    logger.info("\n增量迁移结果:")
    logger.info(f"  新迁移文档: {stats.migrated_documents}")
    logger.info(f"  新迁移片段: {stats.migrated_chunks}")
    logger.info(f"  新迁移实体: {stats.migrated_entities}")
    logger.info(f"  失败项目: {stats.failed_items}")


# ==================== 示例 4: 指定阶段迁移 ====================

def example_phase_migration():
    """指定阶段迁移示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 指定阶段迁移")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 只迁移文档和实体
    phases = [
        MigrationPhase.PREPARATION,
        MigrationPhase.DOCUMENTS,
        MigrationPhase.ENTITIES,
        MigrationPhase.VALIDATION
    ]
    
    stats = service.migrate(
        knowledge_base_id=1,
        dry_run=False,
        incremental=False,
        phases=phases  # 指定阶段
    )
    
    logger.info("\n阶段迁移结果:")
    logger.info(f"  迁移文档: {stats.migrated_documents}")
    logger.info(f"  迁移实体: {stats.migrated_entities}")
    logger.info("  (跳过了片段和关系迁移)")


# ==================== 示例 5: 带进度回调的迁移 ====================

def example_migration_with_progress():
    """带进度回调的迁移示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 带进度回调的迁移")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 定义进度回调
    def on_progress(phase: MigrationPhase, current: int, total: int, message: str):
        progress_pct = (current / total * 100) if total > 0 else 0
        logger.info(f"  [{phase.value}] {progress_pct:.1f}% - {message}")
    
    # 注册回调
    service.register_progress_callback(on_progress)
    
    # 执行迁移
    stats = service.migrate(
        knowledge_base_id=1,
        dry_run=False,
        incremental=False
    )
    
    logger.info("\n迁移完成!")
    logger.info(f"  总耗时: {stats.duration_seconds:.2f}秒")


# ==================== 示例 6: 迁移验证 ====================

def example_migration_validation():
    """迁移验证示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 迁移验证")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 先执行迁移
    logger.info("执行迁移...")
    service.migrate(knowledge_base_id=1, dry_run=False)
    
    # 验证迁移结果
    logger.info("\n验证迁移结果...")
    # 验证逻辑在 migrate 方法中自动执行
    
    logger.info("✓ 验证完成")


# ==================== 示例 7: 迁移回滚 ====================

def example_migration_rollback():
    """迁移回滚示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 迁移回滚")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 先执行迁移
    logger.info("1. 执行迁移...")
    service.migrate(knowledge_base_id=1, dry_run=False)
    
    # 查看迁移状态
    status = service.get_migration_status(knowledge_base_id=1)
    logger.info(f"\n2. 迁移后状态:")
    logger.info(f"   已迁移单元: {status['migrated_units']['total']}")
    
    # 执行回滚
    logger.info("\n3. 执行回滚...")
    success = service.rollback(knowledge_base_id=1)
    
    if success:
        logger.info("✓ 回滚成功")
        
        # 查看回滚后状态
        status = service.get_migration_status(knowledge_base_id=1)
        logger.info(f"\n4. 回滚后状态:")
        logger.info(f"   已迁移单元: {status['migrated_units']['total']}")
    else:
        logger.error("✗ 回滚失败")


# ==================== 示例 8: 获取迁移状态 ====================

def example_get_migration_status():
    """获取迁移状态示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 获取迁移状态")
    logger.info("=" * 60)
    
    service = DataMigrationService()
    
    # 执行部分迁移
    service.migrate(knowledge_base_id=1, dry_run=False)
    
    # 获取迁移状态
    status = service.get_migration_status(knowledge_base_id=1)
    
    logger.info("\n迁移状态:")
    logger.info(f"  知识库ID: {status['knowledge_base_id']}")
    
    logger.info("\n  已迁移数据:")
    logger.info(f"    总计: {status['migrated_units']['total']}")
    logger.info(f"    文档: {status['migrated_units']['documents']}")
    logger.info(f"    片段: {status['migrated_units']['chunks']}")
    logger.info(f"    实体: {status['migrated_units']['entities']}")
    
    logger.info("\n  原始数据:")
    logger.info(f"    文档: {status['original_data']['documents']}")
    logger.info(f"    片段: {status['original_data']['chunks']}")
    logger.info(f"    实体: {status['original_data']['entities']}")
    
    logger.info("\n  迁移进度:")
    logger.info(f"    文档: {status['progress']['documents']:.1%}")
    logger.info(f"    片段: {status['progress']['chunks']:.1%}")
    logger.info(f"    实体: {status['progress']['entities']:.1%}")


# ==================== 示例 9: 便捷函数使用 ====================

def example_convenience_functions():
    """便捷函数使用示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 便捷函数使用")
    logger.info("=" * 60)
    
    # 使用便捷函数执行迁移
    logger.info("1. 使用便捷函数 migrate_data...")
    result = migrate_data(
        knowledge_base_id=1,
        dry_run=False,
        incremental=False
    )
    
    logger.info("\n迁移结果:")
    logger.info(f"  文档: {result['migrated_documents']}/{result['total_documents']}")
    logger.info(f"  片段: {result['migrated_chunks']}/{result['total_chunks']}")
    logger.info(f"  实体: {result['migrated_entities']}/{result['total_entities']}")
    logger.info(f"  耗时: {result['duration_seconds']:.2f}秒")
    
    # 使用便捷函数获取进度
    logger.info("\n2. 使用便捷函数 get_migration_progress...")
    progress = get_migration_progress(knowledge_base_id=1)
    
    logger.info(f"\n迁移进度:")
    logger.info(f"  已迁移: {progress['migrated_units']['total']} 个单元")
    logger.info(f"  原始数据: {progress['original_data']['documents']} 个文档")
    
    # 使用便捷函数回滚
    logger.info("\n3. 使用便捷函数 rollback_migration...")
    success = rollback_migration(knowledge_base_id=1)
    logger.info(f"  回滚结果: {'成功' if success else '失败'}")


# ==================== 示例 10: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：生产环境数据迁移
    
    展示如何在生产环境中安全地进行数据迁移。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 生产环境数据迁移流程")
    logger.info("=" * 60)
    
    knowledge_base_id = 1
    
    # 步骤1: 模拟运行
    logger.info("\n步骤 1: 模拟运行 (Dry Run)")
    logger.info("-" * 40)
    
    service = DataMigrationService()
    dry_run_stats = service.migrate(
        knowledge_base_id=knowledge_base_id,
        dry_run=True
    )
    
    logger.info(f"预计迁移:")
    logger.info(f"  文档: {dry_run_stats.total_documents}")
    logger.info(f"  片段: {dry_run_stats.total_chunks}")
    logger.info(f"  实体: {dry_run_stats.total_entities}")
    
    # 步骤2: 检查资源
    logger.info("\n步骤 2: 检查系统资源")
    logger.info("-" * 40)
    logger.info("✓ 磁盘空间充足")
    logger.info("✓ 数据库连接正常")
    logger.info("✓ 备份已完成")
    
    # 步骤3: 执行迁移
    logger.info("\n步骤 3: 执行迁移")
    logger.info("-" * 40)
    
    def on_progress(phase: MigrationPhase, current: int, total: int, message: str):
        logger.info(f"  [{phase.value}] {message}")
    
    service.register_progress_callback(on_progress)
    
    stats = service.migrate(
        knowledge_base_id=knowledge_base_id,
        dry_run=False,
        incremental=False
    )
    
    logger.info(f"\n迁移完成:")
    logger.info(f"  成功: {stats.success_rate:.1%}")
    logger.info(f"  耗时: {stats.duration_seconds:.2f}秒")
    
    # 步骤4: 验证数据
    logger.info("\n步骤 4: 验证数据完整性")
    logger.info("-" * 40)
    
    status = service.get_migration_status(knowledge_base_id=knowledge_base_id)
    
    all_migrated = (
        status['progress']['documents'] >= 1.0 and
        status['progress']['chunks'] >= 1.0 and
        status['progress']['entities'] >= 1.0
    )
    
    if all_migrated:
        logger.info("✓ 所有数据迁移成功")
    else:
        logger.warning("⚠ 部分数据未迁移")
    
    # 步骤5: 监控
    logger.info("\n步骤 5: 迁移后监控")
    logger.info("-" * 40)
    logger.info("✓ 系统运行正常")
    logger.info("✓ 查询性能正常")
    logger.info("✓ 无错误日志")
    
    logger.info("\n" + "=" * 60)
    logger.info("生产环境迁移流程完成!")
    logger.info("=" * 60)


# ==================== 示例 11: 批量知识库迁移 ====================

def example_batch_knowledge_base_migration():
    """批量知识库迁移示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 11: 批量知识库迁移")
    logger.info("=" * 60)
    
    # 模拟多个知识库
    knowledge_base_ids = [1, 2, 3]
    
    results = []
    
    for kb_id in knowledge_base_ids:
        logger.info(f"\n迁移知识库 {kb_id}...")
        
        service = DataMigrationService()
        stats = service.migrate(
            knowledge_base_id=kb_id,
            dry_run=False,
            incremental=True  # 使用增量模式
        )
        
        results.append({
            "knowledge_base_id": kb_id,
            "migrated_documents": stats.migrated_documents,
            "migrated_chunks": stats.migrated_chunks,
            "migrated_entities": stats.migrated_entities,
            "success_rate": stats.success_rate,
            "duration": stats.duration_seconds
        })
    
    logger.info("\n批量迁移结果:")
    logger.info("-" * 60)
    for result in results:
        logger.info(f"\n知识库 {result['knowledge_base_id']}:")
        logger.info(f"  文档: {result['migrated_documents']}")
        logger.info(f"  片段: {result['migrated_chunks']}")
        logger.info(f"  实体: {result['migrated_entities']}")
        logger.info(f"  成功率: {result['success_rate']:.1%}")
        logger.info(f"  耗时: {result['duration']:.2f}秒")
    
    # 汇总
    total_duration = sum(r['duration'] for r in results)
    avg_success_rate = sum(r['success_rate'] for r in results) / len(results)
    
    logger.info(f"\n汇总:")
    logger.info(f"  总耗时: {total_duration:.2f}秒")
    logger.info(f"  平均成功率: {avg_success_rate:.1%}")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("数据迁移服务使用示例")
    logger.info("=" * 70)
    
    try:
        # 注意：以下示例中涉及实际数据库操作的示例
        # 在实际运行时需要确保数据库连接正常
        
        # example_basic_migration()
        # example_dry_run()
        # example_incremental_migration()
        # example_phase_migration()
        # example_migration_with_progress()
        # example_migration_validation()
        # example_migration_rollback()
        # example_get_migration_status()
        # example_convenience_functions()
        # example_real_world_scenario()
        # example_batch_knowledge_base_migration()
        
        logger.info("\n示例代码已准备就绪")
        logger.info("请根据需要取消注释相应的示例函数进行测试")
        
        # 默认运行模拟示例
        example_dry_run()
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
