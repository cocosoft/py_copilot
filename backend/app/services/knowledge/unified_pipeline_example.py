"""
统一处理流水线使用示例 - 向量化管理模块优化

展示如何使用 UnifiedProcessingPipeline 进行文档处理。

任务编号: BE-010
阶段: Phase 3 - 一体化建设期
"""

import asyncio
import logging
from typing import Dict, Any

from app.services.knowledge.unified_processing_pipeline import (
    UnifiedProcessingPipeline,
    PipelineStage,
    PipelineStatus,
    PipelineContext,
    process_document_with_pipeline
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本用法 ====================

async def example_basic_usage():
    """基本用法示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本用法")
    logger.info("=" * 60)
    
    # 创建流水线
    pipeline = UnifiedProcessingPipeline()
    
    # 处理文档
    context = await pipeline.process(
        document_id="doc_001",
        knowledge_base_id=1,
        file_path="/docs/sample.pdf",
        file_type="pdf"
    )
    
    # 检查结果
    logger.info(f"处理状态: {context.status.value}")
    logger.info(f"完成阶段数: {len(context.stage_results)}")
    
    if context.status == PipelineStatus.COMPLETED:
        logger.info("✓ 处理成功完成")
    else:
        logger.error(f"✗ 处理失败: {context.error_message}")


# ==================== 示例 2: 自定义阶段 ====================

async def example_custom_stages():
    """自定义阶段示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 自定义阶段")
    logger.info("=" * 60)
    
    # 只执行部分阶段
    custom_stages = [
        PipelineStage.DOCUMENT_PARSE,
        PipelineStage.TEXT_CLEAN,
        PipelineStage.SEMANTIC_CHUNK
    ]
    
    pipeline = UnifiedProcessingPipeline(stages=custom_stages)
    
    context = await pipeline.process(
        document_id="doc_002",
        knowledge_base_id=1,
        file_path="/docs/article.txt",
        file_type="txt"
    )
    
    logger.info(f"执行了 {len(context.stage_results)} 个阶段")
    for stage in custom_stages:
        result = context.get_stage_result(stage)
        if result:
            logger.info(f"  - {stage.value}: {'成功' if result.is_success else '失败'}")


# ==================== 示例 3: 进度追踪 ====================

async def example_progress_tracking():
    """进度追踪示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 进度追踪")
    logger.info("=" * 60)
    
    pipeline = UnifiedProcessingPipeline()
    
    # 定义进度回调
    def on_progress(
        document_id: str,
        progress: int,
        stage: str,
        message: str,
        metadata: Dict[str, Any]
    ):
        logger.info(f"[{document_id}] 进度: {progress}% | 阶段: {stage} | {message}")
    
    # 注册回调
    pipeline.register_progress_callback(on_progress)
    
    # 处理文档
    context = await pipeline.process(
        document_id="doc_003",
        knowledge_base_id=1,
        file_path="/docs/report.docx",
        file_type="docx"
    )
    
    logger.info(f"最终状态: {context.status.value}")


# ==================== 示例 4: 阶段结果访问 ====================

async def example_access_stage_results():
    """访问阶段结果示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 访问阶段结果")
    logger.info("=" * 60)
    
    pipeline = UnifiedProcessingPipeline()
    
    context = await pipeline.process(
        document_id="doc_004",
        knowledge_base_id=1,
        file_path="/docs/data.csv",
        file_type="csv"
    )
    
    # 访问各阶段结果
    logger.info("各阶段结果:")
    
    # 文档解析结果
    parse_result = context.get_stage_result(PipelineStage.DOCUMENT_PARSE)
    if parse_result and parse_result.is_success:
        logger.info(f"  文档解析: {parse_result.output_data.get('text_length', 0)} 字符")
    
    # 语义分块结果
    chunk_result = context.get_stage_result(PipelineStage.SEMANTIC_CHUNK)
    if chunk_result and chunk_result.is_success:
        logger.info(f"  语义分块: {chunk_result.output_data.get('chunk_count', 0)} 个块")
    
    # 实体识别结果
    entity_result = context.get_stage_result(PipelineStage.ENTITY_EXTRACT)
    if entity_result and entity_result.is_success:
        logger.info(f"  实体识别: {entity_result.output_data.get('entity_count', 0)} 个实体")
    
    # 向量化结果
    vector_result = context.get_stage_result(PipelineStage.VECTORIZE)
    if vector_result and vector_result.is_success:
        success_rate = vector_result.output_data.get('success_rate', 0)
        logger.info(f"  向量化: 成功率 {success_rate:.1%}")


# ==================== 示例 5: 共享数据访问 ====================

async def example_shared_data():
    """共享数据访问示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 共享数据访问")
    logger.info("=" * 60)
    
    pipeline = UnifiedProcessingPipeline()
    
    context = await pipeline.process(
        document_id="doc_005",
        knowledge_base_id=1,
        file_path="/docs/long_article.txt",
        file_type="txt"
    )
    
    # 访问共享数据
    logger.info("共享数据:")
    logger.info(f"  原始文本长度: {context.get_data('text_length', 0)}")
    logger.info(f"  清理后长度: {context.get_data('cleaned_length', 0)}")
    logger.info(f"  分块数量: {context.get_data('chunk_count', 0)}")
    logger.info(f"  实体数量: {context.get_data('entity_count', 0)}")
    logger.info(f"  关系数量: {context.get_data('relationship_count', 0)}")


# ==================== 示例 6: 流水线统计 ====================

async def example_pipeline_stats():
    """流水线统计示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 流水线统计")
    logger.info("=" * 60)
    
    pipeline = UnifiedProcessingPipeline()
    
    context = await pipeline.process(
        document_id="doc_006",
        knowledge_base_id=1,
        file_path="/docs/paper.pdf",
        file_type="pdf"
    )
    
    # 获取统计信息
    stats = pipeline.get_pipeline_stats(context)
    
    logger.info("流水线统计:")
    logger.info(f"  文档ID: {stats['document_id']}")
    logger.info(f"  状态: {stats['status']}")
    logger.info(f"  总耗时: {stats['total_duration_ms']}ms")
    logger.info(f"  总阶段数: {stats['stage_count']}")
    logger.info(f"  成功阶段: {stats['completed_stages']}")
    logger.info(f"  失败阶段: {stats['failed_stages']}")
    
    logger.info("\n各阶段详情:")
    for stage_stat in stats['stage_stats']:
        status_icon = "✓" if stage_stat['success'] else "✗"
        logger.info(f"  {status_icon} {stage_stat['stage']}: {stage_stat['duration_ms']}ms")


# ==================== 示例 7: 错误处理 ====================

async def example_error_handling():
    """错误处理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 错误处理")
    logger.info("=" * 60)
    
    # 使用不存在的文件测试错误处理
    pipeline = UnifiedProcessingPipeline()
    
    try:
        context = await pipeline.process(
            document_id="doc_007",
            knowledge_base_id=1,
            file_path="/nonexistent/file.pdf",
            file_type="pdf"
        )
        
        if context.status == PipelineStatus.FAILED:
            logger.error(f"处理失败: {context.error_message}")
            logger.error(f"失败阶段: {context.failed_stage.value if context.failed_stage else 'N/A'}")
            
            # 检查是否已回滚
            if context.status == PipelineStatus.ROLLED_BACK:
                logger.info("已自动回滚")
    
    except Exception as e:
        logger.error(f"异常: {e}")


# ==================== 示例 8: 便捷函数 ====================

async def example_convenience_function():
    """便捷函数示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 便捷函数")
    logger.info("=" * 60)
    
    # 使用便捷函数
    context = await process_document_with_pipeline(
        document_id="doc_008",
        knowledge_base_id=1,
        file_path="/docs/notes.md",
        file_type="md",
        stages=[
            PipelineStage.DOCUMENT_PARSE,
            PipelineStage.TEXT_CLEAN,
            PipelineStage.SEMANTIC_CHUNK
        ]
    )
    
    logger.info(f"处理结果: {context.status.value}")
    logger.info(f"完成阶段: {len(context.stage_results)}")


# ==================== 示例 9: 批量处理 ====================

async def example_batch_processing():
    """批量处理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 批量处理")
    logger.info("=" * 60)
    
    pipeline = UnifiedProcessingPipeline()
    
    # 批量处理多个文档
    documents = [
        {"id": "batch_001", "path": "/docs/doc1.pdf", "type": "pdf"},
        {"id": "batch_002", "path": "/docs/doc2.txt", "type": "txt"},
        {"id": "batch_003", "path": "/docs/doc3.docx", "type": "docx"},
    ]
    
    results = []
    for doc in documents:
        context = await pipeline.process(
            document_id=doc["id"],
            knowledge_base_id=1,
            file_path=doc["path"],
            file_type=doc["type"]
        )
        results.append({
            "id": doc["id"],
            "status": context.status.value,
            "completed_stages": len(context.stage_results)
        })
    
    logger.info("批量处理结果:")
    for result in results:
        status_icon = "✓" if result["status"] == "completed" else "✗"
        logger.info(f"  {status_icon} {result['id']}: {result['status']} ({result['completed_stages']} 阶段)")


# ==================== 示例 10: 实际应用场景 ====================

async def example_real_world_scenario():
    """
    实际应用场景：知识库文档导入
    
    展示如何在实际应用中使用统一处理流水线。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 实际应用场景 - 知识库文档导入")
    logger.info("=" * 60)
    
    # 创建流水线
    pipeline = UnifiedProcessingPipeline()
    
    # 定义进度回调（实际应用中可能更新到数据库或发送WebSocket消息）
    def on_progress(
        document_id: str,
        progress: int,
        stage: str,
        message: str,
        metadata: Dict[str, Any]
    ):
        # 实际应用中这里可以：
        # 1. 更新数据库中的进度
        # 2. 发送WebSocket消息给前端
        # 3. 记录到日志系统
        logger.info(f"[导入进度] 文档 {document_id}: {progress}% - {stage}")
    
    pipeline.register_progress_callback(on_progress)
    
    # 模拟导入多个文档
    import_tasks = [
        {
            "document_id": "import_001",
            "title": "人工智能发展报告",
            "file_path": "/uploads/ai_report_2024.pdf",
            "file_type": "pdf"
        },
        {
            "document_id": "import_002",
            "title": "机器学习算法总结",
            "file_path": "/uploads/ml_algorithms.txt",
            "file_type": "txt"
        }
    ]
    
    logger.info(f"开始导入 {len(import_tasks)} 个文档到知识库")
    
    for task in import_tasks:
        logger.info(f"\n导入文档: {task['title']}")
        
        context = await pipeline.process(
            document_id=task["document_id"],
            knowledge_base_id=1,
            file_path=task["file_path"],
            file_type=task["file_type"]
        )
        
        if context.status == PipelineStatus.COMPLETED:
            logger.info(f"✓ 导入成功: {task['title']}")
            
            # 获取处理统计
            stats = pipeline.get_pipeline_stats(context)
            logger.info(f"  总耗时: {stats['total_duration_ms']}ms")
            logger.info(f"  文本长度: {context.get_data('text_length', 0)} 字符")
            logger.info(f"  分块数: {context.get_data('chunk_count', 0)}")
            logger.info(f"  实体数: {context.get_data('entity_count', 0)}")
        else:
            logger.error(f"✗ 导入失败: {task['title']}")
            logger.error(f"  错误: {context.error_message}")
    
    logger.info("\n所有文档导入完成!")


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("统一处理流水线使用示例")
    logger.info("=" * 70)
    
    try:
        await example_basic_usage()
        await example_custom_stages()
        await example_progress_tracking()
        await example_access_stage_results()
        await example_shared_data()
        await example_pipeline_stats()
        await example_error_handling()
        await example_convenience_function()
        await example_batch_processing()
        await example_real_world_scenario()
        
        logger.info("\n" + "=" * 70)
        logger.info("所有示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
