"""知识库搜索工具"""
from typing import Dict, Any, List
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
from app.modules.knowledge.services.knowledge_service import KnowledgeService
import logging

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(BaseTool):
    """知识库搜索工具，用于搜索项目知识库"""
    
    def __init__(self):
        """初始化工具"""
        self.knowledge_service = KnowledgeService()
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        return ToolMetadata(
            name="knowledge_search",
            display_name="知识库搜索",
            description="搜索项目知识库中的文档和信息。适用于：查找项目文档、技术规范、API文档、使用指南等。",
            category="knowledge",
            version="1.0.0",
            author="Py Copilot Team",
            icon="📚",
            tags=["知识库", "文档", "搜索"]
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """返回工具参数定义"""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索查询词",
                required=True
            ),
            ToolParameter(
                name="knowledge_base_id",
                type="string",
                description="知识库ID，不指定则搜索所有知识库",
                required=False
            ),
            ToolParameter(
                name="top_k",
                type="integer",
                description="返回结果数量",
                required=False,
                default=5
            )
        ]
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行知识库搜索"""
        import time
        from sqlalchemy.orm import Session
        from app.core.database import get_db

        start_time = time.time()

        try:
            query = parameters.get("query")
            knowledge_base_id = parameters.get("knowledge_base_id")
            top_k = parameters.get("top_k", 5)
            
            if not query:
                return ToolExecutionResult(
                    success=False,
                    error="搜索查询词不能为空",
                    execution_time=0.0,
                    tool_name=self._metadata.name
                )
            
            logger.info(f"执行知识库搜索: query={query}")
            
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 执行搜索
                search_result = await self.knowledge_service.search(
                    query=query,
                    knowledge_base_id=int(knowledge_base_id) if knowledge_base_id else None,
                    top_k=top_k,
                    db=db
                )
                
                execution_time = time.time() - start_time
                
                if search_result.get("success"):
                    return ToolExecutionResult(
                        success=True,
                        result=search_result.get("results", []),
                        execution_time=execution_time,
                        tool_name=self._metadata.name
                    )
                else:
                    return ToolExecutionResult(
                        success=False,
                        error=search_result.get("error", "搜索失败"),
                        execution_time=execution_time,
                        tool_name=self._metadata.name
                    )
            finally:
                db.close()
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"知识库搜索执行失败: {str(e)}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
