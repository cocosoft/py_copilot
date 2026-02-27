"""MCP (Model Context Protocol) 模块

提供 MCP 服务端和客户端功能，支持工具暴露和外部服务连接。
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from .models import MCPServerConfigModel, MCPClientConfigModel, MCPToolMappingModel, MCPCallLogModel
from .schemas import (
    TransportType,
    AuthType,
    MCPModule,
    MCPServerConfig,
    MCPServerConfigCreate,
    MCPServerConfigUpdate,
    MCPClientConfig,
    MCPClientConfigCreate,
    MCPClientConfigUpdate,
    MCPSettingsData
)
from .client.connection_manager import connection_manager

logger = logging.getLogger(__name__)


async def initialize_mcp_services(db: Optional[Session] = None):
    """初始化 MCP 服务

    在应用启动时调用，初始化 MCP 服务端和客户端。

    Args:
        db: 数据库会话，如果为 None 则自动创建
    """
    try:
        logger.info("开始初始化 MCP 服务...")

        # 如果没有提供数据库会话，创建一个
        if db is None:
            from app.core.database import SessionLocal
            db = SessionLocal()
            close_db = True
        else:
            close_db = False

        try:
            # 初始化连接管理器
            await connection_manager.initialize(db)
            logger.info("MCP 连接管理器初始化完成")

            # 自动连接所有启用的客户端
            connected_count = 0
            for config_id in list(connection_manager.clients.keys()):
                client = connection_manager.clients[config_id]
                if client.config.enabled:
                    success = await connection_manager.connect(config_id)
                    if success:
                        connected_count += 1
                        logger.info(f"自动连接 MCP 客户端成功: {client.config.name}")

            logger.info(f"MCP 服务初始化完成，已连接 {connected_count} 个客户端")

        finally:
            if close_db:
                db.close()

    except Exception as e:
        logger.error(f"初始化 MCP 服务失败: {e}", exc_info=True)
        raise


async def shutdown_mcp_services():
    """关闭 MCP 服务

    在应用关闭时调用，断开所有 MCP 连接。
    """
    try:
        logger.info("正在关闭 MCP 服务...")

        # 断开所有客户端连接
        for config_id in list(connection_manager.clients.keys()):
            await connection_manager.disconnect(config_id)

        logger.info("MCP 服务已关闭")

    except Exception as e:
        logger.error(f"关闭 MCP 服务失败: {e}", exc_info=True)


__all__ = [
    # 模型
    'MCPServerConfigModel',
    'MCPClientConfigModel',
    'MCPToolMappingModel',
    'MCPCallLogModel',
    # Schemas
    'TransportType',
    'AuthType',
    'MCPModule',
    'MCPServerConfig',
    'MCPServerConfigCreate',
    'MCPServerConfigUpdate',
    'MCPClientConfig',
    'MCPClientConfigCreate',
    'MCPClientConfigUpdate',
    'MCPSettingsData',
    # 函数
    'initialize_mcp_services',
    'shutdown_mcp_services',
    'connection_manager'
]
