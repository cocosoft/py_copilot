"""
智能体管理API

提供智能体的创建、查询、更新、删除和状态管理功能。
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .agent_models import (
    Agent, AgentConfig, AgentType, AgentStatus, AgentCapability,
    agent_manager, agent_template
)

router = APIRouter(prefix="/api/agents", tags=["智能体管理"])


class AgentCreateRequest(BaseModel):
    """智能体创建请求模型"""
    name: str
    description: str = ""
    agent_type: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = None


class AgentUpdateRequest(BaseModel):
    """智能体更新请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """智能体响应模型"""
    agent_id: str
    name: str
    description: str
    agent_type: str
    status: str
    config: Dict[str, Any]
    created_by: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class AgentStatsResponse(BaseModel):
    """智能体统计响应模型"""
    total_agents: int
    type_stats: Dict[str, int]
    status_stats: Dict[str, int]
    recent_agents: List[Dict[str, Any]]


class AgentTemplateResponse(BaseModel):
    """智能体模板响应模型"""
    name: str
    display_name: str
    description: str
    agent_type: str
    capabilities: List[str]


class AgentListResponse(BaseModel):
    """智能体列表响应模型"""
    agents: List[AgentResponse]
    total_count: int
    has_more: bool


@router.post("", response_model=AgentResponse)
async def create_agent(request: AgentCreateRequest):
    """创建智能体
    
    Args:
        request: 创建请求
        
    Returns:
        创建的智能体
    """
    try:
        # 验证智能体类型
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {request.agent_type}")
        
        # 创建配置对象
        config = AgentConfig.from_dict(request.config)
        
        # 创建智能体对象
        agent = Agent(
            name=request.name,
            description=request.description,
            agent_type=agent_type,
            status=AgentStatus.CREATED,
            config=config,
            metadata=request.metadata or {}
        )
        
        # 保存到数据库
        if not agent_manager.create_agent(agent):
            raise HTTPException(status_code=500, detail="创建智能体失败")
        
        return AgentResponse(**agent.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建智能体失败: {str(e)}")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """获取智能体
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        智能体信息
    """
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    return AgentResponse(**agent.to_dict())


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: AgentUpdateRequest):
    """更新智能体
    
    Args:
        agent_id: 智能体ID
        request: 更新请求
        
    Returns:
        更新后的智能体
    """
    # 获取现有智能体
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    try:
        # 更新字段
        if request.name is not None:
            agent.name = request.name
            
        if request.description is not None:
            agent.description = request.description
            
        if request.agent_type is not None:
            try:
                agent.agent_type = AgentType(request.agent_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {request.agent_type}")
                
        if request.status is not None:
            try:
                agent.status = AgentStatus(request.status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的智能体状态: {request.status}")
                
        if request.config is not None:
            agent.config = AgentConfig.from_dict(request.config)
            
        if request.metadata is not None:
            agent.metadata = request.metadata
            
        # 更新数据库
        if not agent_manager.update_agent(agent):
            raise HTTPException(status_code=500, detail="更新智能体失败")
        
        return AgentResponse(**agent.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新智能体失败: {str(e)}")


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """删除智能体
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        删除结果
    """
    # 检查智能体是否存在
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    # 删除智能体
    if not agent_manager.delete_agent(agent_id):
        raise HTTPException(status_code=500, detail="删除智能体失败")
    
    return {
        "status": "success",
        "message": f"智能体 {agent_id} 已删除",
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat()
    }


@router.get("", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """列出智能体
    
    Args:
        agent_type: 智能体类型过滤
        status: 状态过滤
        limit: 限制数量
        offset: 偏移量
        
    Returns:
        智能体列表
    """
    try:
        # 解析过滤参数
        agent_type_enum = None
        if agent_type:
            try:
                agent_type_enum = AgentType(agent_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {agent_type}")
                
        status_enum = None
        if status:
            try:
                status_enum = AgentStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的智能体状态: {status}")
                
        # 获取智能体列表
        agents = agent_manager.list_agents(
            agent_type=agent_type_enum,
            status=status_enum,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应模型
        agent_responses = [AgentResponse(**agent.to_dict()) for agent in agents]
        
        # 获取总数（简化实现，实际应该查询总数）
        total_count = len(agents) + offset  # 简化估算
        
        return AgentListResponse(
            agents=agent_responses,
            total_count=total_count,
            has_more=len(agents) == limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体列表失败: {str(e)}")


@router.get("/stats", response_model=AgentStatsResponse)
async def get_agent_stats():
    """获取智能体统计信息
    
    Returns:
        统计信息
    """
    try:
        stats = agent_manager.get_agent_stats()
        
        return AgentStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体统计失败: {str(e)}")


@router.post("/{agent_id}/activate")
async def activate_agent(agent_id: str):
    """激活智能体
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        激活结果
    """
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    # 更新状态
    agent.status = AgentStatus.ACTIVE
    
    if not agent_manager.update_agent(agent):
        raise HTTPException(status_code=500, detail="激活智能体失败")
    
    return {
        "status": "success",
        "message": f"智能体 {agent_id} 已激活",
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(agent_id: str):
    """停用智能体
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        停用结果
    """
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    # 更新状态
    agent.status = AgentStatus.INACTIVE
    
    if not agent_manager.update_agent(agent):
        raise HTTPException(status_code=500, detail="停用智能体失败")
    
    return {
        "status": "success",
        "message": f"智能体 {agent_id} 已停用",
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/{agent_id}/clone")
async def clone_agent(agent_id: str, new_name: str = Query(...)):
    """克隆智能体
    
    Args:
        agent_id: 智能体ID
        new_name: 新智能体名称
        
    Returns:
        克隆结果
    """
    # 获取源智能体
    source_agent = agent_manager.get_agent(agent_id)
    if not source_agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    try:
        # 创建新智能体
        new_agent = Agent(
            name=new_name,
            description=f"克隆自: {source_agent.name}",
            agent_type=source_agent.agent_type,
            status=AgentStatus.CREATED,
            config=source_agent.config,
            metadata=source_agent.metadata.copy()
        )
        
        # 保存到数据库
        if not agent_manager.create_agent(new_agent):
            raise HTTPException(status_code=500, detail="克隆智能体失败")
        
        return {
            "status": "success",
            "message": f"智能体克隆完成",
            "source_agent_id": agent_id,
            "new_agent_id": new_agent.agent_id,
            "new_agent_name": new_agent.name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"克隆智能体失败: {str(e)}")


@router.get("/templates", response_model=List[AgentTemplateResponse])
async def get_agent_templates():
    """获取智能体模板列表
    
    Returns:
        模板列表
    """
    try:
        templates = agent_template.list_templates()
        
        template_responses = []
        for template in templates:
            template_responses.append(AgentTemplateResponse(**template))
            
        return template_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体模板失败: {str(e)}")


@router.post("/templates/{template_name}")
async def create_agent_from_template(template_name: str, name: str = Query(...)):
    """根据模板创建智能体
    
    Args:
        template_name: 模板名称
        name: 智能体名称
        
    Returns:
        创建结果
    """
    # 获取模板
    template = agent_template.get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"模板 {template_name} 未找到")
    
    try:
        # 基于模板创建智能体
        agent = Agent(
            name=name,
            description=template.description,
            agent_type=template.agent_type,
            status=AgentStatus.CREATED,
            config=template.config,
            metadata=template.metadata.copy()
        )
        
        # 保存到数据库
        if not agent_manager.create_agent(agent):
            raise HTTPException(status_code=500, detail="根据模板创建智能体失败")
        
        return {
            "status": "success",
            "message": f"基于模板 {template_name} 创建智能体完成",
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "template_name": template_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"根据模板创建智能体失败: {str(e)}")


@router.get("/types/agent-types")
async def get_agent_types():
    """获取支持的智能体类型
    
    Returns:
        智能体类型列表
    """
    return {
        "agent_types": [agent_type.value for agent_type in AgentType],
        "descriptions": {
            "chatbot": "聊天机器人 - 用于自然对话",
            "assistant": "智能助手 - 多功能任务处理",
            "analyzer": "分析器 - 数据分析和处理",
            "workflow": "工作流执行器 - 复杂工作流协调",
            "custom": "自定义 - 用户自定义类型"
        }
    }


@router.get("/types/status-types")
async def get_status_types():
    """获取支持的智能体状态
    
    Returns:
        智能体状态列表
    """
    return {
        "status_types": [status.value for status in AgentStatus],
        "descriptions": {
            "created": "已创建 - 智能体已创建但未激活",
            "active": "活跃 - 智能体正在运行",
            "inactive": "非活跃 - 智能体已停用",
            "error": "错误 - 智能体遇到错误",
            "deleted": "已删除 - 智能体已被删除"
        }
    }


@router.get("/types/capability-types")
async def get_capability_types():
    """获取支持的智能体能力
    
    Returns:
        智能体能力列表
    """
    return {
        "capability_types": [capability.value for capability in AgentCapability],
        "descriptions": {
            "text_generation": "文本生成 - 生成自然语言文本",
            "code_generation": "代码生成 - 生成编程代码",
            "data_analysis": "数据分析 - 分析和解释数据",
            "file_processing": "文件处理 - 处理各种文件格式",
            "web_search": "网络搜索 - 搜索互联网信息",
            "image_processing": "图像处理 - 处理和分析图像",
            "audio_processing": "音频处理 - 处理和分析音频",
            "workflow_execution": "工作流执行 - 协调多个任务"
        }
    }


@router.get("/search")
async def search_agents(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(50, ge=1, le=100)
):
    """搜索智能体
    
    Args:
        query: 搜索关键词
        limit: 限制数量
        
    Returns:
        搜索结果
    """
    try:
        # 获取所有智能体
        all_agents = agent_manager.list_agents(limit=1000)
        
        # 简单搜索实现（实际应该使用数据库全文搜索）
        matched_agents = []
        for agent in all_agents:
            # 搜索名称和描述
            search_text = f"{agent.name} {agent.description}".lower()
            if query.lower() in search_text:
                matched_agents.append(agent)
                
        # 限制结果数量
        matched_agents = matched_agents[:limit]
        
        # 转换为响应模型
        agent_responses = [AgentResponse(**agent.to_dict()) for agent in matched_agents]
        
        return {
            "query": query,
            "results": agent_responses,
            "total_count": len(matched_agents),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索智能体失败: {str(e)}")


@router.get("/{agent_id}/health")
async def get_agent_health(agent_id: str):
    """获取智能体健康状态
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        健康状态
    """
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
    
    # 简单的健康检查（实际应该检查智能体的实际运行状态）
    health_status = "healthy"
    warnings = []
    
    if agent.status == AgentStatus.ERROR:
        health_status = "error"
        warnings.append("智能体处于错误状态")
    elif agent.status == AgentStatus.INACTIVE:
        health_status = "warning"
        warnings.append("智能体处于非活跃状态")
    
    # 检查配置
    if not agent.config.model_name:
        warnings.append("模型名称未配置")
        
    if not agent.config.capabilities:
        warnings.append("未配置任何能力")
    
    return {
        "agent_id": agent_id,
        "status": health_status,
        "is_healthy": health_status == "healthy",
        "warnings": warnings,
        "agent_status": agent.status.value,
        "last_updated": agent.updated_at.isoformat(),
        "timestamp": datetime.now().isoformat()
    }