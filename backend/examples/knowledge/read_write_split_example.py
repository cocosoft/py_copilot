"""
读写分离服务使用示例 - 向量化管理模块优化

展示如何使用 ReadWriteSplitService 实现向量存储的读写分离。

任务编号: BE-007
阶段: Phase 2 - 架构升级期
"""

import logging
import time
from typing import List

from app.services.knowledge.read_write_split_service import (
    ReadWriteSplitService,
    ReadWriteRouter,
    DataSynchronizer,
    VectorStoreNode,
    NodeConfig,
    NodeRole,
    NodeStatus,
    RoutingStrategy,
    NodeStats,
    create_read_write_split_service,
    read_write_split_service
)

from app.services.knowledge.vector_store_adapter import (
    VectorStoreConfig,
    VectorStoreBackend,
    VectorDocument
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本配置和启动 ====================

def example_basic_setup():
    """基本配置和启动示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本配置和启动")
    logger.info("=" * 60)
    
    # 创建服务
    service = ReadWriteSplitService(
        routing_strategy=RoutingStrategy.ROUND_ROBIN,
        max_sync_lag_ms=100.0,
        enable_sync=True
    )
    
    # 配置主库
    master_config = NodeConfig(
        id="master-1",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008",
            default_collection="documents"
        ),
        weight=10,
        max_connections=100
    )
    
    # 配置从库
    slave_configs = [
        NodeConfig(
            id="slave-1",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string="http://localhost:8009",
                default_collection="documents"
            ),
            weight=5,
            max_connections=50
        ),
        NodeConfig(
            id="slave-2",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string="http://localhost:8010",
                default_collection="documents"
            ),
            weight=5,
            max_connections=50
        )
    ]
    
    # 添加节点
    logger.info("添加主库节点...")
    service.add_node(master_config)
    
    logger.info("添加从库节点...")
    for config in slave_configs:
        service.add_node(config)
    
    # 启动服务
    logger.info("启动读写分离服务...")
    service.start()
    
    logger.info("服务启动完成")
    
    return service


# ==================== 示例 2: 路由策略 ====================

def example_routing_strategies():
    """路由策略示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 路由策略")
    logger.info("=" * 60)
    
    strategies = [
        RoutingStrategy.ROUND_ROBIN,
        RoutingStrategy.RANDOM,
        RoutingStrategy.WEIGHTED,
        RoutingStrategy.LEAST_CONNECTIONS
    ]
    
    for strategy in strategies:
        logger.info(f"\n策略: {strategy.value}")
        
        # 创建使用该策略的服务
        service = ReadWriteSplitService(routing_strategy=strategy)
        
        # 添加节点
        master_config = NodeConfig(
            id="master",
            role=NodeRole.MASTER,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string="http://localhost:8008"
            )
        )
        
        slave_configs = [
            NodeConfig(
                id=f"slave-{i}",
                role=NodeRole.SLAVE,
                config=VectorStoreConfig(
                    backend=VectorStoreBackend.CHROMA,
                    connection_string=f"http://localhost:{8009+i}"
                ),
                weight=i+1
            )
            for i in range(3)
        ]
        
        service.add_node(master_config)
        for config in slave_configs:
            service.add_node(config)
        
        logger.info(f"  已配置 {len(slave_configs)} 个从库")
        logger.info(f"  策略说明: {get_strategy_description(strategy)}")


def get_strategy_description(strategy: RoutingStrategy) -> str:
    """获取策略说明"""
    descriptions = {
        RoutingStrategy.ROUND_ROBIN: "轮询选择，平均分配负载",
        RoutingStrategy.RANDOM: "随机选择，简单高效",
        RoutingStrategy.WEIGHTED: "加权选择，根据权重分配",
        RoutingStrategy.LEAST_CONNECTIONS: "最少连接，优先选择空闲节点",
        RoutingStrategy.NEAREST: "就近选择，选择延迟最低的节点"
    }
    return descriptions.get(strategy, "未知策略")


# ==================== 示例 3: 写操作路由 ====================

def example_write_operations():
    """写操作路由示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 写操作路由（自动路由到主库）")
    logger.info("=" * 60)
    
    service = ReadWriteSplitService()
    
    # 配置节点
    master_config = NodeConfig(
        id="master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008"
        )
    )
    
    service.add_node(master_config)
    service.start()
    
    logger.info("\n写操作列表:")
    
    # 创建集合
    logger.info("  1. create_collection - 创建集合")
    # service.create_collection("test_collection", dimension=1536)
    
    # 添加文档
    logger.info("  2. add_document - 添加单个文档")
    doc = VectorDocument(
        id="doc_001",
        text="测试文档",
        metadata={"source": "test"}
    )
    # service.add_document("test_collection", doc)
    
    # 批量添加
    logger.info("  3. add_documents - 批量添加文档")
    docs = [
        VectorDocument(id=f"doc_{i}", text=f"文档{i}")
        for i in range(10)
    ]
    # service.add_documents("test_collection", docs)
    
    # 删除文档
    logger.info("  4. delete_document - 删除文档")
    # service.delete_document("test_collection", "doc_001")
    
    # 删除集合
    logger.info("  5. delete_collection - 删除集合")
    # service.delete_collection("test_collection")
    
    logger.info("\n所有写操作都会自动路由到主库")


# ==================== 示例 4: 读操作路由 ====================

def example_read_operations():
    """读操作路由示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 读操作路由（自动路由到从库）")
    logger.info("=" * 60)
    
    service = ReadWriteSplitService()
    
    # 配置节点
    master_config = NodeConfig(
        id="master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008"
        )
    )
    
    slave_configs = [
        NodeConfig(
            id=f"slave-{i}",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string=f"http://localhost:{8009+i}"
            )
        )
        for i in range(2)
    ]
    
    service.add_node(master_config)
    for config in slave_configs:
        service.add_node(config)
    
    service.start()
    
    logger.info("\n读操作列表:")
    
    # 获取文档
    logger.info("  1. get_document - 获取文档")
    # doc = service.get_document("collection", "doc_001")
    
    # 搜索
    logger.info("  2. search - 文本搜索")
    # results = service.search("collection", "查询", top_k=5)
    
    # 向量搜索
    logger.info("  3. search_by_vector - 向量搜索")
    # results = service.search_by_vector("collection", [0.1, 0.2, ...], top_k=5)
    
    # 获取数量
    logger.info("  4. count - 获取文档数量")
    # count = service.count("collection")
    
    # 列出集合
    logger.info("  5. list_collections - 列出所有集合")
    # collections = service.list_collections()
    
    # 获取集合信息
    logger.info("  6. get_collection_info - 获取集合信息")
    # info = service.get_collection_info("collection")
    
    logger.info("\n所有读操作都会自动路由到从库（如果可用）")
    logger.info("如果从库不可用或延迟过高，会自动回退到主库")


# ==================== 示例 5: 故障转移 ====================

def example_failover():
    """故障转移示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 故障转移")
    logger.info("=" * 60)
    
    service = ReadWriteSplitService()
    
    # 配置主库和从库
    master_config = NodeConfig(
        id="master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008"
        )
    )
    
    slave_config = NodeConfig(
        id="slave-1",
        role=NodeRole.SLAVE,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8009"
        )
    )
    
    service.add_node(master_config)
    service.add_node(slave_config)
    
    logger.info("\n场景1: 主库故障")
    logger.info("  当主库不可用时，系统会自动尝试提升从库为主库")
    logger.info("  这个过程是自动的，无需人工干预")
    
    logger.info("\n场景2: 从库故障")
    logger.info("  当从库不可用时，读操作会自动路由到其他可用从库")
    logger.info("  如果所有从库都不可用，读操作会回退到主库")
    
    logger.info("\n场景3: 故障恢复")
    logger.info("  节点恢复后，会自动重新加入集群")
    logger.info("  健康检查会定期检测节点状态")


# ==================== 示例 6: 同步监控 ====================

def example_sync_monitoring():
    """同步监控示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 同步监控")
    logger.info("=" * 60)
    
    service = ReadWriteSplitService(
        max_sync_lag_ms=100.0,  # 最大同步延迟100ms
        enable_sync=True
    )
    
    # 配置节点
    master_config = NodeConfig(
        id="master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008"
        )
    )
    
    slave_configs = [
        NodeConfig(
            id=f"slave-{i}",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string=f"http://localhost:{8009+i}"
            )
        )
        for i in range(2)
    ]
    
    service.add_node(master_config)
    for config in slave_configs:
        service.add_node(config)
    
    service.start()
    
    # 获取同步统计
    logger.info("\n同步统计信息:")
    sync_stats = service.get_sync_stats()
    
    for key, value in sync_stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n同步延迟监控:")
    logger.info("  - 最大允许延迟: 100ms")
    logger.info("  - 超过延迟阈值时，读操作会回退到主库")
    logger.info("  - 确保数据一致性")


# ==================== 示例 7: 性能统计 ====================

def example_performance_stats():
    """性能统计示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 性能统计")
    logger.info("=" * 60)
    
    service = ReadWriteSplitService()
    
    # 配置节点
    master_config = NodeConfig(
        id="master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008"
        )
    )
    
    slave_configs = [
        NodeConfig(
            id=f"slave-{i}",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string=f"http://localhost:{8009+i}"
            ),
            weight=5
        )
        for i in range(2)
    ]
    
    service.add_node(master_config)
    for config in slave_configs:
        service.add_node(config)
    
    service.start()
    
    # 模拟一些请求
    logger.info("\n模拟请求...")
    
    # 获取路由统计
    logger.info("\n路由统计:")
    routing_stats = service.get_routing_stats()
    
    for key, value in routing_stats.items():
        logger.info(f"  {key}: {value}")
    
    # 获取节点统计
    logger.info("\n节点统计:")
    node_stats = service.get_node_stats()
    
    for node_id, stats in node_stats.items():
        logger.info(f"\n  节点 {node_id}:")
        for key, value in stats.to_dict().items():
            logger.info(f"    {key}: {value}")


# ==================== 示例 8: 健康检查 ====================

def example_health_check():
    """健康检查示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 健康检查")
    logger.info("=" * 60)
    
    service = ReadWriteSplitService()
    
    # 配置节点
    nodes = [
        NodeConfig(
            id="master",
            role=NodeRole.MASTER,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string="http://localhost:8008"
            )
        ),
        NodeConfig(
            id="slave-1",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string="http://localhost:8009"
            )
        ),
        NodeConfig(
            id="slave-2",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string="http://localhost:8010"
            )
        )
    ]
    
    for config in nodes:
        service.add_node(config)
    
    # 执行健康检查
    logger.info("\n执行健康检查...")
    health = service.health_check()
    
    logger.info("\n健康检查结果:")
    for node_id, status in health.items():
        logger.info(f"  {node_id}:")
        logger.info(f"    状态: {status['status']}")
        logger.info(f"    角色: {status['role']}")


# ==================== 示例 9: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：高并发知识库系统
    
    展示如何在实际应用中使用读写分离服务。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 实际应用场景 - 高并发知识库系统")
    logger.info("=" * 60)
    
    # 场景：大型知识库系统，读多写少
    logger.info("\n场景描述:")
    logger.info("  - 大型知识库系统")
    logger.info("  - 读操作占90%，写操作占10%")
    logger.info("  - 需要支持高并发查询")
    logger.info("  - 要求低延迟响应")
    
    # 配置一主多从
    logger.info("\n架构配置:")
    logger.info("  - 1个主库（处理写操作）")
    logger.info("  - 3个从库（处理读操作，负载均衡）")
    
    master_config = NodeConfig(
        id="kb-master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://master:8008"
        ),
        max_connections=50,
        weight=10
    )
    
    slave_configs = [
        NodeConfig(
            id=f"kb-slave-{i}",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string=f"http://slave-{i}:8008"
            ),
            max_connections=100,
            weight=10
        )
        for i in range(3)
    ]
    
    # 创建服务
    service = create_read_write_split_service(
        master_config=master_config,
        slave_configs=slave_configs,
        routing_strategy=RoutingStrategy.LEAST_CONNECTIONS
    )
    
    logger.info("\n读写分离优势:")
    logger.info("  1. 主库压力降低约40%（读操作分流到从库）")
    logger.info("  2. 读操作性能提升（多从库负载均衡）")
    logger.info("  3. 系统可用性提升（故障自动转移）")
    logger.info("  4. 支持水平扩展（动态添加从库）")
    
    logger.info("\n监控指标:")
    logger.info("  - 主库QPS（写操作）")
    logger.info("  - 从库QPS（读操作）")
    logger.info("  - 同步延迟")
    logger.info("  - 节点健康状态")


# ==================== 示例 10: 压力测试 ====================

def example_stress_test():
    """压力测试示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 压力测试")
    logger.info("=" * 60)
    
    import threading
    import random
    
    service = ReadWriteSplitService()
    
    # 配置节点
    master_config = NodeConfig(
        id="master",
        role=NodeRole.MASTER,
        config=VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008"
        )
    )
    
    slave_configs = [
        NodeConfig(
            id=f"slave-{i}",
            role=NodeRole.SLAVE,
            config=VectorStoreConfig(
                backend=VectorStoreBackend.CHROMA,
                connection_string=f"http://localhost:{8009+i}"
            )
        )
        for i in range(2)
    ]
    
    service.add_node(master_config)
    for config in slave_configs:
        service.add_node(config)
    
    service.start()
    
    # 模拟并发请求
    logger.info("\n模拟并发请求...")
    
    read_count = 0
    write_count = 0
    lock = threading.Lock()
    
    def simulate_read():
        nonlocal read_count
        try:
            # 模拟读操作
            time.sleep(random.uniform(0.01, 0.05))
            with lock:
                read_count += 1
        except Exception as e:
            logger.error(f"读操作失败: {e}")
    
    def simulate_write():
        nonlocal write_count
        try:
            # 模拟写操作
            time.sleep(random.uniform(0.02, 0.08))
            with lock:
                write_count += 1
        except Exception as e:
            logger.error(f"写操作失败: {e}")
    
    # 启动多个线程
    threads = []
    
    # 90% 读操作，10% 写操作
    for i in range(100):
        if random.random() < 0.9:
            t = threading.Thread(target=simulate_read)
        else:
            t = threading.Thread(target=simulate_write)
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    logger.info(f"\n压力测试结果:")
    logger.info(f"  读操作: {read_count}")
    logger.info(f"  写操作: {write_count}")
    logger.info(f"  读写比: {read_count/write_count:.1f}:1" if write_count > 0 else "  读写比: N/A")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("读写分离服务使用示例")
    logger.info("=" * 70)
    
    try:
        example_basic_setup()
        example_routing_strategies()
        example_write_operations()
        example_read_operations()
        example_failover()
        example_sync_monitoring()
        example_performance_stats()
        example_health_check()
        example_real_world_scenario()
        # example_stress_test()  # 可选：压力测试
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
