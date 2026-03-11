"""
向量存储抽象层使用示例 - 向量化管理模块优化

展示如何使用 VectorStoreAdapter 进行统一的向量存储操作。

任务编号: BE-006
阶段: Phase 2 - 架构升级期
"""

import logging
from typing import List

from app.services.knowledge.vector_store_adapter import (
    VectorStoreAdapter,
    VectorStoreConfig,
    VectorStoreBackend,
    VectorStoreStatus,
    VectorDocument,
    SearchResult,
    CollectionInfo,
    VectorStoreFactory,
    create_vector_store_adapter,
    vector_store_adapter
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本使用 ====================

def example_basic_usage():
    """基本使用示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本使用")
    logger.info("=" * 60)
    
    # 创建适配器
    config = VectorStoreConfig(
        backend=VectorStoreBackend.CHROMA,
        connection_string="http://localhost:8008",
        default_collection="documents",
        dimension=1536
    )
    
    adapter = VectorStoreAdapter(config)
    
    # 健康检查
    status = adapter.health_check()
    logger.info(f"存储状态: {status.value}")
    
    # 获取后端类型
    backend = adapter.get_backend_type()
    logger.info(f"后端类型: {backend.value}")
    
    # 列出集合
    collections = adapter.list_collections()
    logger.info(f"集合列表: {collections}")


# ==================== 示例 2: 文档操作 ====================

def example_document_operations():
    """文档操作示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 文档操作")
    logger.info("=" * 60)
    
    adapter = create_vector_store_adapter()
    
    collection_name = "test_collection"
    
    # 创建集合
    logger.info("创建集合...")
    adapter.create_collection(collection_name, dimension=1536)
    
    # 添加单个文档
    logger.info("添加单个文档...")
    doc = VectorDocument(
        id="doc_001",
        text="这是一个测试文档",
        metadata={"source": "test", "category": "example"}
    )
    
    success = adapter.add_document(collection_name, doc)
    logger.info(f"添加文档: {'成功' if success else '失败'}")
    
    # 批量添加文档
    logger.info("批量添加文档...")
    docs = [
        VectorDocument(
            id=f"doc_{i:03d}",
            text=f"这是第{i}个测试文档",
            metadata={"index": i, "category": "batch"}
        )
        for i in range(2, 6)
    ]
    
    result = adapter.add_documents(collection_name, docs)
    logger.info(f"批量添加结果: {result}")
    
    # 获取文档数量
    count = adapter.count(collection_name)
    logger.info(f"文档数量: {count}")
    
    # 获取文档
    logger.info("获取文档...")
    retrieved = adapter.get_document(collection_name, "doc_001")
    if retrieved:
        logger.info(f"文档内容: {retrieved.text[:50]}...")
    
    # 删除文档
    logger.info("删除文档...")
    deleted = adapter.delete_document(collection_name, "doc_005")
    logger.info(f"删除结果: {'成功' if deleted else '失败'}")
    
    # 再次获取数量
    count = adapter.count(collection_name)
    logger.info(f"删除后数量: {count}")


# ==================== 示例 3: 搜索功能 ====================

def example_search_operations():
    """搜索功能示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 搜索功能")
    logger.info("=" * 60)
    
    adapter = create_vector_store_adapter()
    collection_name = "search_test"
    
    # 创建集合并添加文档
    adapter.create_collection(collection_name)
    
    docs = [
        VectorDocument(
            id="python_doc",
            text="Python是一种高级编程语言，具有简洁优雅的语法",
            metadata={"language": "python", "type": "programming"}
        ),
        VectorDocument(
            id="java_doc",
            text="Java是一种面向对象的编程语言，广泛应用于企业开发",
            metadata={"language": "java", "type": "programming"}
        ),
        VectorDocument(
            id="javascript_doc",
            text="JavaScript是Web开发的主要语言，可以在浏览器中运行",
            metadata={"language": "javascript", "type": "programming"}
        ),
        VectorDocument(
            id="ml_doc",
            text="机器学习是人工智能的一个重要分支，Python是主要工具",
            metadata={"category": "ai", "type": "concept"}
        )
    ]
    
    adapter.add_documents(collection_name, docs)
    
    # 文本搜索
    logger.info("\n文本搜索:")
    query = "Python编程语言"
    results = adapter.search(collection_name, query, top_k=3)
    
    logger.info(f"查询: {query}")
    logger.info(f"找到 {len(results)} 个结果:")
    for i, result in enumerate(results, 1):
        logger.info(f"  {i}. {result.id} (得分: {result.score:.4f})")
        logger.info(f"     内容: {result.text[:40]}...")
    
    # 带过滤的搜索
    logger.info("\n带过滤的搜索:")
    results = adapter.search(
        collection_name,
        "编程语言",
        top_k=3,
        filters={"type": "programming"}
    )
    
    logger.info(f"过滤后找到 {len(results)} 个结果")
    for result in results:
        logger.info(f"  - {result.id}: {result.metadata}")


# ==================== 示例 4: 集合管理 ====================

def example_collection_management():
    """集合管理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 集合管理")
    logger.info("=" * 60)
    
    adapter = create_vector_store_adapter()
    
    # 列出所有集合
    logger.info("当前集合列表:")
    collections = adapter.list_collections()
    for name in collections:
        logger.info(f"  - {name}")
    
    # 创建新集合
    new_collection = "example_collection"
    logger.info(f"\n创建集合: {new_collection}")
    adapter.create_collection(new_collection, dimension=768)
    
    # 获取集合信息
    logger.info("获取集合信息...")
    info = adapter.get_collection_info(new_collection)
    if info:
        logger.info(f"  名称: {info.name}")
        logger.info(f"  维度: {info.dimension}")
        logger.info(f"  后端: {info.backend.value}")
        logger.info(f"  文档数: {info.count}")
    
    # 删除集合
    logger.info(f"\n删除集合: {new_collection}")
    adapter.delete_collection(new_collection)
    logger.info("删除完成")


# ==================== 示例 5: 后端切换 ====================

def example_backend_switching():
    """后端切换示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 后端切换")
    logger.info("=" * 60)
    
    # 创建初始适配器（ChromaDB）
    logger.info("创建 ChromaDB 适配器...")
    adapter = create_vector_store_adapter(backend=VectorStoreBackend.CHROMA)
    
    logger.info(f"当前后端: {adapter.get_backend_type().value}")
    logger.info(f"当前状态: {adapter.get_status().value}")
    
    # 切换到另一个后端（示例，实际需要配置）
    logger.info("\n切换到另一个后端...")
    
    # 注意：这里只是演示，实际切换需要可用的后端服务
    # new_config = VectorStoreConfig(
    #     backend=VectorStoreBackend.FAISS,
    #     connection_string="/path/to/faiss/index",
    #     default_collection="documents"
    # )
    # success = adapter.switch_backend(new_config)
    # logger.info(f"切换结果: {'成功' if success else '失败'}")
    
    logger.info("后端切换演示完成（实际切换需要配置对应后端服务）")


# ==================== 示例 6: 工厂模式 ====================

def example_factory_pattern():
    """工厂模式示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 工厂模式")
    logger.info("=" * 60)
    
    # 查看支持的后端
    logger.info("支持的后端列表:")
    backends = VectorStoreFactory.get_supported_backends()
    for backend in backends:
        logger.info(f"  - {backend.value}")
    
    # 使用工厂创建存储
    logger.info("\n使用工厂创建存储...")
    config = VectorStoreConfig(
        backend=VectorStoreBackend.CHROMA,
        connection_string="http://localhost:8008",
        default_collection="factory_test"
    )
    
    store = VectorStoreFactory.create_store(config)
    if store:
        logger.info(f"创建成功: {type(store).__name__}")
        logger.info(f"后端类型: {store.backend_type.value}")
    else:
        logger.error("创建失败")


# ==================== 示例 7: 健康监控 ====================

def example_health_monitoring():
    """健康监控示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 健康监控")
    logger.info("=" * 60)
    
    adapter = create_vector_store_adapter()
    
    # 检查健康状态
    logger.info("检查存储健康状态...")
    status = adapter.health_check()
    
    status_descriptions = {
        VectorStoreStatus.HEALTHY: "健康",
        VectorStoreStatus.DEGRADED: "降级",
        VectorStoreStatus.UNAVAILABLE: "不可用",
        VectorStoreStatus.INITIALIZING: "初始化中"
    }
    
    logger.info(f"状态: {status.value} ({status_descriptions.get(status, '未知')})")
    
    # 获取集合信息并检查
    logger.info("\n检查各集合状态:")
    collections = adapter.list_collections()
    
    for collection_name in collections:
        info = adapter.get_collection_info(collection_name)
        if info:
            logger.info(f"  {collection_name}:")
            logger.info(f"    文档数: {info.count}")
            logger.info(f"    维度: {info.dimension}")


# ==================== 示例 8: 批量操作性能 ====================

def example_batch_performance():
    """批量操作性能示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 批量操作性能")
    logger.info("=" * 60)
    
    import time
    
    adapter = create_vector_store_adapter()
    collection_name = "batch_perf_test"
    
    # 创建集合
    adapter.create_collection(collection_name)
    
    # 准备批量数据
    batch_sizes = [10, 50, 100]
    
    for batch_size in batch_sizes:
        docs = [
            VectorDocument(
                id=f"batch_{batch_size}_{i}",
                text=f"批量测试文档 {i}",
                metadata={"batch_size": batch_size, "index": i}
            )
            for i in range(batch_size)
        ]
        
        # 测量批量添加时间
        start_time = time.time()
        result = adapter.add_documents(collection_name, docs)
        elapsed = time.time() - start_time
        
        logger.info(f"批量添加 {batch_size} 个文档:")
        logger.info(f"  耗时: {elapsed:.3f}秒")
        logger.info(f"  平均: {elapsed/batch_size*1000:.2f}ms/文档")
        logger.info(f"  结果: {result.get('count', 0)} 个成功")


# ==================== 示例 9: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：多租户知识库
    
    展示如何在实际应用中使用向量存储适配器。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 实际应用场景 - 多租户知识库")
    logger.info("=" * 60)
    
    adapter = create_vector_store_adapter()
    
    # 场景1: 为不同租户创建集合
    logger.info("\n场景1: 多租户集合管理")
    
    tenants = ["tenant_a", "tenant_b", "tenant_c"]
    
    for tenant in tenants:
        collection_name = f"kb_{tenant}"
        logger.info(f"  创建租户集合: {collection_name}")
        adapter.create_collection(collection_name, dimension=1536)
    
    # 场景2: 向不同租户添加文档
    logger.info("\n场景2: 多租户文档管理")
    
    for i, tenant in enumerate(tenants):
        collection_name = f"kb_{tenant}"
        
        # 添加租户专属文档
        docs = [
            VectorDocument(
                id=f"{tenant}_doc_{j}",
                text=f"租户 {tenant} 的文档 {j}",
                metadata={
                    "tenant": tenant,
                    "doc_id": j,
                    "category": f"category_{j % 3}"
                }
            )
            for j in range(5)
        ]
        
        result = adapter.add_documents(collection_name, docs)
        logger.info(f"  {tenant}: 添加 {result.get('count', 0)} 个文档")
    
    # 场景3: 租户内搜索
    logger.info("\n场景3: 租户内搜索")
    
    target_tenant = "tenant_a"
    collection_name = f"kb_{target_tenant}"
    
    query = "租户文档"
    results = adapter.search(collection_name, query, top_k=3)
    
    logger.info(f"在 {target_tenant} 中搜索 '{query}':")
    logger.info(f"  找到 {len(results)} 个结果")
    for result in results:
        logger.info(f"    - {result.id} (得分: {result.score:.4f})")
    
    # 场景4: 监控各租户使用情况
    logger.info("\n场景4: 租户使用情况监控")
    
    for tenant in tenants:
        collection_name = f"kb_{tenant}"
        info = adapter.get_collection_info(collection_name)
        
        if info:
            logger.info(f"  {tenant}:")
            logger.info(f"    文档数: {info.count}")
            logger.info(f"    维度: {info.dimension}")


# ==================== 示例 10: 错误处理 ====================

def example_error_handling():
    """错误处理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 错误处理")
    logger.info("=" * 60)
    
    # 创建适配器
    adapter = create_vector_store_adapter()
    
    # 场景1: 操作不存在的集合
    logger.info("\n场景1: 操作不存在的集合")
    
    try:
        result = adapter.get_collection_info("non_existent_collection")
        if result is None:
            logger.info("  正确返回 None")
    except Exception as e:
        logger.error(f"  异常: {e}")
    
    # 场景2: 获取不存在的文档
    logger.info("\n场景2: 获取不存在的文档")
    
    doc = adapter.get_document("test_collection", "non_existent_doc")
    if doc is None:
        logger.info("  正确返回 None")
    
    # 场景3: 搜索空集合
    logger.info("\n场景3: 搜索空集合")
    
    results = adapter.search("empty_collection", "query")
    logger.info(f"  返回空列表: {len(results) == 0}")
    
    # 场景4: 检查状态后操作
    logger.info("\n场景4: 状态检查")
    
    status = adapter.health_check()
    if status == VectorStoreStatus.HEALTHY:
        logger.info("  存储健康，可以安全操作")
    else:
        logger.warning(f"  存储状态异常: {status.value}")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("向量存储抽象层使用示例")
    logger.info("=" * 70)
    
    try:
        example_basic_usage()
        example_document_operations()
        example_search_operations()
        example_collection_management()
        example_factory_pattern()
        example_health_monitoring()
        # example_batch_performance()  # 需要实际服务
        # example_real_world_scenario()  # 需要实际服务
        # example_error_handling()  # 需要实际服务
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
