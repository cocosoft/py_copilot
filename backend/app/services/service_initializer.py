"""
服务初始化模块

用于初始化和注册所有服务实例
"""

import sys
import os

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

import logging
from typing import Dict, Any

from app.services.service_registry import service_registry

# 导入服务实例
from app.services.knowledge.unified_document_processor import unified_document_processor
from app.services.knowledge.unified_vectorization_service import unified_vectorization_service
from app.services.knowledge.unified_entity_service import unified_entity_service

logger = logging.getLogger(__name__)


def initialize_services():
    """
    初始化并注册所有服务
    """
    try:
        logger.info("[ServiceInitializer] 开始初始化服务...")
        
        # 注册文档处理服务
        service_registry.register(
            "document_processor",
            unified_document_processor,
            {
                "description": "统一文档处理器",
                "version": "1.0.0",
                "capabilities": ["text_extraction", "document_parsing", "chunking"]
            }
        )
        
        # 注册向量化服务
        service_registry.register(
            "vectorization_service",
            unified_vectorization_service,
            {
                "description": "统一向量化服务",
                "version": "1.0.0",
                "capabilities": ["text_embedding", "vector_storage", "semantic_search"]
            }
        )
        
        # 注册实体识别服务
        service_registry.register(
            "entity_service",
            unified_entity_service,
            {
                "description": "统一实体识别服务",
                "version": "1.0.0",
                "capabilities": ["entity_recognition", "entity_extraction", "entity_disambiguation"]
            }
        )
        
        # 注册更多服务...
        # 这里可以添加其他服务的注册
        
        service_count = service_registry.get_service_count()
        logger.info(f"[ServiceInitializer] 服务初始化完成，共注册 {service_count} 个服务")
        
        # 打印注册的服务列表
        registered_services = service_registry.list_services()
        logger.info(f"[ServiceInitializer] 注册的服务: {registered_services}")
        
    except Exception as e:
        logger.error(f"[ServiceInitializer] 服务初始化失败: {e}")
        raise


def get_service(service_name: str) -> Any:
    """
    获取服务实例

    Args:
        service_name: 服务名称

    Returns:
        服务实例
    """
    return service_registry.get(service_name)


def get_all_services() -> Dict[str, Any]:
    """
    获取所有服务实例

    Returns:
        所有服务实例的字典
    """
    return service_registry.get_all()


def get_service_metadata(service_name: str) -> Dict[str, Any]:
    """
    获取服务元数据

    Args:
        service_name: 服务名称

    Returns:
        服务元数据
    """
    return service_registry.get_metadata(service_name)


def list_services() -> list:
    """
    列出所有注册的服务

    Returns:
        服务名称列表
    """
    return service_registry.list_services()


if __name__ == "__main__":
    # 测试服务初始化
    initialize_services()
    print("服务初始化完成！")
    print(f"注册的服务: {list_services()}")
