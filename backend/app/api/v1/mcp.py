"""MCP 管理 API 接口

提供 MCP 服务端和客户端配置的管理接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.mcp.services.config_service import MCPConfigService
from app.mcp.client.connection_manager import connection_manager
from app.mcp.client.tool_proxy import sync_client_tools, get_mcp_tools
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerConfigCreate,
    MCPServerConfigUpdate,
    MCPClientConfig,
    MCPClientConfigCreate,
    MCPClientConfigUpdate,
    ConnectionStatus,
    MCPStatusResponse,
    MCPConnectResult,
    TransportType
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_current_user_id(current_user) -> int:
    """获取当前用户ID
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        用户ID
    """
    return current_user.id if hasattr(current_user, 'id') else 1


# ==================== Server Config APIs ====================

@router.get("/servers", response_model=Dict[str, Any])
async def list_server_configs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取 MCP 服务端配置列表
    
    返回当前用户的所有 MCP 服务端配置。
    
    Returns:
        包含配置列表的响应
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        configs = service.get_server_configs(user_id)
        
        return {
            "success": True,
            "data": [config.model_dump() for config in configs]
        }
    except Exception as e:
        logger.error(f"获取 MCP 服务端配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置列表失败: {str(e)}"
        )


@router.get("/servers/{config_id}", response_model=Dict[str, Any])
async def get_server_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取单个 MCP 服务端配置
    
    Args:
        config_id: 配置ID
        
    Returns:
        配置详情
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        config = service.get_server_config(user_id, config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        return {
            "success": True,
            "data": config.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 MCP 服务端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.post("/servers", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_server_config(
    config_data: MCPServerConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建 MCP 服务端配置
    
    Args:
        config_data: 配置数据
        
    Returns:
        创建的配置
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 检查名称是否已存在
        existing_configs = service.get_server_configs(user_id)
        for existing in existing_configs:
            if existing.name == config_data.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"配置名称 '{config_data.name}' 已存在"
                )
        
        new_config = service.create_server_config(user_id, config_data)
        
        return {
            "success": True,
            "data": new_config.model_dump(),
            "message": "配置创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建 MCP 服务端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建配置失败: {str(e)}"
        )


@router.put("/servers/{config_id}", response_model=Dict[str, Any])
async def update_server_config(
    config_id: int,
    config_data: MCPServerConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新 MCP 服务端配置
    
    Args:
        config_id: 配置ID
        config_data: 更新数据
        
    Returns:
        更新后的配置
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 检查配置是否存在
        existing = service.get_server_config(user_id, config_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 如果更新名称，检查是否与其他配置冲突
        if config_data.name:
            all_configs = service.get_server_configs(user_id)
            for config in all_configs:
                if config.id != config_id and config.name == config_data.name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"配置名称 '{config_data.name}' 已存在"
                    )
        
        updated_config = service.update_server_config(user_id, config_id, config_data)
        
        return {
            "success": True,
            "data": updated_config.model_dump(),
            "message": "配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 MCP 服务端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )


@router.delete("/servers/{config_id}", response_model=Dict[str, Any])
async def delete_server_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除 MCP 服务端配置
    
    Args:
        config_id: 配置ID
        
    Returns:
        删除结果
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        success = service.delete_server_config(user_id, config_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        return {
            "success": True,
            "message": "配置删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 MCP 服务端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除配置失败: {str(e)}"
        )


# ==================== Client Config APIs ====================

@router.get("/clients", response_model=Dict[str, Any])
async def list_client_configs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取 MCP 客户端配置列表
    
    Returns:
        包含配置列表的响应
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        configs = service.get_client_configs(user_id)
        
        return {
            "success": True,
            "data": [config.model_dump() for config in configs]
        }
    except Exception as e:
        logger.error(f"获取 MCP 客户端配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置列表失败: {str(e)}"
        )


@router.get("/clients/{config_id}", response_model=Dict[str, Any])
async def get_client_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取单个 MCP 客户端配置
    
    Args:
        config_id: 配置ID
        
    Returns:
        配置详情
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        config = service.get_client_config(user_id, config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        return {
            "success": True,
            "data": config.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 MCP 客户端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.post("/clients", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_client_config(
    config_data: MCPClientConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建 MCP 客户端配置
    
    Args:
        config_data: 配置数据
        
    Returns:
        创建的配置
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 检查名称是否已存在
        existing_configs = service.get_client_configs(user_id)
        for existing in existing_configs:
            if existing.name == config_data.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"配置名称 '{config_data.name}' 已存在"
                )
        
        new_config = service.create_client_config(user_id, config_data)
        
        return {
            "success": True,
            "data": new_config.model_dump(),
            "message": "配置创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建 MCP 客户端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建配置失败: {str(e)}"
        )


@router.put("/clients/{config_id}", response_model=Dict[str, Any])
async def update_client_config(
    config_id: int,
    config_data: MCPClientConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新 MCP 客户端配置
    
    Args:
        config_id: 配置ID
        config_data: 更新数据
        
    Returns:
        更新后的配置
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 检查配置是否存在
        existing = service.get_client_config(user_id, config_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 如果更新名称，检查是否与其他配置冲突
        if config_data.name:
            all_configs = service.get_client_configs(user_id)
            for config in all_configs:
                if config.id != config_id and config.name == config_data.name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"配置名称 '{config_data.name}' 已存在"
                    )
        
        updated_config = service.update_client_config(user_id, config_id, config_data)
        
        return {
            "success": True,
            "data": updated_config.model_dump(),
            "message": "配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 MCP 客户端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )


@router.delete("/clients/{config_id}", response_model=Dict[str, Any])
async def delete_client_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除 MCP 客户端配置
    
    Args:
        config_id: 配置ID
        
    Returns:
        删除结果
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        success = service.delete_client_config(user_id, config_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        return {
            "success": True,
            "message": "配置删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 MCP 客户端配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除配置失败: {str(e)}"
        )


@router.post("/clients/{config_id}/connect", response_model=Dict[str, Any])
async def connect_client(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """连接 MCP 客户端
    
    建立与外部 MCP 服务的连接。
    
    Args:
        config_id: 客户端配置ID
        
    Returns:
        连接结果
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 获取配置
        config = service.get_client_config(user_id, config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 初始化连接管理器
        await connection_manager.initialize(db)
        
        # 刷新客户端配置
        await connection_manager.refresh_client(config_id, config)
        
        # 执行连接
        success = await connection_manager.connect(config_id)
        
        if success:
            # 同步工具
            tools_count = await sync_client_tools(config_id, db)
            
            return {
                "success": True,
                "message": "连接成功",
                "tools_discovered": tools_count
            }
        else:
            client = connection_manager.get_client(config_id)
            error_msg = client.error_message if client else "连接失败"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"连接 MCP 客户端失败: {e}")
        # 更新错误状态
        service.update_client_status(config_id, ConnectionStatus.ERROR, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接失败: {str(e)}"
        )


@router.post("/clients/{config_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_client(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """断开 MCP 客户端连接
    
    Args:
        config_id: 客户端配置ID
        
    Returns:
        断开结果
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 获取配置
        config = service.get_client_config(user_id, config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 执行断开连接
        success = await connection_manager.disconnect(config_id)
        
        if success:
            return {
                "success": True,
                "message": "已断开连接"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="断开连接失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"断开 MCP 客户端连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"断开连接失败: {str(e)}"
        )


# ==================== Tool Management APIs ====================

@router.get("/tools", response_model=Dict[str, Any])
async def list_mcp_tools(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取所有 MCP 工具
    
    返回本地工具、技能和外部客户端工具的合并列表。
    
    Returns:
        工具列表
    """
    try:
        tools = []
        
        # 获取外部 MCP 工具
        mcp_tools = get_mcp_tools()
        for tool in mcp_tools:
            tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "source": "external",
                "inputSchema": tool["inputSchema"],
                "enabled": True
            })
        
        return {
            "success": True,
            "data": tools
        }
    except Exception as e:
        logger.error(f"获取 MCP 工具列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


# ==================== Third-party MCP Services API ====================

def _get_marketplace_servers_data() -> Dict[str, List[Dict[str, Any]]]:
    """获取预定义的 MCP 市场服务数据
    
    Returns:
        市场服务器数据字典
    """
    return {
        "mcpmarket": [
            {
                "id": "github",
                "name": "GitHub MCP",
                "description": "提供 GitHub API 访问能力，支持代码搜索、仓库管理、Issue 操作等",
                "category": "Developer Tools",
                "install_command": "npx -y @modelcontextprotocol/server-github",
                "transport": "stdio",
                "auth_required": True,
                "auth_type": "token",
                "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
                "popularity": 27280
            },
            {
                "id": "playwright",
                "name": "Playwright MCP",
                "description": "自动化浏览器交互，支持网页截图、表单填写、页面导航等",
                "category": "Developer Tools",
                "install_command": "npx -y @modelcontextprotocol/server-playwright",
                "transport": "stdio",
                "auth_required": False,
                "env_vars": [],
                "popularity": 27758
            },
            {
                "id": "filesystem",
                "name": "File System MCP",
                "description": "本地文件系统访问，支持文件读写、目录浏览、文件搜索等",
                "category": "Developer Tools",
                "install_command": "npx -y @modelcontextprotocol/server-filesystem",
                "transport": "stdio",
                "auth_required": False,
                "env_vars": [],
                "popularity": 25000
            },
            {
                "id": "sqlite",
                "name": "SQLite MCP",
                "description": "SQLite 数据库操作，支持查询、插入、更新等数据库操作",
                "category": "Database Management",
                "install_command": "npx -y @modelcontextprotocol/server-sqlite",
                "transport": "stdio",
                "auth_required": False,
                "env_vars": [],
                "popularity": 20000
            },
            {
                "id": "postgres",
                "name": "PostgreSQL MCP",
                "description": "PostgreSQL 数据库操作，支持复杂查询和数据库管理",
                "category": "Database Management",
                "install_command": "npx -y @modelcontextprotocol/server-postgres",
                "transport": "stdio",
                "auth_required": True,
                "auth_type": "connection_string",
                "env_vars": ["DATABASE_URL"],
                "popularity": 18000
            },
            {
                "id": "brave-search",
                "name": "Brave Search MCP",
                "description": "Brave 搜索引擎集成，支持网页搜索、图片搜索",
                "category": "Productivity & Workflow",
                "install_command": "npx -y @modelcontextprotocol/server-brave-search",
                "transport": "stdio",
                "auth_required": True,
                "auth_type": "api_key",
                "env_vars": ["BRAVE_API_KEY"],
                "popularity": 15000
            },
            {
                "id": "fetch",
                "name": "Fetch MCP",
                "description": "网页内容获取，支持获取网页 HTML、转换为 Markdown",
                "category": "Productivity & Workflow",
                "install_command": "npx -y @modelcontextprotocol/server-fetch",
                "transport": "stdio",
                "auth_required": False,
                "env_vars": [],
                "popularity": 14000
            },
            {
                "id": "puppeteer",
                "name": "Puppeteer MCP",
                "description": "基于 Puppeteer 的浏览器自动化，支持网页截图、PDF 生成",
                "category": "Developer Tools",
                "install_command": "npx -y @modelcontextprotocol/server-puppeteer",
                "transport": "stdio",
                "auth_required": False,
                "env_vars": [],
                "popularity": 12000
            },
            {
                "id": "figma",
                "name": "Figma MCP",
                "description": "Figma 设计文件访问，支持获取设计布局信息",
                "category": "API Development",
                "install_command": "npx -y @modelcontextprotocol/server-figma",
                "transport": "stdio",
                "auth_required": True,
                "auth_type": "token",
                "env_vars": ["FIGMA_ACCESS_TOKEN"],
                "popularity": 13267
            },
            {
                "id": "blender",
                "name": "Blender MCP",
                "description": "Blender 3D 建模集成，支持 AI 辅助 3D 场景创建",
                "category": "Developer Tools",
                "install_command": "uvx mcp-blender",
                "transport": "stdio",
                "auth_required": False,
                "env_vars": [],
                "popularity": 17359
            }
        ],
        "modelscope": [
            {
                "id": "aigohotel",
                "name": "全球酒店推荐&预订",
                "description": "全球酒店智能推荐及预订工具，支持城市搜索、星级筛选、价格比较",
                "category": "生活服务",
                "install_command": None,
                "connection_url": "https://mcp.modelscope.cn/sse/aigohotel",
                "transport": "sse",
                "auth_required": True,
                "auth_type": "api_key",
                "env_vars": ["MODELSCOPE_API_KEY"],
                "popularity": 5000
            }
        ]
    }


@router.get("/marketplace/servers", response_model=Dict[str, Any])
async def list_marketplace_servers(
    source: str = Query("mcpmarket", description="MCP市场源: mcpmarket, modelscope"),
    category: Optional[str] = Query(None, description="服务类别筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取第三方 MCP 市场服务列表
    
    从 MCP Market 或 ModelScope 等第三方市场获取可用的 MCP 服务列表。
    
    Args:
        source: 市场源名称 (mcpmarket, modelscope)
        category: 可选的类别筛选
        
    Returns:
        可用的 MCP 服务列表
    """
    try:
        # 获取预定义的 MCP 市场服务数据
        marketplace_servers = _get_marketplace_servers_data()
        
        servers = marketplace_servers.get(source, [])
        
        # 按类别筛选
        if category:
            servers = [s for s in servers if s["category"] == category]
        
        # 按热度排序
        servers = sorted(servers, key=lambda x: x.get("popularity", 0), reverse=True)
        
        return {
            "success": True,
            "data": {
                "source": source,
                "total": len(servers),
                "servers": servers
            }
        }
        
    except Exception as e:
        logger.error(f"获取 MCP 市场服务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务列表失败: {str(e)}"
        )


@router.post("/marketplace/install", response_model=Dict[str, Any])
async def install_marketplace_server(
    server_id: str = Query(..., description="要安装的服务ID"),
    source: str = Query("mcpmarket", description="MCP市场源"),
    name: Optional[str] = Query(None, description="自定义配置名称"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """从 MCP 市场安装服务
    
    从第三方 MCP 市场选择服务并创建客户端配置。
    
    Args:
        server_id: 服务ID
        source: 市场源
        name: 自定义配置名称
        
    Returns:
        安装结果，包含创建的客户端配置ID
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        # 获取市场服务信息
        marketplace_servers = _get_marketplace_servers_data()
        servers = marketplace_servers.get(source, [])
        server_info = next((s for s in servers if s["id"] == server_id), None)
        
        if not server_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到服务: {server_id}"
            )
        
        # 创建客户端配置
        config_name = name or server_info["name"]
        
        # 检查名称是否已存在
        existing_configs = service.get_client_configs(user_id)
        if any(c.name == config_name for c in existing_configs):
            # 添加序号避免重复
            base_name = config_name
            counter = 1
            while any(c.name == config_name for c in existing_configs):
                config_name = f"{base_name} ({counter})"
                counter += 1
        
        # 构建配置数据
        transport = TransportType(server_info["transport"])
        
        config_data = MCPClientConfigCreate(
            name=config_name,
            description=server_info["description"],
            transport=transport,
            connection_url=server_info.get("connection_url"),
            command=server_info.get("install_command"),
            enabled=False,  # 默认不启用，需要用户配置认证信息后手动启用
            auto_connect=False,
            auth_config={"type": server_info.get("auth_type", "none")} if server_info.get("auth_required") else None
        )
        
        # 创建配置
        new_config = service.create_client_config(user_id, config_data)
        
        return {
            "success": True,
            "message": f"服务 '{server_info['name']}' 安装成功",
            "data": {
                "config_id": new_config.id,
                "name": new_config.name,
                "transport": new_config.transport,
                "auth_required": server_info.get("auth_required", False),
                "env_vars": server_info.get("env_vars", []),
                "setup_instructions": _generate_setup_instructions(server_info)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"安装 MCP 服务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"安装服务失败: {str(e)}"
        )


def _generate_setup_instructions(server_info: Dict[str, Any]) -> str:
    """生成服务设置说明
    
    Args:
        server_info: 服务信息
        
    Returns:
        设置说明文本
    """
    instructions = []
    
    if server_info.get("auth_required"):
        instructions.append("此服务需要认证信息，请配置以下环境变量或认证信息：")
        for env_var in server_info.get("env_vars", []):
            instructions.append(f"  - {env_var}")
    
    if server_info.get("install_command"):
        instructions.append(f"\n安装命令: {server_info['install_command']}")
    
    if server_info.get("transport") == "stdio":
        instructions.append("\n使用 Stdio 传输方式，确保命令可在系统 PATH 中找到。")
    elif server_info.get("transport") == "sse":
        instructions.append(f"\n使用 SSE 传输方式，连接地址: {server_info.get('connection_url', 'N/A')}")
    
    return "\n".join(instructions)


@router.get("/marketplace/categories", response_model=Dict[str, Any])
async def list_marketplace_categories(
    source: str = Query("mcpmarket", description="MCP市场源"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取 MCP 市场服务类别
    
    Args:
        source: 市场源名称
        
    Returns:
        服务类别列表
    """
    try:
        categories = {
            "mcpmarket": [
                {"id": "Developer Tools", "name": "开发工具", "count": 4},
                {"id": "Database Management", "name": "数据库管理", "count": 2},
                {"id": "Productivity & Workflow", "name": "生产力与工作流程", "count": 2},
                {"id": "API Development", "name": "API 开发", "count": 2}
            ],
            "modelscope": [
                {"id": "生活服务", "name": "生活服务", "count": 1}
            ]
        }
        
        return {
            "success": True,
            "data": {
                "source": source,
                "categories": categories.get(source, [])
            }
        }
        
    except Exception as e:
        logger.error(f"获取 MCP 市场类别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取类别失败: {str(e)}"
        )


# ==================== Status API ====================

@router.get("/status", response_model=Dict[str, Any])
async def get_mcp_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取 MCP 整体状态
    
    返回服务端和客户端的整体状态概览。
    
    Returns:
        状态信息
    """
    try:
        user_id = get_current_user_id(current_user)
        service = MCPConfigService(db)
        
        server_configs = service.get_server_configs(user_id)
        client_configs = service.get_client_configs(user_id)
        
        # 统计连接状态
        connected_clients = sum(
            1 for c in client_configs 
            if c.status == ConnectionStatus.CONNECTED
        )
        
        return {
            "success": True,
            "data": {
                "server_enabled": any(s.enabled for s in server_configs),
                "server_count": len(server_configs),
                "client_count": len(client_configs),
                "connected_clients": connected_clients,
                "servers": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "enabled": s.enabled,
                        "transport": s.transport,
                        "endpoint": f"{s.host}:{s.port}" if s.transport == "sse" else "stdio"
                    }
                    for s in server_configs
                ],
                "clients": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "status": c.status,
                        "enabled": c.enabled
                    }
                    for c in client_configs
                ]
            }
        }
    except Exception as e:
        logger.error(f"获取 MCP 状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )
