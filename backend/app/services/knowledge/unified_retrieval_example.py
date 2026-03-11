"""
一体化检索服务使用示例 - 向量化管理模块优化

展示如何使用 UnifiedRetrievalService 进行多源检索和结果融合。

任务编号: BE-011
阶段: Phase 3 - 一体化建设期
"""

import asyncio
import logging
from typing import Dict, Any, List

from app.services.knowledge.unified_retrieval_service import (
    UnifiedRetrievalService,
    UnifiedSearchRequest,
    UnifiedSearchResponse,
    RetrievalType,
    FusionAlgorithm,
    SearchResult,
    unified_search,
    unified_retrieval_service
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本向量检索 ====================

async def example_vector_search():
    """向量检索示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本向量检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    # 构建搜索请求
    request = UnifiedSearchRequest(
        query="人工智能的发展历史",
        retrieval_types=[RetrievalType.VECTOR],
        top_k=5,
        knowledge_base_id=1
    )
    
    # 执行搜索
    response = service.search(request)
    
    # 输出结果
    logger.info(f"查询: {response.query}")
    logger.info(f"检索类型: {[t.value for t in response.retrieval_types]}")
    logger.info(f"融合算法: {response.fusion_algorithm.value}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info(f"结果数量: {response.total_results}")
    logger.info("\n检索结果:")
    
    for i, result in enumerate(response.results, 1):
        logger.info(f"  {i}. [{result.source_type.value}] {result.title}")
        logger.info(f"     分数: {result.score:.4f}")
        logger.info(f"     内容: {result.content[:100]}...")


# ==================== 示例 2: 实体检索 ====================

async def example_entity_search():
    """实体检索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 实体检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    request = UnifiedSearchRequest(
        query="机器学习",
        retrieval_types=[RetrievalType.ENTITY],
        top_k=5,
        knowledge_base_id=1,
        entity_types=["TECHNOLOGY", "CONCEPT", "ALGORITHM"]
    )
    
    response = service.search(request)
    
    logger.info(f"查询: {response.query}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info(f"结果数量: {response.total_results}")
    logger.info("\n实体结果:")
    
    for i, result in enumerate(response.results, 1):
        entity_type = result.metadata.get('entity_type', 'UNKNOWN')
        confidence = result.metadata.get('confidence', 0)
        logger.info(f"  {i}. [{entity_type}] {result.content}")
        logger.info(f"     置信度: {confidence:.2f}")


# ==================== 示例 3: 图谱检索 ====================

async def example_graph_search():
    """图谱检索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 图谱检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    request = UnifiedSearchRequest(
        query="深度学习",
        retrieval_types=[RetrievalType.GRAPH],
        top_k=5,
        knowledge_base_id=1,
        relationship_types=["is_a", "used_in", "related_to"]
    )
    
    response = service.search(request)
    
    logger.info(f"查询: {response.query}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info(f"结果数量: {response.total_results}")
    logger.info("\n关系结果:")
    
    for i, result in enumerate(response.results, 1):
        rel_type = result.metadata.get('relationship_type', 'UNKNOWN')
        source = result.metadata.get('source_entity', '')
        target = result.metadata.get('target_entity', '')
        logger.info(f"  {i}. [{rel_type}] {source} -> {target}")
        logger.info(f"     分数: {result.score:.4f}")


# ==================== 示例 4: RRF融合检索 ====================

async def example_rrf_fusion():
    """RRF融合检索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: RRF融合检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    # 使用RRF融合算法
    request = UnifiedSearchRequest(
        query="神经网络应用",
        retrieval_types=[
            RetrievalType.VECTOR,
            RetrievalType.ENTITY,
            RetrievalType.GRAPH
        ],
        fusion_algorithm=FusionAlgorithm.RRF,
        rrf_k=60,  # RRF常数
        top_k=10,
        knowledge_base_id=1
    )
    
    response = service.search(request)
    
    logger.info(f"查询: {response.query}")
    logger.info(f"融合算法: {response.fusion_algorithm.value} (k={request.rrf_k})")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info(f"各源结果数: {response.source_stats}")
    logger.info(f"融合后结果: {response.total_results}")
    logger.info("\n融合结果:")
    
    for i, result in enumerate(response.results, 1):
        logger.info(f"  {i}. [{result.source_type.value}] {result.title}")
        logger.info(f"     RRF分数: {result.score:.4f}")
        logger.info(f"     内容: {result.content[:80]}...")


# ==================== 示例 5: 加权融合检索 ====================

async def example_weighted_fusion():
    """加权融合检索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 加权融合检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    # 使用加权融合算法
    request = UnifiedSearchRequest(
        query="自然语言处理技术",
        retrieval_types=[
            RetrievalType.VECTOR,
            RetrievalType.ENTITY,
            RetrievalType.GRAPH
        ],
        fusion_algorithm=FusionAlgorithm.WEIGHTED,
        vector_weight=0.6,    # 向量权重60%
        entity_weight=0.3,    # 实体权重30%
        graph_weight=0.1,     # 图谱权重10%
        top_k=10,
        knowledge_base_id=1
    )
    
    response = service.search(request)
    
    logger.info(f"查询: {response.query}")
    logger.info(f"融合算法: {response.fusion_algorithm.value}")
    logger.info(f"权重配置: 向量={request.vector_weight}, 实体={request.entity_weight}, 图谱={request.graph_weight}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info("\n加权融合结果:")
    
    for i, result in enumerate(response.results, 1):
        logger.info(f"  {i}. [{result.source_type.value}] {result.title}")
        logger.info(f"     加权分数: {result.score:.4f}")


# ==================== 示例 6: 线性融合检索 ====================

async def example_linear_fusion():
    """线性融合检索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 线性融合检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    # 使用线性融合算法
    request = UnifiedSearchRequest(
        query="计算机视觉算法",
        retrieval_types=[
            RetrievalType.VECTOR,
            RetrievalType.ENTITY
        ],
        fusion_algorithm=FusionAlgorithm.LINEAR,
        top_k=8,
        knowledge_base_id=1
    )
    
    response = service.search(request)
    
    logger.info(f"查询: {response.query}")
    logger.info(f"融合算法: {response.fusion_algorithm.value}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info("\n线性融合结果:")
    
    for i, result in enumerate(response.results, 1):
        logger.info(f"  {i}. [{result.source_type.value}] {result.title}")
        logger.info(f"     分数: {result.score:.4f}")


# ==================== 示例 7: 异步并行检索 ====================

async def example_async_search():
    """异步并行检索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 异步并行检索")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    request = UnifiedSearchRequest(
        query="强化学习算法",
        retrieval_types=[
            RetrievalType.VECTOR,
            RetrievalType.ENTITY,
            RetrievalType.GRAPH
        ],
        fusion_algorithm=FusionAlgorithm.RRF,
        top_k=10,
        knowledge_base_id=1
    )
    
    # 异步执行搜索
    response = await service.search_async(request)
    
    logger.info(f"查询: {response.query}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info(f"结果数量: {response.total_results}")
    logger.info("\n异步检索结果:")
    
    for i, result in enumerate(response.results[:5], 1):
        logger.info(f"  {i}. [{result.source_type.value}] {result.title}")


# ==================== 示例 8: 便捷函数使用 ====================

async def example_convenience_function():
    """便捷函数使用示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 便捷函数使用")
    logger.info("=" * 60)
    
    # 使用便捷函数 unified_search
    results = unified_search(
        query="数据挖掘技术",
        retrieval_types=["vector", "entity"],
        top_k=5,
        knowledge_base_id=1,
        fusion_algorithm="rrf"
    )
    
    logger.info(f"查询: {results['query']}")
    logger.info(f"融合算法: {results['fusion_algorithm']}")
    logger.info(f"处理时间: {results['processing_time_ms']}ms")
    logger.info(f"结果数量: {results['total_results']}")
    logger.info("\n检索结果:")
    
    for i, result in enumerate(results['results'], 1):
        logger.info(f"  {i}. [{result['source_type']}] {result['title']}")
        logger.info(f"     分数: {result['score']:.4f}")


# ==================== 示例 9: 混合检索便捷方法 ====================

async def example_hybrid_search():
    """混合检索便捷方法示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 混合检索便捷方法")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    # 使用混合检索方法（自动使用向量+实体+图谱）
    response = service.hybrid_search(
        query="推荐系统算法",
        top_k=10,
        knowledge_base_id=1,
        use_rrf=True
    )
    
    logger.info(f"查询: {response.query}")
    logger.info(f"融合算法: {response.fusion_algorithm.value}")
    logger.info(f"处理时间: {response.processing_time_ms}ms")
    logger.info(f"各源结果数: {response.source_stats}")
    logger.info("\n混合检索结果:")
    
    # 按来源类型分组显示
    vector_results = [r for r in response.results if r.source_type == RetrievalType.VECTOR]
    entity_results = [r for r in response.results if r.source_type == RetrievalType.ENTITY]
    graph_results = [r for r in response.results if r.source_type == RetrievalType.GRAPH]
    
    if vector_results:
        logger.info("\n  [向量结果]")
        for i, result in enumerate(vector_results[:3], 1):
            logger.info(f"    {i}. {result.title} (分数: {result.score:.4f})")
    
    if entity_results:
        logger.info("\n  [实体结果]")
        for i, result in enumerate(entity_results[:3], 1):
            logger.info(f"    {i}. {result.content} (分数: {result.score:.4f})")
    
    if graph_results:
        logger.info("\n  [图谱结果]")
        for i, result in enumerate(graph_results[:3], 1):
            logger.info(f"    {i}. {result.title} (分数: {result.score:.4f})")


# ==================== 示例 10: 实际应用场景 ====================

async def example_real_world_scenario():
    """
    实际应用场景：智能问答系统的检索模块
    
    展示如何在实际应用中使用一体化检索服务。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 实际应用场景 - 智能问答系统")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    
    # 模拟用户查询
    user_queries = [
        "什么是Transformer模型？",
        "BERT和GPT有什么区别？",
        "如何使用深度学习进行图像分类？",
        "自然语言处理的最新进展"
    ]
    
    logger.info(f"处理 {len(user_queries)} 个用户查询\n")
    
    for query in user_queries:
        logger.info(f"用户查询: {query}")
        
        # 执行混合检索
        response = service.hybrid_search(
            query=query,
            top_k=5,
            knowledge_base_id=1,
            use_rrf=True
        )
        
        logger.info(f"  处理时间: {response.processing_time_ms}ms")
        logger.info(f"  检索来源: {response.source_stats}")
        logger.info(f"  找到 {response.total_results} 个相关结果")
        
        # 显示前3个结果
        logger.info("  最相关结果:")
        for i, result in enumerate(response.results[:3], 1):
            source_icon = {
                RetrievalType.VECTOR: "📄",
                RetrievalType.ENTITY: "🏷️",
                RetrievalType.GRAPH: "🔗"
            }.get(result.source_type, "❓")
            
            logger.info(f"    {i}. {source_icon} {result.title}")
            logger.info(f"       分数: {result.score:.4f}")
            
            # 根据来源类型显示不同信息
            if result.source_type == RetrievalType.ENTITY:
                entity_type = result.metadata.get('entity_type', 'UNKNOWN')
                logger.info(f"       实体类型: {entity_type}")
            elif result.source_type == RetrievalType.GRAPH:
                rel_type = result.metadata.get('relationship_type', 'UNKNOWN')
                logger.info(f"       关系类型: {rel_type}")
        
        logger.info("")
    
    logger.info("所有查询处理完成!")


# ==================== 示例 11: 不同融合算法对比 ====================

async def example_fusion_comparison():
    """不同融合算法对比示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 11: 不同融合算法对比")
    logger.info("=" * 60)
    
    service = UnifiedRetrievalService()
    query = "机器学习算法比较"
    
    algorithms = [
        (FusionAlgorithm.RRF, "RRF融合"),
        (FusionAlgorithm.WEIGHTED, "加权融合"),
        (FusionAlgorithm.LINEAR, "线性融合")
    ]
    
    logger.info(f"查询: {query}\n")
    
    for algorithm, name in algorithms:
        request = UnifiedSearchRequest(
            query=query,
            retrieval_types=[
                RetrievalType.VECTOR,
                RetrievalType.ENTITY,
                RetrievalType.GRAPH
            ],
            fusion_algorithm=algorithm,
            top_k=5,
            knowledge_base_id=1
        )
        
        response = service.search(request)
        
        logger.info(f"[{name}]")
        logger.info(f"  处理时间: {response.processing_time_ms}ms")
        logger.info(f"  结果数量: {response.total_results}")
        logger.info(f"  前3个结果:")
        
        for i, result in enumerate(response.results[:3], 1):
            logger.info(f"    {i}. [{result.source_type.value}] {result.title} (分数: {result.score:.4f})")
        
        logger.info("")


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("一体化检索服务使用示例")
    logger.info("=" * 70)
    
    try:
        await example_vector_search()
        await example_entity_search()
        await example_graph_search()
        await example_rrf_fusion()
        await example_weighted_fusion()
        await example_linear_fusion()
        await example_async_search()
        await example_convenience_function()
        await example_hybrid_search()
        await example_real_world_scenario()
        await example_fusion_comparison()
        
        logger.info("\n" + "=" * 70)
        logger.info("所有示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
