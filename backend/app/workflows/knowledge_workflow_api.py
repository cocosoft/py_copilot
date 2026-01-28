"""
工作流知识库集成API

提供工作流与知识库协同工作的RESTful API接口。
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from .knowledge_workflow import KnowledgeWorkflowEngine, KnowledgeWorkflowStep

router = APIRouter()

# 全局工作流引擎实例
workflow_engine = None


def get_workflow_engine(db: Session = Depends(get_db)) -> KnowledgeWorkflowEngine:
    """获取工作流引擎实例
    
    Args:
        db: 数据库会话
        
    Returns:
        工作流引擎实例
    """
    global workflow_engine
    if workflow_engine is None:
        workflow_engine = KnowledgeWorkflowEngine(db)
    return workflow_engine


@router.post("/workflows")
async def create_workflow(
    name: str = Body(..., description="工作流名称"),
    steps: List[Dict[str, Any]] = Body(..., description="步骤配置列表"),
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """创建工作流
    
    Args:
        name: 工作流名称
        steps: 步骤配置列表
        engine: 工作流引擎
        
    Returns:
        工作流创建结果
    """
    try:
        # 验证步骤配置
        for step_config in steps:
            step_name = step_config.get("name")
            if step_name not in engine.steps:
                raise HTTPException(status_code=400, detail=f"步骤 '{step_name}' 未注册")
        
        # 创建工作流
        workflow_id = engine.create_workflow(name, steps)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "workflow_name": name,
            "step_count": len(steps)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工作流失败: {str(e)}")


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    initial_context: Dict[str, Any] = Body(..., description="初始上下文"),
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """执行工作流
    
    Args:
        workflow_id: 工作流ID
        initial_context: 初始上下文
        engine: 工作流引擎
        
    Returns:
        执行结果
    """
    try:
        result = engine.execute_workflow(workflow_id, initial_context)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "执行失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行工作流失败: {str(e)}")


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """获取工作流信息
    
    Args:
        workflow_id: 工作流ID
        engine: 工作流引擎
        
    Returns:
        工作流信息
    """
    try:
        result = engine.get_workflow_info(workflow_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "工作流不存在"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流信息失败: {str(e)}")


@router.get("/workflows")
async def list_workflows(
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """列出所有工作流
    
    Args:
        engine: 工作流引擎
        
    Returns:
        工作流列表
    """
    try:
        workflows = []
        
        for workflow_id, workflow in engine.workflows.items():
            workflows.append({
                "id": workflow_id,
                "name": workflow.get("name"),
                "step_count": len(workflow.get("steps", [])),
                "created_at": workflow.get("created_at"),
                "status": workflow.get("status")
            })
        
        return {
            "success": True,
            "workflows": workflows,
            "total_count": len(workflows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流列表失败: {str(e)}")


@router.get("/workflows/steps/available")
async def list_available_steps(
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """列出可用的工作流步骤
    
    Args:
        engine: 工作流引擎
        
    Returns:
        步骤列表
    """
    try:
        steps = engine.list_available_steps()
        
        return {
            "success": True,
            "steps": steps,
            "total_count": len(steps)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用步骤失败: {str(e)}")


@router.post("/workflows/steps/register")
async def register_custom_step(
    step_config: Dict[str, Any] = Body(..., description="步骤配置"),
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """注册自定义工作流步骤
    
    Args:
        step_config: 步骤配置
        engine: 工作流引擎
        
    Returns:
        注册结果
    """
    try:
        # 这里应该实现自定义步骤的注册逻辑
        # 由于时间关系，这里简化实现
        
        step_name = step_config.get("name")
        if not step_name:
            raise HTTPException(status_code=400, detail="步骤名称不能为空")
        
        # 检查步骤是否已存在
        if step_name in engine.steps:
            raise HTTPException(status_code=400, detail=f"步骤 '{step_name}' 已存在")
        
        # 创建自定义步骤（简化实现）
        class CustomStep(KnowledgeWorkflowStep):
            def __init__(self, config):
                super().__init__(config.get("name"), config.get("description", ""))
                self.input_schema = config.get("input_schema", {})
                self.output_schema = config.get("output_schema", {})
            
            def execute(self, context, db_session):
                # 简化实现：返回输入上下文
                return {"success": True, "result": context}
        
        custom_step = CustomStep(step_config)
        engine.register_step(custom_step)
        
        return {
            "success": True,
            "step_name": step_name,
            "message": "自定义步骤注册成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册自定义步骤失败: {str(e)}")


@router.post("/workflows/examples/search-analysis")
async def execute_search_analysis_example(
    query: str = Body(..., description="搜索查询"),
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """执行搜索分析示例工作流
    
    Args:
        query: 搜索查询
        engine: 工作流引擎
        
    Returns:
        执行结果
    """
    try:
        # 创建示例工作流
        workflow_steps = [
            {
                "name": "knowledge_search",
                "params": {
                    "query": query,
                    "limit": 5
                }
            },
            {
                "name": "document_analysis",
                "params": {
                    "document_content": "{{search_results[0].content if search_results else ''}}",
                    "analysis_type": "summary"
                }
            }
        ]
        
        # 创建工作流
        workflow_id = engine.create_workflow("搜索分析示例", workflow_steps)
        
        # 执行工作流
        result = engine.execute_workflow(workflow_id, {"query": query})
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行示例工作流失败: {str(e)}")


@router.post("/workflows/examples/decision-making")
async def execute_decision_making_example(
    context: str = Body(..., description="决策上下文"),
    options: List[str] = Body(..., description="决策选项"),
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """执行决策制定示例工作流
    
    Args:
        context: 决策上下文
        options: 决策选项
        engine: 工作流引擎
        
    Returns:
        执行结果
    """
    try:
        # 创建决策制定工作流
        workflow_steps = [
            {
                "name": "knowledge_decision",
                "params": {
                    "decision_context": context,
                    "options": options
                }
            }
        ]
        
        # 创建工作流
        workflow_id = engine.create_workflow("决策制定示例", workflow_steps)
        
        # 执行工作流
        initial_context = {
            "decision_context": context,
            "options": options
        }
        
        result = engine.execute_workflow(workflow_id, initial_context)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行决策制定示例失败: {str(e)}")


@router.get("/workflows/stats")
async def get_workflow_statistics(
    engine: KnowledgeWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """获取工作流统计信息
    
    Args:
        engine: 工作流引擎
        
    Returns:
        统计信息
    """
    try:
        stats = {
            "total_workflows": len(engine.workflows),
            "available_steps": len(engine.steps),
            "active_workflows": len([w for w in engine.workflows.values() if w.get("status") == "active"]),
            "inactive_workflows": len([w for w in engine.workflows.values() if w.get("status") == "inactive"])
        }
        
        # 计算平均步骤数
        if engine.workflows:
            avg_steps = sum(len(w.get("steps", [])) for w in engine.workflows.values()) / len(engine.workflows)
            stats["average_steps_per_workflow"] = round(avg_steps, 2)
        else:
            stats["average_steps_per_workflow"] = 0
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流统计失败: {str(e)}")