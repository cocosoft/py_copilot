"""结果整合服务（新增）"""
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.task import Task

logger = logging.getLogger(__name__)


class TaskResultIntegrator:
    """结果整合服务"""
    
    def __init__(self, db: Session):
        """
        初始化结果整合服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def integrate_results(
        self,
        task: Task,
        execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        整合执行结果
        
        Args:
            task: 任务对象
            execution_results: 执行结果列表
            
        Returns:
            整合后的结果
        """
        try:
            integrated = {
                "task_id": task.id,
                "task_type": task.task_type,
                "status": "completed",
                "skills_executed": len(execution_results),
                "results": execution_results,
                "summary": f"成功执行 {len(execution_results)} 个技能"
            }
            
            # 根据任务类型整合结果
            if task.task_type == "translate":
                integrated["translation_result"] = self._integrate_translation_results(execution_results)
            elif task.task_type == "summarize":
                integrated["summary_result"] = self._integrate_summary_results(execution_results)
            elif task.task_type == "analyze":
                integrated["analysis_result"] = self._integrate_analysis_results(execution_results)
            else:
                integrated["general_result"] = self._integrate_general_results(execution_results)
            
            logger.info(f"任务 {task.id} 结果整合完成")
            
            return integrated
            
        except Exception as e:
            logger.error(f"任务 {task.id} 结果整合失败: {e}")
            raise
    
    def _integrate_translation_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        整合翻译结果
        
        Args:
            results: 执行结果列表
            
        Returns:
            整合后的翻译结果
        """
        # 获取最后一个成功的结果
        for result in reversed(results):
            if result.get("status") == "completed" and result.get("result"):
                return {
                    "translated_text": result["result"],
                    "success": True
                }
        
        return {
            "translated_text": None,
            "success": False,
            "error": "翻译失败"
        }
    
    def _integrate_summary_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        整合摘要结果
        
        Args:
            results: 执行结果列表
            
        Returns:
            整合后的摘要结果
        """
        # 获取最后一个成功的结果
        for result in reversed(results):
            if result.get("status") == "completed" and result.get("result"):
                return {
                    "summary": result["result"],
                    "success": True
                }
        
        return {
            "summary": None,
            "success": False,
            "error": "摘要生成失败"
        }
    
    def _integrate_analysis_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        整合分析结果
        
        Args:
            results: 执行结果列表
            
        Returns:
            整合后的分析结果
        """
        # 合并所有成功的分析结果
        analysis_results = []
        for result in results:
            if result.get("status") == "completed" and result.get("result"):
                analysis_results.append(result["result"])
        
        if analysis_results:
            return {
                "analysis": analysis_results,
                "success": True
            }
        
        return {
            "analysis": None,
            "success": False,
            "error": "分析失败"
        }
    
    def _integrate_general_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        整合通用结果
        
        Args:
            results: 执行结果列表
            
        Returns:
            整合后的通用结果
        """
        # 收集所有成功的结果
        successful_results = []
        for result in results:
            if result.get("status") == "completed":
                successful_results.append({
                    "skill": result.get("skill_name"),
                    "result": result.get("result")
                })
        
        return {
            "results": successful_results,
            "success": len(successful_results) > 0
        }
