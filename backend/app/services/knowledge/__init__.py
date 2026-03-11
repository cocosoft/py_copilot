"""知识库服务

向量化管理模块优化 - Phase 1, Phase 2, Phase 3, Phase 4

任务编号: BE-001, BE-002, BE-003, BE-004, BE-005, BE-006, BE-007, BE-008, BE-009, BE-010, BE-011, BE-012, BE-013
任务名称: 自适应批次处理实现, 查询缓存机制开发, 指标收集系统搭建, 事务性向量操作, 向量版本管理, 向量存储抽象层, 读写分离实现, 多级索引策略, 统一数据模型, 统一处理流水线, 一体化检索服务, 数据迁移, 监控告警系统
"""

# 导出自适应批次处理器
from app.services.knowledge.adaptive_batch_processor import (
    AdaptiveBatchProcessor,
    BatchConfig,
    BatchSizeStrategy,
    BatchResult,
    ProcessingStats,
    process_with_adaptive_batching,
    process_stream_with_adaptive_batching
)

# 导出增强版文档处理器
from app.services.knowledge.adaptive_document_processor import (
    AdaptiveDocumentProcessor,
    process_document_with_adaptive_batching
)

# 导出查询缓存管理器
from app.services.knowledge.query_cache_manager import (
    QueryCacheManager,
    CacheEvictionStrategy,
    CacheStats,
    CacheEntry,
    cached_query,
    query_cache_manager,
    get_cached_query,
    set_cached_query,
    execute_cached_query
)

# 导出带缓存的检索服务
from app.services.knowledge.cached_retrieval_service import (
    CachedRetrievalService,
    CachedAdvancedRetrievalService,
    CacheWarmer,
    cached_search,
    cached_advanced_search,
    get_cache_performance_report
)

# 导出事务性向量操作管理器
from app.services.knowledge.transactional_vector_manager import (
    TransactionalVectorManager,
    TransactionContext,
    VectorOperation,
    VectorOperationType,
    TransactionStatus,
    TransactionRecord,
    add_document_with_transaction,
    batch_add_documents_with_transaction,
    transactional_vector_manager
)

# 导出统一事务服务
from app.services.knowledge.unified_transaction_service import (
    UnifiedTransactionService,
    UnifiedTransactionContext,
    DocumentVectorData,
    add_document_transactional,
    update_document_transactional,
    delete_document_transactional,
    unified_transaction_service
)

# 导出统一知识服务
from app.services.knowledge.unified_knowledge_service import (
    UnifiedKnowledgeService,
    create_knowledge_unit,
    get_knowledge_unit,
    search_knowledge_units,
    unified_knowledge_service
)

# 导出统一处理流水线
from app.services.knowledge.unified_processing_pipeline import (
    UnifiedProcessingPipeline,
    PipelineStage,
    PipelineStatus,
    PipelineContext,
    StageResult,
    PipelineStageHandler,
    process_document_with_pipeline,
    unified_processing_pipeline
)

# 导出一体化检索服务
from app.services.knowledge.unified_retrieval_service import (
    UnifiedRetrievalService,
    UnifiedSearchRequest,
    UnifiedSearchResponse,
    RetrievalType,
    FusionAlgorithm,
    SearchResult,
    VectorRetrievalEngine,
    EntityRetrievalEngine,
    GraphRetrievalEngine,
    ResultFusionEngine,
    unified_search,
    unified_retrieval_service
)

# 导出数据迁移服务
from app.services.knowledge.data_migration_service import (
    DataMigrationService,
    MigrationPhase,
    MigrationStatus,
    MigrationStats,
    ValidationResult,
    MigrationStrategy,
    migrate_data,
    rollback_migration,
    get_migration_progress,
    data_migration_service
)

# 导出监控告警服务
from app.services.knowledge.alerting_monitoring_service import (
    AlertingMonitoringService,
    AlertRule,
    Alert,
    AlertLevel,
    AlertStatus,
    AlertChannel,
    MetricType,
    MetricValue,
    SystemMetrics,
    MetricsCollector,
    create_default_alert_rules,
    alerting_monitoring_service
)

# 导出指标收集服务
from app.services.knowledge.metrics_collection_service import (
    MetricsCollectionService,
    MetricsCollector,
    InMemoryMetricsStorage,
    MetricCategory,
    AggregationType,
    MetricDefinition,
    MetricReport,
    TimeSeries,
    metrics_collection_service
)

# 导出向量版本管理
from app.services.knowledge.vector_version_manager import (
    VectorVersionManager,
    VectorVersion,
    VectorChange,
    VersionComparison,
    VersionStatus,
    ChangeType,
    VectorSnapshot,
    VectorVersionStore,
    create_version_manager,
    vector_version_manager
)

# 导出向量存储抽象层
from app.services.knowledge.vector_store_adapter import (
    VectorStoreAdapter,
    VectorStoreConfig,
    VectorStoreBackend,
    VectorStoreStatus,
    BaseVectorStore,
    ChromaVectorStore,
    VectorStoreFactory,
    VectorDocument,
    SearchResult,
    CollectionInfo,
    create_vector_store_adapter,
    vector_store_adapter
)

# 导出读写分离服务
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

# 导出多级索引服务
from app.services.knowledge.multi_level_index_service import (
    MultiLevelIndexService,
    IndexSelector,
    IndexWarmer,
    IndexType,
    IndexStatus,
    DataDistribution,
    IndexLevel,
    IndexConfig,
    IndexStats,
    FlatIndex,
    HNSWIndex,
    create_multi_level_index,
    multi_level_index_service
)

__all__ = [
    # 自适应批次处理器
    "AdaptiveBatchProcessor",
    "BatchConfig",
    "BatchSizeStrategy",
    "BatchResult",
    "ProcessingStats",
    "process_with_adaptive_batching",
    "process_stream_with_adaptive_batching",
    # 增强版文档处理器
    "AdaptiveDocumentProcessor",
    "process_document_with_adaptive_batching",
    # 查询缓存管理器
    "QueryCacheManager",
    "CacheEvictionStrategy",
    "CacheStats",
    "CacheEntry",
    "CacheWarmer",
    "cached_query",
    "query_cache_manager",
    "get_cached_query",
    "set_cached_query",
    "execute_cached_query",
    # 带缓存的检索服务
    "CachedRetrievalService",
    "CachedAdvancedRetrievalService",
    "cached_search",
    "cached_advanced_search",
    "get_cache_performance_report",
    # 事务性向量操作管理器
    "TransactionalVectorManager",
    "TransactionContext",
    "VectorOperation",
    "VectorOperationType",
    "TransactionStatus",
    "TransactionRecord",
    "add_document_with_transaction",
    "batch_add_documents_with_transaction",
    "transactional_vector_manager",
    # 统一事务服务
    "UnifiedTransactionService",
    "UnifiedTransactionContext",
    "DocumentVectorData",
    "add_document_transactional",
    "update_document_transactional",
    "delete_document_transactional",
    "unified_transaction_service",
    # 统一知识服务
    "UnifiedKnowledgeService",
    "create_knowledge_unit",
    "get_knowledge_unit",
    "search_knowledge_units",
    "unified_knowledge_service",
    # 统一处理流水线
    "UnifiedProcessingPipeline",
    "PipelineStage",
    "PipelineStatus",
    "PipelineContext",
    "StageResult",
    "PipelineStageHandler",
    "process_document_with_pipeline",
    "unified_processing_pipeline",
    # 一体化检索服务
    "UnifiedRetrievalService",
    "UnifiedSearchRequest",
    "UnifiedSearchResponse",
    "RetrievalType",
    "FusionAlgorithm",
    "SearchResult",
    "VectorRetrievalEngine",
    "EntityRetrievalEngine",
    "GraphRetrievalEngine",
    "ResultFusionEngine",
    "unified_search",
    "unified_retrieval_service",
    # 数据迁移服务
    "DataMigrationService",
    "MigrationPhase",
    "MigrationStatus",
    "MigrationStats",
    "ValidationResult",
    "MigrationStrategy",
    "migrate_data",
    "rollback_migration",
    "get_migration_progress",
    "data_migration_service",
    # 监控告警服务
    "AlertingMonitoringService",
    "AlertRule",
    "Alert",
    "AlertLevel",
    "AlertStatus",
    "AlertChannel",
    "MetricType",
    "MetricValue",
    "SystemMetrics",
    "MetricsCollector",
    "create_default_alert_rules",
    "alerting_monitoring_service",
    # 指标收集服务
    "MetricsCollectionService",
    "MetricsCollector",
    "InMemoryMetricsStorage",
    "MetricCategory",
    "AggregationType",
    "MetricDefinition",
    "MetricReport",
    "TimeSeries",
    "metrics_collection_service",
    # 向量版本管理
    "VectorVersionManager",
    "VectorVersion",
    "VectorChange",
    "VersionComparison",
    "VersionStatus",
    "ChangeType",
    "VectorSnapshot",
    "VectorVersionStore",
    "create_version_manager",
    "vector_version_manager",
    # 向量存储抽象层
    "VectorStoreAdapter",
    "VectorStoreConfig",
    "VectorStoreBackend",
    "VectorStoreStatus",
    "BaseVectorStore",
    "ChromaVectorStore",
    "VectorStoreFactory",
    "VectorDocument",
    "SearchResult",
    "CollectionInfo",
    "create_vector_store_adapter",
    "vector_store_adapter",
    # 读写分离服务
    "ReadWriteSplitService",
    "ReadWriteRouter",
    "DataSynchronizer",
    "VectorStoreNode",
    "NodeConfig",
    "NodeRole",
    "NodeStatus",
    "RoutingStrategy",
    "NodeStats",
    "create_read_write_split_service",
    "read_write_split_service",
    # 多级索引服务
    "MultiLevelIndexService",
    "IndexSelector",
    "IndexWarmer",
    "IndexType",
    "IndexStatus",
    "DataDistribution",
    "IndexLevel",
    "IndexConfig",
    "IndexStats",
    "FlatIndex",
    "HNSWIndex",
    "create_multi_level_index",
    "multi_level_index_service",
]