"""微服务入口点基础配置"""
import os
import sys
import importlib
from typing import Dict, Any, Optional
from fastapi import FastAPI
from app.core.logging_config import logger


class MicroserviceApp:
    """微服务应用程序类"""
    
    def __init__(self, service_name: str, app: FastAPI, 
                 router_modules: Optional[Dict[str, str]] = None):
        """
        初始化微服务应用程序
        
        Args:
            service_name: 微服务名称
            app: FastAPI应用实例
            router_modules: 路由模块映射 {"prefix": "module.path"}
        """
        self.service_name = service_name
        self.app = app
        self.router_modules = router_modules or {}
        
        # 配置微服务应用
        self._configure_app()
        
        # 加载路由模块
        self._load_routers()
        
        # 注册服务
        self._register_service()
    
    def _configure_app(self):
        """配置微服务应用程序"""
        # 设置应用元数据
        self.app.title = f"{self.service_name} API"
        self.app.version = "1.0.0"
        
        # 添加健康检查端点
        @self.app.get("/health")
        def health_check():
            return {
                "status": "healthy",
                "service_name": self.service_name,
                "version": "1.0.0"
            }
        
        logger.info(f"配置微服务应用: {self.service_name}")
    
    def _load_routers(self):
        """加载路由模块"""
        for prefix, module_path in self.router_modules.items():
            try:
                # 动态导入路由模块
                router_module = importlib.import_module(module_path)
                
                # 检查模块是否有router属性
                if hasattr(router_module, "router"):
                    # 注册路由
                    self.app.include_router(router_module.router, prefix=prefix)
                    logger.info(f"加载路由模块: {module_path}, 前缀: {prefix}")
                else:
                    logger.warning(f"路由模块 {module_path} 没有router属性")
                    
            except ImportError as e:
                logger.error(f"导入路由模块失败: {module_path}, 错误: {str(e)}")
            except Exception as e:
                logger.error(f"加载路由模块失败: {module_path}, 错误: {str(e)}")
    
    def _register_service(self):
        """注册服务到服务注册中心"""
        try:
            from app.core.microservices import get_service_registry, MicroserviceConfig
            from app.core.microservices_config import microservices_settings
            
            # 获取服务注册中心
            service_registry = get_service_registry()
            
            # 获取服务配置
            config_class = getattr(microservices_settings, f"{self.service_name.upper()}_SETTINGS", None)
            if config_class:
                # 创建服务配置
                config = MicroserviceConfig(
                    name=self.service_name,
                    host=getattr(config_class, "HOST", "localhost"),
                    port=getattr(config_class, "PORT", 8000),
                    api_prefix="/api/v1"
                )
                
                # 注册服务（异步操作）
                import asyncio
                asyncio.create_task(service_registry.register_service(config))
                
                logger.info(f"注册服务到注册中心: {self.service_name}")
            else:
                logger.warning(f"未找到服务配置: {self.service_name}")
                
        except Exception as e:
            logger.error(f"注册服务失败: {self.service_name}, 错误: {str(e)}")


# 微服务列表和路由映射
MICROSERVICES = {
    "auth": {
        "routers": {
            "/auth": "app.modules.auth.api.auth",
        },
        "description": "认证与授权服务"
    },
    "chat": {
        "routers": {
            "/chat": "app.modules.conversation.api.conversations",
            "/conversations": "app.modules.conversation.api.conversations",
        },
        "description": "聊天服务"
    },
    "knowledge": {
        "routers": {
            "/knowledge": "app.modules.knowledge.api.knowledge",
            "/knowledge-graph": "app.modules.knowledge.api.knowledge_graph_api",
            "/entity-config": "app.modules.knowledge.api.entity_config_api",
        },
        "description": "知识服务"
    },
    "workflow": {
        "routers": {
            "/workflows": "app.modules.workflow.api.workflow",
        },
        "description": "工作流服务"
    },
    "capability": {
        "routers": {
            "/capabilities": "app.api.v1.capability",
            "/capability-types": "app.api.v1.capability_types",
            "/capability-dimensions": "app.api.v1.capability_dimensions",
        },
        "description": "能力管理服务"
    },
    "parameter": {
        "routers": {
            "/parameter-templates": "app.api.v1.parameter_template",
            "/parameter-normalization-rules": "app.api.v1.parameter_normalization_rules",
            "/parameter-mappings": "app.api.v1.parameter_mappings",
            "/system-parameters": "app.api.v1.system_parameters",
        },
        "description": "参数管理服务"
    },
    "monitoring": {
        "routers": {
            "/monitoring": "app.services.monitoring.monitoring_service",
        },
        "description": "监控服务"
    },
}


def create_microservice_app(service_name: str) -> Optional[MicroserviceApp]:
    """
    创建微服务应用程序
    
    Args:
        service_name: 微服务名称
        
    Returns:
        MicroserviceApp实例
    """
    if service_name not in MICROSERVICES:
        logger.error(f"未知的微服务名称: {service_name}")
        return None
    
    try:
        # 创建FastAPI应用实例
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI()
        
        # 配置CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 获取路由映射
        service_config = MICROSERVICES[service_name]
        router_modules = service_config["routers"]
        
        # 创建微服务应用实例
        microservice_app = MicroserviceApp(service_name, app, router_modules)
        
        logger.info(f"创建微服务应用成功: {service_name}")
        return microservice_app
        
    except Exception as e:
        logger.error(f"创建微服务应用失败: {service_name}, 错误: {str(e)}")
        return None
