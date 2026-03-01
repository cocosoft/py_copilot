"""
Agent管理API

提供Agent的查询、执行和管理接口
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import User
from app.agents.integration import get_integration, AgentSystemIntegration
from app.services.agent_orchestration_service import (
    AgentOrchestrationService, get_orchestration_service
)

router = APIRouter()


@router.get("/list", response_model=List[dict])
async def list_agents(
    tags: Optional[str] = Query(None, description="标签过滤，逗号分隔"),
    active_only: bool = Query(True, description="仅返回激活的Agent"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent列表

    Args:
        tags: 标签过滤
        active_only: 仅返回激活的

    Returns:
        List[dict]: Agent列表
    """
    integration = get_integration(db)

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    agents = integration.list_agents(tags=tag_list, active_only=active_only)
    return agents


@router.get("/detail/{agent_name}", response_model=dict)
async def get_agent_detail(
    agent_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent详情

    Args:
        agent_name: Agent名称

    Returns:
        dict: Agent详情
    """
    integration = get_integration(db)

    agent_info = integration.get_agent_info(agent_name)

    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 未找到")

    return agent_info


@router.post("/execute/{agent_name}", response_model=dict)
async def execute_agent(
    agent_name: str,
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行Agent

    Args:
        agent_name: Agent名称
        request: 执行请求
            - input: 输入数据
            - parameters: 执行参数
            - session_id: 会话ID

    Returns:
        dict: 执行结果
    """
    service = get_orchestration_service(db)

    result = await service.execute_agent_directly(
        agent_name=agent_name,
        input_data=request.get("input", {}),
        user_id=str(current_user.id) if current_user else None,
        session_id=request.get("session_id"),
        parameters=request.get("parameters", {})
    )

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "execution_time_ms": result.execution_time_ms,
        "metadata": result.metadata
    }


@router.post("/chat", response_model=dict)
async def chat_with_agent(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    与Agent对话（智能路由）

    Args:
        request: 对话请求
            - message: 用户消息
            - context: 上下文
            - session_id: 会话ID

    Returns:
        dict: 对话结果
    """
    service = get_orchestration_service(db)

    result = await service.process_request(
        user_input=request.get("message", ""),
        user_id=str(current_user.id) if current_user else None,
        session_id=request.get("session_id"),
        context=request.get("context", {})
    )

    return result


@router.get("/search", response_model=List[dict])
async def search_agents(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索Agent

    Args:
        query: 搜索关键词
        limit: 返回数量限制

    Returns:
        List[dict]: 匹配的Agent列表
    """
    service = get_orchestration_service(db)

    agents = service.find_agents_for_task(query)
    return agents[:limit]


@router.get("/status", response_model=dict)
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent系统状态

    Returns:
        dict: 系统状态
    """
    service = get_orchestration_service(db)
    return service.get_system_status()


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket对话接口

    支持实时流式对话
    """
    await websocket.accept()

    service = get_orchestration_service(db)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            message = data.get("message", "")
            session_id = data.get("session_id")
            user_id = data.get("user_id")
            context = data.get("context", {})

            # 流式处理
            async for chunk in service.stream_process_request(
                user_input=message,
                user_id=user_id,
                session_id=session_id,
                context=context
            ):
                await websocket.send_text(chunk)

    except WebSocketDisconnect:
        print("WebSocket断开连接")
    except Exception as e:
        await websocket.send_text(f"[ERROR]{str(e)}[/ERROR]")
        await websocket.send_text("[END]")


@router.post("/find-for-task", response_model=List[dict])
async def find_agents_for_task(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为任务查找合适的Agent

    Args:
        request: 查找请求
            - task_description: 任务描述
            - required_capabilities: 必需的能力列表

    Returns:
        List[dict]: 匹配的Agent列表
    """
    service = get_orchestration_service(db)

    agents = service.find_agents_for_task(
        task_description=request.get("task_description", ""),
        required_capabilities=request.get("required_capabilities")
    )

    return agents


@router.get("/official", response_model=List[dict])
async def list_official_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取官方Agent列表

    Returns:
        List[dict]: 官方Agent列表
    """
    integration = get_integration(db)

    # 获取所有Agent并筛选官方的
    agents = integration.list_agents(active_only=True)
    official_agents = [a for a in agents if a.get("is_official", False)]

    return official_agents


@router.get("/categories", response_model=List[str])
async def list_agent_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent分类列表

    Returns:
        List[str]: 分类列表
    """
    integration = get_integration(db)

    agents = integration.list_agents(active_only=True)

    # 提取分类
    categories = set()
    for agent in agents:
        category = agent.get("template_category")
        if category:
            categories.add(category)

    return sorted(list(categories))
