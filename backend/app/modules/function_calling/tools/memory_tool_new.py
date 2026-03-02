"""
记忆管理工具

复用服务：MemoryService
提供记忆的存储、检索、管理功能
"""

from typing import Dict, Any, List, Optional
import time
import logging

from app.modules.function_calling.base_tool import ServiceTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)
from app.modules.memory.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate

logger = logging.getLogger(__name__)


class MemoryTool(ServiceTool):
    """
    记忆管理工具
    
    复用服务：MemoryService
    提供记忆的存储、检索、管理功能
    """
    
    def __init__(self):
        """初始化记忆工具"""
        self._memory_service = None
        super().__init__()
    
    def _get_service(self):
        """
        获取记忆服务实例
        
        Returns:
            MemoryService: 记忆服务实例
        """
        return MemoryService()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="memory",
            display_name="记忆管理",
            description="管理用户记忆，包括存储新记忆、搜索记忆、获取记忆列表等功能",
            category=ToolCategory.MEMORY.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="🧠",
            tags=["记忆", "存储", "检索"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            List[ToolParameter]: 参数定义列表
        """
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=["search", "store", "get", "list"]
            ),
            ToolParameter(
                name="query",
                type="string",
                description="搜索查询词（action=search时使用）",
                required=False
            ),
            ToolParameter(
                name="content",
                type="string",
                description="记忆内容（action=store时使用）",
                required=False
            ),
            ToolParameter(
                name="title",
                type="string",
                description="记忆标题（action=store时使用）",
                required=False
            ),
            ToolParameter(
                name="memory_type",
                type="string",
                description="记忆类型",
                required=False,
                default="SHORT_TERM",
                enum=["SHORT_TERM", "LONG_TERM", "SEMANTIC", "PROCEDURAL"]
            ),
            ToolParameter(
                name="memory_category",
                type="string",
                description="记忆类别",
                required=False,
                default="CONVERSATION",
                enum=["PREFERENCE", "KNOWLEDGE", "CONTEXT", "CONVERSATION"]
            ),
            ToolParameter(
                name="memory_id",
                type="integer",
                description="记忆ID（action=get时使用）",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回结果数量",
                required=False,
                default=10
            ),
            ToolParameter(
                name="user_id",
                type="integer",
                description="用户ID",
                required=True
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行记忆操作
        
        Args:
            **kwargs: 操作参数
                - action: 操作类型（必需）
                - user_id: 用户ID（必需）
                - 其他参数根据action不同而不同
        
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            # 验证参数
            validation_result = self.validate_parameters(**kwargs)
            if not validation_result.is_valid:
                errors = [e.message for e in validation_result.errors]
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"参数验证失败: {'; '.join(errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time=time.time() - start_time
                )
            
            action = kwargs.get("action")
            user_id = kwargs.get("user_id")
            
            logger.info(f"执行记忆操作: action={action}, user_id={user_id}")
            
            # 根据操作类型执行不同逻辑
            if action == "search":
                return await self._handle_search(kwargs, start_time)
            elif action == "store":
                return await self._handle_store(kwargs, start_time)
            elif action == "get":
                return self._handle_get(kwargs, start_time)
            elif action == "list":
                return self._handle_list(kwargs, start_time)
            else:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"不支持的操作类型: {action}",
                    error_code="INVALID_ACTION",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"记忆操作失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"操作失败: {str(e)}",
                error_code="OPERATION_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_search(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理搜索操作"""
        query = kwargs.get("query")
        user_id = kwargs.get("user_id")
        limit = kwargs.get("limit", 10)
        
        if not query:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="搜索操作需要提供query参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "message": "记忆搜索需要数据库会话支持",
                "query": query,
                "user_id": user_id,
                "limit": limit,
                "note": "请在实际使用时传入db参数或使用execute_search_with_db方法"
            },
            execution_time=time.time() - start_time,
            metadata={"requires_db": True}
        )
    
    async def _handle_store(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理存储操作"""
        content = kwargs.get("content")
        user_id = kwargs.get("user_id")
        
        if not content:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="存储操作需要提供content参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "message": "记忆存储需要数据库会话支持",
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "user_id": user_id,
                "note": "请在实际使用时传入db参数或使用execute_store_with_db方法"
            },
            execution_time=time.time() - start_time,
            metadata={"requires_db": True}
        )
    
    def _handle_get(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理获取操作"""
        memory_id = kwargs.get("memory_id")
        user_id = kwargs.get("user_id")
        
        if not memory_id:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="获取操作需要提供memory_id参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "message": "记忆获取需要数据库会话支持",
                "memory_id": memory_id,
                "user_id": user_id,
                "note": "请在实际使用时传入db参数"
            },
            execution_time=time.time() - start_time,
            metadata={"requires_db": True}
        )
    
    def _handle_list(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理列表操作"""
        user_id = kwargs.get("user_id")
        memory_type = kwargs.get("memory_type")
        limit = kwargs.get("limit", 20)
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "message": "记忆列表获取需要数据库会话支持",
                "user_id": user_id,
                "memory_type": memory_type,
                "limit": limit,
                "note": "请在实际使用时传入db参数"
            },
            execution_time=time.time() - start_time,
            metadata={"requires_db": True}
        )
    
    async def execute_search_with_db(
        self,
        db,
        query: str,
        user_id: int,
        limit: int = 10
    ) -> ToolExecutionResult:
        """
        执行记忆搜索（带数据库会话）
        
        Args:
            db: 数据库会话
            query: 搜索查询词
            user_id: 用户ID
            limit: 结果数量
            
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            service = self.get_service()
            results = await service.search_memories_async(
                db=db,
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=results,
                execution_time=time.time() - start_time,
                metadata={
                    "query": query,
                    "user_id": user_id,
                    "result_count": len(results)
                }
            )
            
        except Exception as e:
            logger.error(f"记忆搜索失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"搜索失败: {str(e)}",
                error_code="SEARCH_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def execute_store_with_db(
        self,
        db,
        content: str,
        user_id: int,
        title: Optional[str] = None,
        memory_type: str = "SHORT_TERM",
        memory_category: str = "CONVERSATION"
    ) -> ToolExecutionResult:
        """
        执行记忆存储（带数据库会话）
        
        Args:
            db: 数据库会话
            content: 记忆内容
            user_id: 用户ID
            title: 记忆标题
            memory_type: 记忆类型
            memory_category: 记忆类别
            
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            service = self.get_service()
            
            memory_data = MemoryCreate(
                title=title or "Memory",
                content=content,
                memory_type=memory_type,
                memory_category=memory_category
            )
            
            result = await service.create_memory_async(db, memory_data, user_id)
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "user_id": user_id,
                    "memory_type": memory_type
                }
            )
            
        except Exception as e:
            logger.error(f"记忆存储失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"存储失败: {str(e)}",
                error_code="STORE_ERROR",
                execution_time=time.time() - start_time
            )
