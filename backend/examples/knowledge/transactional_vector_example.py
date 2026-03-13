"""
事务性向量操作使用示例 - 向量化管理模块优化

展示如何使用 TransactionalVectorManager 和 UnifiedTransactionService 进行事务性向量操作。

任务编号: BE-004
阶段: Phase 1 - 基础优化期
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from app.services.knowledge.transactional_vector_manager import (
    TransactionalVectorManager,
    TransactionContext,
    VectorOperationType,
    TransactionStatus,
    add_document_with_transaction,
    batch_add_documents_with_transaction
)
from app.services.knowledge.unified_transaction_service import (
    UnifiedTransactionService,
    UnifiedTransactionContext,
    add_document_transactional,
    update_document_transactional,
    delete_document_transactional
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本事务操作 ====================

async def example_basic_transaction():
    """基本事务操作示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本事务操作")
    logger.info("=" * 60)
    
    manager = TransactionalVectorManager()
    
    # 创建事务
    with manager.transaction() as txn:
        # 添加操作
        op1 = txn.add_operation(
            operation_type=VectorOperationType.ADD,
            document_id="doc_001",
            data={
                "text": "这是第一个文档的内容",
                "metadata": {"title": "文档1", "author": "张三"}
            }
        )
        logger.info(f"添加操作 1: {op1}")
        
        op2 = txn.add_operation(
            operation_type=VectorOperationType.ADD,
            document_id="doc_002",
            data={
                "text": "这是第二个文档的内容",
                "metadata": {"title": "文档2", "author": "李四"}
            }
        )
        logger.info(f"添加操作 2: {op2}")
        
        # 提交事务
        success = await txn.commit()
        logger.info(f"事务提交: {'成功' if success else '失败'}")
        logger.info(f"事务ID: {txn.transaction_id}")
    
    # 查看事务状态
    status = manager.get_transaction_status(txn.transaction_id)
    logger.info(f"事务状态: {status}")


# ==================== 示例 2: 事务回滚 ====================

async def example_transaction_rollback():
    """事务回滚示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 事务回滚")
    logger.info("=" * 60)
    
    manager = TransactionalVectorManager()
    
    # 创建事务
    with manager.transaction() as txn:
        # 添加操作
        txn.add_operation(
            operation_type=VectorOperationType.ADD,
            document_id="doc_rollback_001",
            data={"text": "临时文档 1", "metadata": {}}
        )
        
        txn.add_operation(
            operation_type=VectorOperationType.ADD,
            document_id="doc_rollback_002",
            data={"text": "临时文档 2", "metadata": {}}
        )
        
        logger.info(f"添加了 2 个操作到事务 {txn.transaction_id}")
        
        # 回滚事务
        success = await txn.rollback()
        logger.info(f"事务回滚: {'成功' if success else '失败'}")
    
    # 查看事务状态
    status = manager.get_transaction_status(txn.transaction_id)
    logger.info(f"回滚后状态: {status['status']}")


# ==================== 示例 3: 批量操作事务 ====================

async def example_batch_transaction():
    """批量操作事务示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 批量操作事务")
    logger.info("=" * 60)
    
    # 准备批量数据
    documents = []
    for i in range(5):
        documents.append({
            "id": f"batch_doc_{i:03d}",
            "text": f"这是批量文档 {i} 的内容",
            "metadata": {
                "index": i,
                "batch_id": "batch_001",
                "created_at": datetime.now().isoformat()
            }
        })
    
    # 使用批量事务
    success, txn_id = await batch_add_documents_with_transaction(documents)
    
    logger.info(f"批量添加: {'成功' if success else '失败'}")
    logger.info(f"事务ID: {txn_id}")


# ==================== 示例 4: 统一事务服务 ====================

async def example_unified_transaction():
    """统一事务服务示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 统一事务服务")
    logger.info("=" * 60)
    
    service = UnifiedTransactionService()
    
    async with service.unified_transaction() as txn:
        logger.info(f"开始统一事务: {txn.transaction_id}")
        
        # 模拟数据库操作
        logger.info("执行数据库操作...")
        
        # 添加向量操作
        op_id = await txn.add_vector(
            document_id="unified_doc_001",
            text="统一事务测试文档",
            metadata={"source": "unified_transaction", "test": True}
        )
        logger.info(f"添加向量操作: {op_id}")
        
        # 提交事务
        success = await txn.commit()
        logger.info(f"统一事务提交: {'成功' if success else '失败'}")


# ==================== 示例 5: 错误处理与重试 ====================

async def example_error_handling():
    """错误处理与重试示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 错误处理与重试")
    logger.info("=" * 60)
    
    manager = TransactionalVectorManager(max_retries=3, retry_delay_base=0.5)
    
    with manager.transaction() as txn:
        # 添加多个操作
        for i in range(3):
            txn.add_operation(
                operation_type=VectorOperationType.ADD,
                document_id=f"retry_doc_{i}",
                data={
                    "text": f"重试测试文档 {i}",
                    "metadata": {"test": "retry"}
                }
            )
        
        try:
            success = await txn.commit()
            logger.info(f"事务提交: {'成功' if success else '失败'}")
        except Exception as e:
            logger.error(f"事务失败: {e}")
            await txn.rollback()
    
    # 查看统计
    stats = manager.get_stats()
    logger.info(f"\n事务统计:")
    logger.info(f"  总事务数: {stats['total_transactions']}")
    logger.info(f"  成功事务: {stats['committed_transactions']}")
    logger.info(f"  失败事务: {stats['failed_transactions']}")
    logger.info(f"  重试次数: {stats['retry_count']}")
    logger.info(f"  成功率: {stats['transaction_success_rate']:.1%}")


# ==================== 示例 6: 事务统计与监控 ====================

async def example_transaction_stats():
    """事务统计与监控示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 事务统计与监控")
    logger.info("=" * 60)
    
    manager = TransactionalVectorManager()
    
    # 执行多个事务
    for i in range(10):
        with manager.transaction() as txn:
            txn.add_operation(
                operation_type=VectorOperationType.ADD,
                document_id=f"stats_doc_{i}",
                data={"text": f"统计测试 {i}", "metadata": {}}
            )
            await txn.commit()
    
    # 获取统计
    stats = manager.get_stats()
    
    logger.info("事务统计:")
    logger.info(f"  总事务数: {stats['total_transactions']}")
    logger.info(f"  已提交: {stats['committed_transactions']}")
    logger.info(f"  已回滚: {stats['rolled_back_transactions']}")
    logger.info(f"  失败: {stats['failed_transactions']}")
    logger.info(f"  总操作数: {stats['total_operations']}")
    logger.info(f"  成功操作: {stats['successful_operations']}")
    logger.info(f"  失败操作: {stats['failed_operations']}")
    logger.info(f"  操作成功率: {stats['success_rate']:.1%}")
    logger.info(f"  事务成功率: {stats['transaction_success_rate']:.1%}")
    logger.info(f"  总重试次数: {stats['retry_count']}")
    
    # 获取操作日志
    logs = manager.get_operation_logs(limit=5)
    logger.info(f"\n最近 {len(logs)} 条操作日志:")
    for log in logs:
        logger.info(f"  {log['operation_id']}: {log['operation_type']} - {log['status']}")


# ==================== 示例 7: 数据一致性检查 ====================

async def example_consistency_check():
    """数据一致性检查示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 数据一致性检查")
    logger.info("=" * 60)
    
    service = UnifiedTransactionService(enable_consistency_check=True)
    
    # 执行一致性检查
    result = await service.check_data_consistency()
    
    logger.info("一致性检查结果:")
    logger.info(f"  总文档数: {result['total_documents']}")
    logger.info(f"  一致文档: {result['consistent_documents']}")
    logger.info(f"  不一致文档: {result['inconsistent_documents']}")
    logger.info(f"  一致性率: {result.get('consistency_rate', 0):.1%}")
    
    if result['inconsistent_ids']:
        logger.info(f"  不一致文档ID: {result['inconsistent_ids']}")


# ==================== 示例 8: 复杂事务场景 ====================

async def example_complex_transaction():
    """复杂事务场景示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 复杂事务场景")
    logger.info("=" * 60)
    
    service = UnifiedTransactionService()
    
    async with service.unified_transaction() as txn:
        logger.info(f"开始复杂事务: {txn.transaction_id}")
        
        # 场景：更新知识库文档
        # 1. 删除旧向量
        old_vector_ids = ["old_vec_001", "old_vec_002"]
        await txn.delete_vectors(old_vector_ids)
        logger.info(f"删除旧向量: {old_vector_ids}")
        
        # 2. 添加新向量
        new_vectors = [
            ("new_vec_001", "新内容 1", {"version": 2}),
            ("new_vec_002", "新内容 2", {"version": 2}),
            ("new_vec_003", "新内容 3", {"version": 2}),
        ]
        
        for vec_id, text, metadata in new_vectors:
            await txn.add_vector(vec_id, text, metadata)
        
        logger.info(f"添加 {len(new_vectors)} 个新向量")
        
        # 3. 提交事务
        success = await txn.commit()
        logger.info(f"复杂事务提交: {'成功' if success else '失败'}")


# ==================== 示例 9: 事务超时与死锁处理 ====================

async def example_timeout_handling():
    """事务超时处理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 事务超时与并发控制")
    logger.info("=" * 60)
    
    manager = TransactionalVectorManager()
    
    async def long_operation():
        """模拟长时间操作"""
        with manager.transaction() as txn:
            txn.add_operation(
                operation_type=VectorOperationType.ADD,
                document_id="timeout_doc",
                data={"text": "超时测试", "metadata": {}}
            )
            # 模拟长时间处理
            await asyncio.sleep(0.1)
            await txn.commit()
    
    # 并发执行多个事务
    tasks = [long_operation() for _ in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"并发事务: {len(tasks)} 个, 成功: {success_count} 个")


# ==================== 示例 10: 实际应用场景 ====================

async def example_real_world_scenario():
    """
    实际应用场景：文档导入流程
    
    展示如何在实际应用中使用事务性向量操作。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 实际应用场景 - 文档导入")
    logger.info("=" * 60)
    
    service = UnifiedTransactionService()
    
    # 模拟文档导入数据
    import_data = {
        "title": "人工智能发展报告",
        "content": "人工智能（AI）是计算机科学的一个分支...",
        "chunks": [
            {
                "text": "人工智能（AI）是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。",
                "metadata": {"section": "introduction", "page": 1}
            },
            {
                "text": "机器学习是人工智能的核心技术之一，它使计算机能够从数据中学习而无需明确编程。",
                "metadata": {"section": "machine_learning", "page": 2}
            },
            {
                "text": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。",
                "metadata": {"section": "deep_learning", "page": 3}
            }
        ]
    }
    
    logger.info(f"导入文档: {import_data['title']}")
    logger.info(f"片段数: {len(import_data['chunks'])}")
    
    # 使用统一事务服务导入
    async with service.unified_transaction() as txn:
        # 1. 保存文档元数据到数据库
        logger.info("1. 保存文档元数据...")
        
        # 2. 添加向量
        logger.info("2. 添加文档向量...")
        for i, chunk in enumerate(import_data['chunks']):
            await txn.add_vector(
                document_id=f"doc_import_chunk_{i}",
                text=chunk['text'],
                metadata={
                    **chunk['metadata'],
                    "document_title": import_data['title'],
                    "chunk_index": i
                }
            )
        
        # 3. 提交事务
        logger.info("3. 提交事务...")
        success = await txn.commit()
        
        if success:
            logger.info(f"✓ 文档导入成功！事务ID: {txn.transaction_id}")
        else:
            logger.error(f"✗ 文档导入失败")
    
    # 验证导入
    logger.info("\n验证导入结果:")
    stats = service.vector_manager.get_stats()
    logger.info(f"  事务成功率: {stats['transaction_success_rate']:.1%}")
    logger.info(f"  操作成功率: {stats['success_rate']:.1%}")


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("事务性向量操作使用示例")
    logger.info("=" * 70)
    
    try:
        await example_basic_transaction()
        await example_transaction_rollback()
        await example_batch_transaction()
        await example_unified_transaction()
        await example_error_handling()
        await example_transaction_stats()
        await example_consistency_check()
        await example_complex_transaction()
        await example_timeout_handling()
        await example_real_world_scenario()
        
        logger.info("\n" + "=" * 70)
        logger.info("所有示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
