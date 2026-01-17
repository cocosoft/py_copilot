"""工作流监控服务"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import json
import logging

# 导入工作流模型
from ..models.workflow import Workflow, WorkflowExecution, WorkflowNode, NodeExecution

logger = logging.getLogger(__name__)

class WorkflowMonitoringService:
    """工作流监控服务类"""
    
    def __init__(self, db: Session):
        """初始化工作流监控服务"""
        self.db = db
    
    def get_running_workflows(self) -> List[Dict[str, Any]]:
        """
        获取正在运行的工作流
        
        Returns:
            正在运行的工作流列表
        """
        try:
            logger.info("获取正在运行的工作流")
            
            # 查询状态为running的工作流执行
            running_executions = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.status == "running"
            ).order_by(desc(WorkflowExecution.started_at)).all()
            
            result = []
            for execution in running_executions:
                # 获取对应的工作流信息
                workflow = self.db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
                if workflow:
                    # 获取当前执行的节点
                    current_nodes = self.db.query(NodeExecution).filter(
                        NodeExecution.workflow_execution_id == execution.id,
                        NodeExecution.status == "running"
                    ).all()
                    
                    result.append({
                        "execution_id": execution.id,
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "status": execution.status,
                        "started_at": execution.started_at,
                        "runtime": str(datetime.utcnow() - execution.started_at).split(".")[0],
                        "input_data": execution.input_data,
                        "current_nodes": [node.node_id for node in current_nodes],
                        "created_by": execution.created_by
                    })
            
            logger.info(f"获取正在运行的工作流成功: 数量={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"获取正在运行的工作流失败: {str(e)}")
            raise
    
    def get_workflow_execution_history(self, workflow_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取工作流执行历史
        
        Args:
            workflow_id: 工作流ID
            days: 查询天数
            
        Returns:
            工作流执行历史列表
        """
        try:
            logger.info(f"获取工作流执行历史: workflow_id={workflow_id}, days={days}")
            
            # 计算日期范围
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 查询指定工作流的执行历史
            executions = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.started_at >= start_date
            ).order_by(desc(WorkflowExecution.started_at)).all()
            
            result = []
            for execution in executions:
                # 计算执行时间
                execution_time = ""
                if execution.completed_at:
                    execution_time = str(execution.completed_at - execution.started_at).split(".")[0]
                
                # 获取节点执行数量
                node_execution_count = self.db.query(NodeExecution).filter(
                    NodeExecution.workflow_execution_id == execution.id
                ).count()
                
                # 获取成功和失败的节点数量
                successful_nodes = self.db.query(NodeExecution).filter(
                    NodeExecution.workflow_execution_id == execution.id,
                    NodeExecution.status == "completed"
                ).count()
                
                failed_nodes = self.db.query(NodeExecution).filter(
                    NodeExecution.workflow_execution_id == execution.id,
                    NodeExecution.status == "failed"
                ).count()
                
                result.append({
                    "execution_id": execution.id,
                    "status": execution.status,
                    "started_at": execution.started_at,
                    "completed_at": execution.completed_at,
                    "execution_time": execution_time,
                    "input_data": execution.input_data,
                    "output_data": execution.output_data,
                    "node_count": node_execution_count,
                    "successful_nodes": successful_nodes,
                    "failed_nodes": failed_nodes,
                    "created_by": execution.created_by
                })
            
            logger.info(f"获取工作流执行历史成功: 数量={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"获取工作流执行历史失败: {str(e)}")
            raise
    
    def get_workflow_statistics(self, workflow_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        获取工作流统计信息
        
        Args:
            workflow_id: 工作流ID（可选，不提供则统计所有工作流）
            days: 查询天数
            
        Returns:
            工作流统计信息
        """
        try:
            logger.info(f"获取工作流统计信息: workflow_id={workflow_id}, days={days}")
            
            # 计算日期范围
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询条件
            query = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.started_at >= start_date
            )
            
            if workflow_id:
                query = query.filter(WorkflowExecution.workflow_id == workflow_id)
            
            # 获取所有符合条件的执行
            all_executions = query.all()
            total_executions = len(all_executions)
            
            # 按状态统计
            status_counts = {}
            for status in ["running", "completed", "failed", "canceled", "paused"]:
                status_counts[status] = 0
            
            # 计算平均执行时间
            total_execution_time = 0
            completed_count = 0
            
            for execution in all_executions:
                status_counts[execution.status] += 1
                
                if execution.completed_at and execution.status == "completed":
                    total_execution_time += (execution.completed_at - execution.started_at).total_seconds()
                    completed_count += 1
            
            # 计算平均执行时间
            average_execution_time = 0
            if completed_count > 0:
                average_execution_time = total_execution_time / completed_count
            
            # 计算成功率
            success_rate = 0
            if total_executions > 0:
                success_rate = (status_counts["completed"] / total_executions) * 100
            
            result = {
                "time_range": {
                    "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "days": days
                },
                "total_executions": total_executions,
                "status_counts": status_counts,
                "success_rate": round(success_rate, 2),
                "average_execution_time": round(average_execution_time, 2),  # 秒
                "completed_count": completed_count,
                "failed_count": status_counts["failed"]
            }
            
            logger.info("获取工作流统计信息成功")
            return result
            
        except Exception as e:
            logger.error(f"获取工作流统计信息失败: {str(e)}")
            raise
    
    def get_execution_logs(self, execution_id: int) -> Dict[str, Any]:
        """
        获取工作流执行日志
        
        Args:
            execution_id: 工作流执行ID
            
        Returns:
            工作流执行日志
        """
        try:
            logger.info(f"获取工作流执行日志: execution_id={execution_id}")
            
            # 获取工作流执行信息
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()
            
            if not execution:
                raise ValueError(f"工作流执行不存在: ID={execution_id}")
            
            # 获取工作流信息
            workflow = self.db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
            
            # 获取所有节点执行记录
            node_executions = self.db.query(NodeExecution).filter(
                NodeExecution.workflow_execution_id == execution_id
            ).order_by(NodeExecution.id).all()
            
            # 构建日志结果
            node_logs = []
            for node_exec in node_executions:
                # 计算节点执行时间
                execution_time = 0
                if node_exec.completed_at and node_exec.started_at:
                    execution_time = (node_exec.completed_at - node_exec.started_at).total_seconds()
                
                node_logs.append({
                    "node_id": node_exec.node_id,
                    "node_type": node_exec.node_type,
                    "status": node_exec.status,
                    "input_data": node_exec.input_data,
                    "output_data": node_exec.output_data,
                    "error_message": node_exec.error_message,
                    "started_at": node_exec.started_at,
                    "completed_at": node_exec.completed_at,
                    "execution_time": round(execution_time, 2) if execution_time else None
                })
            
            result = {
                "execution_id": execution.id,
                "workflow_id": execution.workflow_id,
                "workflow_name": workflow.name if workflow else None,
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "input_data": execution.input_data,
                "output_data": execution.output_data,
                "node_logs": node_logs,
                "created_by": execution.created_by
            }
            
            logger.info("获取工作流执行日志成功")
            return result
            
        except Exception as e:
            logger.error(f"获取工作流执行日志失败: {str(e)}")
            raise
    
    def get_recent_failed_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近失败的工作流执行
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最近失败的工作流执行列表
        """
        try:
            logger.info(f"获取最近失败的工作流执行: limit={limit}")
            
            # 查询最近失败的工作流执行
            failed_executions = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.status == "failed"
            ).order_by(desc(WorkflowExecution.completed_at)).limit(limit).all()
            
            result = []
            for execution in failed_executions:
                # 获取对应的工作流信息
                workflow = self.db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
                if workflow:
                    # 获取失败的节点
                    failed_nodes = self.db.query(NodeExecution).filter(
                        NodeExecution.workflow_execution_id == execution.id,
                        NodeExecution.status == "failed"
                    ).all()
                    
                    # 获取第一个失败节点的错误信息
                    error_message = None
                    if failed_nodes:
                        error_message = failed_nodes[0].error_message
                    
                    result.append({
                        "execution_id": execution.id,
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "status": execution.status,
                        "started_at": execution.started_at,
                        "completed_at": execution.completed_at,
                        "execution_time": str(execution.completed_at - execution.started_at).split(".")[0],
                        "error_message": error_message,
                        "failed_nodes": [node.node_id for node in failed_nodes],
                        "created_by": execution.created_by
                    })
            
            logger.info(f"获取最近失败的工作流执行成功: 数量={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"获取最近失败的工作流执行失败: {str(e)}")
            raise
