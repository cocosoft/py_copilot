"""
智能体执行引擎

实现智能体的执行、消息处理、上下文管理和能力调度功能。
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from sqlalchemy.orm import Session

from .agent_models import Agent, AgentConfig, AgentCapability, AgentStatus, agent_manager
from app.skills.skill_engine import skill_engine
from app.logging.structured_logger import app_logger
from .knowledge_integration import AgentKnowledgeIntegration, KnowledgeAwareAgentEngine


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    COMMAND = "command"
    FILE = "file"
    IMAGE = "image"
    AUDIO = "audio"
    SYSTEM = "system"


class Message:
    """消息类"""
    
    def __init__(self, 
                 message_id: str = None,
                 content: str = "",
                 message_type: MessageType = MessageType.TEXT,
                 sender: str = "user",
                 timestamp: datetime = None,
                 metadata: Dict[str, Any] = None):
        """初始化消息
        
        Args:
            message_id: 消息ID
            content: 消息内容
            message_type: 消息类型
            sender: 发送者
            timestamp: 时间戳
            metadata: 元数据
        """
        self.message_id = message_id or str(uuid.uuid4())
        self.content = content
        self.message_type = message_type
        self.sender = sender
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            消息字典
        """
        return {
            "message_id": self.message_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, message_dict: Dict[str, Any]) -> 'Message':
        """从字典创建消息对象
        
        Args:
            message_dict: 消息字典
            
        Returns:
            消息对象
        """
        # 解析枚举值
        try:
            message_type = MessageType(message_dict.get("message_type", "text"))
        except ValueError:
            message_type = MessageType.TEXT
            
        # 解析时间戳
        timestamp = datetime.fromisoformat(message_dict["timestamp"]) if message_dict.get("timestamp") else None
        
        return cls(
            message_id=message_dict.get("message_id"),
            content=message_dict.get("content", ""),
            message_type=message_type,
            sender=message_dict.get("sender", "user"),
            timestamp=timestamp,
            metadata=message_dict.get("metadata", {})
        )


class ConversationContext:
    """对话上下文类"""
    
    def __init__(self, 
                 context_id: str = None,
                 agent_id: str = "",
                 user_id: str = "",
                 messages: List[Message] = None,
                 metadata: Dict[str, Any] = None):
        """初始化对话上下文
        
        Args:
            context_id: 上下文ID
            agent_id: 智能体ID
            user_id: 用户ID
            messages: 消息列表
            metadata: 元数据
        """
        self.context_id = context_id or str(uuid.uuid4())
        self.agent_id = agent_id
        self.user_id = user_id
        self.messages = messages or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def add_message(self, message: Message):
        """添加消息
        
        Args:
            message: 消息对象
        """
        self.messages.append(message)
        self.updated_at = datetime.now()
        
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """获取最近的消息
        
        Args:
            limit: 限制数量
            
        Returns:
            最近的消息列表
        """
        return self.messages[-limit:]
        
    def clear_messages(self):
        """清空消息"""
        self.messages.clear()
        self.updated_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            上下文字典
        """
        return {
            "context_id": self.context_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ExecutionResult:
    """执行结果类"""
    
    def __init__(self, 
                 success: bool = True,
                 output: str = "",
                 error_message: str = "",
                 execution_time: float = 0.0,
                 metadata: Dict[str, Any] = None):
        """初始化执行结果
        
        Args:
            success: 是否成功
            output: 输出内容
            error_message: 错误消息
            execution_time: 执行时间（秒）
            metadata: 元数据
        """
        self.success = success
        self.output = output
        self.error_message = error_message
        self.execution_time = execution_time
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            执行结果字典
        """
        return {
            "success": self.success,
            "output": self.output,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


class CapabilityHandler:
    """能力处理器基类"""
    
    def __init__(self, capability: AgentCapability):
        """初始化能力处理器
        
        Args:
            capability: 能力类型
        """
        self.capability = capability
        
    async def execute(self, agent: Agent, context: ConversationContext, 
                     input_data: Any) -> ExecutionResult:
        """执行能力
        
        Args:
            agent: 智能体
            context: 对话上下文
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        raise NotImplementedError("子类必须实现execute方法")


class TextGenerationHandler(CapabilityHandler):
    """文本生成能力处理器"""
    
    def __init__(self):
        """初始化文本生成处理器"""
        super().__init__(AgentCapability.TEXT_GENERATION)
        
    async def execute(self, agent: Agent, context: ConversationContext, 
                     input_data: str) -> ExecutionResult:
        """执行文本生成
        
        Args:
            agent: 智能体
            context: 对话上下文
            input_data: 输入文本
            
        Returns:
            执行结果
        """
        import time
        start_time = time.time()
        
        try:
            # 构建系统提示词
            system_prompt = agent.config.system_prompt
            
            # 构建对话历史
            conversation_history = []
            for msg in context.get_recent_messages(5):
                role = "assistant" if msg.sender == "agent" else "user"
                conversation_history.append({
                    "role": role,
                    "content": msg.content
                })
            
            # 模拟文本生成（实际应该调用AI模型）
            # 这里使用简单的规则生成响应
            response = f"这是智能体 '{agent.name}' 对 '{input_data}' 的响应。"
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                output=response,
                execution_time=execution_time,
                metadata={
                    "model": agent.config.model_name,
                    "temperature": agent.config.temperature,
                    "max_tokens": agent.config.max_tokens
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


class CodeGenerationHandler(CapabilityHandler):
    """代码生成能力处理器"""
    
    def __init__(self):
        """初始化代码生成处理器"""
        super().__init__(AgentCapability.CODE_GENERATION)
        
    async def execute(self, agent: Agent, context: ConversationContext, 
                     input_data: Dict[str, Any]) -> ExecutionResult:
        """执行代码生成
        
        Args:
            agent: 智能体
            context: 对话上下文
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        import time
        start_time = time.time()
        
        try:
            language = input_data.get("language", "python")
            description = input_data.get("description", "")
            
            # 模拟代码生成
            code = f"""# {description}
# 语言: {language}
# 由智能体 '{agent.name}' 生成

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()"""
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                output=code,
                execution_time=execution_time,
                metadata={
                    "language": language,
                    "description": description
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


class DataAnalysisHandler(CapabilityHandler):
    """数据分析能力处理器"""
    
    def __init__(self):
        """初始化数据分析处理器"""
        super().__init__(AgentCapability.DATA_ANALYSIS)
        
    async def execute(self, agent: Agent, context: ConversationContext, 
                     input_data: Dict[str, Any]) -> ExecutionResult:
        """执行数据分析
        
        Args:
            agent: 智能体
            context: 对话上下文
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        import time
        start_time = time.time()
        
        try:
            data = input_data.get("data", [])
            analysis_type = input_data.get("analysis_type", "summary")
            
            # 模拟数据分析
            if analysis_type == "summary":
                result = f"数据分析摘要: 共 {len(data)} 条记录"
            elif analysis_type == "statistics":
                result = "统计数据: 平均值、最大值、最小值等"
            else:
                result = f"执行了 {analysis_type} 分析"
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                output=result,
                execution_time=execution_time,
                metadata={
                    "analysis_type": analysis_type,
                    "data_count": len(data)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


class AgentEngine:
    """智能体执行引擎"""
    
    def __init__(self, db_session: Session = None):
        """初始化智能体执行引擎
        
        Args:
            db_session: 数据库会话（可选）
        """
        self.handlers = {}
        self.conversations = {}  # 对话上下文缓存
        self.db_session = db_session
        
        # 初始化知识库集成（如果提供了数据库会话）
        self.knowledge_integration = None
        self.knowledge_aware_engine = None
        if db_session:
            self.knowledge_integration = AgentKnowledgeIntegration(db_session)
            self.knowledge_aware_engine = KnowledgeAwareAgentEngine(db_session)
        
        self._register_handlers()
        
    def _register_handlers(self):
        """注册能力处理器"""
        self.handlers[AgentCapability.TEXT_GENERATION] = TextGenerationHandler()
        self.handlers[AgentCapability.CODE_GENERATION] = CodeGenerationHandler()
        self.handlers[AgentCapability.DATA_ANALYSIS] = DataAnalysisHandler()
        # 可以注册更多能力处理器
        
    async def process_message(self, agent_id: str, user_id: str, 
                             message: Message) -> ExecutionResult:
        """处理消息
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            message: 消息
            
        Returns:
            执行结果
        """
        import time
        start_time = time.time()
        
        try:
            # 获取智能体
            agent = agent_manager.get_agent(agent_id)
            if not agent:
                raise Exception(f"智能体 {agent_id} 未找到")
                
            # 检查智能体状态
            if agent.status != AgentStatus.ACTIVE:
                raise Exception(f"智能体 {agent_id} 未激活")
                
            # 获取或创建对话上下文
            context_key = f"{agent_id}:{user_id}"
            if context_key not in self.conversations:
                self.conversations[context_key] = ConversationContext(
                    agent_id=agent_id,
                    user_id=user_id
                )
            
            context = self.conversations[context_key]
            
            # 添加用户消息到上下文
            context.add_message(message)
            
            # 根据消息类型选择处理方式
            if message.message_type == MessageType.TEXT:
                result = await self._process_text_message(agent, context, message)
            elif message.message_type == MessageType.COMMAND:
                result = await self._process_command_message(agent, context, message)
            else:
                result = ExecutionResult(
                    success=False,
                    error_message=f"不支持的消息类型: {message.message_type.value}"
                )
            
            # 添加智能体响应到上下文
            if result.success:
                response_message = Message(
                    content=result.output,
                    message_type=MessageType.TEXT,
                    sender="agent",
                    metadata=result.metadata
                )
                context.add_message(response_message)
            
            result.execution_time = time.time() - start_time
            
            # 记录执行日志
            app_logger.info(
                f"智能体消息处理完成",
                {
                    "agent_id": agent_id,
                    "user_id": user_id,
                    "message_type": message.message_type.value,
                    "success": result.success,
                    "execution_time": result.execution_time
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            app_logger.error(
                f"智能体消息处理失败",
                {
                    "agent_id": agent_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
            
    async def _process_text_message(self, agent: Agent, context: ConversationContext, 
                                   message: Message) -> ExecutionResult:
        """处理文本消息
        
        Args:
            agent: 智能体
            context: 对话上下文
            message: 消息
            
        Returns:
            执行结果
        """
        # 检查智能体能力
        if AgentCapability.TEXT_GENERATION not in agent.config.capabilities:
            return ExecutionResult(
                success=False,
                error_message="智能体不支持文本生成能力"
            )
            
        # 如果启用了知识库集成，使用知识感知引擎
        if self.knowledge_aware_engine and self._should_use_knowledge(agent, message):
            # 构建对话上下文
            conversation_context = self._build_conversation_context(context)
            
            # 使用知识感知引擎处理消息
            response = self.knowledge_aware_engine.process_message_with_knowledge(
                agent_id=int(agent.id),
                message=message.content,
                conversation_context=conversation_context
            )
            
            return ExecutionResult(
                success=True,
                output=response,
                metadata={
                    "knowledge_enhanced": True,
                    "model": agent.config.model_name
                }
            )
        else:
            # 使用文本生成能力
            handler = self.handlers[AgentCapability.TEXT_GENERATION]
            return await handler.execute(agent, context, message.content)
    
    def _should_use_knowledge(self, agent: Agent, message: Message) -> bool:
        """判断是否应该使用知识库
        
        Args:
            agent: 智能体
            message: 消息
            
        Returns:
            是否使用知识库
        """
        if not self.knowledge_integration:
            return False
            
        # 检查智能体配置是否启用了知识库
        if agent.config and agent.config.config_data:
            config_data = agent.config.config_data
            if config_data.get('enable_knowledge_integration', False):
                return True
        
        # 检查消息是否需要知识库（基于消息长度和内容）
        message_length = len(message.content)
        if message_length > 10:  # 较长的消息更可能需要知识库
            return True
            
        return False
    
    def _build_conversation_context(self, context: ConversationContext) -> str:
        """构建对话上下文字符串
        
        Args:
            context: 对话上下文
            
        Returns:
            对话上下文字符串
        """
        if not context.messages:
            return ""
            
        # 获取最近5条消息
        recent_messages = context.get_recent_messages(5)
        context_parts = []
        
        for msg in recent_messages:
            role = "用户" if msg.sender == "user" else "智能体"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
        
    async def _process_command_message(self, agent: Agent, context: ConversationContext, 
                                      message: Message) -> ExecutionResult:
        """处理命令消息
        
        Args:
            agent: 智能体
            context: 对话上下文
            message: 消息
            
        Returns:
            执行结果
        """
        try:
            # 解析命令
            command_data = json.loads(message.content)
            command_type = command_data.get("type", "")
            
            if command_type == "code_generation":
                # 代码生成命令
                if AgentCapability.CODE_GENERATION not in agent.config.capabilities:
                    return ExecutionResult(
                        success=False,
                        error_message="智能体不支持代码生成能力"
                    )
                
                handler = self.handlers[AgentCapability.CODE_GENERATION]
                return await handler.execute(agent, context, command_data)
                
            elif command_type == "data_analysis":
                # 数据分析命令
                if AgentCapability.DATA_ANALYSIS not in agent.config.capabilities:
                    return ExecutionResult(
                        success=False,
                        error_message="智能体不支持数据分析能力"
                    )
                
                handler = self.handlers[AgentCapability.DATA_ANALYSIS]
                return await handler.execute(agent, context, command_data)
                
            elif command_type == "skill_execution":
                # 技能执行命令
                skill_name = command_data.get("skill_name", "")
                skill_params = command_data.get("params", {})
                
                # 使用技能引擎执行技能
                skill_result = await skill_engine.execute_skill(skill_name, skill_params)
                
                return ExecutionResult(
                    success=skill_result.success,
                    output=skill_result.output,
                    error_message=skill_result.error_message,
                    metadata={
                        "skill_name": skill_name,
                        "skill_result": skill_result.to_dict()
                    }
                )
                
            else:
                return ExecutionResult(
                    success=False,
                    error_message=f"未知命令类型: {command_type}"
                )
                
        except json.JSONDecodeError:
            return ExecutionResult(
                success=False,
                error_message="命令格式错误，必须是有效的JSON"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )
            
    def get_conversation_context(self, agent_id: str, user_id: str) -> Optional[ConversationContext]:
        """获取对话上下文
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            
        Returns:
            对话上下文，如果未找到返回None
        """
        context_key = f"{agent_id}:{user_id}"
        return self.conversations.get(context_key)
        
    def clear_conversation_context(self, agent_id: str, user_id: str) -> bool:
        """清空对话上下文
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        context_key = f"{agent_id}:{user_id}"
        if context_key in self.conversations:
            del self.conversations[context_key]
            return True
        return False
        
    async def execute_capability(self, agent_id: str, capability: AgentCapability, 
                                input_data: Any, user_id: str = "system") -> ExecutionResult:
        """直接执行智能体能力
        
        Args:
            agent_id: 智能体ID
            capability: 能力类型
            input_data: 输入数据
            user_id: 用户ID
            
        Returns:
            执行结果
        """
        # 获取智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return ExecutionResult(
                success=False,
                error_message=f"智能体 {agent_id} 未找到"
            )
            
        # 检查能力支持
        if capability not in agent.config.capabilities:
            return ExecutionResult(
                success=False,
                error_message=f"智能体不支持能力: {capability.value}"
            )
            
        # 检查处理器
        if capability not in self.handlers:
            return ExecutionResult(
                success=False,
                error_message=f"未注册的能力处理器: {capability.value}"
            )
            
        # 创建临时上下文
        context = ConversationContext(agent_id=agent_id, user_id=user_id)
        
        # 执行能力
        handler = self.handlers[capability]
        return await handler.execute(agent, context, input_data)
        
    def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息
        
        Returns:
            统计信息
        """
        return {
            "handlers_count": len(self.handlers),
            "conversations_count": len(self.conversations),
            "registered_capabilities": [cap.value for cap in self.handlers.keys()],
            "active_conversations": list(self.conversations.keys())
        }


# 全局智能体执行引擎实例
agent_engine = AgentEngine()