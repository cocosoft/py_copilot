"""智能体任务规划器服务"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.model_capability import ModelCapability
from app.services.capability_assessment_service import CapabilityAssessmentService


class TaskType(Enum):
    """任务类型枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    IMAGE_PROCESSING = "image_processing"
    TOOL_CALLING = "tool_calling"
    MULTIMODAL = "multimodal"
    CONVERSATION = "conversation"


class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = "simple"  # 简单任务，单步骤
    MODERATE = "moderate"  # 中等复杂度，2-3个步骤
    COMPLEX = "complex"  # 复杂任务，多步骤，需要规划


class TaskStep(BaseModel):
    """任务步骤定义"""
    step_id: int
    description: str
    required_capabilities: List[str]
    estimated_duration: int  # 预估耗时（秒）
    dependencies: List[int]  # 依赖的步骤ID
    priority: int  # 优先级（1-10，10最高）


class TaskPlan(BaseModel):
    """任务规划结果"""
    task_id: str
    task_type: TaskType
    complexity: TaskComplexity
    steps: List[TaskStep]
    estimated_total_duration: int
    required_capabilities: List[str]
    critical_path: List[int]  # 关键路径步骤ID


class AgentTaskPlanner:
    """智能体任务规划器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.capability_service = CapabilityAssessmentService()
    
    def analyze_task(self, task_description: str, task_context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        分析任务并生成规划
        
        Args:
            task_description: 任务描述
            task_context: 任务上下文信息
            
        Returns:
            TaskPlan: 任务规划结果
        """
        # 1. 识别任务类型
        task_type = self._identify_task_type(task_description, task_context)
        
        # 2. 评估任务复杂度
        complexity = self._assess_complexity(task_description, task_context)
        
        # 3. 分解任务步骤
        steps = self._decompose_task(task_description, task_type, complexity, task_context)
        
        # 4. 识别所需能力
        required_capabilities = self._identify_required_capabilities(steps)
        
        # 5. 计算关键路径
        critical_path = self._calculate_critical_path(steps)
        
        # 6. 生成任务规划
        task_plan = TaskPlan(
            task_id=self._generate_task_id(),
            task_type=task_type,
            complexity=complexity,
            steps=steps,
            estimated_total_duration=sum(step.estimated_duration for step in steps),
            required_capabilities=required_capabilities,
            critical_path=critical_path
        )
        
        return task_plan
    
    def _identify_task_type(self, task_description: str, task_context: Optional[Dict[str, Any]]) -> TaskType:
        """识别任务类型"""
        description_lower = task_description.lower()
        
        if any(keyword in description_lower for keyword in ["代码", "编程", "开发", "程序"]):
            return TaskType.CODE_GENERATION
        elif any(keyword in description_lower for keyword in ["图片", "图像", "视觉", "照片"]):
            return TaskType.IMAGE_PROCESSING
        elif any(keyword in description_lower for keyword in ["数据", "分析", "统计", "报表"]):
            return TaskType.DATA_ANALYSIS
        elif any(keyword in description_lower for keyword in ["工具", "调用", "执行", "运行"]):
            return TaskType.TOOL_CALLING
        elif any(keyword in description_lower for keyword in ["多模态", "多媒体", "混合"]):
            return TaskType.MULTIMODAL
        elif any(keyword in description_lower for keyword in ["对话", "聊天", "问答"]):
            return TaskType.CONVERSATION
        else:
            return TaskType.TEXT_GENERATION
    
    def _assess_complexity(self, task_description: str, task_context: Optional[Dict[str, Any]]) -> TaskComplexity:
        """评估任务复杂度"""
        # 基于任务描述长度和关键词数量进行简单评估
        word_count = len(task_description.split())
        
        if word_count < 20:
            return TaskComplexity.SIMPLE
        elif word_count < 50:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.COMPLEX
    
    def _decompose_task(self, task_description: str, task_type: TaskType, 
                       complexity: TaskComplexity, task_context: Optional[Dict[str, Any]]) -> List[TaskStep]:
        """分解任务为步骤"""
        steps = []
        
        if complexity == TaskComplexity.SIMPLE:
            # 简单任务：单步骤
            steps.append(TaskStep(
                step_id=1,
                description=task_description,
                required_capabilities=self._get_capabilities_for_task_type(task_type),
                estimated_duration=60,  # 1分钟
                dependencies=[],
                priority=5
            ))
        elif complexity == TaskComplexity.MODERATE:
            # 中等复杂度：2-3个步骤
            steps.append(TaskStep(
                step_id=1,
                description="分析任务需求",
                required_capabilities=["comprehension", "analysis"],
                estimated_duration=30,
                dependencies=[],
                priority=8
            ))
            steps.append(TaskStep(
                step_id=2,
                description="执行主要任务",
                required_capabilities=self._get_capabilities_for_task_type(task_type),
                estimated_duration=120,
                dependencies=[1],
                priority=10
            ))
        else:
            # 复杂任务：多步骤规划
            steps.append(TaskStep(
                step_id=1,
                description="需求分析和规划",
                required_capabilities=["comprehension", "planning"],
                estimated_duration=60,
                dependencies=[],
                priority=9
            ))
            steps.append(TaskStep(
                step_id=2,
                description="数据准备和处理",
                required_capabilities=["data_processing"],
                estimated_duration=90,
                dependencies=[1],
                priority=7
            ))
            steps.append(TaskStep(
                step_id=3,
                description="核心任务执行",
                required_capabilities=self._get_capabilities_for_task_type(task_type),
                estimated_duration=180,
                dependencies=[1, 2],
                priority=10
            ))
            steps.append(TaskStep(
                step_id=4,
                description="结果验证和优化",
                required_capabilities=["evaluation", "optimization"],
                estimated_duration=60,
                dependencies=[3],
                priority=6
            ))
        
        return steps
    
    def _get_capabilities_for_task_type(self, task_type: TaskType) -> List[str]:
        """根据任务类型获取所需能力"""
        capability_mapping = {
            TaskType.TEXT_GENERATION: ["text_generation"],
            TaskType.CODE_GENERATION: ["code_generation", "programming"],
            TaskType.DATA_ANALYSIS: ["data_analysis", "reasoning"],
            TaskType.IMAGE_PROCESSING: ["image_processing", "vision"],
            TaskType.TOOL_CALLING: ["tool_calling", "execution"],
            TaskType.MULTIMODAL: ["multimodal", "text_generation", "image_processing"],
            TaskType.CONVERSATION: ["conversation", "interaction"]
        }
        return capability_mapping.get(task_type, ["text_generation"])
    
    def _identify_required_capabilities(self, steps: List[TaskStep]) -> List[str]:
        """识别所有步骤所需的能力"""
        all_capabilities = set()
        for step in steps:
            all_capabilities.update(step.required_capabilities)
        return list(all_capabilities)
    
    def _calculate_critical_path(self, steps: List[TaskStep]) -> List[int]:
        """计算关键路径"""
        # 简单的关键路径计算：选择优先级最高且依赖最少的步骤
        critical_steps = []
        
        # 首先处理没有依赖的步骤
        independent_steps = [step for step in steps if not step.dependencies]
        if independent_steps:
            critical_steps.append(max(independent_steps, key=lambda x: x.priority).step_id)
        
        # 然后处理依赖步骤
        dependent_steps = [step for step in steps if step.dependencies]
        if dependent_steps:
            critical_steps.append(max(dependent_steps, key=lambda x: x.priority).step_id)
        
        return critical_steps
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"task_{uuid.uuid4().hex[:8]}"
    
    def optimize_plan(self, task_plan: TaskPlan, available_resources: Dict[str, Any]) -> TaskPlan:
        """
        基于可用资源优化任务规划
        
        Args:
            task_plan: 原始任务规划
            available_resources: 可用资源信息
            
        Returns:
            TaskPlan: 优化后的任务规划
        """
        # 根据资源限制调整预估时间
        resource_factor = available_resources.get("resource_factor", 1.0)
        
        optimized_steps = []
        for step in task_plan.steps:
            optimized_step = TaskStep(
                step_id=step.step_id,
                description=step.description,
                required_capabilities=step.required_capabilities,
                estimated_duration=int(step.estimated_duration * resource_factor),
                dependencies=step.dependencies,
                priority=step.priority
            )
            optimized_steps.append(optimized_step)
        
        # 更新任务规划
        optimized_plan = TaskPlan(
            task_id=task_plan.task_id,
            task_type=task_plan.task_type,
            complexity=task_plan.complexity,
            steps=optimized_steps,
            estimated_total_duration=sum(step.estimated_duration for step in optimized_steps),
            required_capabilities=task_plan.required_capabilities,
            critical_path=task_plan.critical_path
        )
        
        return optimized_plan