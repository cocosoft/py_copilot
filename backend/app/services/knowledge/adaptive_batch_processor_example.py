"""
自适应批次处理器使用示例

展示如何使用 AdaptiveBatchProcessor 进行高效的批量处理。

任务编号: BE-001
阶段: Phase 1 - 基础优化期
"""

import asyncio
import logging
from typing import List, Dict, Any

from app.services.knowledge.adaptive_batch_processor import (
    AdaptiveBatchProcessor,
    BatchConfig,
    BatchSizeStrategy,
    process_with_adaptive_batching
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本用法 ====================

async def example_basic_usage():
    """基本用法示例"""
    
    logger.info("=" * 50)
    logger.info("示例 1: 基本用法")
    logger.info("=" * 50)
    
    # 准备测试数据
    documents = [
        {"id": i, "text": f"这是第 {i} 个文档的内容" * 10}
        for i in range(100)
    ]
    
    # 定义处理函数
    async def process_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """模拟文档处理"""
        # 模拟处理延迟
        await asyncio.sleep(0.01)
        return {
            "doc_id": doc["id"],
            "processed": True,
            "word_count": len(doc["text"])
        }
    
    # 创建处理器（使用默认配置）
    processor = AdaptiveBatchProcessor()
    
    # 处理文档
    results, stats = await processor.process_items(
        items=documents,
        processor=process_document,
        progress_callback=lambda current, total: logger.info(f"进度: {current}/{total}")
    )
    
    # 输出结果
    logger.info(f"\n处理完成!")
    logger.info(f"总项目数: {stats.total_items}")
    logger.info(f"成功: {stats.processed_items}")
    logger.info(f"失败: {stats.failed_items}")
    logger.info(f"成功率: {stats.success_rate:.1%}")
    logger.info(f"吞吐量: {stats.throughput:.2f} items/s")
    logger.info(f"总耗时: {stats.total_processing_time:.2f}s")


# ==================== 示例 2: 自定义配置 ====================

async def example_custom_config():
    """自定义配置示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 2: 自定义配置")
    logger.info("=" * 50)
    
    # 创建自定义配置
    config = BatchConfig(
        base_batch_size=30,
        min_batch_size=5,
        max_batch_size=100,
        memory_threshold_low=50.0,
        memory_threshold_high=70.0,
        memory_threshold_critical=85.0,
        strategy=BatchSizeStrategy.AGGRESSIVE,  # 激进策略，最大化吞吐量
        max_retries=5,
        retry_delay_base=0.5,
        max_concurrent_batches=5
    )
    
    # 准备测试数据
    items = list(range(200))
    
    # 定义处理函数
    async def process_item(item: int) -> Dict[str, Any]:
        await asyncio.sleep(0.005)
        return {"value": item, "square": item ** 2}
    
    # 使用自定义配置创建处理器
    processor = AdaptiveBatchProcessor(config)
    
    # 处理项目
    results, stats = await processor.process_items(items, process_item)
    
    logger.info(f"\n处理完成!")
    logger.info(f"批次数量: {stats.total_batches}")
    logger.info(f"成功率: {stats.success_rate:.1%}")
    logger.info(f"吞吐量: {stats.throughput:.2f} items/s")
    
    # 获取性能报告
    report = processor.get_performance_report()
    logger.info(f"\n性能报告:")
    logger.info(f"  平均批次大小: {report['batch_size']['avg']:.1f}")
    logger.info(f"  平均处理时间: {report['processing_time']['avg']:.3f}s")
    logger.info(f"  平均吞吐量: {report['throughput']['avg']:.2f} items/s")


# ==================== 示例 3: 流式处理 ====================

async def example_stream_processing():
    """流式处理示例 - 适用于大文件"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 3: 流式处理")
    logger.info("=" * 50)
    
    # 模拟大文件数据流
    def large_file_stream():
        """生成大量数据"""
        for i in range(1000):
            yield {"line_number": i, "content": f"Line {i}: " + "x" * 100}
    
    # 定义处理函数
    async def process_line(line: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.001)
        return {
            "line": line["line_number"],
            "length": len(line["content"]),
            "processed": True
        }
    
    # 创建处理器
    processor = AdaptiveBatchProcessor(
        BatchConfig(strategy=BatchSizeStrategy.CONSERVATIVE)  # 保守策略，优先稳定性
    )
    
    # 流式处理
    results, stats = await processor.process_stream(
        item_stream=large_file_stream(),
        processor=process_line
    )
    
    logger.info(f"\n流式处理完成!")
    logger.info(f"总项目数: {stats.total_items}")
    logger.info(f"批次数量: {stats.total_batches}")
    logger.info(f"成功率: {stats.success_rate:.1%}")
    logger.info(f"吞吐量: {stats.throughput:.2f} items/s")


# ==================== 示例 4: 错误处理和重试 ====================

async def example_error_handling():
    """错误处理和重试示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 4: 错误处理和重试")
    logger.info("=" * 50)
    
    # 准备测试数据（包含一些会失败的项）
    items = list(range(50))
    
    # 定义一个会随机失败的处理函数
    async def unreliable_processor(item: int) -> Dict[str, Any]:
        # 模拟随机失败（20% 概率）
        import random
        if random.random() < 0.2:
            raise Exception(f"随机错误: 处理项目 {item} 失败")
        
        await asyncio.sleep(0.01)
        return {"item": item, "status": "success"}
    
    # 创建处理器（启用重试）
    config = BatchConfig(
        max_retries=3,
        retry_delay_base=0.1,
        base_batch_size=10
    )
    processor = AdaptiveBatchProcessor(config)
    
    # 处理项目
    results, stats = await processor.process_items(items, unreliable_processor)
    
    logger.info(f"\n处理完成!")
    logger.info(f"总项目数: {stats.total_items}")
    logger.info(f"成功: {stats.processed_items}")
    logger.info(f"失败: {stats.failed_items}")
    logger.info(f"成功率: {stats.success_rate:.1%}")
    
    # 查看失败的项目
    failed_items = []
    for batch_result in results:
        for item in batch_result.items:
            if item.status.value == "failed":
                failed_items.append({
                    "id": item.id,
                    "error": item.error_message,
                    "retry_count": item.retry_count
                })
    
    if failed_items:
        logger.info(f"\n失败项目详情 (前5个):")
        for item in failed_items[:5]:
            logger.info(f"  {item}")


# ==================== 示例 5: 实际应用场景 - 文档向量化 ====================

async def example_document_vectorization():
    """
    实际应用场景：文档向量化处理
    
    展示如何使用自适应批次处理器优化文档向量化流程。
    """
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 5: 文档向量化处理")
    logger.info("=" * 50)
    
    # 模拟文档分块数据
    chunks = [
        {
            "chunk_id": f"doc_{i}_chunk_{j}",
            "document_id": i,
            "content": f"文档 {i} 的第 {j} 个分块内容。" * 20,
            "metadata": {"index": j, "total": 5}
        }
        for i in range(20)  # 20 个文档
        for j in range(5)   # 每个文档 5 个分块
    ]
    
    logger.info(f"准备向量化 {len(chunks)} 个文档分块")
    
    # 模拟向量化处理
    async def vectorize_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
        """模拟向量化处理"""
        # 模拟向量化延迟（实际应用中这里是调用嵌入模型）
        await asyncio.sleep(0.02)
        
        return {
            "chunk_id": chunk["chunk_id"],
            "vector_id": f"vec_{chunk['chunk_id']}",
            "vector_dim": 768,
            "status": "success"
        }
    
    # 使用平衡策略创建处理器
    config = BatchConfig(
        strategy=BatchSizeStrategy.BALANCED,
        base_batch_size=25,
        max_concurrent_batches=2
    )
    processor = AdaptiveBatchProcessor(config)
    
    # 处理分块
    results, stats = await processor.process_items(
        items=chunks,
        processor=vectorize_chunk,
        progress_callback=lambda current, total: logger.info(
            f"向量化进度: {current}/{total} ({current/total*100:.1f}%)"
        )
    )
    
    logger.info(f"\n向量化完成!")
    logger.info(f"总分块数: {stats.total_items}")
    logger.info(f"成功: {stats.processed_items}")
    logger.info(f"失败: {stats.failed_items}")
    logger.info(f"成功率: {stats.success_rate:.1%}")
    logger.info(f"吞吐量: {stats.throughput:.2f} chunks/s")
    logger.info(f"总耗时: {stats.total_processing_time:.2f}s")
    
    # 性能报告
    report = processor.get_performance_report()
    logger.info(f"\n详细性能报告:")
    logger.info(f"  批次统计:")
    logger.info(f"    - 总批次: {report['total_batches']}")
    logger.info(f"    - 平均批次大小: {report['batch_size']['avg']:.1f}")
    logger.info(f"    - 当前批次大小: {report['batch_size']['current']}")
    logger.info(f"  性能统计:")
    logger.info(f"    - 平均吞吐量: {report['throughput']['avg']:.2f} chunks/s")
    logger.info(f"    - 平均处理时间: {report['processing_time']['avg']:.3f}s")
    logger.info(f"  资源使用:")
    logger.info(f"    - 平均内存使用: {report['memory_usage']['avg']:.1f}%")
    logger.info(f"    - 当前内存使用: {report['memory_usage']['current']:.1f}%")


# ==================== 示例 6: 便捷函数用法 ====================

async def example_convenience_function():
    """便捷函数用法示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 6: 便捷函数用法")
    logger.info("=" * 50)
    
    # 准备数据
    data = [{"id": i, "value": i * 2} for i in range(50)]
    
    # 定义处理器
    async def process_data(item: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.005)
        return {"result": item["value"] ** 2}
    
    # 使用便捷函数（一行代码完成处理）
    results, stats = await process_with_adaptive_batching(
        items=data,
        processor=process_data,
        config=BatchConfig(base_batch_size=15)
    )
    
    logger.info(f"\n处理完成!")
    logger.info(f"项目数: {stats.total_items}")
    logger.info(f"成功率: {stats.success_rate:.1%}")
    logger.info(f"吞吐量: {stats.throughput:.2f} items/s")


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("自适应批次处理器使用示例")
    logger.info("=" * 60)
    
    try:
        await example_basic_usage()
        await example_custom_config()
        await example_stream_processing()
        await example_error_handling()
        await example_document_vectorization()
        await example_convenience_function()
        
        logger.info("\n" + "=" * 60)
        logger.info("所有示例运行完成!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
