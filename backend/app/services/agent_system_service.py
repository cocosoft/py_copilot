"""智能体系统主服务"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.agent_task_planner import AgentTaskPlanner, TaskPlan, TaskType, TaskComplexity, TaskStep
from app.services.agent_model_scheduler import AgentModelScheduler, SchedulingResult, ModelSelectionCriteria, SchedulingStrategy
from app.services.tool_integration_service import ToolIntegrationService, ToolExecutionResult
from app.models.agent import Agent


class AgentTaskRequest(BaseModel):
    """智能体任务请求"""
    task_description: str
    agent_id: Optional[int] = None
    task_context: Optional[Dict[str, Any]] = None
    scheduling_strategy: SchedulingStrategy = SchedulingStrategy.BALANCED
    min_capability_strength: int = 3
    max_cost: Optional[float] = None
    max_response_time: Optional[int] = None


class AgentTaskExecution(BaseModel):
    """智能体任务执行结果"""
    task_id: str
    agent_id: int
    task_plan: TaskPlan
    scheduling_result: SchedulingResult
    execution_status: str  # pending, running, completed, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AgentSystemService:
    """智能体系统主服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.task_planner = AgentTaskPlanner(db)
        self.model_scheduler = AgentModelScheduler(db)
        self.tool_service = ToolIntegrationService()
    
    def process_task(self, request: AgentTaskRequest) -> AgentTaskExecution:
        """
        处理智能体任务
        
        Args:
            request: 任务请求
            
        Returns:
            AgentTaskExecution: 任务执行信息
        """
        # 1. 获取或创建智能体
        agent = self._get_or_create_agent(request.agent_id, request.task_description)
        
        # 2. 任务规划
        task_plan = self.task_planner.analyze_task(
            request.task_description, 
            request.task_context
        )
        
        # 3. 模型调度
        criteria = ModelSelectionCriteria(
            required_capabilities=task_plan.required_capabilities,
            min_strength=request.min_capability_strength,
            max_cost=request.max_cost,
            max_response_time=request.max_response_time
        )
        
        scheduling_result = self.model_scheduler.schedule_models(
            task_plan.task_id, 
            criteria, 
            request.scheduling_strategy
        )
        
        # 4. 创建任务执行记录
        execution = AgentTaskExecution(
            task_id=task_plan.task_id,
            agent_id=agent.id,
            task_plan=task_plan,
            scheduling_result=scheduling_result,
            execution_status="pending"
        )
        
        return execution
    
    def execute_task(self, execution: AgentTaskExecution) -> AgentTaskExecution:
        """
        执行智能体任务
        
        Args:
            execution: 任务执行信息
            
        Returns:
            AgentTaskExecution: 更新后的执行信息
        """
        import time
        from datetime import datetime
        
        # 更新执行状态
        execution.execution_status = "running"
        execution.start_time = datetime.now().isoformat()
        
        try:
            # 模拟任务执行过程
            execution_result = self._simulate_task_execution(
                execution.task_plan, 
                execution.scheduling_result
            )
            
            # 更新执行结果
            execution.execution_status = "completed"
            execution.end_time = datetime.now().isoformat()
            execution.execution_result = execution_result
            
            # 记录执行反馈
            self._record_execution_feedback(execution)
            
        except Exception as e:
            # 处理执行错误
            execution.execution_status = "failed"
            execution.end_time = datetime.now().isoformat()
            execution.error_message = str(e)
        
        return execution
    
    def _get_or_create_agent(self, agent_id: Optional[int], task_description: str) -> Agent:
        """获取或创建智能体"""
        if agent_id:
            # 获取现有智能体
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                return agent
        
        # 创建新的通用智能体
        from app.schemas.agent import AgentCreate
        from app.services.agent_service import create_agent
        
        # 基于任务描述生成智能体名称和提示
        agent_name = self._generate_agent_name(task_description)
        agent_prompt = self._generate_agent_prompt(task_description)
        
        agent_create = AgentCreate(
            name=agent_name,
            description=f"处理'{task_description}'任务的智能体",
            prompt=agent_prompt,
            is_public=True
        )
        
        # 使用默认用户ID创建智能体
        agent = create_agent(self.db, agent_create, user_id=1)
        return agent
    
    def _generate_agent_name(self, task_description: str) -> str:
        """基于任务描述生成智能体名称"""
        # 简单的名称生成逻辑
        keywords = task_description.split()[:3]
        base_name = "_".join(keywords).lower()
        return f"agent_{base_name}"
    
    def _generate_agent_prompt(self, task_description: str) -> str:
        """基于任务描述生成智能体提示"""
        return f"""你是一个专门处理以下任务的智能体：

任务描述：{task_description}

请根据任务需求，使用最合适的模型和工具来完成工作。确保结果准确、高效。"""
    
    def _simulate_task_execution(self, task_plan: TaskPlan, scheduling_result: SchedulingResult) -> Dict[str, Any]:
        """模拟任务执行过程（集成工具调用）"""
        import time
        
        execution_steps = []
        tool_results = []
        
        # 按步骤执行任务
        for step in task_plan.steps:
            step_result = {
                "step_id": step.step_id,
                "description": step.description,
                "status": "completed",
                "duration": step.estimated_duration,
                "model_used": scheduling_result.primary_model.model_name,
                "result": f"成功完成步骤 {step.step_id}: {step.description}"
            }
            
            # 检查步骤是否需要工具调用
            tool_usage = self._check_tool_requirements(step.description)
            if tool_usage:
                tool_result = self._execute_tool_for_step(step, tool_usage)
                if tool_result:
                    step_result["tool_used"] = tool_usage["tool_name"]
                    step_result["tool_result"] = tool_result
                    tool_results.append({
                        "step_id": step.step_id,
                        "tool_name": tool_usage["tool_name"],
                        "result": tool_result
                    })
            
            execution_steps.append(step_result)
            
            # 模拟执行时间
            time.sleep(0.1)  # 实际应用中应该使用真实的模型调用
        
        # 生成最终结果
        return {
            "execution_steps": execution_steps,
            "tool_results": tool_results,
            "total_steps": len(task_plan.steps),
            "successful_steps": len(execution_steps),
            "failed_steps": 0,
            "primary_model": scheduling_result.primary_model.model_name,
            "total_cost": scheduling_result.total_estimated_cost,
            "total_time": scheduling_result.total_estimated_time
        }
    
    def _check_tool_requirements(self, step_description: str) -> Optional[Dict[str, Any]]:
        """检查步骤是否需要工具调用"""
        description_lower = step_description.lower()
        
        # 文本处理相关工具
        if any(keyword in description_lower for keyword in ["摘要", "总结", "概括", "summarize", "summary"]):
            return {
                "tool_name": "text_summarizer",
                "parameters": {"text": "需要摘要的文本内容"}
            }
        
        # 代码相关工具
        elif any(keyword in description_lower for keyword in ["代码", "编程", "format", "格式化", "code"]):
            return {
                "tool_name": "code_formatter",
                "parameters": {"code": "需要格式化的代码", "language": "python"}
            }
        
        # 数据分析相关工具
        elif any(keyword in description_lower for keyword in ["数据", "分析", "统计", "data", "analyze"]):
            return {
                "tool_name": "data_analyzer",
                "parameters": {"data": "需要分析的数据", "analysis_type": "statistics"}
            }
        
        # JSON处理相关工具
        elif any(keyword in description_lower for keyword in ["json", "解析", "parse", "格式化"]):
            return {
                "tool_name": "json_parser",
                "parameters": {"json_string": "需要解析的JSON字符串", "format": True}
            }
        
        # 内容生成相关工具
        elif any(keyword in description_lower for keyword in ["生成", "创建", "写", "generate", "create"]):
            return {
                "tool_name": "content_generator",
                "parameters": {"keywords": "关键词", "content_type": "article", "length": 500}
            }
        
        return None
    
    def _execute_tool_for_step(self, step: TaskStep, tool_usage: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """为步骤执行工具"""
        try:
            # 在实际实现中，这里应该根据步骤内容动态生成参数
            # 这里使用简化的参数生成逻辑
            tool_name = tool_usage["tool_name"]
            base_parameters = tool_usage["parameters"]
            
            # 根据步骤描述调整参数
            adjusted_parameters = self._adjust_tool_parameters(step.description, base_parameters)
            
            # 执行工具
            result = self.tool_service.execute_tool(tool_name, adjusted_parameters)
            
            if result.success:
                return {
                    "success": True,
                    "result": result.result,
                    "execution_time": result.execution_time
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "execution_time": result.execution_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0.0
            }
    
    def _adjust_tool_parameters(self, step_description: str, base_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """根据步骤描述调整工具参数"""
        # 在实际实现中，这里应该使用更智能的参数调整逻辑
        # 这里返回基础参数作为示例
        return base_parameters
    
    def _record_execution_feedback(self, execution: AgentTaskExecution):
        """记录任务执行反馈"""
        # 这里可以记录执行结果用于后续的学习和优化
        # 实际实现中应该存储到数据库
        
        feedback_data = {
            "task_id": execution.task_id,
            "agent_id": execution.agent_id,
            "execution_status": execution.execution_status,
            "primary_model": execution.scheduling_result.primary_model.model_name,
            "total_cost": execution.scheduling_result.total_estimated_cost,
            "total_time": execution.scheduling_result.total_estimated_time,
            "success_rate": 1.0 if execution.execution_status == "completed" else 0.0
        }
        
        # 在实际实现中，这里应该将反馈数据存储到数据库
        # self.db.add(ExecutionFeedback(**feedback_data))
        # self.db.commit()
    
    def get_agent_performance(self, agent_id: int) -> Dict[str, Any]:
        """获取智能体性能统计"""
        # 在实际实现中，这里应该从数据库查询执行历史
        # 这里返回模拟数据
        
        return {
            "agent_id": agent_id,
            "total_tasks": 10,
            "completed_tasks": 8,
            "failed_tasks": 2,
            "success_rate": 0.8,
            "average_cost": 0.05,
            "average_time": 120,
            "preferred_models": ["gpt-4", "claude-3"],
            "common_task_types": ["text_generation", "code_generation"]
        }
    
    def optimize_agent_strategy(self, agent_id: int) -> Dict[str, Any]:
        """优化智能体策略"""
        # 基于历史执行数据优化智能体的模型选择策略
        performance_data = self.get_agent_performance(agent_id)
        
        optimization_suggestions = []
        
        if performance_data["success_rate"] < 0.9:
            optimization_suggestions.append(
                "建议使用能力优先策略提高任务成功率"
            )
        
        if performance_data["average_cost"] > 0.1:
            optimization_suggestions.append(
                "建议使用成本优先策略降低执行成本"
            )
        
        if performance_data["average_time"] > 300:
            optimization_suggestions.append(
                "建议使用性能优先策略减少响应时间"
            )
        
        return {
            "agent_id": agent_id,
            "optimization_suggestions": optimization_suggestions,
            "recommended_strategy": self._recommend_best_strategy(performance_data)
        }
    
    def _recommend_best_strategy(self, performance_data: Dict[str, Any]) -> SchedulingStrategy:
        """推荐最佳调度策略"""
        success_rate = performance_data["success_rate"]
        avg_cost = performance_data["average_cost"]
        avg_time = performance_data["average_time"]
        
        if success_rate < 0.8:
            return SchedulingStrategy.CAPABILITY_FIRST
        elif avg_cost > 0.08:
            return SchedulingStrategy.COST_EFFECTIVE
        elif avg_time > 200:
            return SchedulingStrategy.PERFORMANCE_OPTIMIZED
        else:
            return SchedulingStrategy.BALANCED