"""
向量版本管理系统使用示例 - 向量化管理模块优化

展示如何使用 VectorVersionManager 进行向量版本控制、回滚和对比。

任务编号: BE-005
阶段: Phase 1 - 基础优化期
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.services.knowledge.vector_version_manager import (
    VectorVersionManager,
    VectorVersion,
    VectorChange,
    VersionComparison,
    VersionStatus,
    ChangeType,
    vector_version_manager
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本使用 ====================

def example_basic_usage():
    """基本使用示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本使用")
    logger.info("=" * 60)
    
    # 创建版本管理器
    manager = VectorVersionManager()
    
    knowledge_base_id = 1
    
    # 创建版本
    logger.info(f"创建版本: kb_{knowledge_base_id}")
    version = manager.create_version(
        knowledge_base_id=knowledge_base_id,
        name="初始版本",
        description="向量数据的初始版本",
        created_by="system"
    )
    
    logger.info(f"版本创建成功:")
    logger.info(f"  版本ID: {version.version_id}")
    logger.info(f"  版本名: {version.name}")
    logger.info(f"  向量数: {version.vector_count}")
    logger.info(f"  创建时间: {version.created_at}")
    
    # 获取活跃版本
    active = manager.get_active_version(knowledge_base_id)
    logger.info(f"\n当前活跃版本: {active.version_id if active else 'None'}")


# ==================== 示例 2: 版本列表和查询 ====================

def example_version_listing():
    """版本列表和查询示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 版本列表和查询")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 创建多个版本
    for i in range(3):
        version = manager.create_version(
            knowledge_base_id=1,
            name=f"版本v{i+1}",
            description=f"测试版本{i+1}",
            created_by="admin"
        )
        logger.info(f"创建版本: {version.version_id}")
        
        # 模拟版本之间的延迟
        time.sleep(0.1)
    
    # 列出版本
    versions = manager.list_versions(knowledge_base_id=1)
    
    logger.info(f"\n版本列表 (共 {len(versions)} 个):")
    for v in versions:
        logger.info(f"  - {v.name}: {v.version_id}, 状态: {v.status.value}, 向量数: {v.vector_count}")


# ==================== 示例 3: 版本对比 ====================

def example_version_comparison():
    """版本对比示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 版本对比")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 创建基线版本
    logger.info("创建基线版本...")
    base_version = manager.create_version(
        knowledge_base_id=1,
        name="基线版本",
        description="基线测试版本",
        created_by="system"
    )
    
    # 模拟数据变更（创建新版本）
    logger.info("创建新版本...")
    new_version = manager.create_version(
        knowledge_base_id=1,
        name="更新版本",
        description="数据更新后的版本",
        created_by="system",
        parent_version_id=base_version.version_id
    )
    
    # 对比两个版本
    logger.info(f"\n对比版本: {base_version.version_id} -> {new_version.version_id}")
    
    comparison = manager.compare_versions(
        base_version.version_id,
        new_version.version_id
    )
    
    logger.info(f"\n对比结果:")
    logger.info(f"  新增: {comparison.added_count}")
    logger.info(f"  修改: {comparison.modified_count}")
    logger.info(f"  删除: {comparison.deleted_count}")
    logger.info(f"  未变: {comparison.unchanged_count}")
    
    # 显示变更详情
    if comparison.changes:
        logger.info(f"\n变更详情:")
        for change in comparison.changes[:5]:  # 只显示前5个
            logger.info(f"  [{change.change_type.value}] {change.vector_id}")


# ==================== 示例 4: 版本回滚 ====================

def example_version_rollback():
    """版本回滚示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 版本回滚")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 创建初始版本
    logger.info("创建初始版本...")
    v1 = manager.create_version(
        knowledge_base_id=1,
        name="版本V1",
        description="初始版本",
        created_by="system"
    )
    logger.info(f"V1版本: {v1.version_id}, 向量数: {v1.vector_count}")
    
    # 创建新版本
    logger.info("创建新版本V2...")
    v2 = manager.create_version(
        knowledge_base_id=1,
        name="版本V2",
        description="更新版本",
        created_by="system",
        parent_version_id=v1.version_id
    )
    logger.info(f"V2版本: {v2.version_id}, 向量数: {v2.vector_count}")
    
    # 查看当前活跃版本
    active = manager.get_active_version(1)
    logger.info(f"\n当前活跃版本: {active.version_id if active else 'None'}")
    
    # 回滚到V1
    logger.info("\n回滚到V1...")
    success = manager.rollback_to_version(v1.version_id, confirmed=True)
    
    if success:
        logger.info("回滚成功!")
        
        # 再次查看活跃版本
        active = manager.get_active_version(1)
        logger.info(f"回滚后活跃版本: {active.version_id if active else 'None'}")


# ==================== 示例 5: 版本归档和删除 ====================

def example_version_archive_delete():
    """版本归档和删除示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 版本归档和删除")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 创建多个版本
    logger.info("创建多个版本...")
    for i in range(5):
        manager.create_version(
            knowledge_base_id=1,
            name=f"版本{i+1}",
            description=f"测试版本{i+1}",
            created_by="system"
        )
    
    # 列出版本
    versions = manager.list_versions(knowledge_base_id=1)
    logger.info(f"当前版本数: {len(versions)}")
    
    # 归档第二个版本
    if len(versions) >= 2:
        version_to_archive = versions[1]
        logger.info(f"\n归档版本: {version_to_archive.name}")
        manager.archive_version(version_to_archive.version_id)
    
    # 列出版本（包含归档）
    versions = manager.list_versions(knowledge_base_id=1, include_archived=True)
    logger.info(f"\n包含归档的版本列表:")
    for v in versions:
        logger.info(f"  - {v.name}: {v.status.value}")


# ==================== 示例 6: 版本变更详情 ====================

def example_version_changes():
    """版本变更详情示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 版本变更详情")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 创建父子版本
    logger.info("创建父子版本...")
    parent = manager.create_version(
        knowledge_base_id=1,
        name="父版本",
        description="父版本",
        created_by="system"
    )
    
    child = manager.create_version(
        knowledge_base_id=1,
        name="子版本",
        description="子版本",
        created_by="system",
        parent_version_id=parent.version_id
    )
    
    # 获取变更详情
    logger.info(f"\n获取版本 {child.version_id} 的变更详情:")
    changes = manager.get_version_changes(child.version_id)
    
    logger.info(f"变更数量: {len(changes)}")
    
    # 按类型统计
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]
    deleted = [c for c in changes if c.change_type == ChangeType.DELETED]
    
    logger.info(f"\n变更统计:")
    logger.info(f"  新增: {len(added)}")
    logger.info(f"  修改: {len(modified)}")
    logger.info(f"  删除: {len(deleted)}")


# ==================== 示例 7: 版本统计信息 ====================

def example_version_statistics():
    """版本统计信息示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 版本统计信息")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 创建多个版本
    logger.info("创建测试版本...")
    for i in range(3):
        manager.create_version(
            knowledge_base_id=1,
            name=f"统计测试版本{i+1}",
            description=f"测试{i+1}",
            created_by="system"
        )
    
    # 获取统计信息
    stats = manager.get_version_statistics(knowledge_base_id=1)
    
    logger.info(f"\n版本统计信息:")
    logger.info(f"  总版本数: {stats['total_versions']}")
    logger.info(f"  活跃版本: {stats['active_versions']}")
    logger.info(f"  已归档版本: {stats['archived_versions']}")
    logger.info(f"  已回滚版本: {stats['rolled_back_versions']}")
    logger.info(f"  向量总数: {stats['total_vectors']}")
    
    if stats['latest_version']:
        lv = stats['latest_version']
        logger.info(f"\n最新版本:")
        logger.info(f"  名称: {lv['name']}")
        logger.info(f"  ID: {lv['version_id']}")
        logger.info(f"  向量数: {lv['vector_count']}")


# ==================== 示例 8: 版本回调 ====================

def example_version_callbacks():
    """版本回调示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 版本回调")
    logger.info("=" * 60)
    
    manager = VectorVersionManager()
    
    # 定义回调函数
    def version_change_callback(version: VectorVersion, action: str):
        logger.info(f"[回调] 版本事件: {action} - {version.name}")
    
    # 注册回调
    manager.register_version_callback(version_change_callback)
    
    # 创建版本（会触发回调）
    logger.info("创建版本...")
    version = manager.create_version(
        knowledge_base_id=1,
        name="回调测试版本",
        description="测试回调功能",
        created_by="system"
    )
    
    logger.info(f"版本创建完成: {version.version_id}")


# ==================== 示例 9: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：知识库版本管理
    
    展示如何在实际应用中使用版本管理功能。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 实际应用场景 - 知识库版本管理")
    logger.info("=" * 60)
    
    knowledge_base_id = 1
    manager = VectorVersionManager()
    
    # 场景1: 定期创建版本快照
    logger.info("\n场景1: 定期版本快照")
    
    snapshots = [
        ("初始导入", "首次导入文档"),
        ("增量更新1", "添加新文档"),
        ("增量更新2", "更新现有文档"),
        ("清理数据", "删除过时数据")
    ]
    
    parent_id = None
    for name, desc in snapshots:
        logger.info(f"  创建版本: {name}")
        version = manager.create_version(
            knowledge_base_id=knowledge_base_id,
            name=name,
            description=desc,
            created_by="scheduler",
            parent_version_id=parent_id
        )
        parent_id = version.version_id
        time.sleep(0.1)
    
    # 场景2: 数据变更前创建备份
    logger.info("\n场景2: 数据变更前备份")
    
    current = manager.get_active_version(knowledge_base_id)
    logger.info(f"当前版本: {current.name if current else 'None'}")
    
    backup_version = manager.create_version(
        knowledge_base_id=knowledge_base_id,
        name="变更前备份",
        description="数据变更前的备份",
        created_by="admin"
    )
    logger.info(f"备份版本: {backup_version.version_id}")
    
    # 场景3: 出现问题时回滚
    logger.info("\n场景3: 回滚到稳定版本")
    
    logger.info(f"查看版本历史...")
    versions = manager.list_versions(knowledge_base_id=knowledge_base_id)
    
    stable_version = None
    for v in versions:
        if "初始导入" in v.name:
            stable_version = v
            break
    
    if stable_version:
        logger.info(f"找到稳定版本: {stable_version.name}")
        
        logger.info("执行回滚...")
        success = manager.rollback_to_version(stable_version.version_id, confirmed=True)
        
        if success:
            logger.info("✓ 回滚成功")
        else:
            logger.error("✗ 回滚失败")
    else:
        logger.warning("未找到稳定版本")
    
    # 场景4: 版本对比分析
    logger.info("\n场景4: 版本对比分析")
    
    if len(versions) >= 2:
        v1 = versions[-1]
        v2 = versions[0]
        
        logger.info(f"对比 {v1.name} 和 {v2.name}")
        
        comparison = manager.compare_versions(v1.version_id, v2.version_id)
        
        logger.info(f"\n对比结果:")
        logger.info(f"  新增向量: {comparison.added_count}")
        logger.info(f"  修改向量: {comparison.modified_count}")
        logger.info(f"  删除向量: {comparison.deleted_count}")
        logger.info(f"  未变向量: {comparison.unchanged_count}")


# ==================== 示例 10: 版本策略配置 ====================

def example_version_strategy():
    """版本策略配置示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 版本策略配置")
    logger.info("=" * 60)
    
    # 配置版本管理器参数
    max_versions = 10
    
    logger.info(f"创建版本管理器 (max_versions={max_versions})...")
    
    manager = VectorVersionManager(max_versions_per_kb=max_versions)
    
    # 测试自动清理
    logger.info("\n创建超过限制的版本...")
    
    for i in range(15):
        manager.create_version(
            knowledge_base_id=1,
            name=f"自动清理测试{i+1}",
            description=f"测试{i+1}",
            created_by="system"
        )
    
    # 检查版本数量
    versions = manager.list_versions(knowledge_base_id=1)
    active_count = sum(1 for v in versions if v.status == VersionStatus.ACTIVE)
    
    logger.info(f"\n版本数量:")
    logger.info(f"  总数: {len(versions)}")
    logger.info(f"  活跃: {active_count}")
    logger.info(f"  最大限制: {max_versions}")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("向量版本管理系统使用示例")
    logger.info("=" * 70)
    
    try:
        example_basic_usage()
        example_version_listing()
        example_version_comparison()
        example_version_rollback()
        example_version_archive_delete()
        example_version_changes()
        example_version_statistics()
        example_version_callbacks()
        # example_real_world_scenario()  # 输出较多，可选运行
        # example_version_strategy()  # 耗时较长，可选运行
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
