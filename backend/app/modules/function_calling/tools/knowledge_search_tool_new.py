"""
知识库搜索工具

复用服务：KnowledgeService
提供知识库文档搜索功能
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
from app.modules.knowledge.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(ServiceTool):
    """
    知识库搜索工具
    
    复用服务：KnowledgeService
    提供知识库文档搜索和检索功能
    """
    
    def __init__(self):
        """初始化知识库搜索工具"""
        self._knowledge_service = None
        super().__init__()
    
    def _get_service(self):
        """
        获取知识库服务实例
        
        Returns:
            KnowledgeService: 知识库服务实例
        """
        return KnowledgeService()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="knowledge_search",
            display_name="知识库搜索",
            description="在知识库中搜索文档，支持向量检索和文本匹配",
            category=ToolCategory.KNOWLEDGE.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="📚",
            tags=["知识库", "搜索", "文档检索"],
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
                name="query",
                type="string",
                description="搜索查询词",
                required=True
            ),
            ToolParameter(
                name="knowledge_base_id",
                type="integer",
                description="知识库ID（可选，不指定则搜索所有知识库）",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回结果数量",
                required=False,
                default=10
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行知识库搜索
        
        Args:
            **kwargs: 搜索参数
                - query: 搜索查询词（必需）
                - knowledge_base_id: 知识库ID（可选）
                - limit: 结果数量（可选，默认10）
        
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
            
            # 提取参数
            query = kwargs.get("query")
            knowledge_base_id = kwargs.get("knowledge_base_id")
            limit = kwargs.get("limit", 10)
            
            # 执行搜索
            logger.info(f"执行知识库搜索: query={query}, knowledge_base_id={knowledge_base_id}")
            
            service = self.get_service()
            
            # 注意：这里需要数据库会话，实际使用时需要从调用方传入
            # 或者使用依赖注入获取数据库会话
            # 这里简化处理，返回需要数据库会话的提示
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result={
                    "message": "知识库搜索需要数据库会话支持",
                    "query": query,
                    "knowledge_base_id": knowledge_base_id,
                    "limit": limit,
                    "note": "请在实际使用时传入db参数"
                },
                execution_time=time.time() - start_time,
                metadata={
                    "requires_db": True
                }
            )
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"搜索失败: {str(e)}",
                error_code="SEARCH_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def execute_with_db(
        self,
        db,
        query: str,
        knowledge_base_id: Optional[int] = None,
        limit: int = 10
    ) -> ToolExecutionResult:
        """
        执行知识库搜索（带数据库会话）
        
        Args:
            db: 数据库会话
            query: 搜索查询词
            knowledge_base_id: 知识库ID
            limit: 结果数量
            
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            service = self.get_service()
            results = await service.search_documents_async(
                query=query,
                limit=limit,
                knowledge_base_id=knowledge_base_id,
                db=db
            )
            
            formatted_results = self._format_search_results(results)
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=formatted_results,
                execution_time=time.time() - start_time,
                metadata={
                    "query": query,
                    "knowledge_base_id": knowledge_base_id,
                    "result_count": len(formatted_results)
                }
            )
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"搜索失败: {str(e)}",
                error_code="SEARCH_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化搜索结果
        
        Args:
            results: 原始搜索结果列表
            
        Returns:
            List[Dict[str, Any]]: 格式化后的结果列表
        """
        formatted = []
        
        for item in results:
            formatted.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "content_preview": item.get("content", "")[:500] + "..." if len(item.get("content", "")) > 500 else item.get("content", ""),
                "file_type": item.get("file_type", ""),
                "knowledge_base_id": item.get("knowledge_base_id"),
                "score": item.get("score", 0.0),
                "source": item.get("source", "unknown")
            })
        
        return formatted
