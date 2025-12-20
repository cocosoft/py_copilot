"""智能体系统API路由"""
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.services.agent_system_service import (
    AgentSystemService, 
    AgentTaskRequest, 
    AgentTaskExecution,
    SchedulingStrategy
)
from app.services.agent_task_planner import TaskType, TaskComplexity
from app.services.agent_model_scheduler import ModelSelectionCriteria

router = APIRouter()


class TaskRequest(BaseModel):
    """任务请求模型"""
    task_description: str
    agent_id: Optional[int] = None
    task_context: Optional[Dict[str, Any]] = None
    scheduling_strategy: SchedulingStrategy = SchedulingStrategy.BALANCED
    min_capability_strength: int = 3
    max_cost: Optional[float] = None
    max_response_time: Optional[int] = None


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    agent_id: int
    task_type: TaskType
    complexity: TaskComplexity
    estimated_duration: int
    required_capabilities: List[str]
    selected_models: List[Dict[str, Any]]
    total_estimated_cost: float
    execution_status: str


class ExecutionRequest(BaseModel):
    """执行请求模型"""
    task_id: str


class ExecutionResponse(BaseModel):
    """执行响应模型"""
    task_id: str
    execution_status: str
    start_time: Optional[str]
    end_time: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    error_message: Optional[str]


class AgentPerformanceResponse(BaseModel):
    """智能体性能响应模型"""
    agent_id: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    average_cost: float
    average_time: int
    preferred_models: List[str]
    common_task_types: List[str]


class OptimizationResponse(BaseModel):
    """优化响应模型"""
    agent_id: int
    optimization_suggestions: List[str]
    recommended_strategy: SchedulingStrategy


@router.post("/tasks/plan", response_model=TaskResponse)
def plan_task(
    request: TaskRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    规划智能体任务
    
    Args:
        request: 任务请求
        db: 数据库会话
        
    Returns:
        任务规划结果
    """
    try:
        agent_system = AgentSystemService(db)
        
        # 创建任务请求
        agent_request = AgentTaskRequest(
            task_description=request.task_description,
            agent_id=request.agent_id,
            task_context=request.task_context,
            scheduling_strategy=request.scheduling_strategy,
            min_capability_strength=request.min_capability_strength,
            max_cost=request.max_cost,
            max_response_time=request.max_response_time
        )
        
        # 处理任务
        execution = agent_system.process_task(agent_request)
        
        # 构建响应
        response = TaskResponse(
            task_id=execution.task_id,
            agent_id=execution.agent_id,
            task_type=execution.task_plan.task_type,
            complexity=execution.task_plan.complexity,
            estimated_duration=execution.task_plan.estimated_total_duration,
            required_capabilities=execution.task_plan.required_capabilities,
            selected_models=[
                {
                    "model_id": model.model_id,
                    "model_name": model.model_name,
                    "supplier_name": model.supplier_name,
                    "role": "primary" if model.model_id == execution.scheduling_result.primary_model.model_id else "fallback",
                    "estimated_cost": model.estimated_cost,
                    "estimated_response_time": model.estimated_response_time
                }
                for model in execution.scheduling_result.selected_models
            ],
            total_estimated_cost=execution.scheduling_result.total_estimated_cost,
            execution_status=execution.execution_status
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务规划失败: {str(e)}"
        )


@router.post("/tasks/execute", response_model=ExecutionResponse)
def execute_task(
    request: ExecutionRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    执行智能体任务
    
    Args:
        request: 执行请求
        db: 数据库会话
        
    Returns:
        任务执行结果
    """
    try:
        agent_system = AgentSystemService(db)
        
        # 在实际实现中，这里应该从数据库获取任务执行记录
        # 这里使用模拟的执行记录
        
        # 创建模拟的任务执行记录
        task_request = AgentTaskRequest(
            task_description="模拟任务",
            scheduling_strategy=SchedulingStrategy.BALANCED
        )
        
        execution = agent_system.process_task(task_request)
        execution.task_id = request.task_id
        
        # 执行任务
        execution = agent_system.execute_task(execution)
        
        # 构建响应
        response = ExecutionResponse(
            task_id=execution.task_id,
            execution_status=execution.execution_status,
            start_time=execution.start_time,
            end_time=execution.end_time,
            execution_result=execution.execution_result,
            error_message=execution.error_message
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务执行失败: {str(e)}"
        )


@router.get("/agents/{agent_id}/performance", response_model=AgentPerformanceResponse)
def get_agent_performance(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体性能统计
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
        
    Returns:
        智能体性能数据
    """
    try:
        agent_system = AgentSystemService(db)
        performance_data = agent_system.get_agent_performance(agent_id)
        
        response = AgentPerformanceResponse(**performance_data)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体性能失败: {str(e)}"
        )


@router.post("/agents/{agent_id}/optimize", response_model=OptimizationResponse)
def optimize_agent_strategy(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    优化智能体策略
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
        
    Returns:
        优化建议
    """
    try:
        agent_system = AgentSystemService(db)
        optimization_data = agent_system.optimize_agent_strategy(agent_id)
        
        response = OptimizationResponse(**optimization_data)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"优化智能体策略失败: {str(e)}"
        )


@router.get("/capabilities")
def get_available_capabilities() -> Any:
    """
    获取可用能力列表
    
    Returns:
        能力列表
    """
    capabilities = [
        {"name": "text_generation", "display_name": "文本生成", "description": "生成自然语言文本的能力"},
        {"name": "code_generation", "display_name": "代码生成", "description": "生成编程代码的能力"},
        {"name": "data_analysis", "display_name": "数据分析", "description": "分析和处理数据的能力"},
        {"name": "image_processing", "display_name": "图像处理", "description": "处理和分析图像的能力"},
        {"name": "tool_calling", "display_name": "工具调用", "description": "调用外部工具的能力"},
        {"name": "multimodal", "display_name": "多模态", "description": "处理多种类型数据的能力"},
        {"name": "conversation", "display_name": "对话", "description": "进行自然对话的能力"},
        {"name": "comprehension", "display_name": "理解", "description": "理解复杂信息的能力"},
        {"name": "reasoning", "display_name": "推理", "description": "逻辑推理和问题解决能力"},
        {"name": "planning", "display_name": "规划", "description": "制定计划和策略的能力"}
    ]
    
    return {"capabilities": capabilities}


@router.get("/scheduling-strategies")
def get_scheduling_strategies() -> Any:
    """
    获取调度策略列表
    
    Returns:
        调度策略列表
    """
    strategies = [
        {
            "name": "capability_first", 
            "display_name": "能力优先", 
            "description": "优先选择能力最强的模型，确保任务质量"
        },
        {
            "name": "cost_effective", 
            "display_name": "成本优先", 
            "description": "优先选择成本最低的模型，优化资源使用"
        },
        {
            "name": "performance_optimized", 
            "display_name": "性能优先", 
            "description": "优先选择响应最快的模型，提高执行效率"
        },
        {
            "name": "balanced", 
            "display_name": "平衡策略", 
            "description": "综合考虑能力、成本、性能的平衡选择"
        }
    ]
    
    return {"strategies": strategies}