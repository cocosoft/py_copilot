"""内存管理工具"""
from typing import Dict, Any, List
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
from app.modules.memory.services.memory_service import MemoryService
import logging

logger = logging.getLogger(__name__)


class MemoryTool(BaseTool):
    """内存管理工具，用于存储和检索对话记忆"""
    
    def __init__(self):
        """初始化工具"""
        self.memory_service = MemoryService()
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        return ToolMetadata(
            name="memory",
            display_name="内存管理",
            description="管理对话记忆，包括存储、检索和清理记忆。适用于：记住用户偏好、保存重要信息、检索历史对话等。",
            category="memory",
            version="1.0.0",
            author="Py Copilot Team",
            icon="🧠",
            tags=["内存", "记忆", "存储"]
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """返回工具参数定义"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=["store", "retrieve", "search", "clear"]
            ),
            ToolParameter(
                name="content",
                type="string",
                description="要存储的内容（store操作需要）",
                required=False
            ),
            ToolParameter(
                name="query",
                type="string",
                description="搜索查询词（search操作需要）",
                required=False
            ),
            ToolParameter(
                name="memory_id",
                type="string",
                description="记忆ID（retrieve和clear操作需要）",
                required=False
            )
        ]
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行内存管理操作"""
        import time
        from sqlalchemy.orm import Session
        from app.core.database import get_db

        start_time = time.time()

        try:
            action = parameters.get("action")

            if action == "store":
                return await self._store_memory(**parameters)
            elif action == "retrieve":
                return await self._retrieve_memory(**parameters)
            elif action == "search":
                return await self._search_memory(**parameters)
            elif action == "clear":
                return await self._clear_memory(**parameters)
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"不支持的操作类型: {action}",
                    execution_time=0.0,
                    tool_name=self._metadata.name
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"内存管理操作失败: {str(e)}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
    
    async def _store_memory(self, **kwargs) -> ToolExecutionResult:
        """存储记忆"""
        import time
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        
        start_time = time.time()
        
        content = kwargs.get("content")
        
        if not content:
            return ToolExecutionResult(
                success=False,
                error="content参数不能为空",
                execution_time=0.0,
                tool_name=self._metadata.name
            )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 存储记忆
            result = await self.memory_service.store_memory(
                content=content,
                metadata=kwargs.get("metadata", {}),
                db=db
            )
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                success=result.get("success", False),
                result=result.get("data"),
                error=result.get("error"),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
        finally:
            db.close()
    
    async def _retrieve_memory(self, **kwargs) -> ToolExecutionResult:
        """检索记忆"""
        import time
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        
        start_time = time.time()
        
        memory_id = kwargs.get("memory_id")
        
        if not memory_id:
            return ToolExecutionResult(
                success=False,
                error="memory_id参数不能为空",
                execution_time=0.0,
                tool_name=self._metadata.name
            )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 检索记忆
            result = await self.memory_service.get_memory(
                memory_id=memory_id,
                db=db
            )
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                success=result.get("success", False),
                result=result.get("data"),
                error=result.get("error"),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
        finally:
            db.close()
    
    async def _search_memory(self, **kwargs) -> ToolExecutionResult:
        """搜索记忆"""
        import time
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        
        start_time = time.time()
        
        query = kwargs.get("query")
        
        if not query:
            return ToolExecutionResult(
                success=False,
                error="query参数不能为空",
                execution_time=0.0,
                tool_name=self._metadata.name
            )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 搜索记忆
            result = await self.memory_service.search_memories(
                query=query,
                limit=kwargs.get("limit", 5),
                db=db
            )
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                success=result.get("success", False),
                result=result.get("data"),
                error=result.get("error"),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
        finally:
            db.close()
    
    async def _clear_memory(self, **kwargs) -> ToolExecutionResult:
        """清理记忆"""
        import time
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        
        start_time = time.time()
        
        memory_id = kwargs.get("memory_id")
        
        if not memory_id:
            return ToolExecutionResult(
                success=False,
                error="memory_id参数不能为空",
                execution_time=0.0,
                tool_name=self._metadata.name
            )
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 清理记忆
            result = await self.memory_service.delete_memory(
                memory_id=memory_id,
                db=db
            )
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                success=result.get("success", False),
                result=result.get("data"),
                error=result.get("error"),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
        finally:
            db.close()
