from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
from ..models.workflow import Workflow, WorkflowExecution, WorkflowNode, NodeExecution
from ..schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowExecutionCreate
from datetime import datetime
import json
import logging
import traceback

# 导入性能监控装饰器
from app.core.logging_config import log_execution

logger = logging.getLogger(__name__)

def transaction_handler(func: Callable) -> Callable:
    """事务处理装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except SQLAlchemyError as e:
            logger.error(f"数据库事务错误 - {func.__name__}: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
        except Exception as e:
            logger.error(f"操作失败 - {func.__name__}: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    return wrapper

class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
    
    def begin_transaction(self):
        """开始事务"""
        logger.debug("开始数据库事务")
        # SQLAlchemy默认使用隐式事务，这里主要用于标记事务开始
        
    def commit_transaction(self):
        """提交事务"""
        logger.debug("提交数据库事务")
        self.db.commit()
    
    def rollback_transaction(self):
        """回滚事务"""
        logger.debug("回滚数据库事务")
        self.db.rollback()
    
    def execute_in_transaction(self, func: Callable, *args, **kwargs):
        """在事务中执行函数"""
        logger.debug(f"在事务中执行函数: {func.__name__}")
        try:
            self.begin_transaction()
            result = func(*args, **kwargs)
            self.commit_transaction()
            return result
        except Exception as e:
            logger.error(f"事务执行失败: {func.__name__}, 错误: {str(e)}")
            self.rollback_transaction()
            raise
    
    @log_execution
    def batch_create_workflows(self, workflows_data: List[WorkflowCreate], user_id: Optional[int] = None) -> List[Workflow]:
        """批量创建工作流"""
        logger.info(f"批量创建工作流: 数量={len(workflows_data)}")
        
        if not workflows_data:
            logger.warning("批量创建工作流: 空的工作流数据列表")
            return []
        
        try:
            workflows = []
            for i, workflow_data in enumerate(workflows_data):
                logger.debug(f"创建第 {i+1}/{len(workflows_data)} 个工作流")
                workflow = self.create_workflow(workflow_data, user_id)
                workflows.append(workflow)
            
            logger.info(f"批量创建工作流成功: 数量={len(workflows)}")
            return workflows
            
        except Exception as e:
            logger.error(f"批量创建工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    def batch_update_workflows(self, updates: List[Dict[str, Any]]) -> List[Workflow]:
        """批量更新工作流"""
        logger.info(f"批量更新工作流: 数量={len(updates)}")
        
        if not updates:
            logger.warning("批量更新工作流: 空的更新列表")
            return []
        
        try:
            updated_workflows = []
            for i, update in enumerate(updates):
                workflow_id = update.get("workflow_id")
                workflow_data = update.get("workflow_data")
                
                if not workflow_id or not workflow_data:
                    logger.warning(f"跳过无效的更新项: 索引={i}")
                    continue
                
                logger.debug(f"更新第 {i+1}/{len(updates)} 个工作流: ID={workflow_id}")
                workflow = self.update_workflow(workflow_id, workflow_data)
                if workflow:
                    updated_workflows.append(workflow)
            
            logger.info(f"批量更新工作流成功: 数量={len(updated_workflows)}")
            return updated_workflows
            
        except Exception as e:
            logger.error(f"批量更新工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    def batch_delete_workflows(self, workflow_ids: List[int]) -> Dict[str, Any]:
        """批量删除工作流"""
        logger.info(f"批量删除工作流: 数量={len(workflow_ids)}")
        
        if not workflow_ids:
            logger.warning("批量删除工作流: 空的工作流ID列表")
            return {"success": True, "deleted_count": 0}
        
        try:
            deleted_count = 0
            failed_ids = []
            
            for i, workflow_id in enumerate(workflow_ids):
                logger.debug(f"删除第 {i+1}/{len(workflow_ids)} 个工作流: ID={workflow_id}")
                try:
                    success = self.delete_workflow(workflow_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_ids.append(workflow_id)
                except Exception as delete_error:
                    logger.error(f"删除工作流失败: ID={workflow_id}, 错误: {str(delete_error)}")
                    failed_ids.append(workflow_id)
            
            result = {
                "success": len(failed_ids) == 0,
                "deleted_count": deleted_count,
                "failed_count": len(failed_ids),
                "failed_ids": failed_ids
            }
            
            logger.info(f"批量删除工作流完成: 成功={deleted_count}, 失败={len(failed_ids)}")
            return result
            
        except Exception as e:
            logger.error(f"批量删除工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    @log_execution
    def create_workflow(self, workflow_data: WorkflowCreate, user_id: Optional[int] = None) -> Workflow:
        """创建新工作流"""
        logger.info(f"开始创建工作流: {workflow_data.name}")
        
        # 验证输入数据
        if not workflow_data.name or not workflow_data.name.strip():
            error_msg = "工作流名称不能为空"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            workflow = Workflow(
                name=workflow_data.name.strip(),
                description=workflow_data.description or "",
                definition=workflow_data.definition or {},
                status="draft",
                version="1.0",
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)
            
            logger.info(f"工作流创建成功: ID={workflow.id}, 名称={workflow.name}")
            return workflow
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 创建工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"创建工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    
    @log_execution
    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """获取工作流详情"""
        logger.info(f"获取工作流详情: ID={workflow_id}")
        
        try:
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            if workflow:
                logger.info(f"成功获取工作流: ID={workflow_id}, 名称={workflow.name}")
            else:
                logger.warning(f"工作流不存在: ID={workflow_id}")
                
            return workflow
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 获取工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"数据库查询失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"获取工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    @log_execution
    def get_workflows(self, skip: int = 0, limit: int = 100) -> List[Workflow]:
        """获取工作流列表"""
        logger.info(f"获取工作流列表: skip={skip}, limit={limit}")
        
        # 验证参数
        if skip < 0:
            skip = 0
        if limit <= 0 or limit > 1000:
            limit = 100
            logger.warning(f"limit参数超出范围，使用默认值: {limit}")
        
        try:
            workflows = self.db.query(Workflow).offset(skip).limit(limit).all()
            logger.info(f"成功获取工作流列表: 数量={len(workflows)}")
            return workflows
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 获取工作流列表失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"数据库查询失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"获取工作流列表失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    @log_execution
    def update_workflow(self, workflow_id: int, workflow_data: WorkflowUpdate) -> Optional[Workflow]:
        """更新工作流"""
        logger.info(f"更新工作流: ID={workflow_id}")
        
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                logger.warning(f"工作流不存在，无法更新: ID={workflow_id}")
                return None
            
            # 验证更新数据
            update_data = workflow_data.dict(exclude_unset=True)
            if not update_data:
                logger.warning(f"没有提供有效的更新数据: ID={workflow_id}")
                return workflow
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(workflow, key):
                    setattr(workflow, key, value)
                else:
                    logger.warning(f"工作流模型没有属性: {key}")
            
            workflow.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(workflow)
            
            logger.info(f"工作流更新成功: ID={workflow_id}")
            return workflow
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 更新工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"更新工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    
    @log_execution
    def delete_workflow(self, workflow_id: int) -> bool:
        """删除工作流"""
        logger.info(f"删除工作流: ID={workflow_id}")
        
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                logger.warning(f"工作流不存在，无法删除: ID={workflow_id}")
                return False
            
            self.db.delete(workflow)
            self.db.commit()
            
            logger.info(f"工作流删除成功: ID={workflow_id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 删除工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"删除工作流失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    
    def create_execution(self, execution_data: WorkflowExecutionCreate, user_id: Optional[int] = None) -> WorkflowExecution:
        """创建工作流执行实例"""
        logger.info(f"创建工作流执行实例: workflow_id={execution_data.workflow_id}")
        
        # 验证工作流是否存在
        workflow = self.get_workflow(execution_data.workflow_id)
        if not workflow:
            error_msg = f"工作流不存在: ID={execution_data.workflow_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            execution = WorkflowExecution(
                workflow_id=execution_data.workflow_id,
                input_data=execution_data.input_data or {},
                status="running",
                started_at=datetime.utcnow(),
                created_by=user_id
            )
            
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)
            
            logger.info(f"工作流执行实例创建成功: ID={execution.id}, workflow_id={execution_data.workflow_id}")
            return execution
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 创建工作流执行实例失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"创建工作流执行实例失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    
    def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """获取工作流执行详情"""
        logger.info(f"获取工作流执行详情: ID={execution_id}")
        
        try:
            execution = self.db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
            
            if execution:
                logger.info(f"成功获取工作流执行: ID={execution_id}, 状态={execution.status}")
            else:
                logger.warning(f"工作流执行不存在: ID={execution_id}")
                
            return execution
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 获取工作流执行失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"数据库查询失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"获取工作流执行失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise

    @log_execution
    def get_executions(self, skip: int = 0, limit: int = 100) -> List[WorkflowExecution]:
        """获取工作流执行列表"""
        logger.info(f"获取工作流执行列表: skip={skip}, limit={limit}")
        
        # 验证参数
        if skip < 0:
            skip = 0
        if limit <= 0 or limit > 1000:
            limit = 100
            logger.warning(f"limit参数超出范围，使用默认值: {limit}")
        
        try:
            executions = self.db.query(WorkflowExecution).order_by(WorkflowExecution.started_at.desc()).offset(skip).limit(limit).all()
            logger.info(f"成功获取工作流执行列表: 数量={len(executions)}")
            return executions
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 获取工作流执行列表失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"数据库查询失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"获取工作流执行列表失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    def update_execution_status(self, execution_id: int, status: str, output_data: Optional[Dict[str, Any]] = None) -> bool:
        """更新工作流执行状态"""
        logger.info(f"更新工作流执行状态: ID={execution_id}, 状态={status}")
        
        # 验证状态值
        valid_statuses = ["running", "completed", "failed", "canceled", "paused"]
        if status not in valid_statuses:
            error_msg = f"无效的状态值: {status}, 有效状态: {valid_statuses}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            execution = self.get_execution(execution_id)
            if not execution:
                logger.warning(f"工作流执行不存在，无法更新状态: ID={execution_id}")
                return False
            
            execution.status = status
            if output_data is not None:
                execution.output_data = output_data
            if status in ["completed", "failed", "canceled"]:
                execution.completed_at = datetime.utcnow()
                
            self.db.commit()
            
            logger.info(f"工作流执行状态更新成功: ID={execution_id}, 新状态={status}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 更新工作流执行状态失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"更新工作流执行状态失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    
    def create_node_execution(self, execution_id: int, node_id: str, node_type: str, input_data: Optional[Dict[str, Any]] = None) -> NodeExecution:
        """创建节点执行记录"""
        logger.info(f"创建节点执行记录: execution_id={execution_id}, node_id={node_id}, node_type={node_type}")
        
        # 验证执行实例是否存在
        execution = self.get_execution(execution_id)
        if not execution:
            error_msg = f"工作流执行实例不存在: ID={execution_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            node_execution = NodeExecution(
                workflow_execution_id=execution_id,
                node_id=node_id,
                node_type=node_type,
                input_data=input_data,
                status="running",
                started_at=datetime.utcnow()
            )
            
            self.db.add(node_execution)
            self.db.commit()
            self.db.refresh(node_execution)
            
            logger.info(f"节点执行记录创建成功: ID={node_execution.id}, node_id={node_id}")
            return node_execution
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 创建节点执行记录失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"创建节点执行记录失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise
    
    def update_node_execution(self, node_execution_id: int, status: str, output_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> bool:
        """更新节点执行记录"""
        logger.info(f"更新节点执行记录: ID={node_execution_id}, 状态={status}")
        
        # 验证状态值
        valid_statuses = ["running", "completed", "failed"]
        if status not in valid_statuses:
            error_msg = f"无效的状态值: {status}, 有效状态: {valid_statuses}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            node_execution = self.db.query(NodeExecution).filter(NodeExecution.id == node_execution_id).first()
            if not node_execution:
                logger.warning(f"节点执行记录不存在，无法更新: ID={node_execution_id}")
                return False
            
            node_execution.status = status
            if output_data is not None:
                node_execution.output_data = output_data
            if error_message:
                node_execution.error_message = error_message
            if status in ["completed", "failed"]:
                node_execution.completed_at = datetime.utcnow()
                
            self.db.commit()
            
            logger.info(f"节点执行记录更新成功: ID={node_execution_id}, 新状态={status}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库错误 - 更新节点执行记录失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise ValueError(f"数据库操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"更新节点执行记录失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.db.rollback()
            raise

class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow_service = WorkflowService(db)
        self.node_executors = {}
        self.register_node_executors()
    
    def register_node_executors(self):
        """注册节点执行器"""
        logger.info("开始注册节点执行器")
        
        try:
            from .node_executors import (
                StartNodeExecutor,
                EndNodeExecutor,
                InputNodeExecutor,
                OutputNodeExecutor,
                KnowledgeSearchExecutor,
                EntityExtractionExecutor,
                RelationshipAnalysisExecutor,
                BranchNodeExecutor,
                ConditionNodeExecutor,
                ProcessNodeExecutor
            )
            
            # 定义节点执行器映射
            executor_classes = {
                "start": StartNodeExecutor,
                "end": EndNodeExecutor,
                "input": InputNodeExecutor,
                "output": OutputNodeExecutor,
                "knowledge_search": KnowledgeSearchExecutor,
                "entity_extraction": EntityExtractionExecutor,
                "relationship_analysis": RelationshipAnalysisExecutor,
                "branch": BranchNodeExecutor,
                "condition": ConditionNodeExecutor,
                "process": ProcessNodeExecutor
            }
            
            # 创建执行器实例
            self.node_executors = {}
            for node_type, executor_class in executor_classes.items():
                try:
                    executor_instance = executor_class(self.db)
                    self.node_executors[node_type] = executor_instance
                    logger.info(f"成功注册节点执行器: {node_type}")
                except Exception as executor_error:
                    logger.error(f"注册节点执行器失败: {node_type}, 错误: {str(executor_error)}")
                    logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            if not self.node_executors:
                logger.warning("没有成功注册任何节点执行器")
            else:
                logger.info(f"成功注册节点执行器: {list(self.node_executors.keys())}")
            
        except ImportError as e:
            logger.error(f"导入节点执行器模块失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.node_executors = {}
            
        except Exception as e:
            logger.error(f"注册节点执行器失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.node_executors = {}
    
    @log_execution
    def execute_workflow(self, workflow_id: int, input_data: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> WorkflowExecution:
        """执行工作流"""
        logger.info(f"开始执行工作流: ID={workflow_id}")
        
        # 验证输入数据
        if input_data is None:
            input_data = {}
            logger.info("使用空的输入数据")
        
        # 验证输入数据类型
        if not isinstance(input_data, dict):
            error_msg = f"输入数据必须是字典类型, 实际类型: {type(input_data)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        execution = None
        
        try:
            # 开始事务
            self.workflow_service.begin_transaction()
            
            # 创建工作流执行实例
            execution_data = WorkflowExecutionCreate(
                workflow_id=workflow_id,
                input_data=input_data
            )
            
            execution = self.workflow_service.create_execution(execution_data, user_id)
            logger.info(f"工作流执行实例创建成功: ID={execution.id}")
            
            # 获取工作流定义
            workflow = self.workflow_service.get_workflow(workflow_id)
            if not workflow:
                error_msg = f"工作流不存在: ID={workflow_id}"
                logger.error(error_msg)
                self.workflow_service.update_execution_status(execution.id, "failed", {"error": error_msg})
                self.workflow_service.commit_transaction()
                raise ValueError(error_msg)
            
            logger.info(f"获取工作流定义成功: 名称={workflow.name}")
            
            # 验证工作流定义
            if not workflow.definition:
                error_msg = "工作流定义为空"
                logger.error(error_msg)
                self.workflow_service.update_execution_status(execution.id, "failed", {"error": error_msg})
                self.workflow_service.commit_transaction()
                raise ValueError(error_msg)
            
            # 提取节点和边
            nodes = workflow.definition.get("nodes", [])
            edges = workflow.definition.get("edges", [])
            
            # 验证节点定义
            if not isinstance(nodes, list):
                error_msg = "工作流节点定义格式错误，应为列表类型"
                logger.error(error_msg)
                self.workflow_service.update_execution_status(execution.id, "failed", {"error": error_msg})
                self.workflow_service.commit_transaction()
                raise ValueError(error_msg)
            
            if len(nodes) == 0:
                error_msg = "工作流节点定义为空，无法执行"
                logger.error(error_msg)
                self.workflow_service.update_execution_status(execution.id, "failed", {"error": error_msg})
                self.workflow_service.commit_transaction()
                raise ValueError(error_msg)
            
            # 验证边定义
            if not isinstance(edges, list):
                logger.warning("工作流边定义格式错误，应为列表类型，使用空边列表")
                edges = []
            
            logger.info(f"开始执行工作流: 节点数量={len(nodes)}, 边数量={len(edges)}")
            
            # 按节点连接关系执行工作流
            result = self.execute_workflow_by_connections(execution.id, nodes, edges, input_data)
            
            # 更新执行状态为完成
            self.workflow_service.update_execution_status(execution.id, "completed", result)
            
            # 提交事务
            self.workflow_service.commit_transaction()
            logger.info(f"工作流执行完成: ID={execution.id}")
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 回滚事务
            self.workflow_service.rollback_transaction()
            
            # 确保执行实例存在后再更新状态
            if execution:
                try:
                    # 在回滚后重新创建执行记录以记录失败状态
                    execution_data = WorkflowExecutionCreate(
                        workflow_id=workflow_id,
                        input_data=input_data
                    )
                    execution = self.workflow_service.create_execution(execution_data, user_id)
                    self.workflow_service.update_execution_status(execution.id, "failed", {"error": str(e)})
                except Exception as recovery_error:
                    logger.error(f"恢复执行记录失败: {str(recovery_error)}")
            
            raise
        
        return execution
    
    def execute_workflow_by_connections(self, execution_id: int, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """按节点连接关系执行工作流"""
        logger.info("开始按节点连接关系执行工作流")
        
        # 将节点列表转换为字典，便于查找
        node_dict = {node['id']: node for node in nodes}
        
        # 构建邻接表，表示节点之间的连接关系
        adjacency_list = {node_id: [] for node_id in node_dict.keys()}
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target and source in adjacency_list:
                adjacency_list[source].append(target)
        
        logger.debug(f"邻接表: {adjacency_list}")
        
        # 查找开始节点
        start_nodes = [node for node in nodes if node.get('type') == 'start']
        if not start_nodes:
            # 如果没有开始节点，使用第一个节点
            start_nodes = [nodes[0]]
            logger.warning("未找到开始节点，使用第一个节点作为开始")
        
        # 执行上下文
        context = input_data.copy()
        
        # 已执行的节点
        executed_nodes = set()
        
        # 执行节点的函数
        def execute_node_recursive(node_id: str):
            """递归执行节点及其后续节点"""
            if node_id in executed_nodes:
                logger.debug(f"节点 {node_id} 已执行，跳过")
                return
            
            executed_nodes.add(node_id)
            node = node_dict.get(node_id)
            if not node:
                logger.warning(f"节点 {node_id} 不存在，跳过")
                return
            
            try:
                # 执行当前节点
                logger.info(f"执行节点: {node_id}")
                result = self.execute_node(execution_id, node, context)
                
                # 将节点执行结果添加到上下文
                if result.get('success'):
                    if 'context_data' in result:
                        context.update(result['context_data'])
                    if 'final_result' in result:
                        context.update(result['final_result'])
                    if 'output_data' in result:
                        context.update(result['output_data'])
                    if 'processed_value' in result and 'output_field' in result:
                        context[result['output_field']] = result['processed_value']
                
                # 执行后续节点
                for next_node_id in adjacency_list[node_id]:
                    logger.debug(f"从节点 {node_id} 连接到节点 {next_node_id}")
                    execute_node_recursive(next_node_id)
                    
            except Exception as e:
                logger.error(f"节点 {node_id} 执行失败: {str(e)}")
                raise
        
        try:
            # 执行所有开始节点
            for start_node in start_nodes:
                execute_node_recursive(start_node['id'])
            
            logger.info(f"工作流执行完成: 已执行 {len(executed_nodes)} 个节点")
            
            return {
                "message": "工作流执行完成",
                "executed_nodes": list(executed_nodes),
                "final_context": context
            }
            
        except Exception as e:
            logger.error(f"按连接关系执行工作流失败: {str(e)}")
            raise
    
    def execute_node(self, execution_id: int, node: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个节点"""
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "unknown")
        # 同时支持config和data属性，以兼容前端ReactFlow的数据结构
        node_config = node.get("config", node.get("data", {}))
        
        logger.info(f"开始执行节点: ID={node_id}, 类型={node_type}")
        
        # 验证节点信息
        if not node_id or node_id == "unknown":
            error_msg = "节点缺少必要的ID信息"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not node_type or node_type == "unknown":
            error_msg = f"节点缺少必要的类型信息: ID={node_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 确保配置是字典类型
        if not isinstance(node_config, dict):
            logger.warning(f"节点配置类型错误: {type(node_config)}, 使用空配置")
            node_config = {}
        
        # 创建节点执行记录
        try:
            node_execution = self.workflow_service.create_node_execution(
                execution_id, node_id, node_type, node_config
            )
            logger.info(f"节点执行记录创建成功: ID={node_execution.id}")
            
        except Exception as e:
            logger.error(f"创建节点执行记录失败: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
        
        try:
            # 获取节点执行器
            executor = self.node_executors.get(node_type)
            if not executor:
                error_msg = f"未知的节点类型: {node_type}, 可用类型: {list(self.node_executors.keys())}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"找到节点执行器: {node_type}")
            
            # 验证执行器是否实现了execute方法
            if not hasattr(executor, 'execute') or not callable(getattr(executor, 'execute')):
                error_msg = f"节点执行器缺少execute方法: {node_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 执行节点
            logger.info(f"开始执行节点逻辑: ID={node_id}")
            logger.debug(f"节点配置: {node_config}")
            logger.debug(f"上下文数据: {context_data}")
            
            result = executor.execute(node_config, context_data)
            
            # 验证执行结果
            if not isinstance(result, dict):
                error_msg = f"节点执行结果格式错误: 期望字典类型, 实际类型={type(result)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            success = result.get("success", False)
            logger.info(f"节点执行完成: ID={node_id}, 成功={success}")
            
            # 更新节点执行记录
            self.workflow_service.update_node_execution(
                node_execution.id, "completed", result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"节点执行失败: ID={node_id}, 类型={node_type}, 错误: {str(e)}")
            logger.error(f"节点配置: {node_config}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 更新节点执行记录为失败状态
            try:
                self.workflow_service.update_node_execution(
                    node_execution.id, "failed", error_message=str(e)
                )
            except Exception as update_error:
                logger.error(f"更新节点执行记录失败: {str(update_error)}")
            
            raise