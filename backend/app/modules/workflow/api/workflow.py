from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logging_config import log_execution
from ..schemas.workflow import (
    Workflow, WorkflowCreate, WorkflowUpdate, 
    WorkflowExecution, WorkflowExecutionCreate,
    WorkflowExecutionRequest, WorkflowExecutionResponse,
    WorkflowAutoComposeRequest, WorkflowAutoComposeResponse
)
from ..services.workflow_service import WorkflowService, WorkflowEngine
from ..services.workflow_monitoring_service import WorkflowMonitoringService

router = APIRouter()

# 工作流管理API
@router.get("/workflows", response_model=List[Workflow])
@log_execution
def get_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流列表"""
    workflow_service = WorkflowService(db)
    workflows = workflow_service.get_workflows(skip, limit)
    return workflows

@router.post("/workflows", response_model=Workflow)
@log_execution
def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建新工作流"""
    try:
        workflow_service = WorkflowService(db)
        return workflow_service.create_workflow(workflow, current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工作流失败: {str(e)}")

@router.get("/workflows/{workflow_id}", response_model=Workflow)
@log_execution
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流详情"""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflow

@router.put("/workflows/{workflow_id}", response_model=Workflow)
@log_execution
def update_workflow(
    workflow_id: int,
    workflow: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新工作流"""
    workflow_service = WorkflowService(db)
    updated_workflow = workflow_service.update_workflow(workflow_id, workflow)
    if not updated_workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return updated_workflow

@router.delete("/workflows/{workflow_id}")
@log_execution
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除工作流"""
    workflow_service = WorkflowService(db)
    success = workflow_service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"message": "工作流删除成功"}

# 工作流执行API
@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
@log_execution
def execute_workflow(
    workflow_id: int,
    execution_request: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """执行工作流"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"开始执行工作流: {workflow_id}")
        logger.info(f"请求数据: {execution_request.dict()}")
        
        workflow_engine = WorkflowEngine(db)
        
        execution = workflow_engine.execute_workflow(
            workflow_id,
            execution_request.input_data,
            current_user["id"]
        )
        
        logger.info(f"工作流执行启动成功: {execution.id}")
        
        return WorkflowExecutionResponse(
            execution_id=execution.id,
            status=execution.status,
            message="工作流执行已启动"
        )
        
    except Exception as e:
        import traceback
        logger.error(f"工作流执行失败: {str(e)}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")

@router.get("/executions", response_model=List[WorkflowExecution])
@log_execution
def get_executions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流执行列表"""
    workflow_service = WorkflowService(db)
    executions = workflow_service.get_executions(skip, limit)
    return executions

@router.get("/executions/{execution_id}", response_model=WorkflowExecution)
@log_execution
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流执行详情"""
    workflow_service = WorkflowService(db)
    execution = workflow_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution

# 知识图谱相关的工作流API
@router.post("/workflows/knowledge-search/test")
@log_execution
def test_knowledge_search(
    query: str,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """测试知识搜索节点"""
    try:
        from ..services.node_executors import KnowledgeSearchExecutor
        
        executor = KnowledgeSearchExecutor(db)
        config = {
            "search_query": query,
            "knowledge_base_id": knowledge_base_id
        }
        
        result = executor.execute(config, {})
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/workflows/entity-extraction/test")
def test_entity_extraction(
    text: str,
    entity_types: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """测试实体抽取节点"""
    try:
        from ..services.node_executors import EntityExtractionExecutor
        
        executor = EntityExtractionExecutor(db)
        config = {
            "text_input": text,
            "entity_types": entity_types
        }
        
        result = executor.execute(config, {})
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/workflows/relationship-analysis/test")
def test_relationship_analysis(
    entity_ids: List[str],
    relationship_types: Optional[List[str]] = None,
    max_depth: int = 2,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """测试关系分析节点"""
    try:
        from ..services.node_executors import RelationshipAnalysisExecutor
        
        executor = RelationshipAnalysisExecutor(db)
        config = {
            "entity_ids": entity_ids,
            "relationship_types": relationship_types,
            "max_depth": max_depth
        }
        
        result = executor.execute(config, {})
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 自动生成工作流API
@router.post("/workflows/auto-compose", response_model=WorkflowAutoComposeResponse)
@log_execution
async def auto_compose_workflow(
    request: WorkflowAutoComposeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """根据任务描述自动生成工作流"""
    try:
        workflow_service = WorkflowService(db)
        
        # 生成工作流
        workflow = await workflow_service.create_workflow_from_description(
            task_description=request.task_description,
            user_id=current_user["id"]
        )
        
        # 计算节点和边的数量
        node_count = len(workflow.definition.get("nodes", []))
        edge_count = len(workflow.definition.get("edges", []))
        
        return WorkflowAutoComposeResponse(
            workflow=workflow,
            message="工作流自动生成成功",
            node_count=node_count,
            edge_count=edge_count
        )
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"自动生成工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"工作流生成失败: {str(e)}")


# 工作流监控API
@router.get("/workflows/monitoring/running", response_model=List[Dict[str, Any]])
@log_execution
def get_running_workflows(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取正在运行的工作流"""
    try:
        monitoring_service = WorkflowMonitoringService(db)
        return monitoring_service.get_running_workflows()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取正在运行的工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取正在运行的工作流失败: {str(e)}")


@router.get("/workflows/{workflow_id}/monitoring/history", response_model=List[Dict[str, Any]])
@log_execution
def get_workflow_execution_history(
    workflow_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流执行历史"""
    try:
        monitoring_service = WorkflowMonitoringService(db)
        return monitoring_service.get_workflow_execution_history(workflow_id, days)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取工作流执行历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取工作流执行历史失败: {str(e)}")


@router.get("/workflows/{workflow_id}/monitoring/statistics", response_model=Dict[str, Any])
@log_execution
def get_workflow_statistics(
    workflow_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流统计信息"""
    try:
        monitoring_service = WorkflowMonitoringService(db)
        return monitoring_service.get_workflow_statistics(workflow_id, days)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取工作流统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取工作流统计信息失败: {str(e)}")


@router.get("/workflows/executions/{execution_id}/logs", response_model=Dict[str, Any])
@log_execution
def get_execution_logs(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取工作流执行日志"""
    try:
        monitoring_service = WorkflowMonitoringService(db)
        return monitoring_service.get_execution_logs(execution_id)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取工作流执行日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取工作流执行日志失败: {str(e)}")


@router.get("/workflows/monitoring/failed", response_model=List[Dict[str, Any]])
@log_execution
def get_recent_failed_executions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取最近失败的工作流执行"""
    try:
        monitoring_service = WorkflowMonitoringService(db)
        return monitoring_service.get_recent_failed_executions(limit)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取最近失败的工作流执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取最近失败的工作流执行失败: {str(e)}")
