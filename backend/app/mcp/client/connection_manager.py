"""MCP 连接管理器

管理所有 MCP 客户端连接。
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.mcp.client.client import MCPClient
from app.mcp.services.config_service import MCPConfigService
from app.mcp.schemas import MCPClientConfig, ConnectionStatus

logger = logging.getLogger(__name__)


class MCPConnectionManager:
    """MCP 连接管理器
    
    管理所有 MCP 客户端连接的生命周期。
    
    Attributes:
        clients: 客户端字典
        db: 数据库会话
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化连接管理器"""
        if self._initialized:
            return
        
        self.clients: Dict[int, MCPClient] = {}
        self._db: Optional[Session] = None
        self._initialized = True
        
    async def initialize(self, db: Session) -> None:
        """初始化连接管理器
        
        Args:
            db: 数据库会话
        """
        self._db = db
        
        # 加载所有启用的客户端配置
        service = MCPConfigService(db)
        
        # 获取所有配置（这里简化处理，实际应该按用户ID获取）
        # 由于需要用户ID，这里只初始化框架
        logger.info("MCP 连接管理器已初始化")
    
    async def load_user_clients(self, user_id: int) -> None:
        """加载用户的所有客户端配置
        
        Args:
            user_id: 用户ID
        """
        if not self._db:
            logger.error("连接管理器未初始化")
            return
        
        try:
            service = MCPConfigService(self._db)
            configs = service.get_client_configs(user_id)
            
            for config in configs:
                # 如果客户端已存在，跳过
                if config.id in self.clients:
                    continue
                
                # 创建客户端实例
                client = MCPClient(config)
                self.clients[config.id] = client
                
                # 如果启用自动连接，尝试连接
                if config.enabled and config.auto_connect:
                    asyncio.create_task(self._connect_client(config.id, client, service))
            
            logger.info(f"已加载用户 {user_id} 的 {len(configs)} 个 MCP 客户端配置")
            
        except Exception as e:
            logger.error(f"加载用户客户端失败: {e}", exc_info=True)
    
    async def _connect_client(
        self,
        config_id: int,
        client: MCPClient,
        service: MCPConfigService
    ) -> None:
        """连接客户端（内部方法）
        
        Args:
            config_id: 配置ID
            client: 客户端实例
            service: 配置服务
        """
        try:
            # 更新状态为连接中
            service.update_client_status(config_id, ConnectionStatus.CONNECTING)
            
            # 执行连接
            success = await client.connect()
            
            if success:
                service.update_client_status(config_id, ConnectionStatus.CONNECTED)
                logger.info(f"客户端 {config_id} 已连接")
            else:
                service.update_client_status(
                    config_id,
                    ConnectionStatus.ERROR,
                    client.error_message
                )
                logger.error(f"客户端 {config_id} 连接失败: {client.error_message}")
                
        except Exception as e:
            logger.error(f"连接客户端 {config_id} 失败: {e}", exc_info=True)
            service.update_client_status(config_id, ConnectionStatus.ERROR, str(e))
    
    async def connect(self, config_id: int) -> bool:
        """连接指定客户端
        
        Args:
            config_id: 客户端配置ID
            
        Returns:
            是否连接成功
        """
        if not self._db:
            logger.error("连接管理器未初始化")
            return False
        
        try:
            # 获取配置
            service = MCPConfigService(self._db)
            
            # 查找配置所属用户（简化处理）
            # 实际应该通过配置ID查找
            
            # 检查客户端是否已存在
            client = self.clients.get(config_id)
            if not client:
                logger.error(f"客户端 {config_id} 不存在")
                return False
            
            # 执行连接
            await self._connect_client(config_id, client, service)
            
            return client.is_connected
            
        except Exception as e:
            logger.error(f"连接客户端失败: {e}", exc_info=True)
            return False
    
    async def disconnect(self, config_id: int) -> bool:
        """断开指定客户端
        
        Args:
            config_id: 客户端配置ID
            
        Returns:
            是否断开成功
        """
        client = self.clients.get(config_id)
        if not client:
            logger.warning(f"客户端 {config_id} 不存在")
            return True
        
        try:
            success = await client.disconnect()
            
            if self._db:
                service = MCPConfigService(self._db)
                service.update_client_status(
                    config_id,
                    ConnectionStatus.DISCONNECTED
                )
            
            return success
            
        except Exception as e:
            logger.error(f"断开客户端失败: {e}", exc_info=True)
            return False
    
    async def disconnect_all(self) -> None:
        """断开所有客户端"""
        tasks = []
        
        for config_id, client in self.clients.items():
            if client.is_connected:
                tasks.append(self.disconnect(config_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("所有 MCP 客户端已断开")
    
    def get_client(self, config_id: int) -> Optional[MCPClient]:
        """获取客户端实例
        
        Args:
            config_id: 客户端配置ID
            
        Returns:
            客户端实例
        """
        return self.clients.get(config_id)
    
    def get_all_clients(self) -> Dict[int, MCPClient]:
        """获取所有客户端
        
        Returns:
            客户端字典
        """
        return self.clients.copy()
    
    def get_connected_clients(self) -> Dict[int, MCPClient]:
        """获取已连接的客户端
        
        Returns:
            已连接的客户端字典
        """
        return {
            k: v for k, v in self.clients.items()
            if v.is_connected
        }
    
    async def call_tool(
        self,
        config_id: int,
        tool_name: str,
        arguments: Dict
    ) -> Optional[Dict]:
        """调用指定客户端的工具
        
        Args:
            config_id: 客户端配置ID
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具调用结果
        """
        client = self.clients.get(config_id)
        if not client:
            logger.error(f"客户端 {config_id} 不存在")
            return None
        
        if not client.is_connected:
            logger.error(f"客户端 {config_id} 未连接")
            return None
        
        try:
            return await client.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"调用工具失败: {e}", exc_info=True)
            return None
    
    async def refresh_client(self, config_id: int, config: MCPClientConfig) -> None:
        """刷新客户端配置
        
        Args:
            config_id: 客户端配置ID
            config: 新配置
        """
        # 断开现有连接
        await self.disconnect(config_id)
        
        # 移除旧客户端
        if config_id in self.clients:
            del self.clients[config_id]
        
        # 创建新客户端
        client = MCPClient(config)
        self.clients[config_id] = client
        
        # 如果启用自动连接，尝试连接
        if config.enabled and config.auto_connect and self._db:
            service = MCPConfigService(self._db)
            asyncio.create_task(self._connect_client(config_id, client, service))
    
    def remove_client(self, config_id: int) -> None:
        """移除客户端
        
        Args:
            config_id: 客户端配置ID
        """
        if config_id in self.clients:
            client = self.clients[config_id]
            if client.is_connected:
                asyncio.create_task(client.disconnect())
            del self.clients[config_id]
            logger.info(f"客户端 {config_id} 已移除")
    
    def get_status(self) -> Dict:
        """获取连接管理器状态
        
        Returns:
            状态信息字典
        """
        total = len(self.clients)
        connected = sum(1 for c in self.clients.values() if c.is_connected)
        
        return {
            "total_clients": total,
            "connected_clients": connected,
            "clients": {
                cid: client.get_status()
                for cid, client in self.clients.items()
            }
        }


# 全局连接管理器实例
connection_manager = MCPConnectionManager()
