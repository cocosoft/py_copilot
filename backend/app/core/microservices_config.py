"""微服务配置文件"""
import os
from typing import Dict, Any
from pydantic import BaseSettings


class MicroservicesSettings(BaseSettings):
    """微服务配置设置"""
    
    # 网关配置
    GATEWAY_HOST: str = "localhost"
    GATEWAY_PORT: int = 8000
    
    # 聊天服务配置
    CHAT_SERVICE_HOST: str = "localhost"
    CHAT_SERVICE_PORT: int = 8001
    CHAT_SERVICE_WORKERS: int = 2
    
    # 搜索服务配置
    SEARCH_SERVICE_HOST: str = "localhost"
    SEARCH_SERVICE_PORT: int = 8002
    SEARCH_SERVICE_WORKERS: int = 1
    
    # 文件服务配置
    FILE_SERVICE_HOST: str = "localhost"
    FILE_SERVICE_PORT: int = 8003
    FILE_SERVICE_WORKERS: int = 1
    FILE_UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 语音服务配置
    VOICE_SERVICE_HOST: str = "localhost"
    VOICE_SERVICE_PORT: int = 8004
    VOICE_SERVICE_WORKERS: int = 1
    
    # 监控服务配置
    MONITORING_SERVICE_HOST: str = "localhost"
    MONITORING_SERVICE_PORT: int = 8005
    MONITORING_SERVICE_WORKERS: int = 1
    
    # 记忆增强聊天服务配置
    ENHANCED_CHAT_SERVICE_HOST: str = "localhost"
    ENHANCED_CHAT_SERVICE_PORT: int = 8006
    ENHANCED_CHAT_SERVICE_WORKERS: int = 2
    
    # Redis配置（用于服务注册和消息队列）
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # 断路器配置
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 30
    
    # 服务发现配置
    SERVICE_REGISTRY_TTL: int = 30  # 服务注册TTL（秒）
    HEALTH_CHECK_INTERVAL: int = 10  # 健康检查间隔（秒）
    
    # 消息队列配置
    MESSAGE_QUEUE_CHANNELS: Dict[str, Any] = {
        "chat_messages": {
            "max_length": 1000,
            "consumer_group": "chat_consumers"
        },
        "file_events": {
            "max_length": 500,
            "consumer_group": "file_consumers"
        },
        "voice_events": {
            "max_length": 500,
            "consumer_group": "voice_consumers"
        },
        "search_events": {
            "max_length": 500,
            "consumer_group": "search_consumers"
        }
    }
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
microservices_settings = MicroservicesSettings()


# 服务配置字典
SERVICE_CONFIGS = {
    "gateway": {
        "name": "api-gateway",
        "host": microservices_settings.GATEWAY_HOST,
        "port": microservices_settings.GATEWAY_PORT,
        "description": "API网关服务"
    },
    "chat": {
        "name": "chat-service",
        "host": microservices_settings.CHAT_SERVICE_HOST,
        "port": microservices_settings.CHAT_SERVICE_PORT,
        "description": "聊天功能服务"
    },
    "search": {
        "name": "search-service",
        "host": microservices_settings.SEARCH_SERVICE_HOST,
        "port": microservices_settings.SEARCH_SERVICE_PORT,
        "description": "搜索功能服务"
    },
    "file": {
        "name": "file-service",
        "host": microservices_settings.FILE_SERVICE_HOST,
        "port": microservices_settings.FILE_SERVICE_PORT,
        "description": "文件处理服务"
    },
    "voice": {
        "name": "voice-service",
        "host": microservices_settings.VOICE_SERVICE_HOST,
        "port": microservices_settings.VOICE_SERVICE_PORT,
        "description": "语音处理服务"
    },
    "monitoring": {
        "name": "monitoring-service",
        "host": microservices_settings.MONITORING_SERVICE_HOST,
        "port": microservices_settings.MONITORING_SERVICE_PORT,
        "description": "监控服务"
    },
    "enhanced_chat": {
        "name": "enhanced-chat-service",
        "host": microservices_settings.ENHANCED_CHAT_SERVICE_HOST,
        "port": microservices_settings.ENHANCED_CHAT_SERVICE_PORT,
        "description": "记忆增强流式响应聊天服务"
    }
}


def get_service_config(service_name: str) -> Dict[str, Any]:
    """获取服务配置"""
    return SERVICE_CONFIGS.get(service_name, {})


def get_all_service_configs() -> Dict[str, Dict[str, Any]]:
    """获取所有服务配置"""
    return SERVICE_CONFIGS