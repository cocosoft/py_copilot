"""
服务注册中心

提供统一的服务注册、发现和管理机制

任务编号: Phase1-Week2
阶段: 第一阶段 - 功能重复问题优化
"""

import logging
from typing import Dict, Any, Type, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import inspect

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态"""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ERROR = "error"


class ServicePriority(Enum):
    """服务优先级"""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    service_type: Type
    instance: Optional[Any] = None
    status: ServiceStatus = ServiceStatus.REGISTERED
    priority: ServicePriority = ServicePriority.PRIMARY
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceCategory:
    """服务类别"""
    name: str
    description: str
    services: List[str] = field(default_factory=list)


class ServiceRegistry:
    """服务注册中心"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._services: Dict[str, ServiceInfo] = {}
        self._categories: Dict[str, ServiceCategory] = {}
        self._aliases: Dict[str, str] = {}
        self._factories: Dict[str, Callable] = {}
        self._initialized = True
        
        self._register_default_categories()
        
        logger.info("服务注册中心初始化完成")
    
    def _register_default_categories(self):
        """注册默认服务类别"""
        default_categories = [
            ServiceCategory("document_processing", "文档处理服务"),
            ServiceCategory("vectorization", "向量化服务"),
            ServiceCategory("entity_recognition", "实体识别服务"),
            ServiceCategory("knowledge_graph", "知识图谱服务"),
            ServiceCategory("semantic_search", "语义搜索服务"),
            ServiceCategory("text_processing", "文本处理服务"),
            ServiceCategory("storage", "存储服务"),
            ServiceCategory("cache", "缓存服务"),
        ]
        
        for category in default_categories:
            self._categories[category.name] = category
    
    def register(self, name: str, service_type: Type,
                instance: Optional[Any] = None,
                priority: ServicePriority = ServicePriority.PRIMARY,
                version: str = "1.0.0",
                description: str = "",
                tags: List[str] = None,
                category: str = None,
                dependencies: List[str] = None,
                metadata: Dict[str, Any] = None,
                factory: Optional[Callable] = None) -> bool:
        """
        注册服务
        
        Args:
            name: 服务名称
            service_type: 服务类型
            instance: 服务实例（可选）
            priority: 服务优先级
            version: 服务版本
            description: 服务描述
            tags: 服务标签
            category: 服务类别
            dependencies: 服务依赖
            metadata: 服务元数据
            factory: 服务工厂函数
            
        Returns:
            注册是否成功
        """
        try:
            service_info = ServiceInfo(
                name=name,
                service_type=service_type,
                instance=instance,
                status=ServiceStatus.REGISTERED,
                priority=priority,
                version=version,
                description=description,
                tags=tags or [],
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            
            self._services[name] = service_info
            
            if factory:
                self._factories[name] = factory
            
            if category:
                if category not in self._categories:
                    self._categories[category] = ServiceCategory(category, f"{category}服务")
                self._categories[category].services.append(name)
            
            logger.info(f"服务注册成功: {name} (v{version})")
            return True
            
        except Exception as e:
            logger.error(f"服务注册失败: {name}, 错误: {e}")
            return False
    
    def unregister(self, name: str) -> bool:
        """
        注销服务
        
        Args:
            name: 服务名称
            
        Returns:
            注销是否成功
        """
        if name in self._services:
            del self._services[name]
            
            for alias, service_name in list(self._aliases.items()):
                if service_name == name:
                    del self._aliases[alias]
            
            for category in self._categories.values():
                if name in category.services:
                    category.services.remove(name)
            
            if name in self._factories:
                del self._factories[name]
            
            logger.info(f"服务注销成功: {name}")
            return True
        
        return False
    
    def get(self, name: str, auto_create: bool = True) -> Optional[Any]:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            auto_create: 是否自动创建实例
            
        Returns:
            服务实例
        """
        service_info = self._services.get(name)
        
        if not service_info:
            name = self._aliases.get(name)
            service_info = self._services.get(name) if name else None
        
        if not service_info:
            logger.warning(f"服务未找到: {name}")
            return None
        
        service_info.last_accessed = datetime.now()
        service_info.access_count += 1
        
        if service_info.instance:
            service_info.status = ServiceStatus.ACTIVE
            return service_info.instance
        
        if auto_create and name in self._factories:
            try:
                service_info.status = ServiceStatus.INITIALIZING
                instance = self._factories[name]()
                service_info.instance = instance
                service_info.status = ServiceStatus.ACTIVE
                return instance
            except Exception as e:
                service_info.status = ServiceStatus.ERROR
                logger.error(f"服务实例创建失败: {name}, 错误: {e}")
                return None
        
        if auto_create:
            try:
                service_info.status = ServiceStatus.INITIALIZING
                instance = service_info.service_type()
                service_info.instance = instance
                service_info.status = ServiceStatus.ACTIVE
                return instance
            except Exception as e:
                service_info.status = ServiceStatus.ERROR
                logger.error(f"服务实例创建失败: {name}, 错误: {e}")
                return None
        
        return None
    
    def get_info(self, name: str) -> Optional[ServiceInfo]:
        """
        获取服务信息
        
        Args:
            name: 服务名称
            
        Returns:
            服务信息
        """
        return self._services.get(name) or self._services.get(self._aliases.get(name, ""))
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """
        获取所有服务
        
        Returns:
            所有服务信息
        """
        return self._services.copy()
    
    def get_services_by_category(self, category: str) -> List[ServiceInfo]:
        """
        按类别获取服务
        
        Args:
            category: 服务类别
            
        Returns:
            服务列表
        """
        category_info = self._categories.get(category)
        if not category_info:
            return []
        
        return [self._services[name] for name in category_info.services if name in self._services]
    
    def get_services_by_tag(self, tag: str) -> List[ServiceInfo]:
        """
        按标签获取服务
        
        Args:
            tag: 服务标签
            
        Returns:
            服务列表
        """
        return [info for info in self._services.values() if tag in info.tags]
    
    def register_alias(self, alias: str, service_name: str) -> bool:
        """
        注册服务别名
        
        Args:
            alias: 别名
            service_name: 服务名称
            
        Returns:
            注册是否成功
        """
        if service_name not in self._services:
            logger.warning(f"服务不存在，无法注册别名: {service_name}")
            return False
        
        self._aliases[alias] = service_name
        logger.info(f"服务别名注册成功: {alias} -> {service_name}")
        return True
    
    def get_categories(self) -> Dict[str, ServiceCategory]:
        """
        获取所有服务类别
        
        Returns:
            服务类别字典
        """
        return self._categories.copy()
    
    def health_check(self, name: str = None) -> Dict[str, Any]:
        """
        服务健康检查
        
        Args:
            name: 服务名称（可选，不提供则检查所有服务）
            
        Returns:
            健康检查结果
        """
        if name:
            service_info = self._services.get(name)
            if not service_info:
                return {"status": "not_found", "name": name}
            
            return {
                "name": name,
                "status": service_info.status.value,
                "version": service_info.version,
                "access_count": service_info.access_count,
                "last_accessed": service_info.last_accessed.isoformat() if service_info.last_accessed else None,
                "has_instance": service_info.instance is not None
            }
        
        results = {}
        for service_name, info in self._services.items():
            results[service_name] = {
                "status": info.status.value,
                "version": info.version,
                "access_count": info.access_count,
                "has_instance": info.instance is not None
            }
        
        return {
            "total_services": len(self._services),
            "active_services": sum(1 for i in self._services.values() if i.status == ServiceStatus.ACTIVE),
            "services": results
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            统计信息
        """
        status_counts = {}
        for status in ServiceStatus:
            status_counts[status.value] = sum(1 for s in self._services.values() if s.status == status)
        
        category_counts = {name: len(cat.services) for name, cat in self._categories.items()}
        
        total_access = sum(s.access_count for s in self._services.values())
        
        return {
            "total_services": len(self._services),
            "total_aliases": len(self._aliases),
            "total_categories": len(self._categories),
            "status_distribution": status_counts,
            "category_distribution": category_counts,
            "total_access_count": total_access
        }


service_registry = ServiceRegistry()


def register_service(name: str, **kwargs):
    """
    服务注册装饰器
    
    Args:
        name: 服务名称
        **kwargs: 其他注册参数
    """
    def decorator(cls):
        service_registry.register(name, cls, **kwargs)
        return cls
    return decorator


def get_service(name: str) -> Optional[Any]:
    """
    获取服务实例的便捷函数
    
    Args:
        name: 服务名称
        
    Returns:
        服务实例
    """
    return service_registry.get(name)


def register_core_services():
    """注册核心服务"""
    
    try:
        from app.services.knowledge.unified_document_processor import UnifiedDocumentProcessor
        service_registry.register(
            "document_processor",
            UnifiedDocumentProcessor,
            description="统一文档处理服务",
            category="document_processing",
            tags=["core", "document", "processing"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.unified_vectorization_service import UnifiedVectorizationService
        service_registry.register(
            "vectorization_service",
            UnifiedVectorizationService,
            description="统一向量化服务",
            category="vectorization",
            tags=["core", "vector", "embedding"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.semantic_search_service import SemanticSearchService
        service_registry.register(
            "semantic_search",
            SemanticSearchService,
            description="语义搜索服务",
            category="semantic_search",
            tags=["core", "search", "semantic"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
        service_registry.register(
            "knowledge_graph",
            KnowledgeGraphService,
            description="知识图谱服务",
            category="knowledge_graph",
            tags=["core", "graph", "knowledge"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
        service_registry.register(
            "text_processor",
            AdvancedTextProcessor,
            description="高级文本处理服务",
            category="text_processing",
            tags=["core", "text", "nlp"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.knowledge_graph_cache import KnowledgeGraphCache
        service_registry.register(
            "knowledge_graph_cache",
            KnowledgeGraphCache,
            description="知识图谱缓存服务",
            category="cache",
            tags=["cache", "graph"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.memory_optimizer import MemoryOptimizer
        service_registry.register(
            "memory_optimizer",
            MemoryOptimizer,
            description="内存优化服务",
            category="storage",
            tags=["memory", "optimization"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.intelligent_rerank_service import IntelligentRerankService
        service_registry.register(
            "rerank_service",
            IntelligentRerankService,
            description="智能重排序服务",
            category="semantic_search",
            tags=["rerank", "search"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.hierarchy_manager import HierarchyManager
        service_registry.register(
            "hierarchy_manager",
            HierarchyManager,
            description="层次化管理服务",
            category="knowledge_graph",
            tags=["hierarchy", "management"]
        )
    except ImportError:
        pass
    
    try:
        from app.services.knowledge.relation_management_service import RelationManagementService
        service_registry.register(
            "relation_management",
            RelationManagementService,
            description="关系管理服务",
            category="knowledge_graph",
            tags=["relation", "management"]
        )
    except ImportError:
        pass
    
    logger.info(f"核心服务注册完成，共注册 {len(service_registry.get_all_services())} 个服务")
