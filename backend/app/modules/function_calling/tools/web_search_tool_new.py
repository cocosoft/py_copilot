"""
联网搜索工具

复用服务：WebSearchService
提供网络搜索功能
"""

from typing import Dict, Any, List
import time
import logging

from app.modules.function_calling.base_tool import ServiceTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)


class WebSearchTool(ServiceTool):
    """
    联网搜索工具
    
    复用服务：WebSearchService
    提供网络搜索功能，支持多种搜索引擎
    """
    
    def __init__(self):
        """初始化联网搜索工具"""
        self._search_service = None
        super().__init__()
    
    def _get_service(self):
        """
        获取搜索服务实例
        
        Returns:
            WebSearchService: 搜索服务实例
        """
        return web_search_service
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="web_search",
            display_name="联网搜索",
            description="使用搜索引擎查询网络信息，支持Google、Bing、百度等多种搜索引擎",
            category=ToolCategory.SEARCH.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="🔍",
            tags=["搜索", "网络", "信息检索"],
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
                name="engine",
                type="string",
                description="搜索引擎名称",
                required=False,
                default="google",
                enum=["google", "bing", "baidu"]
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="返回结果数量",
                required=False,
                default=5
            ),
            ToolParameter(
                name="safe_search",
                type="boolean",
                description="是否启用安全搜索",
                required=False,
                default=True
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行搜索
        
        Args:
            **kwargs: 搜索参数
                - query: 搜索查询词（必需）
                - engine: 搜索引擎（可选，默认google）
                - num_results: 结果数量（可选，默认5）
                - safe_search: 安全搜索（可选，默认True）
        
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
            engine = kwargs.get("engine", "google")
            num_results = kwargs.get("num_results", 5)
            safe_search = kwargs.get("safe_search", True)
            
            # 检查搜索引擎是否可用
            service = self.get_service()
            if not service.is_engine_available(engine):
                available_engines = service.get_available_engines()
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"搜索引擎 '{engine}' 不可用或未配置API密钥。可用引擎: {', '.join(available_engines) if available_engines else '无'}",
                    error_code="ENGINE_NOT_AVAILABLE",
                    execution_time=time.time() - start_time
                )
            
            # 执行搜索
            logger.info(f"执行联网搜索: query={query}, engine={engine}")
            result = await service.search_async(
                query=query,
                engine=engine,
                num_results=num_results,
                safe_search=safe_search
            )
            
            # 格式化结果
            formatted_result = self._format_search_result(result)
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=formatted_result,
                execution_time=execution_time,
                metadata={
                    "query": query,
                    "engine": engine,
                    "result_count": len(formatted_result.get("results", []))
                }
            )
            
        except Exception as e:
            logger.error(f"联网搜索失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"搜索失败: {str(e)}",
                error_code="SEARCH_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _format_search_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化搜索结果
        
        Args:
            result: 原始搜索结果
            
        Returns:
            Dict[str, Any]: 格式化后的结果
        """
        if not result.get("success", False):
            return {
                "success": False,
                "error": result.get("error", "未知错误"),
                "results": []
            }
        
        results = result.get("results", [])
        formatted_results = []
        
        for item in results:
            formatted_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "relevance_score": item.get("relevance_score", 0.0)
            })
        
        return {
            "success": True,
            "query": result.get("query", ""),
            "engine": result.get("engine", ""),
            "total_results": len(formatted_results),
            "results": formatted_results
        }
