# Agent设计方案 - 深度细化文档

本文档对核心模块进行深度细化，包含完整的数据结构、算法逻辑和实现细节。

---

## 一、能力适配器深度实现

### 1.1 Skill能力适配器完整实现

```python
# app/capabilities/adapters/skill_adapter.py

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.capabilities.validators import InputValidator
from app.models.skill import Skill, SkillExecutionLog, SkillArtifact
from app.services.skill_execution_engine import SkillExecutionEngine
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SkillCapability(BaseCapability):
    """
    Skill能力适配器
    
    将现有Skill系统适配为统一Capability接口。
    
    适配映射关系：
    - Skill.name → CapabilityMetadata.name
    - Skill.display_name → CapabilityMetadata.display_name
    - Skill.description → CapabilityMetadata.description
    - Skill.parameters_schema → CapabilityMetadata.input_schema
    - Skill.tags → CapabilityMetadata.tags
    - Skill.dependencies → CapabilityMetadata.dependencies
    
    Attributes:
        skill: 原始Skill模型实例
        execution_engine: Skill执行引擎
        _db_session: 数据库会话
    """
    
    def __init__(self, skill: Skill):
        """
        初始化Skill能力适配器
        
        Args:
            skill: Skill模型实例
        """
        # 处理tags字段（可能是JSON字符串或列表）
        tags = self._parse_tags(skill.tags)
        
        # 构建元数据
        metadata = CapabilityMetadata(
            name=skill.name,
            display_name=skill.display_name or skill.name,
            description=skill.description or "",
            capability_type=CapabilityType.SKILL,
            level=self._determine_level(skill),
            category="skill",
            tags=tags,
            input_schema=skill.parameters_schema or {},
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "artifacts": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            },
            dependencies=[
                dep.dependency_skill.name 
                for dep in skill.dependencies 
                if dep.dependency_skill
            ],
            timeout_seconds=300,  # Skill默认5分钟超时
            max_retries=skill.config.get("max_retries", 3) if skill.config else 3,
            version=skill.version or "1.0.0",
            author=skill.author or "system"
        )
        
        super().__init__(metadata)
        self.skill = skill
        self.execution_engine = SkillExecutionEngine()
        self._db_session = None
    
    def _parse_tags(self, tags) -> list:
        """
        解析tags字段
        
        Args:
            tags: 可能是JSON字符串或列表
            
        Returns:
            list: 标签列表
        """
        if tags is None:
            return []
        
        if isinstance(tags, list):
            return tags
        
        if isinstance(tags, str):
            try:
                return json.loads(tags)
            except json.JSONDecodeError:
                return tags.split(",") if "," in tags else [tags]
        
        return []
    
    def _determine_level(self, skill: Skill) -> CapabilityLevel:
        """
        确定能力级别
        
        根据Skill的复杂度判断：
        - 有execution_flow的视为WORKFLOW
        - 有依赖的视为COMPOSITE
        - 否则为ATOMIC
        
        Args:
            skill: Skill模型
            
        Returns:
            CapabilityLevel: 能力级别
        """
        if skill.execution_flow and len(skill.execution_flow) > 0:
            return CapabilityLevel.WORKFLOW
        
        if skill.dependencies and len(skill.dependencies) > 0:
            return CapabilityLevel.COMPOSITE
        
        return CapabilityLevel.ATOMIC
    
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        执行Skill
        
        完整的执行流程：
        1. 创建执行日志
        2. 调用Skill执行引擎
        3. 处理执行结果
        4. 处理Artifacts
        5. 更新执行日志
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        execution_log = None
        
        try:
            # 1. 创建执行日志
            execution_log = await self._create_execution_log(input_data, context)
            
            # 2. 准备执行参数
            execution_params = {
                "skill_id": self.skill.id,
                "params": input_data,
                "user_id": context.user_id,
                "conversation_id": context.conversation_id,
                "session_id": context.session_id,
                "context": context.context_data
            }
            
            # 3. 调用执行引擎
            logger.info(f"开始执行Skill: {self.skill.name}, log_id={execution_log.id}")
            
            raw_result = await self.execution_engine.execute(**execution_params)
            
            # 4. 解析结果
            success = raw_result.get("status") == "success"
            output = raw_result.get("output", "")
            error = raw_result.get("error")
            
            # 5. 处理Artifacts
            artifacts = []
            if success and "artifacts" in raw_result:
                for artifact_data in raw_result["artifacts"]:
                    artifacts.append({
                        "type": artifact_data.get("type", "unknown"),
                        "name": artifact_data.get("name", ""),
                        "content": artifact_data.get("content", "")[:1000],  # 截断
                        "url": artifact_data.get("url")
                    })
            
            # 6. 更新执行日志
            await self._update_execution_log(
                execution_log,
                success=success,
                output=output,
                error=error
            )
            
            logger.info(f"Skill执行完成: {self.skill.name}, success={success}")
            
            return CapabilityResult(
                success=success,
                output=output if success else None,
                error=error if not success else None,
                artifacts=artifacts,
                metadata={
                    "skill_id": self.skill.id,
                    "skill_name": self.skill.name,
                    "execution_log_id": execution_log.id,
                    "execution_params": execution_params
                }
            )
            
        except Exception as e:
            logger.error(f"Skill执行异常: {self.skill.name}, error={e}", exc_info=True)
            
            # 更新执行日志为失败状态
            if execution_log:
                await self._update_execution_log(
                    execution_log,
                    success=False,
                    error=str(e)
                )
            
            return CapabilityResult(
                success=False,
                error=f"Skill执行异常: {str(e)}",
                metadata={
                    "skill_id": self.skill.id,
                    "skill_name": self.skill.name,
                    "exception_type": type(e).__name__
                }
            )
    
    async def _create_execution_log(self,
                                   input_data: Dict[str, Any],
                                   context: ExecutionContext) -> SkillExecutionLog:
        """
        创建执行日志
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            SkillExecutionLog: 执行日志实例
        """
        db = SessionLocal()
        try:
            log = SkillExecutionLog(
                skill_id=self.skill.id,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                task_description=self.skill.description or "",
                input_params=input_data,
                status="running"
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        finally:
            db.close()
    
    async def _update_execution_log(self,
                                   log: SkillExecutionLog,
                                   success: bool,
                                   output: str = "",
                                   error: str = ""):
        """
        更新执行日志
        
        Args:
            log: 执行日志实例
            success: 是否成功
            output: 输出内容
            error: 错误信息
        """
        db = SessionLocal()
        try:
            log.status = "completed" if success else "failed"
            log.output_result = output
            log.error_message = error
            db.commit()
        finally:
            db.close()
    
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据
        
        使用Skill的parameters_schema进行验证
        
        Args:
            input_data: 输入数据
            
        Returns:
            ValidationResult: 验证结果
        """
        if not self.metadata.input_schema:
            # 没有定义schema，直接通过
            return ValidationResult(valid=True)
        
        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)
    
    async def get_capabilities(self) -> list:
        """
        获取子能力列表
        
        返回依赖的Skill列表
        
        Returns:
            list: 子能力名称列表
        """
        return self.metadata.dependencies
    
    def get_skill_info(self) -> Dict[str, Any]:
        """
        获取Skill详细信息
        
        Returns:
            Dict: Skill信息
        """
        return {
            "id": self.skill.id,
            "name": self.skill.name,
            "display_name": self.skill.display_name,
            "description": self.skill.description,
            "version": self.skill.version,
            "status": self.skill.status,
            "is_official": self.skill.is_official,
            "dependencies_count": len(self.skill.dependencies),
            "usage_count": self.skill.usage_count,
            "last_used_at": self.skill.last_used_at.isoformat() if self.skill.last_used_at else None
        }
```

### 1.2 Tool能力适配器完整实现

```python
# app/capabilities/adapters/tool_adapter.py

import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.capabilities.validators import InputValidator
from app.models.tool import Tool, ToolExecutionLog
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ToolCapability(BaseCapability):
    """
    Tool能力适配器
    
    将现有Tool系统适配为统一Capability接口。
    
    支持三种Tool类型：
    1. local: 本地工具，直接调用处理函数
    2. mcp: MCP工具，通过MCP客户端调用
    3. official: 官方工具，使用内置实现
    
    Attributes:
        tool: 原始Tool模型实例
        _handler: 本地处理函数（仅local类型）
        _mcp_client: MCP客户端（仅mcp类型）
    """
    
    # 本地工具处理函数注册表
    _local_handlers: Dict[str, Callable] = {}
    
    def __init__(self, tool: Tool):
        """
        初始化Tool能力适配器
        
        Args:
            tool: Tool模型实例
        """
        # 处理tags
        tags = self._parse_tags(tool.tags)
        
        # 构建元数据
        metadata = CapabilityMetadata(
            name=tool.name,
            display_name=tool.display_name or tool.name,
            description=tool.description or "",
            capability_type=CapabilityType.TOOL,
            level=CapabilityLevel.ATOMIC,
            category=tool.category or "general",
            tags=tags,
            input_schema=tool.parameters_schema or {},
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "any"},
                    "metadata": {"type": "object"}
                }
            },
            timeout_seconds=30,  # Tool默认30秒超时
            max_retries=2,
            version=tool.version or "1.0.0",
            author=tool.author or "system"
        )
        
        super().__init__(metadata)
        self.tool = tool
        self._handler = None
        self._mcp_client = None
    
    def _parse_tags(self, tags) -> list:
        """解析tags字段"""
        if tags is None:
            return []
        
        if isinstance(tags, list):
            return tags
        
        if isinstance(tags, str):
            try:
                return json.loads(tags)
            except json.JSONDecodeError:
                return []
        
        return []
    
    @classmethod
    def register_local_handler(cls, tool_name: str, handler: Callable):
        """
        注册本地工具处理函数
        
        Args:
            tool_name: 工具名称
            handler: 处理函数
        """
        cls._local_handlers[tool_name] = handler
        logger.info(f"注册本地工具处理器: {tool_name}")
    
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        执行Tool
        
        根据Tool类型选择执行方式
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        execution_log = None
        
        try:
            # 创建执行日志
            execution_log = await self._create_execution_log(input_data, context)
            
            # 根据类型执行
            if self.tool.tool_type == "mcp":
                result = await self._execute_mcp(input_data, context)
            elif self.tool.tool_type == "official":
                result = await self._execute_official(input_data, context)
            else:  # local
                result = await self._execute_local(input_data, context)
            
            # 更新执行日志
            await self._update_execution_log(
                execution_log,
                success=result.success,
                output=str(result.output) if result.output else "",
                error=result.error
            )
            
            # 添加执行日志ID到metadata
            result.metadata["execution_log_id"] = execution_log.id
            
            return result
            
        except Exception as e:
            logger.error(f"Tool执行异常: {self.tool.name}, error={e}", exc_info=True)
            
            if execution_log:
                await self._update_execution_log(
                    execution_log,
                    success=False,
                    error=str(e)
                )
            
            return CapabilityResult(
                success=False,
                error=f"Tool执行异常: {str(e)}",
                metadata={
                    "tool_id": self.tool.id,
                    "tool_name": self.tool.name,
                    "tool_type": self.tool.tool_type
                }
            )
    
    async def _execute_local(self,
                            input_data: Dict[str, Any],
                            context: ExecutionContext) -> CapabilityResult:
        """
        执行本地Tool
        
        通过handler_module和handler_class动态加载处理类
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        # 方法1: 使用注册的处理函数
        if self.tool.name in self._local_handlers:
            handler = self._local_handlers[self.tool.name]
            result = await handler(input_data, context)
            return CapabilityResult(
                success=True,
                output=result
            )
        
        # 方法2: 动态加载处理类
        if self.tool.handler_module and self.tool.handler_class:
            try:
                # 动态导入模块
                module = __import__(
                    self.tool.handler_module,
                    fromlist=[self.tool.handler_class]
                )
                handler_class = getattr(module, self.tool.handler_class)
                handler = handler_class()
                
                # 调用处理方法
                result = await handler.execute(input_data, context)
                
                return CapabilityResult(
                    success=True,
                    output=result
                )
                
            except Exception as e:
                return CapabilityResult(
                    success=False,
                    error=f"加载Tool处理器失败: {str(e)}"
                )
        
        return CapabilityResult(
            success=False,
            error=f"Tool '{self.tool.name}' 没有配置处理器"
        )
    
    async def _execute_mcp(self,
                          input_data: Dict[str, Any],
                          context: ExecutionContext) -> CapabilityResult:
        """
        通过MCP执行Tool
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        try:
            from app.mcp.client.connection_manager import MCPConnectionManager
            
            # 获取MCP客户端
            client = await MCPConnectionManager.get_client(
                self.tool.mcp_client_config_id
            )
            
            if not client:
                return CapabilityResult(
                    success=False,
                    error=f"MCP客户端未连接: config_id={self.tool.mcp_client_config_id}"
                )
            
            # 调用MCP工具
            logger.info(f"调用MCP工具: {self.tool.mcp_tool_name}")
            
            result = await client.call_tool(
                tool_name=self.tool.mcp_tool_name,
                params=input_data
            )
            
            return CapabilityResult(
                success=True,
                output=result,
                metadata={
                    "mcp_client_id": self.tool.mcp_client_config_id,
                    "mcp_tool_name": self.tool.mcp_tool_name
                }
            )
            
        except Exception as e:
            return CapabilityResult(
                success=False,
                error=f"MCP调用失败: {str(e)}"
            )
    
    async def _execute_official(self,
                               input_data: Dict[str, Any],
                               context: ExecutionContext) -> CapabilityResult:
        """
        执行官方Tool
        
        使用内置的官方工具实现
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        # 官方工具映射到具体实现
        official_implementations = {
            "web_search": self._official_web_search,
            "file_reader": self._official_file_reader,
            "email_sender": self._official_email_sender,
            # ... 其他官方工具
        }
        
        implementation = official_implementations.get(self.tool.name)
        
        if implementation:
            return await implementation(input_data, context)
        
        return CapabilityResult(
            success=False,
            error=f"官方工具 '{self.tool.name}' 未实现"
        )
    
    async def _official_web_search(self,
                                  input_data: Dict[str, Any],
                                  context: ExecutionContext) -> CapabilityResult:
        """官方Web搜索实现"""
        query = input_data.get("query", "")
        
        try:
            # 这里集成实际的搜索服务
            # 例如：Google Search API、Bing Search API等
            
            # 模拟搜索结果
            search_results = [
                {"title": "示例结果1", "url": "https://example.com/1", "snippet": "..."},
                {"title": "示例结果2", "url": "https://example.com/2", "snippet": "..."}
            ]
            
            return CapabilityResult(
                success=True,
                output={
                    "query": query,
                    "results": search_results,
                    "total": len(search_results)
                }
            )
            
        except Exception as e:
            return CapabilityResult(
                success=False,
                error=f"搜索失败: {str(e)}"
            )
    
    async def _create_execution_log(self,
                                   input_data: Dict[str, Any],
                                   context: ExecutionContext) -> ToolExecutionLog:
        """创建执行日志"""
        db = SessionLocal()
        try:
            log = ToolExecutionLog(
                tool_id=self.tool.id,
                agent_id=context.agent_id,
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                input_params=input_data,
                status="pending"
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        finally:
            db.close()
    
    async def _update_execution_log(self,
                                   log: ToolExecutionLog,
                                   success: bool,
                                   output: str = "",
                                   error: str = ""):
        """更新执行日志"""
        db = SessionLocal()
        try:
            log.status = "success" if success else "failed"
            log.output_result = output
            log.error_message = error
            db.commit()
        finally:
            db.close()
    
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入"""
        if not self.metadata.input_schema:
            return ValidationResult(valid=True)
        
        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)
```

### 1.3 MCP能力适配器完整实现

```python
# app/capabilities/adapters/mcp_adapter.py

import logging
from typing import Dict, Any, Optional

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.capabilities.validators import InputValidator
from app.mcp.models import MCPClientConfigModel, MCPToolMappingModel
from app.mcp.client.client import MCPClient

logger = logging.getLogger(__name__)


class MCPCapability(BaseCapability):
    """
    MCP能力适配器
    
    将MCP服务封装为统一Capability接口。
    
    每个MCPCapability对应一个MCP工具映射，通过MCPClient
    与外部MCP服务通信。
    
    Attributes:
        client_config: MCP客户端配置
        tool_mapping: MCP工具映射
        _client: MCPClient实例（延迟初始化）
    """
    
    def __init__(self,
                 client_config: MCPClientConfigModel,
                 tool_mapping: MCPToolMappingModel):
        """
        初始化MCP能力适配器
        
        Args:
            client_config: MCP客户端配置
            tool_mapping: MCP工具映射
        """
        metadata = CapabilityMetadata(
            name=tool_mapping.local_name,
            display_name=tool_mapping.local_name,
            description=tool_mapping.description or "",
            capability_type=CapabilityType.MCP,
            level=CapabilityLevel.ATOMIC,
            category="mcp",
            tags=["mcp", "external"],
            input_schema=tool_mapping.input_schema or {},
            timeout_seconds=60,  # MCP默认60秒超时
            max_retries=2
        )
        
        super().__init__(metadata)
        self.client_config = client_config
        self.tool_mapping = tool_mapping
        self._client: Optional[MCPClient] = None
    
    async def _ensure_client(self) -> bool:
        """
        确保MCP客户端已连接
        
        Returns:
            bool: 是否成功连接
        """
        if self._client and self._client.is_connected:
            return True
        
        try:
            self._client = MCPClient(self.client_config)
            connected = await self._client.connect()
            
            if connected:
                logger.info(f"MCP客户端已连接: {self.client_config.name}")
            else:
                logger.error(f"MCP客户端连接失败: {self.client_config.name}")
            
            return connected
            
        except Exception as e:
            logger.error(f"MCP客户端初始化失败: {e}")
            return False
    
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        执行MCP能力
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        try:
            # 确保客户端连接
            if not await self._ensure_client():
                return CapabilityResult(
                    success=False,
                    error=f"无法连接到MCP服务: {self.client_config.name}"
                )
            
            # 调用MCP工具
            logger.info(f"调用MCP工具: {self.tool_mapping.original_name}")
            
            result = await self._client.call_tool(
                tool_name=self.tool_mapping.original_name,
                params=input_data
            )
            
            return CapabilityResult(
                success=True,
                output=result,
                metadata={
                    "mcp_client": self.client_config.name,
                    "mcp_tool": self.tool_mapping.original_name,
                    "local_name": self.tool_mapping.local_name
                }
            )
            
        except Exception as e:
            logger.error(f"MCP调用失败: {e}")
            return CapabilityResult(
                success=False,
                error=f"MCP调用失败: {str(e)}"
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入"""
        if not self.metadata.input_schema:
            return ValidationResult(valid=True)
        
        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)
    
    async def disconnect(self):
        """断开MCP连接"""
        if self._client:
            await self._client.disconnect()
            self._client = None
```

---

## 二、意图理解引擎深度实现

### 2.1 多维度意图分类器

```python
# app/orchestration/intent_classification.py

from typing import Dict, Any, List, Tuple
from enum import Enum
import re

from app.services.llm_service import LLMService


class IntentCategory(Enum):
    """意图主分类"""
    QUERY = "query"              # 查询类
    ACTION = "action"            # 操作类
    CREATION = "creation"        # 创作类
    ANALYSIS = "analysis"        # 分析类
    CONVERSATION = "conversation"  # 对话类


class IntentSubCategory(Enum):
    """意图子分类"""
    # 查询类
    INFORMATION_SEARCH = "information_search"
    KNOWLEDGE_QUERY = "knowledge_query"
    STATUS_CHECK = "status_check"
    
    # 操作类
    TASK_EXECUTION = "task_execution"
    CONFIGURATION = "configuration"
    NOTIFICATION = "notification"
    
    # 创作类
    CONTENT_WRITING = "content_writing"
    MEDIA_GENERATION = "media_generation"
    DOCUMENT_CREATION = "document_creation"
    
    # 分析类
    DATA_ANALYSIS = "data_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"


class IntentClassifier:
    """
    多维度意图分类器
    
    结合规则匹配和LLM分类，提供高准确率的意图识别
    """
    
    # 规则模式定义
    RULE_PATTERNS = {
        IntentCategory.QUERY: {
            "patterns": [
                r".*?(查询|搜索|查找|什么是|怎么样|如何|为什么).*",
                r".*?([几|多少|什么|谁|哪里|何时]).*",
            ],
            "keywords": ["查询", "搜索", "查找", "什么是", "怎么样", "如何"]
        },
        IntentCategory.ACTION: {
            "patterns": [
                r".*?(帮我|请|需要|想要|执行|运行|启动|停止).*",
            ],
            "keywords": ["帮我", "请", "执行", "运行", "发送", "设置"]
        },
        IntentCategory.CREATION: {
            "patterns": [
                r".*?(生成|创建|制作|写|画|设计).*",
            ],
            "keywords": ["生成", "创建", "制作", "写", "画", "设计", "生成"]
        },
        IntentCategory.ANALYSIS: {
            "patterns": [
                r".*?(分析|统计|对比|比较|评估|预测).*",
            ],
            "keywords": ["分析", "统计", "对比", "比较", "评估"]
        }
    }
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def classify(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        多维度意图分类
        
        策略：
        1. 先使用规则快速匹配
        2. 规则不确定时使用LLM分类
        3. 结合历史上下文提高准确率
        
        Args:
            text: 输入文本
            context: 上下文信息
            
        Returns:
            Dict: 分类结果
        """
        # 1. 规则匹配
        rule_result = self._rule_based_classify(text)
        
        # 2. 如果规则置信度高，直接返回
        if rule_result["confidence"] > 0.8:
            return rule_result
        
        # 3. 使用LLM分类
        llm_result = await self._llm_classify(text, context)
        
        # 4. 融合结果
        final_result = self._fuse_results(rule_result, llm_result)
        
        return final_result
    
    def _rule_based_classify(self, text: str) -> Dict[str, Any]:
        """
        基于规则的分类
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 分类结果
        """
        scores = {}
        
        for category, rules in self.RULE_PATTERNS.items():
            score = 0
            
            # 模式匹配
            for pattern in rules["patterns"]:
                if re.match(pattern, text, re.IGNORECASE):
                    score += 0.5
            
            # 关键词匹配
            for keyword in rules["keywords"]:
                if keyword in text:
                    score += 0.3
            
            scores[category] = min(1.0, score)
        
        # 找出最高分
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        return {
            "category": best_category.value,
            "confidence": best_score,
            "method": "rule",
            "all_scores": {k.value: v for k, v in scores.items()}
        }
    
    async def _llm_classify(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        基于LLM的分类
        
        Args:
            text: 输入文本
            context: 上下文信息
            
        Returns:
            Dict: 分类结果
        """
        prompt = f"""
        请分析以下用户输入的意图，选择最匹配的类别。
        
        用户输入："{text}"
        
        可选类别：
        - query: 查询类（搜索信息、询问问题）
        - action: 操作类（执行任务、设置配置）
        - creation: 创作类（生成内容、创建文档）
        - analysis: 分析类（数据分析、趋势预测）
        - conversation: 对话类（闲聊、问候）
        
        请输出JSON格式：
        {{
            "category": "类别",
            "confidence": 0.95,
            "reason": "分类理由"
        }}
        """
        
        try:
            result = await self.llm_service.generate_json(prompt)
            return {
                "category": result.get("category", "conversation"),
                "confidence": result.get("confidence", 0.5),
                "method": "llm",
                "reason": result.get("reason", "")
            }
        except Exception as e:
            return {
                "category": "conversation",
                "confidence": 0.3,
                "method": "llm",
                "error": str(e)
            }
    
    def _fuse_results(self, rule_result: Dict, llm_result: Dict) -> Dict[str, Any]:
        """
        融合规则和LLM的结果
        
        Args:
            rule_result: 规则分类结果
            llm_result: LLM分类结果
            
        Returns:
            Dict: 融合后的结果
        """
        # 如果两者一致，提高置信度
        if rule_result["category"] == llm_result["category"]:
            return {
                "category": rule_result["category"],
                "confidence": min(1.0, (rule_result["confidence"] + llm_result["confidence"]) / 2 + 0.1),
                "method": "fused",
                "rule_confidence": rule_result["confidence"],
                "llm_confidence": llm_result["confidence"]
            }
        
        # 如果不一致，选择置信度高的
        if rule_result["confidence"] > llm_result["confidence"]:
            return {
                "category": rule_result["category"],
                "confidence": rule_result["confidence"] * 0.9,  # 降低置信度
                "method": "fused_rule",
                "alternative": llm_result["category"]
            }
        else:
            return {
                "category": llm_result["category"],
                "confidence": llm_result["confidence"],
                "method": "fused_llm",
                "alternative": rule_result["category"]
            }
```

### 2.2 实体提取器

```python
# app/orchestration/entity_extraction.py

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class Entity:
    """实体定义"""
    type: str
    value: Any
    start: int
    end: int
    confidence: float
    normalized_value: Any = None


class EntityExtractor:
    """
    多策略实体提取器
    
    结合正则表达式、模式匹配和LLM提取实体
    """
    
    # 预定义实体模式
    ENTITY_PATTERNS = {
        "time": {
            "patterns": [
                (r"(\d{4})年(\d{1,2})月(\d{1,2})日", "date"),
                (r"(\d{1,2})月(\d{1,2})日", "date_short"),
                (r"(明天|今天|昨天|后天|大后天)", "relative_date"),
                (r"(\d{1,2}):(\d{2})", "time"),
                (r"(早上|上午|中午|下午|晚上)(\d{1,2})点", "time_period"),
            ]
        },
        "number": {
            "patterns": [
                (r"(\d+\.?\d*)\s*(个|件|张|份|次|小时|分钟|天)", "quantity"),
                (r"(\d+\.?\d*)%", "percentage"),
                (r"(\d+\.?\d*)元", "money"),
            ]
        },
        "email": {
            "patterns": [
                (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "email"),
            ]
        },
        "url": {
            "patterns": [
                (r"https?://[^\s]+", "url"),
                (r"www\.[^\s]+", "url_short"),
            ]
        },
        "phone": {
            "patterns": [
                (r"1[3-9]\d{9}", "mobile"),
                (r"\d{3,4}-\d{7,8}", "landline"),
            ]
        }
    }
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def extract(self, text: str, context: Dict[str, Any] = None) -> List[Entity]:
        """
        提取实体
        
        Args:
            text: 输入文本
            context: 上下文
            
        Returns:
            List[Entity]: 实体列表
        """
        entities = []
        
        # 1. 基于规则的提取
        rule_entities = self._extract_by_rules(text)
        entities.extend(rule_entities)
        
        # 2. 基于LLM的提取（复杂实体）
        llm_entities = await self._extract_by_llm(text, context)
        entities.extend(llm_entities)
        
        # 3. 去重和排序
        entities = self._deduplicate_entities(entities)
        
        # 4. 规范化
        for entity in entities:
            entity.normalized_value = self._normalize_entity(entity)
        
        return entities
    
    def _extract_by_rules(self, text: str) -> List[Entity]:
        """基于规则提取实体"""
        entities = []
        
        for entity_type, config in self.ENTITY_PATTERNS.items():
            for pattern, subtype in config["patterns"]:
                for match in re.finditer(pattern, text):
                    entity = Entity(
                        type=f"{entity_type}.{subtype}",
                        value=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9
                    )
                    entities.append(entity)
        
        return entities
    
    async def _extract_by_llm(self, text: str, context: Dict[str, Any] = None) -> List[Entity]:
        """基于LLM提取实体"""
        prompt = f"""
        请从以下文本中提取关键实体。
        
        文本："{text}"
        
        需要提取的实体类型：
        - person: 人物名称
        - organization: 组织/公司/部门名称
        - location: 地点
        - product: 产品/服务名称
        - event: 事件/活动
        - concept: 概念/主题
        
        请输出JSON格式：
        {{
            "entities": [
                {{
                    "type": "实体类型",
                    "value": "实体值",
                    "start": 0,
                    "end": 5
                }}
            ]
        }}
        """
        
        try:
            result = await self.llm_service.generate_json(prompt)
            
            entities = []
            for entity_data in result.get("entities", []):
                entity = Entity(
                    type=entity_data["type"],
                    value=entity_data["value"],
                    start=entity_data.get("start", -1),
                    end=entity_data.get("end", -1),
                    confidence=0.8
                )
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            return []
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """去重实体"""
        # 按位置排序
        entities.sort(key=lambda e: (e.start, -e.end))
        
        # 去重（保留置信度高的）
        seen = {}
        for entity in entities:
            key = (entity.start, entity.end)
            if key not in seen or seen[key].confidence < entity.confidence:
                seen[key] = entity
        
        return list(seen.values())
    
    def _normalize_entity(self, entity: Entity) -> Any:
        """规范化实体值"""
        if entity.type.startswith("time"):
            return self._normalize_time(entity.value)
        elif entity.type.startswith("number"):
            return self._normalize_number(entity.value)
        
        return entity.value
    
    def _normalize_time(self, value: str) -> Dict[str, Any]:
        """规范化时间"""
        # 解析相对时间
        relative_dates = {
            "今天": 0,
            "明天": 1,
            "后天": 2,
            "大后天": 3,
            "昨天": -1
        }
        
        if value in relative_dates:
            from datetime import timedelta
            target_date = datetime.now() + timedelta(days=relative_dates[value])
            return {
                "type": "relative",
                "value": value,
                "normalized": target_date.strftime("%Y-%m-%d")
            }
        
        return {"type": "absolute", "value": value}
    
    def _normalize_number(self, value: str) -> Dict[str, Any]:
        """规范化数字"""
        # 提取数字和单位
        match = re.match(r"(\d+\.?\d*)\s*(.*)", value)
        if match:
            return {
                "number": float(match.group(1)),
                "unit": match.group(2)
            }
        
        return {"value": value}
```

---

## 三、任务规划优化策略

### 3.1 任务分解策略

```python
# app/orchestration/task_decomposition.py

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class DecompositionStrategy(Enum):
    """任务分解策略"""
    SEQUENTIAL = "sequential"      # 顺序分解
    PARALLEL = "parallel"          # 并行分解
    HIERARCHICAL = "hierarchical"  # 层次分解
    CONDITIONAL = "conditional"    # 条件分解


@dataclass
class SubTask:
    """子任务定义"""
    id: str
    name: str
    description: str
    dependencies: List[str]
    estimated_time: int  # 估计执行时间（秒）
    required_capabilities: List[str]
    input_requirements: List[str]
    output_productions: List[str]
    can_parallel: bool = False


class TaskDecomposer:
    """
    智能任务分解器
    
    根据任务特征选择最优分解策略
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def decompose(self,
                       task_description: str,
                       complexity: int,
                       context: Dict[str, Any] = None) -> List[SubTask]:
        """
        分解任务
        
        Args:
            task_description: 任务描述
            complexity: 复杂度（1-4）
            context: 上下文
            
        Returns:
            List[SubTask]: 子任务列表
        """
        # 根据复杂度选择策略
        if complexity <= 2:
            return await self._simple_decompose(task_description)
        elif complexity == 3:
            return await self._moderate_decompose(task_description, context)
        else:
            return await self._complex_decompose(task_description, context)
    
    async def _simple_decompose(self, task_description: str) -> List[SubTask]:
        """
        简单任务分解（1-2步）
        
        使用规则快速分解
        """
        # 识别常见模式
        patterns = [
            {
                "pattern": ["搜索", "然后", "生成"],
                "steps": [
                    {"name": "信息收集", "capability": "web_search"},
                    {"name": "内容生成", "capability": "content_creation"}
                ]
            },
            {
                "pattern": ["分析", "数据"],
                "steps": [
                    {"name": "数据获取", "capability": "data_retrieval"},
                    {"name": "数据分析", "capability": "data_analysis"}
                ]
            }
        ]
        
        # 匹配模式
        for pattern_def in patterns:
            if all(p in task_description for p in pattern_def["pattern"]):
                return [
                    SubTask(
                        id=f"step_{i}",
                        name=step["name"],
                        description=f"执行{step['name']}",
                        dependencies=[f"step_{i-1}"] if i > 0 else [],
                        estimated_time=30,
                        required_capabilities=[step["capability"]],
                        input_requirements=[],
                        output_productions=[],
                        can_parallel=False
                    )
                    for i, step in enumerate(pattern_def["steps"])
                ]
        
        # 默认单步
        return [SubTask(
            id="step_0",
            name="执行任务",
            description=task_description,
            dependencies=[],
            estimated_time=30,
            required_capabilities=[],
            input_requirements=[],
            output_productions=[]
        )]
    
    async def _moderate_decompose(self,
                                 task_description: str,
                                 context: Dict[str, Any]) -> List[SubTask]:
        """
        中等复杂度任务分解（3-5步）
        
        使用LLM辅助分解
        """
        prompt = f"""
        请将以下任务分解为3-5个具体的执行步骤。
        
        任务：{task_description}
        
        要求：
        1. 每个步骤应该是原子的、可执行的
        2. 明确步骤之间的依赖关系
        3. 估计每个步骤的执行时间
        4. 识别可以并行执行的步骤
        
        请输出JSON格式：
        {{
            "steps": [
                {{
                    "id": "step_1",
                    "name": "步骤名称",
                    "description": "详细描述",
                    "dependencies": [],
                    "estimated_time": 30,
                    "required_capabilities": ["capability_name"],
                    "can_parallel": false
                }}
            ]
        }}
        """
        
        result = await self.llm_service.generate_json(prompt)
        
        subtasks = []
        for step_data in result.get("steps", []):
            subtask = SubTask(
                id=step_data["id"],
                name=step_data["name"],
                description=step_data["description"],
                dependencies=step_data.get("dependencies", []),
                estimated_time=step_data.get("estimated_time", 30),
                required_capabilities=step_data.get("required_capabilities", []),
                input_requirements=[],
                output_productions=[],
                can_parallel=step_data.get("can_parallel", False)
            )
            subtasks.append(subtask)
        
        return subtasks
    
    async def _complex_decompose(self,
                                task_description: str,
                                context: Dict[str, Any]) -> List[SubTask]:
        """
        复杂任务分解（5步以上）
        
        使用层次化分解
        """
        # 先分解为阶段
        phases_prompt = f"""
        请将以下复杂任务分解为几个主要阶段。
        
        任务：{task_description}
        
        请输出JSON格式：
        {{
            "phases": [
                {{
                    "name": "阶段名称",
                    "description": "阶段描述",
                    "objective": "阶段目标"
                }}
            ]
        }}
        """
        
        phases_result = await self.llm_service.generate_json(phases_prompt)
        
        # 然后分解每个阶段
        all_subtasks = []
        for i, phase in enumerate(phases_result.get("phases", [])):
            phase_tasks = await self._decompose_phase(phase, i)
            all_subtasks.extend(phase_tasks)
        
        return all_subtasks
    
    async def _decompose_phase(self, phase: Dict[str, str], phase_index: int) -> List[SubTask]:
        """分解单个阶段"""
        prompt = f"""
        请将以下阶段分解为具体的执行步骤。
        
        阶段：{phase['name']}
        描述：{phase['description']}
        目标：{phase['objective']}
        
        请输出JSON格式：
        {{
            "steps": [
                {{
                    "id": "p{phase_index}_step_1",
                    "name": "步骤名称",
                    "description": "详细描述",
                    "dependencies": []
                }}
            ]
        }}
        """
        
        result = await self.llm_service.generate_json(prompt)
        
        subtasks = []
        for step_data in result.get("steps", []):
            subtask = SubTask(
                id=step_data["id"],
                name=step_data["name"],
                description=step_data["description"],
                dependencies=[
                    f"p{phase_index}_{dep}" if not dep.startswith("p") else dep
                    for dep in step_data.get("dependencies", [])
                ],
                estimated_time=30,
                required_capabilities=[],
                input_requirements=[],
                output_productions=[]
            )
            subtasks.append(subtask)
        
        return subtasks
```

---

## 四、能力发现与匹配算法

### 4.1 语义匹配算法

```python
# app/capabilities/matching/semantic_matcher.py

from typing import Dict, Any, List, Tuple
import numpy as np


class SemanticMatcher:
    """
    语义匹配器
    
    使用向量相似度计算查询与能力的语义匹配度
    """
    
    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self._capability_embeddings: Dict[str, np.ndarray] = {}
    
    async def index_capability(self,
                              capability_name: str,
                              description: str,
                              tags: List[str]):
        """
        索引能力
        
        为能力生成语义向量
        
        Args:
            capability_name: 能力名称
            description: 能力描述
            tags: 能力标签
        """
        # 构建文本
        text = f"{capability_name}. {description}. Tags: {', '.join(tags)}"
        
        # 生成向量
        embedding = await self.embedding_service.embed(text)
        
        self._capability_embeddings[capability_name] = embedding
    
    async def match(self,
                   query: str,
                   top_k: int = 5,
                   min_score: float = 0.3) -> List[Tuple[str, float]]:
        """
        语义匹配
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            min_score: 最小匹配分数
            
        Returns:
            List[Tuple[str, float]]: (能力名称, 匹配分数)列表
        """
        # 生成查询向量
        query_embedding = await self.embedding_service.embed(query)
        
        # 计算相似度
        scores = []
        for name, embedding in self._capability_embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= min_score:
                scores.append((name, float(similarity)))
        
        # 排序并返回top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class EmbeddingService:
    """向量嵌入服务"""
    
    async def embed(self, text: str) -> np.ndarray:
        """
        生成文本向量
        
        这里应该集成实际的embedding模型
        例如：OpenAI、BERT、Sentence-BERT等
        """
        # 模拟实现
        # 实际应该调用embedding API
        import hashlib
        
        # 使用文本哈希生成确定性向量（仅用于演示）
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val)
        
        return np.random.randn(384)  # 384维向量
```

### 4.2 多维度匹配融合

```python
# app/capabilities/matching/fusion_matcher.py

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class MatchResult:
    """匹配结果"""
    capability_name: str
    semantic_score: float
    tag_score: float
    history_score: float
    scene_score: float
    final_score: float
    match_reason: str


class FusionMatcher:
    """
    融合匹配器
    
    融合多种匹配策略的结果
    """
    
    # 权重配置
    WEIGHTS = {
        "semantic": 0.4,
        "tag": 0.2,
        "history": 0.2,
        "scene": 0.2
    }
    
    def __init__(self):
        self.semantic_matcher = SemanticMatcher()
        self.tag_matcher = TagMatcher()
        self.history_matcher = HistoryMatcher()
        self.scene_matcher = SceneMatcher()
    
    async def match(self,
                   query: str,
                   user_id: int,
                   scene: str = None,
                   top_k: int = 5) -> List[MatchResult]:
        """
        多维度融合匹配
        
        Args:
            query: 查询文本
            user_id: 用户ID
            scene: 场景
            top_k: 返回结果数
            
        Returns:
            List[MatchResult]: 匹配结果列表
        """
        # 1. 语义匹配
        semantic_matches = await self.semantic_matcher.match(query, top_k=10)
        semantic_dict = {name: score for name, score in semantic_matches}
        
        # 2. 标签匹配
        tag_matches = await self.tag_matcher.match(query, top_k=10)
        tag_dict = {name: score for name, score in tag_matches}
        
        # 3. 历史匹配
        history_matches = await self.history_matcher.match(user_id, query, top_k=10)
        history_dict = {name: score for name, score in history_matches}
        
        # 4. 场景匹配
        scene_dict = {}
        if scene:
            scene_matches = await self.scene_matcher.match(scene, top_k=10)
            scene_dict = {name: score for name, score in scene_matches}
        
        # 5. 融合所有匹配结果
        all_capabilities = set()
        all_capabilities.update(semantic_dict.keys())
        all_capabilities.update(tag_dict.keys())
        all_capabilities.update(history_dict.keys())
        all_capabilities.update(scene_dict.keys())
        
        results = []
        for cap_name in all_capabilities:
            semantic_score = semantic_dict.get(cap_name, 0)
            tag_score = tag_dict.get(cap_name, 0)
            history_score = history_dict.get(cap_name, 0)
            scene_score = scene_dict.get(cap_name, 0)
            
            # 加权融合
            final_score = (
                semantic_score * self.WEIGHTS["semantic"] +
                tag_score * self.WEIGHTS["tag"] +
                history_score * self.WEIGHTS["history"] +
                scene_score * self.WEIGHTS["scene"]
            )
            
            # 生成匹配理由
            reason = self._generate_reason(
                semantic_score, tag_score, history_score, scene_score
            )
            
            results.append(MatchResult(
                capability_name=cap_name,
                semantic_score=semantic_score,
                tag_score=tag_score,
                history_score=history_score,
                scene_score=scene_score,
                final_score=final_score,
                match_reason=reason
            ))
        
        # 排序并返回
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_k]
    
    def _generate_reason(self,
                        semantic_score: float,
                        tag_score: float,
                        history_score: float,
                        scene_score: float) -> str:
        """生成匹配理由"""
        reasons = []
        
        if semantic_score > 0.7:
            reasons.append("语义高度匹配")
        elif semantic_score > 0.5:
            reasons.append("语义相关")
        
        if tag_score > 0.7:
            reasons.append("标签匹配")
        
        if history_score > 0.7:
            reasons.append("历史使用频繁")
        
        if scene_score > 0.7:
            reasons.append("当前场景推荐")
        
        return "; ".join(reasons) if reasons else "综合匹配"
```

---

## 五、执行引擎容错机制

### 5.1 重试策略

```python
# app/orchestration/resilience/retry_policy.py

import asyncio
import random
from typing import Callable, Any
from enum import Enum


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"           # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"         # 线性增长


class RetryPolicy:
    """
    重试策略配置
    """
    
    def __init__(self,
                 max_retries: int = 3,
                 strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 retryable_exceptions: tuple = (Exception,)):
        """
        初始化重试策略
        
        Args:
            max_retries: 最大重试次数
            strategy: 重试策略
            base_delay: 基础延迟（秒）
            max_delay: 最大延迟（秒）
            retryable_exceptions: 可重试的异常类型
        """
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行带重试的函数
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数返回值
            
        Raises:
            Exception: 重试耗尽后抛出最后一次异常
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
                
            except self.retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    print(f"执行失败，{delay}秒后重试（{attempt + 1}/{self.max_retries}）: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"重试耗尽，最终失败: {e}")
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟
        
        Args:
            attempt: 当前尝试次数（从0开始）
            
        Returns:
            float: 延迟时间（秒）
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
            
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
            
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        
        else:
            delay = self.base_delay
        
        # 添加随机抖动（避免惊群效应）
        jitter = random.uniform(0, 0.1 * delay)
        delay += jitter
        
        # 限制最大延迟
        return min(delay, self.max_delay)
```

### 5.2 熔断器模式

```python
# app/orchestration/resilience/circuit_breaker.py

import time
from typing import Callable, Any
from enum import Enum


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 关闭（正常）
    OPEN = "open"          # 打开（熔断）
    HALF_OPEN = "half_open"  # 半开（尝试恢复）


class CircuitBreaker:
    """
    熔断器
    
    防止级联故障，保护系统稳定性
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值（触发熔断）
            recovery_timeout: 恢复超时时间（秒）
            half_open_max_calls: 半开状态最大尝试次数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        调用受保护的函数
        
        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数返回值
            
        Raises:
            CircuitBreakerOpen: 熔断器打开时抛出
        """
        # 检查状态
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._enter_half_open()
            else:
                raise CircuitBreakerOpen("熔断器已打开，服务暂时不可用")
        
        elif self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpen("半开状态尝试次数已用完")
            self.half_open_calls += 1
        
        # 执行调用
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """处理成功"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # 连续成功，关闭熔断器
            if self.success_count >= self.half_open_max_calls:
                self._close_circuit()
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """处理失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # 半开状态失败，重新打开
            self._open_circuit()
        elif self.failure_count >= self.failure_threshold:
            # 达到失败阈值，打开熔断器
            self._open_circuit()
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _enter_half_open(self):
        """进入半开状态"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        print("熔断器进入半开状态，尝试恢复")
    
    def _open_circuit(self):
        """打开熔断器"""
        self.state = CircuitState.OPEN
        print(f"熔断器已打开（失败次数: {self.failure_count}）")
    
    def _close_circuit(self):
        """关闭熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        print("熔断器已关闭，服务恢复正常")


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""
    pass
```

---

## 六、性能优化策略

### 6.1 缓存策略

```python
# app/capabilities/caching/capability_cache.py

import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta


class CapabilityCache:
    """
    能力结果缓存
    
    缓存能力执行结果，提高响应速度
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存
        
        Args:
            ttl_seconds: 缓存过期时间（秒）
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any