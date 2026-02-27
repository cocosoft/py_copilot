"""MCP 配置服务

提供 MCP 配置的 CRUD 操作和状态管理。
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.mcp.models import MCPServerConfigModel, MCPClientConfigModel, MCPToolMappingModel
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerConfigCreate,
    MCPServerConfigUpdate,
    MCPClientConfig,
    MCPClientConfigCreate,
    MCPClientConfigUpdate,
    ConnectionStatus
)

logger = logging.getLogger(__name__)


class MCPConfigService:
    """MCP 配置服务类
    
    提供 MCP 服务端和客户端配置的完整管理功能。
    
    Attributes:
        db: 数据库会话
    """
    
    def __init__(self, db: Session):
        """初始化配置服务
        
        Args:
            db: SQLAlchemy 数据库会话
        """
        self.db = db
    
    # ==================== Server Config Methods ====================
    
    def get_server_configs(self, user_id: int) -> List[MCPServerConfig]:
        """获取用户的所有 MCP 服务端配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            MCP 服务端配置列表
        """
        configs = self.db.query(MCPServerConfigModel).filter(
            MCPServerConfigModel.user_id == user_id
        ).order_by(desc(MCPServerConfigModel.created_at)).all()
        
        return [MCPServerConfig.model_validate(config) for config in configs]
    
    def get_server_config(self, user_id: int, config_id: int) -> Optional[MCPServerConfig]:
        """获取单个 MCP 服务端配置
        
        Args:
            user_id: 用户ID
            config_id: 配置ID
            
        Returns:
            MCP 服务端配置，如果不存在返回 None
        """
        config = self.db.query(MCPServerConfigModel).filter(
            MCPServerConfigModel.user_id == user_id,
            MCPServerConfigModel.id == config_id
        ).first()
        
        return MCPServerConfig.model_validate(config) if config else None
    
    def create_server_config(self, user_id: int, config_data: MCPServerConfigCreate) -> MCPServerConfig:
        """创建 MCP 服务端配置
        
        Args:
            user_id: 用户ID
            config_data: 配置数据
            
        Returns:
            创建的配置
        """
        db_config = MCPServerConfigModel(
            user_id=user_id,
            name=config_data.name,
            description=config_data.description,
            transport=config_data.transport.value,
            host=config_data.host,
            port=config_data.port,
            enabled=config_data.enabled,
            auth_type=config_data.auth_type.value,
            auth_config=config_data.auth_config,
            exposed_modules=[module.value for module in config_data.exposed_modules]
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        logger.info(f"创建 MCP 服务端配置: user_id={user_id}, name={config_data.name}")
        
        return MCPServerConfig.model_validate(db_config)
    
    def update_server_config(
        self,
        user_id: int,
        config_id: int,
        config_data: MCPServerConfigUpdate
    ) -> Optional[MCPServerConfig]:
        """更新 MCP 服务端配置
        
        Args:
            user_id: 用户ID
            config_id: 配置ID
            config_data: 更新数据
            
        Returns:
            更新后的配置，如果不存在返回 None
        """
        config = self.db.query(MCPServerConfigModel).filter(
            MCPServerConfigModel.user_id == user_id,
            MCPServerConfigModel.id == config_id
        ).first()
        
        if not config:
            return None
        
        # 更新字段
        update_data = config_data.model_dump(exclude_unset=True)
        
        if 'transport' in update_data and update_data['transport']:
            update_data['transport'] = update_data['transport'].value
        
        if 'auth_type' in update_data and update_data['auth_type']:
            update_data['auth_type'] = update_data['auth_type'].value
        
        if 'exposed_modules' in update_data and update_data['exposed_modules']:
            update_data['exposed_modules'] = [
                module.value if hasattr(module, 'value') else module
                for module in update_data['exposed_modules']
            ]
        
        for key, value in update_data.items():
            setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        
        logger.info(f"更新 MCP 服务端配置: user_id={user_id}, config_id={config_id}")
        
        return MCPServerConfig.model_validate(config)
    
    def delete_server_config(self, user_id: int, config_id: int) -> bool:
        """删除 MCP 服务端配置
        
        Args:
            user_id: 用户ID
            config_id: 配置ID
            
        Returns:
            是否删除成功
        """
        config = self.db.query(MCPServerConfigModel).filter(
            MCPServerConfigModel.user_id == user_id,
            MCPServerConfigModel.id == config_id
        ).first()
        
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        
        logger.info(f"删除 MCP 服务端配置: user_id={user_id}, config_id={config_id}")
        
        return True
    
    # ==================== Client Config Methods ====================
    
    def get_client_configs(self, user_id: int) -> List[MCPClientConfig]:
        """获取用户的所有 MCP 客户端配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            MCP 客户端配置列表
        """
        configs = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.user_id == user_id
        ).order_by(desc(MCPClientConfigModel.created_at)).all()
        
        return [MCPClientConfig.model_validate(config) for config in configs]
    
    def get_client_config(self, user_id: int, config_id: int) -> Optional[MCPClientConfig]:
        """获取单个 MCP 客户端配置
        
        Args:
            user_id: 用户ID
            config_id: 配置ID
            
        Returns:
            MCP 客户端配置，如果不存在返回 None
        """
        config = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.user_id == user_id,
            MCPClientConfigModel.id == config_id
        ).first()
        
        return MCPClientConfig.model_validate(config) if config else None
    
    def create_client_config(self, user_id: int, config_data: MCPClientConfigCreate) -> MCPClientConfig:
        """创建 MCP 客户端配置
        
        Args:
            user_id: 用户ID
            config_data: 配置数据
            
        Returns:
            创建的配置
        """
        db_config = MCPClientConfigModel(
            user_id=user_id,
            name=config_data.name,
            description=config_data.description,
            transport=config_data.transport.value,
            connection_url=config_data.connection_url,
            command=config_data.command,
            enabled=config_data.enabled,
            auto_connect=config_data.auto_connect,
            auth_config=config_data.auth_config,
            tool_whitelist=config_data.tool_whitelist,
            tool_blacklist=config_data.tool_blacklist,
            status=ConnectionStatus.DISCONNECTED.value
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        logger.info(f"创建 MCP 客户端配置: user_id={user_id}, name={config_data.name}")
        
        return MCPClientConfig.model_validate(db_config)
    
    def update_client_config(
        self,
        user_id: int,
        config_id: int,
        config_data: MCPClientConfigUpdate
    ) -> Optional[MCPClientConfig]:
        """更新 MCP 客户端配置
        
        Args:
            user_id: 用户ID
            config_id: 配置ID
            config_data: 更新数据
            
        Returns:
            更新后的配置，如果不存在返回 None
        """
        config = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.user_id == user_id,
            MCPClientConfigModel.id == config_id
        ).first()
        
        if not config:
            return None
        
        # 更新字段
        update_data = config_data.model_dump(exclude_unset=True)
        
        if 'transport' in update_data and update_data['transport']:
            update_data['transport'] = update_data['transport'].value
        
        for key, value in update_data.items():
            setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        
        logger.info(f"更新 MCP 客户端配置: user_id={user_id}, config_id={config_id}")
        
        return MCPClientConfig.model_validate(config)
    
    def delete_client_config(self, user_id: int, config_id: int) -> bool:
        """删除 MCP 客户端配置
        
        Args:
            user_id: 用户ID
            config_id: 配置ID
            
        Returns:
            是否删除成功
        """
        config = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.user_id == user_id,
            MCPClientConfigModel.id == config_id
        ).first()
        
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        
        logger.info(f"删除 MCP 客户端配置: user_id={user_id}, config_id={config_id}")
        
        return True
    
    def update_client_status(
        self,
        config_id: int,
        status: ConnectionStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """更新 MCP 客户端连接状态
        
        Args:
            config_id: 配置ID
            status: 连接状态
            error_message: 错误信息（可选）
            
        Returns:
            是否更新成功
        """
        config = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.id == config_id
        ).first()
        
        if not config:
            return False
        
        config.status = status.value
        config.error_message = error_message
        
        if status == ConnectionStatus.CONNECTED:
            from datetime import datetime
            config.last_connected_at = datetime.now()
        
        self.db.commit()
        
        logger.info(f"更新 MCP 客户端状态: config_id={config_id}, status={status.value}")
        
        return True
    
    # ==================== Tool Mapping Methods ====================
    
    def get_tool_mappings(self, client_config_id: int) -> List[Dict[str, Any]]:
        """获取客户端的工具映射
        
        Args:
            client_config_id: 客户端配置ID
            
        Returns:
            工具映射列表
        """
        mappings = self.db.query(MCPToolMappingModel).filter(
            MCPToolMappingModel.client_config_id == client_config_id
        ).all()
        
        return [
            {
                'id': m.id,
                'original_name': m.original_name,
                'local_name': m.local_name,
                'description': m.description,
                'input_schema': m.input_schema,
                'enabled': m.enabled,
                'cached_at': m.cached_at
            }
            for m in mappings
        ]
    
    def save_tool_mappings(
        self,
        client_config_id: int,
        tools: List[Dict[str, Any]]
    ) -> int:
        """保存工具映射
        
        Args:
            client_config_id: 客户端配置ID
            tools: 工具列表
            
        Returns:
            保存的工具数量
        """
        # 删除旧的映射
        self.db.query(MCPToolMappingModel).filter(
            MCPToolMappingModel.client_config_id == client_config_id
        ).delete()
        
        # 添加新的映射
        count = 0
        for tool in tools:
            mapping = MCPToolMappingModel(
                client_config_id=client_config_id,
                original_name=tool['name'],
                local_name=tool.get('local_name', tool['name']),
                description=tool.get('description', ''),
                input_schema=tool.get('inputSchema', {}),
                enabled=True
            )
            self.db.add(mapping)
            count += 1
        
        self.db.commit()
        
        logger.info(f"保存工具映射: client_config_id={client_config_id}, count={count}")
        
        return count
    
    def update_tool_mapping_enabled(
        self,
        mapping_id: int,
        enabled: bool
    ) -> bool:
        """更新工具映射的启用状态
        
        Args:
            mapping_id: 映射ID
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        mapping = self.db.query(MCPToolMappingModel).filter(
            MCPToolMappingModel.id == mapping_id
        ).first()
        
        if not mapping:
            return False
        
        mapping.enabled = enabled
        self.db.commit()
        
        return True
