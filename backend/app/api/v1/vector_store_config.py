"""
向量存储配置管理 API

提供向量存储后端配置的管理接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.knowledge.vectorization import VectorStoreFactory
from app.core.config import settings

router = APIRouter()


class VectorStoreConfig(BaseModel):
    """向量存储配置模型"""
    backend: str
    sqlite_db_path: str
    chromadb_server_url: str
    chromadb_collection: str


class VectorStoreStatus(BaseModel):
    """向量存储状态模型"""
    backend: str
    healthy: bool
    message: str
    details: Dict[str, Any]


@router.get("/config", response_model=VectorStoreConfig)
async def get_vector_store_config():
    """
    获取当前向量存储配置
    
    Returns:
        当前向量存储配置信息
    """
    return VectorStoreConfig(
        backend=settings.vector_store_backend,
        sqlite_db_path=settings.vector_store_db_path,
        chromadb_server_url=settings.chromadb_server_url,
        chromadb_collection=settings.chromadb_collection
    )


@router.post("/config")
async def update_vector_store_config(config: VectorStoreConfig):
    """
    更新向量存储配置
    
    注意：此端点仅更新内存中的配置，重启后会恢复。
    要永久保存配置，请修改 .env 文件。
    
    Args:
        config: 新的配置
        
    Returns:
        更新结果
    """
    try:
        # 验证后端类型
        if config.backend not in ["sqlite", "chromadb"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的向量存储后端: {config.backend}，可选: sqlite, chromadb"
            )
        
        # 更新配置
        settings.vector_store_backend = config.backend
        settings.vector_store_db_path = config.sqlite_db_path
        settings.chromadb_server_url = config.chromadb_server_url
        settings.chromadb_collection = config.chromadb_collection
        
        # 重置工厂实例，使新配置生效
        VectorStoreFactory.reset_instance()
        VectorStoreFactory.set_default_backend(config.backend)
        
        return {
            "success": True,
            "message": "向量存储配置已更新",
            "config": {
                "backend": config.backend,
                "sqlite_db_path": config.sqlite_db_path,
                "chromadb_server_url": config.chromadb_server_url,
                "chromadb_collection": config.chromadb_collection
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/status", response_model=Dict[str, VectorStoreStatus])
async def get_vector_store_status():
    """
    获取向量存储状态
    
    检查所有可用后端的运行状态
    
    Returns:
        各后端的健康状态
    """
    try:
        health_results = VectorStoreFactory.health_check()
        
        formatted_results = {}
        for backend, status in health_results.items():
            formatted_results[backend] = VectorStoreStatus(
                backend=backend,
                healthy=status.get("healthy", False),
                message=status.get("message", ""),
                details=status.get("details", {})
            )
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/switch/{backend}")
async def switch_vector_store_backend(backend: str):
    """
    切换向量存储后端
    
    Args:
        backend: 目标后端，"sqlite" 或 "chromadb"
        
    Returns:
        切换结果
    """
    try:
        if backend not in ["sqlite", "chromadb"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的向量存储后端: {backend}，可选: sqlite, chromadb"
            )
        
        # 更新配置
        settings.vector_store_backend = backend
        
        # 重置工厂实例
        VectorStoreFactory.reset_instance()
        VectorStoreFactory.set_default_backend(backend)
        
        # 测试新后端是否可用
        store = VectorStoreFactory.get_store(backend)
        health = store.health_check()
        
        return {
            "success": True,
            "message": f"已切换到 {backend} 后端",
            "backend": backend,
            "healthy": health.get("healthy", False),
            "health_details": health
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换后端失败: {str(e)}")


@router.post("/health-check")
async def perform_health_check():
    """
    执行健康检查
    
    对所有后端执行健康检查并返回结果
    
    Returns:
        健康检查结果
    """
    try:
        results = VectorStoreFactory.health_check()
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")
