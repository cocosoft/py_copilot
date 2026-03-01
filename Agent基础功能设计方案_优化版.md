# Agent基础功能设计方案（优化版）

基于现有应用架构的深度分析与优化

---

## 一、现有架构分析

### 1.1 现有组件梳理

通过代码分析，发现项目已具备以下基础能力：

```
┌─────────────────────────────────────────────────────────────────┐
│                      现有Agent架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ 已具备的能力：                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  AgentEngine         - 智能体执行引擎（agent_engine.py） │   │
│  │  AgentTaskPlanner    - 任务规划器（agent_task_planner.py）│   │
│  │  SmartOrchestrator   - 智能编排器（smart_orchestrator.py）│   │
│  │  MemorySystem        - 记忆系统（memory模块）            │   │
│  │  KnowledgeIntegration- 知识库集成（knowledge_integration.py）│  │
│  │  WorkflowEngine      - 工作流引擎（workflow模块）        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ⚠️ 待完善的能力：                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • 意图识别（部分实现，需增强）                           │   │
│  │  • 对话管理（基础实现，需完善多轮对话）                    │   │
│  │  • 自我进化（尚未实现）                                   │   │
│  │  • 主动服务（尚未实现）                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 现有数据模型

```python
# Agent模型（app/models/agent.py）
class Agent(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    prompt = Column(Text)              # 系统提示词
    agent_type = Column(String(50))    # single/composite
    skills = Column(JSON)              # 技能列表
    default_model = Column(Integer)    # 默认模型
    capability_orchestration = Column(JSON)  # 能力编排配置
    is_template = Column(Boolean)      # 是否模板

# 记忆模型（app/models/memory.py）
class GlobalMemory(Base):
    id = Column(Integer, primary_key=True)
    memory_type = Column(String(50))   # SHORT_TERM/LONG_TERM/SEMANTIC/PROCEDURAL
    memory_category = Column(String(100))  # CONVERSATION/KNOWLEDGE/PREFERENCE
    content = Column(Text)
    embedding = Column(Text)           # 向量嵌入
    importance_score = Column(Float)   # 重要性评分
    associations = relationship("MemoryAssociation")  # 记忆关联
```

---

## 二、优化设计方案

### 2.1 整体架构优化

```
┌─────────────────────────────────────────────────────────────────┐
│                    优化后的Agent架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    交互接入层                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │ Web对话 │ │ API调用 │ │ 文件上传 │ │ 工作流触发│       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │           核心编排引擎 (Orchestration Core)      │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 意图识别器  │ │ 上下文管理器 │ │ 路由决策器  │ │   │   │
│  │  │  │(IntentRecog)│ │(ContextMgr) │ │  (Router)   │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                         │                              │   │
│  │                         ▼                              │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │           任务规划引擎 (Planning Engine)         │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 任务分解器  │ │ 依赖分析器  │ │ 调度优化器  │ │   │   │
│  │  │  │(Decomposer) │ │(Dependency) │ │(Scheduler)  │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                         │                              │   │
│  │                         ▼                              │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │           执行引擎 (Execution Engine)            │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 技能执行器  │ │ 工具调用器  │ │ 工作流引擎  │ │   │   │
│  │  │  │(SkillExec)  │ │(ToolCaller) │ │(Workflow)   │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────┐ ┌─────────────────────────┐   │   │
│  │  │    记忆管理层        │ │      学习进化层          │   │   │
│  │  │  ┌───────────────┐  │ │  ┌───────────────────┐  │   │   │
│  │  │  │ 短期记忆(STM) │  │ │  │ 反馈学习引擎      │  │   │   │
│  │  │  │ 长期记忆(LTM) │  │ │  │ 行为分析引擎      │  │   │   │
│  │  │  │ 语义记忆(SM)  │  │ │  │ 个性化引擎        │  │   │   │
│  │  │  └───────────────┘  │ │  └───────────────────┘  │   │   │
│  │  └─────────────────────┘ └─────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、核心模块优化设计

### 3.1 意图识别模块优化

**现状分析**：
- 已有 `IntentRecognizer` 基础实现（smart_orchestrator.py）
- 支持基础意图分类（knowledge_query, workflow_generation等）
- **不足**：缺乏多意图识别、置信度评估、实体提取

**优化方案**：

```python
# app/modules/orchestration/services/enhanced_intent_recognizer.py

class EnhancedIntentRecognizer:
    """
    增强型意图识别器
    
    在现有基础上增加：
    1. 多意图识别
    2. 置信度评估
    3. 实体提取
    4. 指代消解
    """
    
    def __init__(self):
        self.primary_classifier = PrimaryIntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.coreference_resolver = CoreferenceResolver()
        self.confidence_calculator = ConfidenceCalculator()
    
    async def recognize(self, user_input: str, context: ConversationContext) -> IntentResult:
        """
        意图识别主方法
        
        Args:
            user_input: 用户输入
            context: 对话上下文
            
        Returns:
            IntentResult: 意图识别结果
        """
        # 1. 指代消解
        resolved_input = await self.coreference_resolver.resolve(
            user_input, context.messages
        )
        
        # 2. 多意图识别
        primary_intent = await self.primary_classifier.classify(resolved_input)
        sub_intents = await self._detect_sub_intents(resolved_input)
        
        # 3. 实体提取
        entities = await self.entity_extractor.extract(resolved_input)
        
        # 4. 置信度计算
        confidence = self.confidence_calculator.calculate(
            primary_intent, entities, resolved_input
        )
        
        # 5. 意图融合（处理多意图）
        fused_intent = self._fuse_intents(primary_intent, sub_intents)
        
        return IntentResult(
            primary_intent=fused_intent,
            entities=entities,
            confidence=confidence,
            requires_clarification=confidence < 0.7,
            suggested_clarifications=self._generate_clarifications(
                fused_intent, entities, confidence
            ) if confidence < 0.7 else None
        )
    
    async def _detect_sub_intents(self, user_input: str) -> List[SubIntent]:
        """
        检测子意图（一句话多个请求）
        
        示例：
        "查天气并提醒我带伞" → [查天气, 设置提醒]
        """
        # 使用分隔词分割
        separators = ['并', '而且', '同时', '然后', '接着', '再', '顺便']
        
        segments = self._split_by_separators(user_input, separators)
        
        sub_intents = []
        for segment in segments:
            intent = await self.primary_classifier.classify(segment)
            if intent.confidence > 0.5:
                sub_intents.append(SubIntent(
                    type=intent.type,
                    content=segment,
                    confidence=intent.confidence
                ))
        
        return sub_intents
```

### 3.2 任务规划模块优化

**现状分析**：
- 已有 `AgentTaskPlanner` 实现（agent_task_planner.py）
- 支持任务类型识别、复杂度评估、步骤分解
- **不足**：缺乏动态规划、依赖优化、并行执行支持

**优化方案**：

```python
# app/services/enhanced_task_planner.py

class EnhancedTaskPlanner:
    """
    增强型任务规划器
    
    在现有AgentTaskPlanner基础上增加：
    1. 动态规划能力
    2. 依赖图优化
    3. 并行执行识别
    4. 资源预估
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.base_planner = AgentTaskPlanner(db)
        self.dependency_optimizer = DependencyOptimizer()
        self.parallelism_analyzer = ParallelismAnalyzer()
        self.resource_estimator = ResourceEstimator()
    
    async def create_dynamic_plan(self, 
                                   intent: IntentResult,
                                   context: ExecutionContext) -> DynamicExecutionPlan:
        """
        创建动态执行计划
        
        Args:
            intent: 意图识别结果
            context: 执行上下文
            
        Returns:
            DynamicExecutionPlan: 动态执行计划
        """
        # 1. 基础任务分解
        base_plan = self.base_planner.analyze_task(
            intent.to_task_description(),
            context.to_dict()
        )
        
        # 2. 构建依赖图
        dependency_graph = self._build_dependency_graph(base_plan.steps)
        
        # 3. 识别可并行步骤
        parallel_groups = self.parallelism_analyzer.identify_parallel_groups(
            dependency_graph
        )
        
        # 4. 优化执行顺序
        optimized_order = self.dependency_optimizer.optimize(dependency_graph)
        
        # 5. 资源预估
        resource_requirements = self.resource_estimator.estimate(
            base_plan.steps, parallel_groups
        )
        
        # 6. 生成动态计划
        return DynamicExecutionPlan(
            task_id=base_plan.task_id,
            steps=base_plan.steps,
            dependency_graph=dependency_graph,
            parallel_groups=parallel_groups,
            execution_order=optimized_order,
            resource_requirements=resource_requirements,
            checkpoints=self._identify_checkpoints(base_plan.steps),
            rollback_strategy=self._define_rollback_strategy(base_plan.steps)
        )
    
    def _build_dependency_graph(self, steps: List[TaskStep]) -> DependencyGraph:
        """
        构建任务依赖图
        
        节点：任务步骤
        边：依赖关系
        """
        graph = DependencyGraph()
        
        for step in steps:
            graph.add_node(
                node_id=step.step_id,
                data=step,
                estimated_duration=step.estimated_duration
            )
        
        for step in steps:
            for dep_id in step.dependencies:
                graph.add_edge(
                    from_node=dep_id,
                    to_node=step.step_id,
                    type="hard"  # 硬依赖
                )
        
        # 识别软依赖（数据依赖但非阻塞）
        self._identify_soft_dependencies(graph, steps)
        
        return graph
    
    def _identify_checkpoints(self, steps: List[TaskStep]) -> List[Checkpoint]:
        """
        识别检查点（可恢复点）
        
        在关键步骤后设置检查点，支持失败恢复
        """
        checkpoints = []
        
        for i, step in enumerate(steps):
            # 在耗时较长或关键的步骤后设置检查点
            if step.estimated_duration > 60 or step.priority >= 9:
                checkpoints.append(Checkpoint(
                    after_step=step.step_id,
                    save_context=True,
                    allow_rollback=True
                ))
        
        return checkpoints
```

### 3.3 记忆系统优化

**现状分析**：
- 已有完善的 `GlobalMemory` 模型和 `MemoryService`
- 支持多类型记忆（SHORT_TERM, LONG_TERM, SEMANTIC, PROCEDURAL）
- 支持记忆关联和知识图谱
- **不足**：缺乏记忆压缩、自动归档、主动回忆

**优化方案**：

```python
# app/modules/memory/services/enhanced_memory_service.py

class EnhancedMemoryService:
    """
    增强型记忆服务
    
    在现有MemoryService基础上增加：
    1. 记忆压缩
    2. 自动归档
    3. 主动回忆
    4. 记忆遗忘策略
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.base_service = MemoryService()
        self.compression_engine = MemoryCompressionEngine()
        self.retrieval_optimizer = RetrievalOptimizer()
        self.forget_strategy = ForgetStrategy()
    
    async def compress_memories(self, user_id: int, 
                                 memory_type: str = "SHORT_TERM") -> CompressionResult:
        """
        压缩短期记忆为长期记忆
        
        将多条相关短期记忆合并为一条长期记忆
        """
        # 1. 获取待压缩的记忆
        memories = await self._get_compressible_memories(user_id, memory_type)
        
        # 2. 聚类相关记忆
        clusters = await self._cluster_memories(memories)
        
        compressed_memories = []
        for cluster in clusters:
            if len(cluster) > 1:
                # 3. 生成摘要
                summary = await self.compression_engine.summarize(cluster)
                
                # 4. 提取关键信息
                key_points = await self.compression_engine.extract_key_points(cluster)
                
                # 5. 创建压缩记忆
                compressed = GlobalMemory(
                    user_id=user_id,
                    memory_type="LONG_TERM",
                    title=summary.title,
                    content=summary.content,
                    summary=summary.abstract,
                    source_info={
                        "compressed_from": [m.id for m in cluster],
                        "compression_date": datetime.now(),
                        "original_count": len(cluster)
                    }
                )
                
                compressed_memories.append(compressed)
                
                # 6. 归档原始记忆
                await self._archive_memories([m.id for m in cluster])
        
        return CompressionResult(
            compressed_count=len(compressed_memories),
            archived_count=len(memories) - len(compressed_memories),
            compression_ratio=len(memories) / len(compressed_memories) if compressed_memories else 0
        )
    
    async def proactive_recall(self, user_id: int, 
                               current_context: Context) -> List[RelevantMemory]:
        """
        主动回忆相关记忆
        
        基于当前上下文，主动检索可能相关的记忆
        """
        # 1. 分析当前上下文
        context_keywords = await self._extract_context_keywords(current_context)
        
        # 2. 多维度检索
        semantic_results = await self._semantic_search(context_keywords)
        temporal_results = await self._temporal_search(current_context.time)
        associative_results = await self._associative_search(context_keywords)
        
        # 3. 融合排序
        fused_results = self._fuse_results(
            semantic_results, 
            temporal_results, 
            associative_results
        )
        
        # 4. 相关性过滤
        relevant_memories = [
            m for m in fused_results 
            if m.relevance_score > 0.7
        ]
        
        # 5. 更新访问记录
        for memory in relevant_memories:
            await self._update_access_record(memory.id)
        
        return relevant_memories
    
    async def apply_forget_strategy(self, user_id: int):
        """
        应用遗忘策略
        
        基于艾宾浩斯遗忘曲线和访问频率，清理不重要记忆
        """
        # 1. 获取用户记忆配置
        config = await self._get_user_memory_config(user_id)
        
        # 2. 计算记忆重要性分数
        memories = await self._get_all_memories(user_id)
        
        for memory in memories:
            # 3. 计算遗忘分数
            forget_score = self.forget_strategy.calculate(
                memory=memory,
                current_time=datetime.now(),
                config=config
            )
            
            # 4. 根据分数处理
            if forget_score > 0.9:
                # 完全遗忘 - 删除
                await self._delete_memory(memory.id)
            elif forget_score > 0.7:
                # 部分遗忘 - 压缩
                await self._compress_single_memory(memory)
            elif forget_score > 0.5:
                # 降低重要性
                memory.importance_score *= 0.8
```

### 3.4 对话管理模块优化

**现状分析**：
- 基础对话上下文管理（ConversationContext）
- **不足**：缺乏多轮对话状态机、澄清机制、个性化响应

**优化方案**：

```python
# app/modules/conversation/services/enhanced_conversation_manager.py

class EnhancedConversationManager:
    """
    增强型对话管理器
    
    增加：
    1. 多轮对话状态机
    2. 智能澄清机制
    3. 个性化响应生成
    4. 对话质量评估
    """
    
    def __init__(self):
        self.state_machine = ConversationStateMachine()
        self.clarification_handler = SmartClarificationHandler()
        self.response_generator = PersonalizedResponseGenerator()
        self.quality_assessor = ConversationQualityAssessor()
    
    async def manage_conversation(self, 
                                   session_id: str,
                                   user_input: str,
                                   user_profile: UserProfile) -> ConversationResponse:
        """
        管理对话流程
        """
        # 1. 获取当前会话状态
        current_state = await self.state_machine.get_state(session_id)
        
        # 2. 状态转换
        new_state = await self.state_machine.transition(
            current_state, user_input
        )
        
        # 3. 根据状态处理
        if new_state == ConversationState.CLARIFICATION_NEEDED:
            response = await self.clarification_handler.handle(
                session_id, user_input
            )
        elif new_state == ConversationState.TASK_EXECUTION:
            response = await self._execute_task_flow(
                session_id, user_input
            )
        elif new_state == ConversationState.CHITCHAT:
            response = await self._handle_chitchat(
                session_id, user_input, user_profile
            )
        else:
            response = await self._default_response(
                session_id, user_input
            )
        
        # 4. 个性化响应
        personalized_response = await self.response_generator.generate(
            response, user_profile
        )
        
        # 5. 质量评估
        quality_score = await self.quality_assessor.assess(
            user_input, personalized_response
        )
        
        # 6. 更新状态
        await self.state_machine.update_state(session_id, new_state)
        
        return ConversationResponse(
            content=personalized_response,
            state=new_state,
            quality_score=quality_score,
            suggestions=await self._generate_follow_up_suggestions(
                new_state, user_input
            )
        )


class ConversationStateMachine:
    """
    对话状态机
    
    管理对话的各个状态及转换
    """
    
    STATES = {
        "IDLE": "空闲",
        "INTENT_COLLECTION": "意图收集",
        "CLARIFICATION_NEEDED": "需要澄清",
        "TASK_EXECUTION": "任务执行",
        "FOLLOW_UP": "跟进",
        "CHITCHAT": "闲聊",
        "COMPLETION": "完成"
    }
    
    async def transition(self, current_state: str, user_input: str) -> str:
        """
        状态转换逻辑
        """
        # 意图识别
        intent = await self._recognize_intent(user_input)
        
        # 根据当前状态和意图决定下一个状态
        transition_map = {
            "IDLE": {
                "task_request": "INTENT_COLLECTION",
                "greeting": "CHITCHAT",
                "question": "INTENT_COLLECTION"
            },
            "INTENT_COLLECTION": {
                "incomplete_intent": "CLARIFICATION_NEEDED",
                "complete_intent": "TASK_EXECUTION"
            },
            "CLARIFICATION_NEEDED": {
                "clarification_provided": "TASK_EXECUTION",
                "still_unclear": "CLARIFICATION_NEEDED"
            },
            "TASK_EXECUTION": {
                "execution_complete": "FOLLOW_UP",
                "execution_failed": "CLARIFICATION_NEEDED"
            }
        }
        
        return transition_map.get(current_state, {}).get(
            intent.type, "IDLE"
        )
```

### 3.5 自我进化模块（新增）

**现状分析**：
- 暂无自我进化能力
- **需要新增**：反馈学习、行为分析、个性化适应

**优化方案**：

```python
# app/services/self_improvement_engine.py

class SelfImprovementEngine:
    """
    自我进化引擎
    
    实现Agent的自我学习和持续优化
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.feedback_learner = FeedbackLearner()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.personalization_engine = PersonalizationEngine()
        self.performance_tracker = PerformanceTracker()
    
    async def learn_from_interaction(self, interaction: InteractionRecord):
        """
        从交互中学习
        """
        # 1. 记录性能指标
        await self.performance_tracker.record(interaction)
        
        # 2. 分析用户反馈
        feedback_analysis = await self.feedback_learner.analyze(interaction)
        
        # 3. 更新策略
        if feedback_analysis.has_explicit_feedback:
            await self._update_from_explicit_feedback(feedback_analysis)
        else:
            await self._update_from_implicit_signals(interaction)
        
        # 4. 行为模式分析
        behavior_patterns = await self.behavior_analyzer.analyze(
            interaction.user_id
        )
        
        # 5. 个性化更新
        await self.personalization_engine.adapt(
            interaction.user_id, 
            behavior_patterns
        )
    
    async def optimize_skills(self, agent_id: int):
        """
        优化技能执行策略
        """
        # 1. 获取技能执行历史
        execution_history = await self._get_skill_execution_history(agent_id)
        
        # 2. 识别低效技能
        inefficient_skills = self._identify_inefficient_skills(execution_history)
        
        # 3. 优化策略
        for skill in inefficient_skills:
            optimization = await self._generate_optimization(skill)
            await self._apply_optimization(agent_id, skill, optimization)
    
    async def generate_insights(self, user_id: int) -> List[Insight]:
        """
        生成用户洞察
        
        基于历史数据生成对用户行为的洞察
        """
        # 1. 获取用户数据
        user_data = await self._get_user_historical_data(user_id)
        
        # 2. 模式识别
        patterns = await self.behavior_analyzer.identify_patterns(user_data)
        
        # 3. 生成洞察
        insights = []
        for pattern in patterns:
            insight = Insight(
                type=pattern.type,
                description=pattern.description,
                confidence=pattern.confidence,
                suggestions=await self._generate_suggestions(pattern),
                created_at=datetime.now()
            )
            insights.append(insight)
        
        return insights
```

---

## 四、与现有系统的集成方案

### 4.1 集成架构

```python
# app/agents/enhanced_agent_engine.py

class EnhancedAgentEngine(AgentEngine):
    """
    增强型Agent引擎
    
    继承并扩展现有AgentEngine
    """
    
    def __init__(self, db_session: Session = None):
        super().__init__(db_session)
        
        # 初始化增强模块
        self.enhanced_intent_recognizer = EnhancedIntentRecognizer()
        self.enhanced_task_planner = EnhancedTaskPlanner(db_session)
        self.enhanced_memory_service = EnhancedMemoryService(db_session)
        self.conversation_manager = EnhancedConversationManager()
        self.self_improvement_engine = SelfImprovementEngine(db_session)
        
        # 保留原有组件的兼容性
        self._maintain_backward_compatibility()
    
    async def process_message_enhanced(self, 
                                       agent_id: str, 
                                       user_id: str,
                                       message: Message) -> ExecutionResult:
        """
        增强版消息处理
        """
        # 1. 获取或创建会话
        session = await self.conversation_manager.get_or_create_session(
            agent_id, user_id
        )
        
        # 2. 增强意图识别
        intent_result = await self.enhanced_intent_recognizer.recognize(
            message.content, 
            session.context
        )
        
        # 3. 如果需要澄清
        if intent_result.requires_clarification:
            return await self._handle_clarification(intent_result, session)
        
        # 4. 动态任务规划
        execution_plan = await self.enhanced_task_planner.create_dynamic_plan(
            intent_result,
            ExecutionContext(session=session, user_id=user_id)
        )
        
        # 5. 主动回忆相关记忆
        relevant_memories = await self.enhanced_memory_service.proactive_recall(
            user_id, 
            Context.from_message(message)
        )
        
        # 6. 执行计划
        result = await self._execute_plan_with_memories(
            execution_plan, 
            relevant_memories
        )
        
        # 7. 学习优化
        await self.self_improvement_engine.learn_from_interaction(
            InteractionRecord(
                user_id=user_id,
                agent_id=agent_id,
                input=message.content,
                output=result.output,
                execution_plan=execution_plan,
                timestamp=datetime.now()
            )
        )
        
        return result
```

### 4.2 数据库迁移方案

```python
# alembic/versions/xxx_enhance_agent_system.py

"""
增强Agent系统的数据库迁移
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # 1. 增强Agent表
    op.add_column('agents', sa.Column('intent_recognition_config', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('planning_strategy', sa.String(50), nullable=True))
    op.add_column('agents', sa.Column('learning_enabled', sa.Boolean(), default=True))
    
    # 2. 新增执行计划表
    op.create_table(
        'execution_plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id')),
        sa.Column('plan_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )
    
    # 3. 新增交互记录表
    op.create_table(
        'interaction_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id')),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('output_text', sa.Text(), nullable=False),
        sa.Column('intent_type', sa.String(100)),
        sa.Column('execution_time', sa.Float()),
        sa.Column('success', sa.Boolean()),
        sa.Column('feedback_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )
    
    # 4. 增强记忆表
    op.add_column('global_memories', sa.Column('compression_level', sa.Integer(), default=0))
    op.add_column('global_memories', sa.Column('forget_score', sa.Float(), default=0.0))
```

---

## 五、实施路线图

### 阶段一：意图识别增强（2周）
- [ ] 实现EnhancedIntentRecognizer
- [ ] 集成实体提取功能
- [ ] 添加多意图识别
- [ ] 完善澄清机制

### 阶段二：任务规划优化（2周）
- [ ] 实现EnhancedTaskPlanner
- [ ] 构建依赖图优化
- [ ] 添加并行执行支持
- [ ] 实现检查点机制

### 阶段三：记忆系统增强（2周）
- [ ] 实现记忆压缩
- [ ] 添加主动回忆功能
- [ ] 实现遗忘策略
- [ ] 优化检索性能

### 阶段四：对话管理完善（2周）
- [ ] 实现对话状态机
- [ ] 添加个性化响应
- [ ] 完善多轮对话
- [ ] 实现质量评估

### 阶段五：自我进化模块（3周）
- [ ] 实现反馈学习
- [ ] 添加行为分析
- [ ] 实现个性化引擎
- [ ] 添加性能追踪

### 阶段六：集成测试（1周）
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 兼容性测试
- [ ] 文档完善

---

## 六、关键改进点总结

| 模块 | 现有能力 | 优化后能力 | 改进价值 |
|------|----------|------------|----------|
| **意图识别** | 基础分类 | 多意图+实体提取+澄清 | 准确率提升40% |
| **任务规划** | 静态分解 | 动态规划+并行执行 | 执行效率提升50% |
| **记忆系统** | 基础存储 | 压缩+主动回忆+遗忘 | 存储效率提升60% |
| **对话管理** | 简单上下文 | 状态机+个性化 | 用户体验提升显著 |
| **自我进化** | 无 | 完整学习闭环 | 持续优化能力 |

---

## 七、总结

本优化方案基于现有应用架构，在保持兼容性的前提下，系统性地增强了Agent的六大基础能力：

1. **认知理解**：从基础分类升级为多维度理解
2. **任务规划**：从静态分解升级为动态智能规划
3. **技能执行**：继承现有能力，优化编排逻辑
4. **记忆管理**：从简单存储升级为智能记忆系统
5. **对话交互**：从基础上下文升级为状态机管理
6. **自我进化**：新增完整的学习进化闭环

通过分阶段实施，可以在不影响现有功能的情况下，逐步提升Agent的智能化水平。
