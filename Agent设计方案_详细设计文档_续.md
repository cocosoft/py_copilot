

---

## 三、智能编排引擎设计

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    智能编排引擎架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              IntelligentOrchestrator                    │   │
│  │                  (智能编排引擎)                          │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  输入: 用户输入 + 上下文 ──────┐                        │   │
│  │                               ▼                        │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              IntentUnderstanding                 │   │   │
│  │  │                (意图理解层)                       │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 意图分类器   │ │ 实体提取器   │ │ 场景识别器   │ │   │   │
│  │  │  │             │ │             │ │             │ │   │   │
│  │  │  │ • 任务类型   │ │ • 关键参数   │ │ • 用户场景   │ │   │   │
│  │  │  │ • 紧急程度   │ │ • 约束条件   │ │ • 时间上下文 │ │   │   │
│  │  │  │ • 复杂程度   │ │ • 目标对象   │ │ • 历史场景   │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                               │                        │   │
│  │                               ▼                        │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │               TaskPlanner                        │   │   │
│  │  │                (任务规划层)                       │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 任务分解器   │ │ 依赖分析器   │ │ 执行优化器   │ │   │   │
│  │  │  │             │ │             │ │             │ │   │   │
│  │  │  │ • 原子任务   │ │ • 数据依赖   │ │ • 并行识别   │ │   │   │
│  │  │  │ • 子任务链   │ │ • 执行顺序   │ │ • 资源分配   │ │   │   │
│  │  │  │ • 任务边界   │ │ • 条件分支   │ │ • 时间估算   │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                               │                        │   │
│  │                               ▼                        │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │            CapabilityOrchestrator                │   │   │
│  │  │               (能力编排层)                        │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 能力发现器   │ │ 能力选择器   │ │ 能力编排器   │ │   │   │
│  │  │  │             │ │             │ │             │ │   │   │
│  │  │  │ • 语义匹配   │ │ • 评分算法   │ │ • 执行计划   │ │   │   │
│  │  │  │ • 历史匹配   │ │ • 成功率权重 │ │ • 回退策略   │ │   │   │
│  │  │  │ • 场景匹配   │ │ • 性能权重   │ │ • 结果融合   │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                               │                        │   │
│  │                               ▼                        │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │            ExecutionEngine                       │   │   │
│  │  │               (执行引擎层)                        │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 执行调度器   │ │ 监控器       │ │ 容错处理器   │ │   │   │
│  │  │  │             │ │             │ │             │ │   │   │
│  │  │  │ • 顺序执行   │ │ • 进度追踪   │ │ • 重试机制   │ │   │   │
│  │  │  │ • 并行执行   │ │ • 性能监控   │ │ • 降级策略   │ │   │   │
│  │  │  │ • 条件执行   │ │ • 异常告警   │ │ • 回滚机制   │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                               │                        │   │
│  │                               ▼                        │   │
│  │  输出: 执行结果 + 执行报告 + 记忆更新                    │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 详细代码实现

#### 3.2.1 意图理解模块

```python
# app/orchestration/intent_understanding.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import re

from app.services.llm_service import LLMService


class IntentType(Enum):
    """意图类型枚举"""
    INFORMATION_QUERY = "information_query"      # 信息查询
    TASK_EXECUTION = "task_execution"            # 任务执行
    CONTENT_CREATION = "content_creation"        # 内容创作
    DATA_ANALYSIS = "data_analysis"              # 数据分析
    CONVERSATION = "conversation"                # 闲聊对话
    MULTI_STEP_TASK = "multi_step_task"          # 多步骤任务


class UrgencyLevel(Enum):
    """紧急程度枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ComplexityLevel(Enum):
    """复杂程度枚举"""
    SIMPLE = 1       # 单一步骤
    MODERATE = 2     # 2-3个步骤
    COMPLEX = 3      # 多个步骤，有依赖
    VERY_COMPLEX = 4 # 复杂工作流


@dataclass
class ExtractedEntity:
    """提取的实体"""
    entity_type: str           # 实体类型
    value: Any                 # 实体值
    confidence: float          # 置信度
    start_pos: int             # 起始位置
    end_pos: int               # 结束位置


@dataclass
class IntentUnderstanding:
    """意图理解结果"""
    # 基础信息
    raw_input: str
    intent_type: IntentType
    confidence: float
    
    # 分类信息
    urgency: UrgencyLevel
    complexity: ComplexityLevel
    
    # 提取信息
    entities: List[ExtractedEntity] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # 场景信息
    scene: Optional[str] = None
    context_references: List[str] = field(default_factory=list)
    
    # 任务信息
    task_description: str = ""
    expected_output: str = ""
    constraints: List[str] = field(default_factory=list)
    
    # 元数据
    processing_time_ms: int = 0
    model_used: str = ""


class IntentUnderstandingEngine:
    """
    意图理解引擎
    
    分析用户输入，理解用户意图、提取关键信息
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        
        # 意图分类提示词
        self.intent_classification_prompt = """
        请分析用户的输入，识别用户的意图类型。
        
        可选的意图类型：
        - information_query: 信息查询（如"查询天气"、"搜索资料"）
        - task_execution: 任务执行（如"发送邮件"、"设置提醒"）
        - content_creation: 内容创作（如"写一篇文章"、"生成PPT"）
        - data_analysis: 数据分析（如"分析销售数据"、"统计报表"）
        - conversation: 闲聊对话（如"你好"、"讲个笑话"）
        - multi_step_task: 多步骤任务（如"搜索资料并生成报告"）
        
        请输出JSON格式：
        {
            "intent_type": "意图类型",
            "confidence": 0.95,
            "urgency": "low/medium/high/critical",
            "complexity": "simple/moderate/complex/very_complex",
            "keywords": ["关键词1", "关键词2"],
            "task_description": "任务描述",
            "expected_output": "期望输出",
            "constraints": ["约束条件1"]
        }
        
        用户输入：{user_input}
        历史上下文：{context}
        """
        
        # 实体提取提示词
        self.entity_extraction_prompt = """
        请从用户输入中提取关键实体。
        
        需要提取的实体类型：
        - time: 时间（如"明天下午3点"、"2024年1月1日"）
        - location: 地点（如"北京"、"会议室A"）
        - person: 人物（如"张三"、"李经理"）
        - organization: 组织（如"技术部"、"ABC公司"）
        - file: 文件（如"report.pdf"、"数据表"）
        - url: 链接（如"https://example.com"）
        - number: 数字（如"100"、"50%"）
        - keyword: 关键词
        
        请输出JSON格式：
        {
            "entities": [
                {
                    "type": "实体类型",
                    "value": "实体值",
                    "confidence": 0.95
                }
            ]
        }
        
        用户输入：{user_input}
        """
    
    async def understand(self,
                        user_input: str,
                        context: Dict[str, Any]) -> IntentUnderstanding:
        """
        理解用户意图
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            IntentUnderstanding: 意图理解结果
        """
        import time
        start_time = time.time()
        
        # 1. 意图分类
        intent_result = await self._classify_intent(user_input, context)
        
        # 2. 实体提取
        entities = await self._extract_entities(user_input)
        
        # 3. 场景识别
        scene = await self._recognize_scene(user_input, context)
        
        # 4. 复杂度评估
        complexity = self._assess_complexity(user_input, intent_result, entities)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return IntentUnderstanding(
            raw_input=user_input,
            intent_type=IntentType(intent_result["intent_type"]),
            confidence=intent_result["confidence"],
            urgency=UrgencyLevel[intent_result["urgency"].upper()],
            complexity=complexity,
            entities=entities,
            keywords=intent_result.get("keywords", []),
            scene=scene,
            task_description=intent_result.get("task_description", ""),
            expected_output=intent_result.get("expected_output", ""),
            constraints=intent_result.get("constraints", []),
            processing_time_ms=processing_time,
            model_used="gpt-4"
        )
    
    async def _classify_intent(self,
                              user_input: str,
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """意图分类"""
        prompt = self.intent_classification_prompt.format(
            user_input=user_input,
            context=context.get("history", "")
        )
        
        response = await self.llm_service.generate_json(prompt)
        return response
    
    async def _extract_entities(self, user_input: str) -> List[ExtractedEntity]:
        """实体提取"""
        prompt = self.entity_extraction_prompt.format(user_input=user_input)
        
        response = await self.llm_service.generate_json(prompt)
        
        entities = []
        for entity_data in response.get("entities", []):
            # 查找位置
            value = str(entity_data["value"])
            start_pos = user_input.find(value)
            end_pos = start_pos + len(value) if start_pos >= 0 else -1
            
            entities.append(ExtractedEntity(
                entity_type=entity_data["type"],
                value=entity_data["value"],
                confidence=entity_data.get("confidence", 0.8),
                start_pos=start_pos,
                end_pos=end_pos
            ))
        
        return entities
    
    async def _recognize_scene(self,
                              user_input: str,
                              context: Dict[str, Any]) -> Optional[str]:
        """场景识别"""
        # 基于关键词匹配场景
        scene_keywords = {
            "work": ["会议", "报告", "项目", "邮件", "客户"],
            "study": ["学习", "课程", "考试", "论文", "笔记"],
            "life": ["购物", "出行", "餐厅", "电影", "旅游"],
            "dev": ["代码", "bug", "部署", "测试", "git"]
        }
        
        max_score = 0
        best_scene = None
        
        for scene, keywords in scene_keywords.items():
            score = sum(1 for kw in keywords if kw in user_input)
            if score > max_score:
                max_score = score
                best_scene = scene
        
        return best_scene
    
    def _assess_complexity(self,
                          user_input: str,
                          intent_result: Dict[str, Any],
                          entities: List[ExtractedEntity]) -> ComplexityLevel:
        """评估复杂度"""
        # 基于多个因素评估
        score = 0
        
        # 1. 输入长度
        if len(user_input) > 100:
            score += 1
        if len(user_input) > 200:
            score += 1
        
        # 2. 实体数量
        if len(entities) > 3:
            score += 1
        if len(entities) > 6:
            score += 1
        
        # 3. 关键词分析
        complex_keywords = ["然后", "接着", "之后", "同时", "并且", "分析", "生成", "创建"]
        complex_count = sum(1 for kw in complex_keywords if kw in user_input)
        if complex_count >= 2:
            score += 1
        if complex_count >= 4:
            score += 1
        
        # 4. 意图类型
        if intent_result.get("intent_type") == "multi_step_task":
            score += 2
        
        # 映射到复杂度级别
        if score <= 2:
            return ComplexityLevel.SIMPLE
        elif score <= 4:
            return ComplexityLevel.MODERATE
        elif score <= 6:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX
```

#### 3.2.2 任务规划模块

```python
# app/orchestration/task_planner.py

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

from app.orchestration.intent_understanding import (
    IntentUnderstanding,
    ComplexityLevel,
    IntentType
)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    """任务步骤"""
    # 基本信息
    id: str
    name: str
    description: str
    
    # 执行信息
    capability_requirements: List[str] = field(default_factory=list)
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    
    # 依赖信息
    dependencies: List[str] = field(default_factory=list)
    
    # 状态信息
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    
    # 元数据
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30


@dataclass
class TaskPlan:
    """任务计划"""
    # 基本信息
    plan_id: str
    intent: IntentUnderstanding
    
    # 步骤信息
    steps: List[TaskStep] = field(default_factory=list)
    execution_mode: str = "sequential"  # sequential/parallel/conditional
    
    # 依赖图
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    
    # 执行信息
    estimated_time_ms: int = 0
    required_capabilities: Set[str] = field(default_factory=set)
    
    # 状态
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def get_ready_steps(self) -> List[TaskStep]:
        """获取可以执行的步骤（依赖已满足）"""
        ready = []
        completed_ids = {s.id for s in self.steps if s.status == TaskStatus.COMPLETED}
        
        for step in self.steps:
            if step.status == TaskStatus.PENDING:
                # 检查所有依赖是否已完成
                if all(dep in completed_ids for dep in step.dependencies):
                    ready.append(step)
        
        return ready
    
    def get_step(self, step_id: str) -> Optional[TaskStep]:
        """获取指定步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


class TaskPlanner:
    """
    任务规划器
    
    将意图理解结果分解为可执行的任务步骤
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def plan(self,
                  intent: IntentUnderstanding,
                  memories: List[Dict[str, Any]],
                  context: Dict[str, Any]) -> TaskPlan:
        """
        创建任务计划
        
        Args:
            intent: 意图理解结果
            memories: 相关记忆
            context: 上下文
            
        Returns:
            TaskPlan: 任务计划
        """
        # 1. 根据复杂度选择规划策略
        if intent.complexity == ComplexityLevel.SIMPLE:
            return await self._plan_simple_task(intent)
        elif intent.complexity == ComplexityLevel.MODERATE:
            return await self._plan_moderate_task(intent, memories)
        else:
            return await self._plan_complex_task(intent, memories, context)
    
    async def _plan_simple_task(self, intent: IntentUnderstanding) -> TaskPlan:
        """规划简单任务（单一步骤）"""
        step = TaskStep(
            id=str(uuid.uuid4()),
            name="execute_task",
            description=intent.task_description or intent.raw_input,
            capability_requirements=[intent.intent_type.value],
            max_retries=3,
            timeout_seconds=30
        )
        
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            intent=intent,
            steps=[step],
            execution_mode="sequential",
            required_capabilities={intent.intent_type.value},
            created_at=datetime.now().isoformat()
        )
    
    async def _plan_moderate_task(self,
                                 intent: IntentUnderstanding,
                                 memories: List[Dict[str, Any]]) -> TaskPlan:
        """规划中等复杂度任务（2-3个步骤）"""
        # 使用LLM分解任务
        prompt = f"""
        请将以下任务分解为2-3个具体的执行步骤。
        
        任务描述：{intent.task_description}
        期望输出：{intent.expected_output}
        
        可用能力类型：
        - information_query: 信息查询
        - content_creation: 内容创作
        - data_analysis: 数据分析
        - task_execution: 任务执行
        
        请输出JSON格式：
        {{
            "steps": [
                {{
                    "name": "步骤名称",
                    "description": "步骤描述",
                    "capability_type": "所需能力类型",
                    "input_requirements": ["输入参数1", "输入参数2"],
                    "output_production": ["输出结果1"]
                }}
            ],
            "execution_mode": "sequential"
        }}
        """
        
        response = await self.llm_service.generate_json(prompt)
        
        steps = []
        required_capabilities = set()
        
        for i, step_data in enumerate(response.get("steps", [])):
            step = TaskStep(
                id=str(uuid.uuid4()),
                name=step_data["name"],
                description=step_data["description"],
                capability_requirements=[step_data["capability_type"]],
                input_mapping={req: req for req in step_data.get("input_requirements", [])},
                output_mapping={out: out for out in step_data.get("output_production", [])},
                dependencies=[steps[-1].id] if steps else []
            )
            steps.append(step)
            required_capabilities.add(step_data["capability_type"])
        
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            intent=intent,
            steps=steps,
            execution_mode=response.get("execution_mode", "sequential"),
            required_capabilities=required_capabilities,
            created_at=datetime.now().isoformat()
        )
    
    async def _plan_complex_task(self,
                                intent: IntentUnderstanding,
                                memories: List[Dict[str, Any]],
                                context: Dict[str, Any]) -> TaskPlan:
        """规划复杂任务（多步骤，有依赖关系）"""
        # 构建更详细的规划提示
        memory_context = "\n".join([
            f"- {m.get('summary', '')}" for m in memories[:5]
        ])
        
        prompt = f"""
        请将以下复杂任务分解为详细的执行计划。
        
        任务描述：{intent.task_description}
        期望输出：{intent.expected_output}
        约束条件：{', '.join(intent.constraints)}
        
        相关历史记忆：
        {memory_context}
        
        请输出JSON格式：
        {{
            "steps": [
                {{
                    "id": "step_1",
                    "name": "步骤名称",
                    "description": "详细描述",
                    "capability_type": "所需能力",
                    "dependencies": ["依赖的步骤id"],
                    "input_mapping": {{"参数名": "来源"}},
                    "output_mapping": {{"结果名": "输出键"}},
                    "can_parallel": false
                }}
            ],
            "execution_mode": "conditional",
            "estimated_steps": 5
        }}
        """
        
        response = await self.llm_service.generate_json(prompt)
        
        steps = []
        required_capabilities = set()
        dependency_graph = {}
        
        for step_data in response.get("steps", []):
            step = TaskStep(
                id=step_data.get("id", str(uuid.uuid4())),
                name=step_data["name"],
                description=step_data["description"],
                capability_requirements=[step_data["capability_type"]],
                input_mapping=step_data.get("input_mapping", {}),
                output_mapping=step_data.get("output_mapping", {}),
                dependencies=step_data.get("dependencies", [])
            )
            steps.append(step)
            required_capabilities.add(step_data["capability_type"])
            dependency_graph[step.id] = step.dependencies
        
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            intent=intent,
            steps=steps,
            execution_mode=response.get("execution_mode", "conditional"),
            dependency_graph=dependency_graph,
            required_capabilities=required_capabilities,
            created_at=datetime.now().isoformat()
        )
```

#### 3.2.3 能力编排模块

```python
# app/orchestration/capability_orchestrator.py

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import asyncio

from app.capabilities.unified_capability_center import (
    UnifiedCapabilityCenter,
    CapabilityMatch
)
from app.orchestration.task_planner import TaskPlan, TaskStep
from app.capabilities.types import ExecutionContext, CapabilityResult


@dataclass
class CapabilityAssignment:
    """能力分配结果"""
    step_id: str
    capability_name: str
    confidence: float
    fallback_capabilities: List[str]
    input_preparation: Dict[str, Any]


@dataclass
class OrchestrationPlan:
    """编排计划"""
    task_plan: TaskPlan
    assignments: List[CapabilityAssignment]
    execution_strategy: str  # sequential/parallel/mixed
    rollback_strategy: str   # none/compensate/retry


class CapabilityOrchestrator:
    """
    能力编排器
    
    为任务步骤分配合适的能力，并制定执行策略
    """
    
    def __init__(self, capability_center: UnifiedCapabilityCenter):
        self.capability_center = capability_center
        
        # 能力类型到能力名称的映射（用于快速查找）
        self._capability_type_mapping = {
            "information_query": ["web_search", "knowledge_search", "chat"],
            "content_creation": ["content_creation", "image_generation", "video_generation"],
            "data_analysis": ["data_analysis", "chart_generation"],
            "task_execution": ["task_execution", "email_send", "reminder_set"]
        }
    
    async def orchestrate(self,
                         task_plan: TaskPlan,
                         context: ExecutionContext) -> OrchestrationPlan:
        """
        编排能力
        
        Args:
            task_plan: 任务计划
            context: 执行上下文
            
        Returns:
            OrchestrationPlan: 编排计划
        """
        assignments = []
        
        # 为每个步骤分配合适的能力
        for step in task_plan.steps:
            assignment = await self._assign_capability(step, context)
            assignments.append(assignment)
        
        # 确定执行策略
        execution_strategy = self._determine_execution_strategy(task_plan)
        
        # 确定回滚策略
        rollback_strategy = self._determine_rollback_strategy(task_plan)
        
        return OrchestrationPlan(
            task_plan=task_plan,
            assignments=assignments,
            execution_strategy=execution_strategy,
            rollback_strategy=rollback_strategy
        )
    
    async def _assign_capability(self,
                                step: TaskStep,
                                context: ExecutionContext) -> CapabilityAssignment:
        """
        为步骤分配合适的能力
        
        Args:
            step: 任务步骤
            context: 执行上下文
            
        Returns:
            CapabilityAssignment: 能力分配结果
        """
        # 1. 基于步骤描述发现能力
        matches = await self.capability_center.discover_capabilities(
            query=step.description,
            context=context,
            top_k=5
        )
        
        # 2. 如果没有发现，尝试基于capability_requirements查找
        if not matches and step.capability_requirements:
            for req in step.capability_requirements:
                # 查找预定义的映射
                candidates = self._capability_type_mapping.get(req, [])
                for cap_name in candidates:
                    cap = self.capability_center.get_capability(cap_name)
                    if cap:
                        matches.append(CapabilityMatch(
                            name=cap_name,
                            match_score=0.7,
                            match_type="mapping",
                            metadata=cap.metadata,
                            confidence=0.7,
                            reason=f"基于类型映射: {req}"
                        ))
        
        # 3. 评分和排序
        scored_matches = await self._score_capabilities(matches, step, context)
        
        # 4. 选择最佳能力
        if scored_matches:
            best_match = scored_matches[0]
            fallback = [m.name for m in scored_matches[1:3]]
            
            # 准备输入
            input_prep = await self._prepare_input(
                step,
                best_match.metadata,
                context
            )
            
            return CapabilityAssignment(
                step_id=step.id,
                capability_name=best_match.name,
                confidence=best_match.confidence,
                fallback_capabilities=fallback,
                input_preparation=input_prep
            )
        else:
            # 未找到合适能力
            return CapabilityAssignment(
                step_id=step.id,
                capability_name="",
                confidence=0.0,
                fallback_capabilities=[],
                input_preparation={}
            )
    
    async def _score_capabilities(self,
                                 matches: List[CapabilityMatch],
                                 step: TaskStep,
                                 context: ExecutionContext) -> List[CapabilityMatch]:
        """
        为能力匹配结果评分
        
        综合考虑：
        - 匹配分数
        - 历史成功率
        - 执行时间
        - 用户偏好
        """
        scored = []
        
        for match in matches:
            score = match.match_score
            
            # 获取能力统计
            capability = self.capability_center.get_capability(match.name)
            if capability:
                stats = capability.execution_stats
                
                # 成功率权重（0.2）
                if stats["total_calls"] > 0:
                    success_rate = stats["successful_calls"] / stats["total_calls"]
                    score += success_rate * 0.2
                
                # 执行时间权重（0.1）
                if stats["average_execution_time_ms"] > 0:
                    # 执行时间越短越好
                    time_score = max(0, 1.0 - stats["average_execution_time_ms"] / 5000)
                    score += time_score * 0.1
                
                # 使用频率权重（0.1）
                if stats["total_calls"] > 10:
                    score += 0.1
            
            # 更新分数
            match.match_score = min(1.0, score)
            scored.append(match)
        
        # 排序
        scored.sort(key=lambda x: x.match_score, reverse=True)
        return scored
    
    async def _prepare_input(self,
                            step: TaskStep,
                            capability_metadata: Any,
                            context: ExecutionContext) -> Dict[str, Any]:
        """
        准备能力输入
        
        根据步骤的input_mapping和上下文准备输入数据
        """
        prepared = {}
        
        for param_name, source in step.input_mapping.items():
            # 从上下文获取值
            if source.startswith("context."):
                key = source.replace("context.", "")
                value = context.get(key)
            elif source.startswith("step."):
                # 从其他步骤结果获取
                step_ref = source.replace("step.", "")
                # 这里需要实现步骤结果引用逻辑
                value = None
            else:
                # 直接使用值
                value = source
            
            prepared[param_name] = value
        
        return prepared
    
    def _determine_execution_strategy(self, task_plan: TaskPlan) -> str:
        """确定执行策略"""
        # 分析依赖图
        if not task_plan.dependency_graph:
            return "sequential"
        
        # 检查是否可以并行
        parallel_possible = False
        for step in task_plan.steps:
            if not step.dependencies:
                parallel_possible = True
                break
        
        if parallel_possible and len(task_plan.steps) > 2:
            return "mixed"  # 部分并行
        
        return task_plan.execution_mode
    
    def _determine_rollback_strategy(self, task_plan: TaskPlan) -> str:
        """确定回滚策略"""
        # 简单任务不需要回滚
        if len(task_plan.steps) == 1:
            return "none"
        
        # 复杂任务使用补偿策略
        if len(task_plan.steps) > 3:
            return "compensate"
        
        return "retry"
```

#### 3.2.4 执行引擎模块

```python
# app/orchestration/execution_engine.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time

from app.orchestration.capability_orchestrator import OrchestrationPlan, CapabilityAssignment
from app.orchestration.task_planner import TaskPlan, TaskStep, TaskStatus
from app.capabilities.types import ExecutionContext, CapabilityResult


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepExecutionResult:
    """步骤执行结果"""
    step_id: str
    capability_name: str
    status: TaskStatus
    result: CapabilityResult
    start_time: float
    end_time: float
    retry_count: int = 0


@dataclass
class ExecutionReport:
    """执行报告"""
    plan_id: str
    status: ExecutionStatus
    step_results: List[StepExecutionResult] = field(default_factory=list)
    total_time_ms: int = 0
    success_count: int = 0
    failed_count: int = 0
    errors: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    """
    执行引擎
    
    执行编排计划，管理步骤执行、监控、容错
    """
    
    def __init__(self, capability_center):
        self.capability_center = capability_center
        self._running_executions: Dict[str, ExecutionStatus] = {}
    
    async def execute(self,
                     orchestration_plan: OrchestrationPlan,
                     context: ExecutionContext) -> ExecutionReport:
        """
        执行编排计划
        
        Args:
            orchestration_plan: 编排计划
            context: 执行上下文
            
        Returns:
            ExecutionReport: 执行报告
        """
        plan = orchestration_plan.task_plan
        assignments = {a.step_id: a for a in orchestration_plan.assignments}
        
        report = ExecutionReport(
            plan_id=plan.plan_id,
            status=ExecutionStatus.RUNNING
        )
        
        self._running_executions[plan.plan_id] = ExecutionStatus.RUNNING
        
        start_time = time.time()
        
        try:
            if orchestration_plan.execution_strategy == "sequential":
                await self._execute_sequential(
                    plan, assignments, context, report
                )
            elif orchestration_plan.execution_strategy == "parallel":
                await self._execute_parallel(
                    plan, assignments, context, report
                )
            else:  # mixed
                await self._execute_mixed(
                    plan, assignments, context, report
                )
            
            # 确定最终状态
            if report.failed_count == 0:
                report.status = ExecutionStatus.COMPLETED
            elif report.success_count == 0:
                report.status = ExecutionStatus.FAILED
            else:
                report.status = ExecutionStatus.COMPLETED  # 部分成功
                
        except Exception as e:
            report.status = ExecutionStatus.FAILED
            report.errors.append(str(e))
        
        finally:
            report.total_time_ms = int((time.time() - start_time) * 1000)
            self._running_executions.pop(plan.plan_id, None)
        
        return report
    
    async def _execute_sequential(self,
                                 plan: TaskPlan,
                                 assignments: Dict[str, CapabilityAssignment],
                                 context: ExecutionContext,
                                 report: ExecutionReport):
        """顺序执行"""
        for step in plan.steps:
            if self._running_executions.get(plan.plan_id) == ExecutionStatus.CANCELLED:
                break
            
            result = await self._execute_step(step, assignments[step.id], context)
            report.step_results.append(result)
            
            if result.status == TaskStatus.COMPLETED:
                report.success_count += 1
                # 保存输出供后续步骤使用
                report.outputs[step.id] = result.result.output
            else:
                report.failed_count += 1
                report.errors.append(f"步骤 {step.name} 失败: {result.result.error}")
                
                # 检查是否需要回滚
                if report.failed_count > 0:
                    break
    
    async def _execute_parallel(self,
                               plan: TaskPlan,
                               assignments: Dict[str, CapabilityAssignment],
                               context: ExecutionContext,
                               report: ExecutionReport):
        """并行执行"""
        tasks = []
        for step in plan.steps:
            task = self._execute_step(step, assignments[step.id], context)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                report.failed_count += 1
                report.errors.append(str(result))
            else:
                report.step_results.append(result)
                if result.status == TaskStatus.COMPLETED:
                    report.success_count += 1
                else:
                    report.failed_count += 1
    
    async def _execute_mixed(self,
                            plan: TaskPlan,
                            assignments: Dict[str, CapabilityAssignment],
                            context: ExecutionContext,
                            report: ExecutionReport):
        """混合执行（部分并行）"""
        completed_steps = set()
        remaining_steps = set(s.id for s in plan.steps)
        
        while remaining_steps:
            # 找出可以执行的步骤（依赖已满足）
            ready_steps = []
            for step in plan.steps:
                if step.id in remaining_steps:
                    if all(dep in completed_steps for dep in step.dependencies):
                        ready_steps.append(step)
            
            if not ready_steps:
                break
            
            # 并行执行就绪的步骤
            tasks = []
            for step in ready_steps:
                task = self._execute_step(step, assignments[step.id], context)
                tasks.append((step.id, task))
            
            results = await asyncio.gather(
                *[t for _, t in tasks],
                return_exceptions=True
            )
            
            # 处理结果
            for (step_id, _), result in zip(tasks, results):
                remaining_steps.discard(step_id)
                
                if isinstance(result, Exception):
                    report.failed_count += 1
                    report.errors.append(str(result))
                else:
                    report.step_results.append(result)
                    if result.status == TaskStatus.COMPLETED:
                        report.success_count += 1
                        completed_steps.add(step_id)
                        report.outputs[step_id] = result.result.output
                    else:
                        report.failed_count += 1
    
    async def _execute_step(self,
                           step: TaskStep,
                           assignment: CapabilityAssignment,
                           context: ExecutionContext) -> StepExecutionResult:
        """
        执行单个步骤
        
        包含重试逻辑
        """
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= assignment.fallback_capabilities.__len__():
            capability_name = (
                assignment.capability_name if retry_count == 0
                else assignment.fallback_capabilities[retry_count - 1]
            )
            
            if not capability_name:
                break
            
            try:
                # 执行能力
                result = await self.capability_center.execute_capability(
                    capability_name=capability_name,
                    input_data=assignment.input_preparation,
                    context=context
                )
                
                if result.success:
                    return StepExecutionResult(
                        step_id=step.id,
                        capability_name=capability_name,
                        status=TaskStatus.COMPLETED,
                        result=result,
                        start_time=start_time,
                        end_time=time.time(),
                        retry_count=retry_count
                    )
                else:
                    # 执行失败，尝试回退
                    retry_count += 1
                    
            except Exception as e:
                retry_count += 1
                if retry_count > len(assignment.fallback_capabilities):
                    return StepExecutionResult(
                        step_id=step.id,
                        capability_name=capability_name,
                        status=TaskStatus.FAILED,
                        result=CapabilityResult(
                            success=False,
                            error=str(e)
                        ),
                        start_time=start_time,
                        end_time=time.time(),
                        retry_count=retry_count
                    )
        
        # 所有尝试都失败
        return StepExecutionResult(
            step_id=step.id,
            capability_name="",
            status=TaskStatus.FAILED,
            result=CapabilityResult(
                success=False,
                error="所有能力执行失败"
            ),
            start_time=start_time,
            end_time=time.time(),
            retry_count=retry_count
        )
```

---

## 四、11个官方能力封装

### 4.1 官方能力注册表

```python
# app/capabilities/official/__init__.py

from typing import Dict, List
from app.capabilities.base_capability import BaseCapability

from app.capabilities.official.chat_capability import ChatCapability
from app.capabilities.official.translation_capability import TranslationCapability
from app.capabilities.official.knowledge_search_capability import KnowledgeSearchCapability
from app.capabilities.official.web_search_capability import WebSearchCapability
from app.capabilities.official.image_generation_capability import ImageGenerationCapability
from app.capabilities.official.image_recognition_capability import ImageRecognitionCapability
from app.capabilities.official.video_generation_capability import VideoGenerationCapability
from app.capabilities.official.video_analysis_capability import VideoAnalysisCapability
from app.capabilities.official.speech_recognition_capability import SpeechRecognitionCapability
from app.capabilities.official.tts_capability import TTSCapability
from app.capabilities.official.stt_capability import STTCapability


class OfficialCapabilitiesRegistry:
    """
    官方能力注册表
    
    管理所有11个官方能力的注册和发现
    """
    
    def __init__(self):
        self.capabilities: Dict[str, BaseCapability] = {}
    
    def register_all(self):
        """注册所有官方能力"""
        official_capabilities = [
            ChatCapability(),
            TranslationCapability(),
            KnowledgeSearchCapability(),
            WebSearchCapability(),
            ImageGenerationCapability(),
            ImageRecognitionCapability(),
            VideoGenerationCapability(),
            VideoAnalysisCapability(),
            SpeechRecognitionCapability(),
            TTSCapability(),
            STTCapability()
        ]
        
        for capability in official_capabilities:
            self.capabilities[capability.metadata.name] = capability
            
    def get_capability(self, name: str) -> BaseCapability:
        """获取指定能力"""
        return self.capabilities.get(name)
    
    def list_all(self) -> List[BaseCapability]:
        """列出所有官方能力"""
        return list(self.capabilities.values())
```

### 4.2 具体能力实现示例

#### 4.2.1 聊天对话能力

```python
# app/capabilities/official/chat_capability.py

from typing import Dict, Any
from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.services.llm_service import LLMService


class ChatCapability(BaseCapability):
    """
    聊天对话能力
    
    原"聊天助手"智能体的能力化封装
    
    功能：
    - 通用对话
    - 问答
    - 建议提供
    - 上下文理解
    """
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="chat",
            display_name="聊天对话",
            description="通用对话能力，支持日常聊天、问答、提供建议等。"
                       "能够理解上下文，保持对话连贯性。",
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.COMPOSITE,
            category="conversation",
            tags=["对话", "聊天", "问答", "通用", "日常"],
            input_schema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "用户消息"
                    },
                    "history": {
                        "type": "array",
                        "description": "对话历史",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "系统提示词",
                        "default": "你是一个友好、专业的AI助手。"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "温度参数",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 2
                    }
                },
                "required": ["message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "AI回复"
                    },
                    "suggestions": {
                        "type": "array",
                        "description": "建议的后续问题",
                        "items": {"type": "string"}
                    }
                }
            },
            timeout_seconds=30,
            max_retries=2
        )
        super().__init__(metadata)
        self.llm_service = LLMService()
    
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """执行聊天"""
        message = input_data.get("message")
        history = input_data.get("history", [])
        system_prompt = input_data.get("system_prompt", self.metadata.input_schema["properties"]["system_prompt"]["default"])
        temperature = input_data.get("temperature", 0.7)
        
        # 如果没有提供历史，从上下文加载
        if not history and context.conversation_id:
            history = await self._load_history(context.conversation_id)
        
        # 调用LLM
        response = await self.llm_service.chat(
            message=message,
            history=history,
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        # 生成建议
        suggestions = await self._generate_suggestions(message, response)
        
        return CapabilityResult(
            success=True,
            output={
                "response": response,
                "suggestions": suggestions
            }
        )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入"""
        if not input_data.get("message"):
            return ValidationResult(
                valid=False,
                error="消息不能为空"
            )
        
        if len(input_data.get("message", "")) > 10000:
            return ValidationResult(
                valid=False,
                error="消息长度不能超过10000字符"
            )
        
        return ValidationResult(valid=True)
    
    async def _load_history(self, conversation_id: int) -> List[Dict]:
        """加载对话历史"""
        # 从数据库或缓存加载
        # 这里简化处理
        return []
    
    async def _generate_suggestions(self, message: str, response: str) -> List[str]:
        """生成建议"""
        # 基于对话内容生成3个建议的后续问题
        # 这里简化处理
        return []
```

#### 4.2.2 知识搜索能力

```python
# app/capabilities/official/knowledge_search_capability.py

from typing import Dict, Any, List
from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService


class KnowledgeSearchCapability(BaseCapability):
    """
    知识搜索能力
    
    原"知识库搜索"智能体的能力化封装
    
    功能：
    - 知识库检索
    - 语义搜索
    - 答案生成
    - 来源引用
    """
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="knowledge_search",
            display_name="知识库搜索",
            description="在知识库中搜索和检索信息，支持语义搜索和智能问答。"
                       "能够基于检索结果生成准确、有来源引用的答案。",
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.COMPOSITE,
            category="search",
            tags=["搜索", "知识", "检索", "问答", "RAG"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "knowledge_base_id": {
                        "type": "integer",
                        "description": "知识库ID",
                        "nullable": True
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "generate_answer": {
                        "type": "boolean",
                        "description": "是否生成答案",
                        "default": True
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "生成的答案"
                    },
                    "sources": {
                        "type": "array",
                        "description": "信息来源",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "score": {"type": "number"}
                            }
                        }
                    }
                }
            },
            timeout_seconds=30,
            max_retries=2
        )
        super().__init__(metadata)
        self.retrieval_service = RetrievalService()
        self.llm_service = LLMService()
    
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """执行知识搜索"""
        query = input_data.get("query")
        kb_id = input_data.get("knowledge_base_id")
        top_k = input_data.get("top_k", 5)
        generate_answer = input_data.get("generate_answer", True)
        
        # 1. 执行检索
        search_results = await self.retrieval_service.search(
            query=query,
            knowledge_base_id=kb_id,
            top_k=top_k
        )
        
        if not search_results:
            return CapabilityResult(
                success=True,
                output={
                    "answer": "未找到相关信息。",
                    "sources": []
                }
            )
        
        # 2. 格式化来源
        sources = [
            {
                "title": result.title,
                "content": result.content[:500],  # 截断
                "score": result.score,
                "source": result.source
            }
            for result in search_results
        ]
        
        # 3. 生成答案
        answer = ""
        if generate_answer:
            answer = await self._generate_answer(query, search_results)
        
        return CapabilityResult(
            success=True,
            output={
                "answer": answer,
                "sources": sources
            },
            metadata={
                "total_sources": len(sources),
                "knowledge_base_id": kb_id
            }
        )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入"""
        if not input_data.get("query"):
            return ValidationResult(
                valid=False,
                error="查询内容不能为空"
            )
        
        return ValidationResult(valid=True)
    
    async def _generate_answer(self, query: str, search_results: List[Any]) -> str:
        """基于搜索结果生成答案"""
        # 构建提示
        context_text = "\n\n".join([
            f"[来源{i+1}] {r.title}\n{r.content}"
            for i, r in enumerate(search_results[:3])
        ])
        
        prompt = f"""基于以下信息回答问题。

问题：{query}

相关信息：
{context_text}

请给出准确、简洁的回答，并标注信息来源。如果信息不足，请明确说明。"""
        
        answer = await self.llm_service.generate(prompt)
        return answer
```

（其他9个能力的实现类似，此处省略...）

---

## 五、能力编排执行流程

### 5.1 完整执行流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    能力编排完整执行流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入                                                        │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. 接收输入                                              │    │
│  │    - 文本/语音/文件                                       │    │
│  │    - 参数提取                                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 2. 意图理解 (IntentUnderstandingEngine)                  │    │
│  │    - 意图分类 → intent_type                              │    │
│  │    - 实体提取 → entities                                 │    │
│  │    - 场景识别 → scene                                    │    │
│  │    - 复杂度评估 → complexity                             │    │
│  │    - 紧急程度 → urgency                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 3. 记忆检索 (MemoryService)                              │    │
│  │    - 相关历史查询                                         │    │
│  │    - 用户偏好加载                                         │    │
│  │    - 上下文恢复                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 4. 任务规划 (TaskPlanner)                                │    │
│  │    - 任务分解 → TaskStep[]                               │    │
│  │    - 依赖分析 → dependency_graph                         │    │
│  │    - 执行模式确定 → execution_mode                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 5. 能力发现 (UnifiedCapabilityCenter)                    │    │
│  │    对每个任务步骤：                                        │    │
│  │    - 语义搜索 → semantic_matches                         │    │
│  │    - 标签匹配 → tag_matches                              │    │
│  │    - 历史匹配 → history_matches                          │    │
│  │    - 场景匹配 → scene_matches                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 6. 能力编排 (CapabilityOrchestrator)                     │    │
│  │    对每个任务步骤：                                        │    │
│  │    - 能力评分排序                                         │    │
│  │    - 最佳能力选择                                         │    │
│  │    - 回退能力指定                                         │    │
│  │    - 输入参数准备                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 7. 执行计划生成 (OrchestrationPlan)                      │    │
│  │    - 执行策略确定 → execution_strategy                   │    │
│  │    - 回滚策略确定 → rollback_strategy                    │    │
│  │    - 超时配置                                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 8. 计划执行 (ExecutionEngine)                            │    │
│  │    ┌─────────────────────────────────────────────────┐   │    │
│  │    │ 执行模式：                                       │   │    │
│  │    │ - sequential: 步骤1 → 步骤2 → 步骤3              │   │    │
│  │    │ - parallel:   步骤1 + 步骤2 + 步骤3（同时）       │   │    │
│  │    │ - mixed:      步骤1 + 步骤2 → 步骤3              │   │    │
│  │    └─────────────────────────────────────────────────┘   │    │
│  │    - 步骤执行监控                                         │    │
│  │    - 异常处理（重试/回退）                                 │    │
│  │    - 结果收集                                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 9. 结果融合                                              │    │
│  │    - 多步骤结果整合                                       │    │
│  │    - 最终响应生成                                         │    │
│  │    - 建议生成                                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 10. 记忆更新 (MemoryService)                             │    │
│  │    - 交互记录存储                                         │    │
│  │    - 执行结果缓存                                         │    │
│  │    - 用户偏好学习                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│     │                                                            │
│     ▼                                                            │
│  返回结果给用户                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 执行时序图

```
用户    UnifiedAgent    IntelligentOrchestrator    UnifiedCapabilityCenter    能力执行
 │           │                    │                           │              │
 │──输入────►│                    │                           │              │
 │           │──orchestrate()────►│                           │              │
 │           │                    │                           │              │
 │           │                    │──1. 意图理解──────────────►│              │
 │           │                    │◄──────────────────────────│              │
 │           │                    │                           │              │
 │           │                    │──2. 任务规划──────────────►│              │
 │           │                    │◄──────────────────────────│              │
 │           │                    │                           │              │
 │           │                    │──3. 能力发现──────────────►│              │
 │           │                    │◄──────────────────────────│              │
 │           │                    │                           │              │
 │           │                    │──4. 能力编排──────────────►│              │
 │           │                    │◄──────────────────────────│              │
 │           │                    │                           │              │
 │           │                    │──────execute_capability()─►│              │
 │           │                    │                           │──execute()──►│
 │           │                    │                           │◄─────────────│
 │           │                    │◄──────────────────────────│              │
 │           │                    │                           │              │
 │           │◄──结果─────────────│                           │              │
 │◄──响应────│                    │                           │              │
 │           │                    │                           │              │
```

---

## 六、数据库模型设计

### 6.1 新增数据表

```python
# alembic/versions/xxx_unified_capability_support.py

"""
统一能力中心支持的数据库迁移
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # 1. 能力编排日志表
    op.create_table(
        'capability_orchestration_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('execution_id', sa.String(100), unique=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('intent_type', sa.String(100)),
        sa.Column('intent_confidence', sa.Float()),
        sa.Column('complexity_level', sa.String(50)),
        sa.Column('execution_plan', sa.JSON(), default=dict),
        sa.Column('used_capabilities', sa.JSON(), default=list),
        sa.Column('execution_steps', sa.JSON(), default=list),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Index('idx_orchestration_user_id', 'user_id'),
        sa.Index('idx_orchestration_created_at', 'created_at')
    )
    
    # 2. 能力执行日志表
    op.create_table(
        'capability_execution_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('orchestration_id', sa.String(100)),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('capability_type', sa.String(50)),
        sa.Column('input_data', sa.JSON()),
        sa.Column('output_data', sa.JSON()),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Index('idx_capability_exec_name', 'capability_name'),
        sa.Index('idx_capability_exec_time', 'created_at')
    )
    
    # 3. 能力使用统计表
    op.create_table(
        'capability_usage_stats',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('capability_name', sa.String(100), unique=True, nullable=False),
        sa.Column('capability_type', sa.String(50)),
        sa.Column('total_calls', sa.Integer(), default=0),
        sa.Column('successful_calls', sa.Integer(), default=0),
        sa.Column('failed_calls', sa.Integer(), default=0),
        sa.Column('total_execution_time_ms', sa.Integer(), default=0),
        sa.Column('average_execution_time_ms', sa.Float(), default=0.0),
        sa.Column('success_rate', sa.Float(), default=1.0),
        sa.Column('last_used_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now())
    )
    
    # 4. 能力依赖关系表
    op.create_table(
        'capability_dependencies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_capability', sa.String(100), nullable=False),
        sa.Column('target_capability', sa.String(100), nullable=False),
        sa.Column('dependency_type', sa.String(50), default='soft'),  # hard/soft
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('source_capability', 'target_capability', name='uq_capability_dependency')
    )
    
    # 5. 扩展现有Agent表
    op.add_column('agents', sa.Column('unified_mode', sa.Boolean(), default=False))
    op.add_column('agents', sa.Column('orchestration_config', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('preferred_capabilities', sa.JSON(), default=list))
    
    # 6. 扩展现有Skill表
    op.add_column('skills', sa.Column('capability_name', sa.String(100), nullable=True))
    op.add_column('skills', sa.Column('capability_metadata', sa.JSON(), nullable=True))
    
    # 7. 扩展现有Tool表
    op.add_column('tools', sa.Column('capability_name', sa.String(100), nullable=True))
    op.add_column('tools', sa.Column('capability_metadata', sa.JSON(), nullable=True))


def downgrade():
    # 删除新增表
    op.drop_table('capability_dependencies')
    op.drop_table('capability_usage_stats')
    op.drop_table('capability_execution_logs')
    op.drop_table('capability_orchestration_logs')
    
    # 删除新增列
    op.drop_column('tools', 'capability_metadata')
    op.drop_column('tools', 'capability_name')
    op.drop_column('skills', 'capability_metadata')
    op.drop_column('skills', 'capability_name')
    op.drop_column('agents', 'preferred_capabilities')
    op.drop_column('agents', 'orchestration_config')
    op.drop_column('agents', 'unified_mode')
```

### 6.2 数据库模型类

```python
# app/models/capability_orchestration.py

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, JSON, Index
from sqlalchemy.sql import func
from app.models.base import Base


class CapabilityOrchestrationLog(Base):
    """能力编排日志模型"""
    
    __tablename__ = 'capability_orchestration_logs'
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), unique=True, nullable=False)
    agent_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    input_text = Column(Text, nullable=False)
    intent_type = Column(String(100))
    intent_confidence = Column(Float)
    complexity_level = Column(String(50))
    execution_plan = Column(JSON, default=dict)
    used_capabilities = Column(JSON, default=list)
    execution_steps = Column(JSON, default=list)
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_orchestration_user_id', 'user_id'),
        Index('idx_orchestration_created_at', 'created_at'),
    )


class CapabilityExecutionLog(Base):
    """能力执行日志模型"""
    
    __tablename__ = 'capability_execution_logs'
    
    id = Column(Integer, primary_key=True)
    orchestration_id = Column(String(100))
    capability_name = Column(String(100), nullable=False)
    capability_type = Column(String(50))
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_capability_exec_name', 'capability_name'),
        Index('idx_capability_exec_time', 'created_at'),
    )


class CapabilityUsageStats(Base):
    """能力使用统计模型"""
    
    __tablename__ = 'capability_usage_stats'
    
    id = Column(Integer, primary_key=True)
    capability_name = Column(String(100), unique=True, nullable=False)
    capability_type = Column(String(50))
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    total_execution_time_ms = Column(Integer, default=0)
    average_execution_time_ms = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    last_used_at = Column(DateTime)
    updated_at = Column(DateTime, onupdate=func.now())


class CapabilityDependency(Base):
    """能力依赖关系模型"""
    
    __tablename__ = 'capability_dependencies'
    
    id = Column(Integer, primary_key=True)
    source_capability = Column(String(100), nullable=False)
    target_capability = Column(String(100), nullable=False)
    dependency_type = Column(String(50), default='soft')
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_capability_dep_source', 'source_capability'),
        Index('idx_capability_dep_target', 'target_capability'),
    )
```

---

## 七、API接口设计

### 7.1 RESTful API

```python
# app/api/v1/capability_center.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user
from app.capabilities.unified_capability_center import UnifiedCapabilityCenter
from app.orchestration.intelligent_orchestrator import IntelligentOrchestrator

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


# ==================== 请求/响应模型 ====================

class CapabilityExecuteRequest(BaseModel):
    """能力执行请求"""
    capability_name: str = Field(..., description="能力名称")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    conversation_id: Optional[int] = Field(None, description="对话ID")
    timeout: Optional[int] = Field(None, description="超时时间（秒）")


class CapabilityExecuteResponse(BaseModel):
    """能力执行响应"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateRequest(BaseModel):
    """编排请求"""
    input: str = Field(..., description="用户输入")
    conversation_id: Optional[int] = Field(None, description="对话ID")
    agent_id: Optional[int] = Field(None, description="智能体ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文")


class OrchestrateResponse(BaseModel):
    """编排响应"""
    success: bool
    result: Any = None
    execution_plan: Dict[str, Any] = Field(default_factory=dict)
    used_capabilities: List[str] = Field(default_factory=list)
    execution_time_ms: int


class CapabilityInfo(BaseModel):
    """能力信息"""
    name: str
    display_name: str
    description: str
    capability_type: str
    category: str
    tags: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


# ==================== API端点 ====================

@router.get("/list", response_model=List[CapabilityInfo])
async def list_capabilities(
    category: Optional[str] = Query(None, description="分类筛选"),
    capability_type: Optional[str] = Query(None, description="类型筛选: skill/tool/mcp"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取能力列表
    
    支持按分类和类型筛选
    """
    center = UnifiedCapabilityCenter(db)
    await center.initialize()
    
    from app.capabilities.types import CapabilityType
    
    cap_type = None
    if capability_type:
        cap_type = CapabilityType(capability_type)
    
    capabilities = center.list_capabilities(
        category=category,
        capability_type=cap_type
    )
    
    return [
        CapabilityInfo(
            name=cap.name,
            display_name=cap.display_name,
            description=cap.description,
            capability_type=cap.capability_type.value,
            category=cap.category,
            tags=cap.tags,
            input_schema=cap.input_schema,
            output_schema=cap.output_schema
        )
        for cap in capabilities
    ]


@router.post("/execute", response_model=CapabilityExecuteResponse)
async def execute_capability(
    request: CapabilityExecuteRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    执行指定能力
    
    直接调用单个能力
    """
    center = UnifiedCapabilityCenter(db)
    await center.initialize()
    
    from app.capabilities.types import ExecutionContext
    
    context = ExecutionContext(
        user_id=current_user.id,
        conversation_id=request.conversation_id
    )
    
    result = await center.execute_capability(
        capability_name=request.capability_name,
        input_data=request.input_data,
        context=context,
        timeout=request.timeout
    )
    
    return CapabilityExecuteResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
        metadata=result.metadata
    )


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(
    request: OrchestrateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    智能编排
    
    自动分析用户意图，编排多个能力完成任务
    """
    center = UnifiedCapabilityCenter(db)
    await center.initialize()
    
    orchestrator = IntelligentOrchestrator(center)
    
    from app.capabilities.types import ExecutionContext
    
    context = ExecutionContext(
        user_id=current_user.id,
        agent_id=request.agent_id,
        conversation_id=request.conversation_id,
        context_data=request.context
    )
    
    result = await orchestrator.orchestrate(
        user_input=request.input,
        context=context
    )
    
    return OrchestrateResponse(
        success=result.success,
        result=result.result,
        execution_plan=result.execution_plan,
        used_capabilities=result.used_capabilities,
        execution_time_ms=result.execution_time_ms
    )


@router.get("/discover")
async def discover_capabilities(
    query: str = Query(..., description="查询文本"),
    top_k: int = Query(5, description="返回数量"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    发现能力
    
    基于查询文本发现相关能力
    """
    center = UnifiedCapabilityCenter(db)
    await center.initialize()
    
    from app.capabilities.types import ExecutionContext
    
    context = ExecutionContext(
        user_id=current_user.id
    )
    
    matches = await center.discover_capabilities(
        query=query,
        context=context,
        top_k=top_k
    )
    
    return {
        "matches": [
            {
                "name": match.name,
                "display_name": match.metadata.display_name if match.metadata else match.name,
                "match_score": match.match_score,
                "match_type": match.match_type,
                "confidence": match.confidence,
                "reason": match.reason
            }
            for match in matches
        ]
    }


@router.get("/stats")
async def get_capability_stats(
    capability_name: Optional[str] = Query(None, description="能力名称"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取能力统计
    
    获取能力使用统计数据
    """
    from app.models.capability_orchestration import CapabilityUsageStats
    
    query = db.query(CapabilityUsageStats)
    
    if capability_name:
        query = query.filter(CapabilityUsageStats.capability_name == capability_name)
    
    stats = query.all()
    
    return {
        "stats": [
            {
                "capability_name": stat.capability_name,
                "capability_type": stat.capability_type,
                "total_calls": stat.total_calls,
                "successful_calls": stat.successful_calls,
                "failed_calls": stat.failed_calls,
                "success_rate": stat.success_rate,
                "average_execution_time_ms": stat.average_execution_time_ms,
                "last_used_at": stat.last_used_at.isoformat() if stat.last_used_at else None
            }
            for stat in stats
        ]
    }
```

### 7.2 WebSocket实时接口

```python
# app/api/v1/capability_websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

from app.capabilities.unified_capability_center import UnifiedCapabilityCenter
from app.orchestration.intelligent_orchestrator import IntelligentOrchestrator

router = APIRouter()


@router.websocket("/ws/capability-stream")
async def capability_stream_websocket(websocket: WebSocket):
    """
    能力执行流式WebSocket
    
    实时返回能力执行进度和结果
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "execute":
                # 执行能力
                await _handle_execute_stream(websocket, message)
            
            elif action == "orchestrate":
                # 编排执行
                await _handle_orchestrate_stream(websocket, message)
            
            elif action == "cancel":
                # 取消执行
                await _handle_cancel(websocket, message)
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })


async def _handle_execute_stream(websocket: WebSocket, message: dict):
    """处理流式执行"""
    capability_name = message.get("capability_name")
    input_data = message.get("input_data", {})
    
    # 发送开始消息
    await websocket.send_json({
        "type": "start",
        "capability_name": capability_name
    })
    
    try:
        # 执行能力（这里简化处理，实际应该支持真正的流式输出）
        # 模拟进度更新
        for progress in [25, 50, 75, 100]:
            await asyncio.sleep(0.5)
            await websocket.send_json({
                "type": "progress",
                "progress": progress
            })
        
        # 发送完成消息
        await websocket.send_json({
            "type": "complete",
            "result": {"output": "执行结果示例"}
        })
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })


async def _handle_orchestrate_stream(websocket: WebSocket, message: dict):
    """处理流式编排"""
    user_input = message.get("input")
    
    # 发送开始消息
    await websocket.send_json({
        "type": "start",
        "input": user_input
    })
    
    # 模拟编排过程
    steps = [
        {"name": "意图理解", "status": "running"},
        {"name": "任务规划", "status": "pending"},
        {"name": "能力发现", "status": "pending"},
        {"name": "能力编排", "status": "pending"},
        {"name": "执行", "status": "pending"}
    ]
    
    for i, step in enumerate(steps):
        # 更新当前步骤状态
        await websocket.send_json({
            "type": "step_update",
            "step": step["name"],
            "status": "running",
            "progress": int((i / len(steps)) * 100)
        })
        
        await asyncio.sleep(1)
        
        # 标记完成
        await websocket.send_json({
            "type": "step_update",
            "step": step["name"],
            "status": "completed"
        })
    
    # 发送最终结果
    await websocket.send_json({
        "type": "complete",
        "result": {
            "response": "编排执行完成",
            "used_capabilities": ["web_search", "content_creation"]
        }
    })


async def _handle_cancel(websocket: WebSocket, message: dict):
    """处理取消请求"""
    execution_id = message.get("execution_id")
    
    # 这里应该实现真正的取消逻辑
    await websocket.send_json({
        "type": "cancelled",
        "execution_id": execution_id
    })
```

---

## 八、与现有系统的集成

### 8.1 集成架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    与现有系统的集成架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    新架构层                              │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │   │
│  │  │ UnifiedAgent│ │ UnifiedCap  │ │ Intelligent │       │   │
│  │  │             │ │ abilityCenter│ │ Orchestrator│       │   │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘       │   │
│  │         │               │               │              │   │
│  │         └───────────────┼───────────────┘              │   │
│  │                         │                              │   │
│  │              ┌──────────┴──────────┐                   │   │
│  │              │   CapabilityAdapter  │                   │   │
│  │              │    (适配器层)         │                   │   │
│  │              └──────────┬──────────┘                   │   │
│  └─────────────────────────┼──────────────────────────────┘   │
│                            │                                   │
│  ┌─────────────────────────┼──────────────────────────────┐   │
│  │                    现有系统层                           │   │
│  │                         │                               │   │
│  │  ┌─────────────┐ ┌──────┴──────┐ ┌─────────────┐       │   │
│  │  │   Agent     │ │   Skill     │ │    Tool     │       │   │
│  │  │   模型      │ │   模型      │ │    模型     │       │   │
│  │  │             │ │             │ │             │       │   │
│  │  │ • Agent表   │ │ • Skill表   │ │ • Tool表    │       │   │
│  │  │ • Agent配置 │ │ • Skill内容 │ │ • Tool配置  │       │   │
│  │  │ • Agent关联 │ │ • Skill执行 │ │ • Tool执行  │       │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │   │
│  │                                                         │   │
│  │  ┌─────────────┐ ┌─────────────┐                       │   │
│  │  │    MCP      │ │   Memory    │                       │   │
│  │  │   模型      │ │   系统      │                       │   │
│  │  │             │ │             │                       │   │
│  │  │ • MCP配置   │ │ • 记忆表    │                       │   │
│  │  │ • MCP工具   │ │ • 上下文    │                       │   │
│  │  │ • MCP连接   │ │ • 用户画像  │                       │   │
│  │  └─────────────┘ └─────────────┘                       │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 适配器实现

```python
# app/capabilities/adapters/skill_adapter.py

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import CapabilityMetadata, CapabilityResult, ExecutionContext, ValidationResult
from app.models.skill import Skill
from app.services.skill_execution_engine import SkillExecutionEngine


class SkillCapability(BaseCapability):
    """
    Skill能力适配器
    
    将现有Skill系统适配为统一Capability接口
    """
    
    def __init__(self, skill: Skill):
        metadata = CapabilityMetadata(
            name=skill.name,
            display_name=skill.display_name or skill.name,
            description=skill.description or "",
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.WORKFLOW,
            category="skill",
            tags=skill.tags if isinstance(skill.tags, list) else [],
            input_schema=skill.parameters_schema or {},
            version=skill.version or "1.0.0",
            author=skill.author
        )
        super().__init__(metadata)
        self.skill = skill
        self.execution_engine = SkillExecutionEngine()
    
    async def _do_execute(self, input_data: dict, context: ExecutionContext) -> CapabilityResult:
        """执行Skill"""
        result = await self.execution_engine.execute(
            skill_id=self.skill.id,
            params=input_data,
            user_id=context.user_id,
            conversation_id=context.conversation_id
        )
        
        return CapabilityResult(
            success=result.get("status") == "success",
            output=result.get("output"),
            artifacts=result.get("artifacts", []),
            metadata={
                "skill_id": self.skill.id,
                "execution_id": result.get("execution_id")
            }
        )
    
    async def validate_input(self, input_data: dict) -> ValidationResult:
        """验证输入"""
        # 使用Skill的参数schema验证
        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)


# app/capabilities/adapters/tool_adapter.py

class ToolCapability(BaseCapability):
    """
    Tool能力适配器
    
    将现有Tool系统适配为统一Capability接口
    """
    
    def __init__(self, tool: Tool):
        metadata = CapabilityMetadata(
            name=tool.name,
            display_name=tool.display_name or tool.name,
            description=tool.description or "",
            capability_type=CapabilityType.TOOL,
            level=CapabilityLevel.ATOMIC,
            category=tool.category or "general",
            tags=tool.tags if isinstance(tool.tags, list) else [],
            input_schema=tool.parameters_schema or {}
        )
        super().__init__(metadata)
        self.tool = tool
    
    async def _do_execute(self, input_data: dict, context: ExecutionContext) -> CapabilityResult:
        """执行Tool"""
        if self.tool.tool_type == "mcp":
            return await self._execute_mcp(input_data, context)
        else:
            return await self._execute_local(input_data, context)
    
    async def _execute_mcp(self, input_data: dict, context: ExecutionContext) -> CapabilityResult:
        """通过MCP执行"""
        from app.mcp.client.connection_manager import MCPConnectionManager
        
        client = await MCPConnectionManager.get_client(self.tool.mcp_client_config_id)
        result = await client.call_tool(
            tool_name=self.tool.mcp_tool_name,
            params=input_data
        )
        
        return CapabilityResult(
            success=True,
            output=result
        )
    
    async def _execute_local(self, input_data: dict, context: ExecutionContext) -> CapabilityResult:
        """本地执行"""
        # 调用本地Tool处理器
        # 这里需要根据实际的Tool执行机制实现
        pass
    
    async def validate_input(self, input_data: dict) -> ValidationResult:
        """验证输入"""
        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)
```

---

## 九、总结

本详细设计文档涵盖了统一能力中心方案的完整实现细节：

### 核心组件

1. **统一能力抽象层** - BaseCapability基类，统一Skill/Tool/MCP接口
2. **统一能力中心** - UnifiedCapabilityCenter，统一管理所有能力
3. **智能编排引擎** - IntelligentOrchestrator，自动编排能力完成任务
4. **11个官方能力** - 将官方智能体封装为可复用能力

### 关键特性

- **统一接口** - 所有能力使用相同的调用方式
- **智能发现** - 基于语义、标签、历史等多维度发现能力
- **自动编排** - 自动分解任务、选择能力、制定执行策略
- **容错机制** - 支持重试、回退、降级
- **完整监控** - 执行日志、统计、性能监控

### 与现有系统集成

- 保留所有现有功能
- 通过适配器模式无缝集成
- 数据库迁移脚本提供平滑升级
- API接口兼容现有调用方式
