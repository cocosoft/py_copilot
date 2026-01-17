"""智能体执行引擎核心组件"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.skill import SkillExecutionLog
from app.services import agent_service
from app.services.agent_capability_service import AgentCapabilityService
from app.services.skill_execution_engine import SkillExecutionEngine
from app.services.llm_service import LLMService
from app.services.memory_cache_service import MemoryCacheService
from app.services.performance_monitor import performance_monitor, cached
from app.core.database import get_db
from app.core.config import settings


class ExecutionContext:
    """执行上下文管理器"""
    
    def __init__(self, db: Session, agent_id: int, conversation_id: Optional[int] = None, user_id: Optional[int] = None):
        self.db = db
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.context_data = {
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "execution_start_time": datetime.now(),
            "history": [],
            "current_step": "initialization",
            "skill_results": {},
            "capability_results": {},
            "model_responses": [],
            "params": {}
        }
        self.memory_service = MemoryCacheService()
    
    def load_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """加载对话历史"""
        if not self.conversation_id:
            return []
            
        # 从内存服务加载历史记录
        history = self.memory_service.get_conversation_history(self.conversation_id, limit=limit)
        if not history:
            # 如果内存中没有，从数据库加载
            from app.services.conversation_service import ConversationService
            history = ConversationService.get_conversation_history(self.db, self.conversation_id, limit=limit)
            # 缓存到内存
            self.memory_service.set_conversation_history(self.conversation_id, history)
        
        self.context_data["history"] = history
        return history
    
    def update_context(self, key: str, value: Any) -> None:
        """更新上下文数据"""
        self.context_data[key] = value
    
    def get_context(self, key: Optional[str] = None) -> Any:
        """获取上下文数据"""
        if key:
            return self.context_data.get(key)
        return self.context_data
    
    def add_skill_result(self, skill_id: int, result: Dict[str, Any]) -> None:
        """添加技能执行结果"""
        self.context_data["skill_results"][skill_id] = result
    
    def add_capability_result(self, capability_name: str, result: Any) -> None:
        """添加能力执行结果"""
        self.context_data["capability_results"][capability_name] = result
    
    def add_model_response(self, response: Any) -> None:
        """添加模型响应"""
        self.context_data["model_responses"].append(response)
    
    def save_context(self) -> None:
        """保存上下文到内存"""
        if self.conversation_id:
            self.memory_service.set_execution_context(self.conversation_id, self.context_data)
    
    def end_execution(self) -> Dict[str, Any]:
        """结束执行，返回最终上下文"""
        self.context_data["execution_end_time"] = datetime.now()
        self.context_data["execution_duration_ms"] = int(
            (self.context_data["execution_end_time"] - self.context_data["execution_start_time"]).total_seconds() * 1000
        )
        self.save_context()
        return self.context_data


class AgentExecutionEngine:
    """智能体执行引擎核心类"""
    
    def __init__(self, db: Session):
        self.db = db
        # 直接使用agent_service模块中的函数，而不是尝试实例化不存在的AgentService类
        self.skill_execution_engine = SkillExecutionEngine(db)
        self.llm_service = LLMService()
    
    @performance_monitor.monitor
    def execute(self, agent_id: int, user_input: str, conversation_id: Optional[int] = None, 
                user_id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行智能体核心逻辑"""
        # 创建执行上下文
        context = ExecutionContext(
            db=self.db,
            agent_id=agent_id,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        try:
            # 加载对话历史
            context.update_context("current_step", "loading_history")
            context.load_history()
            
            # 加载智能体配置
            context.update_context("current_step", "loading_agent_config")
            agent = self._load_agent(agent_id)
            context.update_context("agent", {
                "id": agent.id,
                "name": agent.name,
                "model_id": agent.model_id,
                "model_version": agent.model_version,
                "capabilities": agent.capabilities,
                "skills": agent.skills,
                "execution_config": agent.execution_config
            })
            
            # 合并参数
            if params:
                context.update_context("params", params)
            
            # 处理用户输入
            context.update_context("current_step", "processing_input")
            processed_input = self._process_user_input(user_input, context)
            
            # 调用模型获取响应
            context.update_context("current_step", "calling_model")
            model_response = self._call_model(agent, processed_input, context)
            context.add_model_response(model_response)
            
            # 分析模型响应，决定是否调用技能或能力
            context.update_context("current_step", "analyzing_model_response")
            skill_calls, capability_calls, final_response = self._analyze_model_response(model_response, context)
            
            skill_results = {}
            capability_results = {}
            
            # 执行技能调用
            if skill_calls:
                context.update_context("current_step", "executing_skills")
                skill_results = self._execute_skills(skill_calls, context)
            
            # 执行能力调用
            if capability_calls:
                context.update_context("current_step", "executing_capabilities")
                for capability_call in capability_calls:
                    capability_name = capability_call.get("capability_name")
                    params = capability_call.get("params", {})
                    if capability_name:
                        result = self._execute_capability(capability_name, params, context)
                        capability_results[capability_name] = result
                        context.add_capability_result(capability_name, result)
            
            # 根据技能结果和能力结果再次调用模型生成最终响应
            if skill_results or capability_results:
                context.update_context("current_step", "generating_final_response")
                final_response = self._generate_final_response(agent, user_input, model_response, skill_results, capability_results, context)
            
            # 保存执行上下文
            context.update_context("current_step", "saving_context")
            context.save_context()
            
            # 构建返回结果
            result = {
                "success": True,
                "response": final_response,
                "context": context.end_execution(),
                "execution_time_ms": context.get_context("execution_duration_ms"),
                "model_responses": context.get_context("model_responses"),
                "skill_results": context.get_context("skill_results"),
                "capability_results": context.get_context("capability_results")
            }
            
            return result
            
        except Exception as e:
            # 处理执行错误
            context.update_context("error", str(e))
            context.update_context("current_step", "error")
            
            # 构建错误响应
            return {
                "success": False,
                "error": str(e),
                "context": context.end_execution(),
                "execution_time_ms": context.get_context("execution_duration_ms")
            }
    
    @cached(maxsize=128)
    def _load_agent(self, agent_id: int) -> Agent:
        """加载智能体配置（带缓存）"""
        agent = agent_service.get_agent(self.db, agent_id)
        if not agent:
            raise ValueError(f"智能体不存在，ID: {agent_id}")
        return agent
    
    def _process_user_input(self, user_input: str, context: ExecutionContext) -> str:
        """处理用户输入"""
        # 这里可以添加输入预处理逻辑，如：
        # 1. 输入验证
        # 2. 实体识别
        # 3. 意图识别
        # 4. 上下文补全
        
        return user_input
    
    @performance_monitor.monitor
    def _call_model(self, agent: Agent, user_input: str, context: ExecutionContext) -> Any:
        """调用模型获取响应"""
        # 获取模型配置
        model_id = agent.model_id
        model_version = agent.model_version
        
        # 准备模型输入
        messages = []
        
        # 添加系统提示词
        if agent.prompt:
            messages.append({"role": "system", "content": agent.prompt})
        
        # 添加对话历史
        history = context.get_context("history")
        for message in history:
            messages.append({
                "role": message.get("role", "user"),
                "content": message.get("content", "")
            })
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        # 调用模型服务
        response = self.llm_service.call_llm(
            model_id=model_id,
            model_version=model_version,
            messages=messages,
            params=context.get_context("params")
        )
        
        return response
    
    @performance_monitor.monitor
    def _analyze_model_response(self, model_response: Any, context: ExecutionContext) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        """分析模型响应，决定是否调用技能或能力"""
        skill_calls = []
        capability_calls = []
        final_response = model_response.get("content", "")
        
        # 1. 检查模型响应中是否包含工具调用
        if isinstance(model_response, dict):
            # 检查OpenAI格式的工具调用
            if model_response.get("tool_calls"):
                return self._parse_openai_tool_calls(model_response["tool_calls"], context)
            
            # 检查自定义格式的技能调用
            if model_response.get("skill_calls"):
                skill_calls = self._parse_custom_skill_calls(model_response["skill_calls"], context)
            
            # 检查自定义格式的能力调用
            if model_response.get("capability_calls"):
                capability_calls = self._parse_custom_capability_calls(model_response["capability_calls"], context)
        
        # 2. 如果没有明确的工具调用，尝试从响应内容中解析
        if not skill_calls and not capability_calls:
            content = model_response.get("content", "")
            if content:
                # 尝试解析JSON格式的调用指令
                import json
                import re
                
                # 查找JSON格式的调用指令
                json_pattern = r'\{[\s\S]*?\}'
                matches = re.findall(json_pattern, content)
                
                for match in matches:
                    try:
                        call_data = json.loads(match)
                        if call_data.get("type") == "skill_call":
                            skill_calls.append(call_data)
                        elif call_data.get("type") == "capability_call":
                            capability_calls.append(call_data)
                    except json.JSONDecodeError:
                        continue
        
        # 3. 验证并处理调用指令
        if skill_calls:
            skill_calls = self._validate_skill_calls(skill_calls, context)
        
        if capability_calls:
            capability_calls = self._validate_capability_calls(capability_calls, context)
        
        # 如果有调用指令，清空最终响应，等待调用结果
        if skill_calls or capability_calls:
            final_response = ""
        
        return skill_calls, capability_calls, final_response
    
    def _parse_openai_tool_calls(self, tool_calls: List[Dict[str, Any]], context: ExecutionContext) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        """解析OpenAI格式的工具调用"""
        skill_calls = []
        capability_calls = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            
            # 解析工具参数
            import json
            try:
                args = json.loads(tool_args)
            except json.JSONDecodeError:
                continue
            
            # 根据工具名称决定是技能调用还是能力调用
            if tool_name.startswith("skill_"):
                # 技能调用
                skill_id = args.get("skill_id")
                if skill_id:
                    skill_calls.append({
                        "skill_id": skill_id,
                        "params": args.get("params", {})
                    })
            else:
                # 能力调用
                capability_calls.append({
                    "capability_name": tool_name,
                    "params": args
                })
        
        return skill_calls, capability_calls, ""
    
    def _parse_custom_skill_calls(self, skill_calls: List[Dict[str, Any]], context: ExecutionContext) -> List[Dict[str, Any]]:
        """解析自定义格式的技能调用"""
        validated_calls = []
        for call in skill_calls:
            if "skill_id" in call:
                validated_calls.append({
                    "skill_id": call["skill_id"],
                    "params": call.get("params", {})
                })
        return validated_calls
    
    def _parse_custom_capability_calls(self, capability_calls: List[Dict[str, Any]], context: ExecutionContext) -> List[Dict[str, Any]]:
        """解析自定义格式的能力调用"""
        validated_calls = []
        for call in capability_calls:
            if "capability_name" in call:
                validated_calls.append({
                    "capability_name": call["capability_name"],
                    "params": call.get("params", {})
                })
        return validated_calls
    
    def _validate_skill_calls(self, skill_calls: List[Dict[str, Any]], context: ExecutionContext) -> List[Dict[str, Any]]:
        """验证技能调用的有效性"""
        validated_calls = []
        agent = context.get_context("agent")
        
        for call in skill_calls:
            skill_id = call.get("skill_id")
            if skill_id:
                # 检查智能体是否具备该技能
                if agent and agent.get("skills"):
                    has_skill = any(skill.get("id") == skill_id for skill in agent["skills"])
                    if has_skill:
                        validated_calls.append(call)
                else:
                    # 如果智能体没有技能信息，暂时信任调用请求
                    validated_calls.append(call)
        
        return validated_calls
    
    def _validate_capability_calls(self, capability_calls: List[Dict[str, Any]], context: ExecutionContext) -> List[Dict[str, Any]]:
        """验证能力调用的有效性"""
        validated_calls = []
        agent = context.get_context("agent")
        
        for call in capability_calls:
            capability_name = call.get("capability_name")
            if capability_name:
                # 检查智能体是否具备该能力
                if agent and agent.get("capabilities"):
                    has_capability = any(cap.get("name") == capability_name for cap in agent["capabilities"])
                    if has_capability:
                        validated_calls.append(call)
                else:
                    # 如果智能体没有能力信息，暂时信任调用请求
                    validated_calls.append(call)
        
        return validated_calls
    
    @performance_monitor.monitor
    def _execute_capability(self, capability_name: str, params: Dict[str, Any], context: ExecutionContext) -> Any:
        """执行模型能力调用"""
        # 获取智能体信息
        agent_id = context.get_context("agent_id")
        agent = self._load_agent(agent_id)
        
        # 检查智能体是否具备该能力
        from app.services.agent_capability_service import AgentCapabilityService
        if not AgentCapabilityService.check_agent_capability(self.db, agent_id, capability_name):
            raise ValueError(f"智能体不具备该能力: {capability_name}")
        
        # 根据能力类型执行不同的逻辑
        if capability_name == "text_generation":
            # 文本生成能力
            return self._execute_text_generation(params, context)
        elif capability_name == "image_generation":
            # 图像生成能力
            return self._execute_image_generation(params, context)
        elif capability_name == "code_generation":
            # 代码生成能力
            return self._execute_code_generation(params, context)
        elif capability_name == "knowledge_retrieval":
            # 知识检索能力
            return self._execute_knowledge_retrieval(params, context)
        else:
            # 默认处理，直接调用模型
            return self._call_model_with_capability(agent, capability_name, params, context)
    
    def _execute_text_generation(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        """执行文本生成能力"""
        # 准备文本生成参数
        messages = params.get("messages", [])
        if not messages:
            raise ValueError("文本生成需要messages参数")
        
        # 调用模型服务
        response = self.llm_service.call_llm(
            model_id=context.get_context("agent").get("model_id"),
            model_version=context.get_context("agent").get("model_version"),
            messages=messages,
            params=params.get("model_params", {})
        )
        
        # 返回响应内容
        return response.get("content", "")
    
    def _execute_image_generation(self, params: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行图像生成能力"""
        # 图像生成能力的具体实现
        # 这里假设我们使用第三方API或内部服务
        prompt = params.get("prompt", "")
        if not prompt:
            raise ValueError("图像生成需要prompt参数")
        
        # 调用图像生成服务
        # 这里仅返回模拟结果
        return {
            "success": True,
            "image_url": f"https://example.com/generated_image?prompt={prompt}",
            "prompt": prompt
        }
    
    def _execute_code_generation(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        """执行代码生成能力"""
        # 代码生成能力的具体实现
        prompt = params.get("prompt", "")
        if not prompt:
            raise ValueError("代码生成需要prompt参数")
        
        # 准备代码生成的messages
        messages = [
            {"role": "system", "content": "你是一个代码生成专家，请根据用户需求生成高质量的代码。"},
            {"role": "user", "content": prompt}
        ]
        
        # 调用模型服务
        response = self.llm_service.call_llm(
            model_id=context.get_context("agent").get("model_id"),
            model_version=context.get_context("agent").get("model_version"),
            messages=messages,
            params={"max_tokens": 2000, "temperature": 0.7}
        )
        
        return response.get("content", "")
    
    def _execute_knowledge_retrieval(self, params: Dict[str, Any], context: ExecutionContext) -> List[Dict[str, Any]]:
        """执行知识检索能力"""
        # 知识检索能力的具体实现
        query = params.get("query", "")
        if not query:
            raise ValueError("知识检索需要query参数")
        
        # 调用知识检索服务
        from app.services.knowledge.retrieval_service import RetrievalService
        retrieval_service = RetrievalService()
        results = retrieval_service.search_documents(query, limit=params.get("top_k", 5))
        
        return results
    
    def _call_model_with_capability(self, agent: Agent, capability_name: str, params: Dict[str, Any], context: ExecutionContext) -> Any:
        """使用特定能力调用模型"""
        # 准备调用参数
        messages = params.get("messages", [])
        if not messages:
            raise ValueError("能力调用需要messages参数")
        
        # 添加能力特定的系统提示词
        capability_system_prompt = f"请以{capability_name}能力专家的身份回应。"
        messages.insert(0, {"role": "system", "content": capability_system_prompt})
        
        # 调用模型
        return self.llm_service.call_llm(
            model_id=agent.model_id,
            model_version=agent.model_version,
            messages=messages,
            params=params.get("model_params", {})
        )
    
    @performance_monitor.monitor
    def _execute_skills(self, skill_calls: List[Dict[str, Any]], context: ExecutionContext) -> Dict[int, Any]:
        """执行技能调用"""
        results = {}
        
        for skill_call in skill_calls:
            skill_id = skill_call.get("skill_id")
            params = skill_call.get("params", {})
            
            if not skill_id:
                continue
            
            # 执行技能
            skill_result = self.skill_execution_engine.execute(
                skill_id=skill_id,
                params=params,
                context=context.get_context()
            )
            
            # 保存技能结果
            results[skill_id] = skill_result
            context.add_skill_result(skill_id, skill_result)
        
        return results
    
    @performance_monitor.monitor
    def _generate_final_response(self, agent: Agent, user_input: str, model_response: Any, 
                                skill_results: Dict[int, Any], capability_results: Dict[str, Any], 
                                context: ExecutionContext) -> str:
        """根据技能结果和能力结果生成最终响应"""
        # 准备最终模型输入
        messages = []
        
        # 添加系统提示词
        if agent.prompt:
            messages.append({"role": "system", "content": agent.prompt})
        
        # 添加对话历史
        history = context.get_context("history")
        for message in history:
            messages.append({
                "role": message.get("role", "user"),
                "content": message.get("content", "")
            })
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        # 添加初始模型响应
        messages.append({
            "role": "assistant", 
            "content": model_response.get("content", "")
        })
        
        # 构建执行结果文本
        execution_results = ""
        
        # 添加技能执行结果
        if skill_results:
            execution_results += "\n技能执行结果：\n"
            for skill_id, result in skill_results.items():
                execution_results += f"\n技能ID {skill_id}: {result.get('result', '')}"
        
        # 添加能力执行结果
        if capability_results:
            execution_results += "\n能力执行结果：\n"
            for capability_name, result in capability_results.items():
                execution_results += f"\n能力 {capability_name}: {str(result)}"
        
        # 如果有执行结果，添加到消息中
        if execution_results:
            messages.append({
                "role": "system", 
                "content": execution_results
            })
        
        # 添加生成最终响应的指令
        messages.append({
            "role": "system", 
            "content": "请根据用户输入、初始模型响应和执行结果，生成一个综合的最终响应。"
        })
        
        # 调用模型生成最终响应
        final_response = self.llm_service.call_llm(
            model_id=agent.model_id,
            model_version=agent.model_version,
            messages=messages,
            params=context.get_context("params")
        )
        
        return final_response.get("content", "")
