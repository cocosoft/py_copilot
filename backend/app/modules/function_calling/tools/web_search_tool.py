"""Web搜索工具"""
from typing import Dict, Any, List
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
from app.services.web_search_service import web_search_service
import logging

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Web搜索工具，用于搜索网络信息"""
    
    def _get_metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        return ToolMetadata(
            name="web_search",
            display_name="Web搜索",
            description="当用户的问题需要最新的网络信息时使用此工具。适用于：时事新闻、最新数据、产品信息、技术文档、实时数据等场景。",
            category="search",
            version="1.0.0",
            author="Py Copilot Team",
            icon="🔍",
            tags=["搜索", "网络", "实时"]
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """返回工具参数定义"""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索查询词，应该简洁明确地表达用户的搜索意图",
                required=True
            ),
            ToolParameter(
                name="engine",
                type="string",
                description="搜索引擎",
                required=False,
                default="google",
                enum=["google", "bing", "baidu"]
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="返回结果数量",
                required=False,
                default=5,
                enum=[1, 3, 5, 10]
            )
        ]
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行Web搜索"""
        import time
        
        start_time = time.time()
        
        try:
            query = parameters.get("query")
            engine = parameters.get("engine", "google")
            num_results = parameters.get("num_results", 5)
            
            if not query:
                return ToolExecutionResult(
                    success=False,
                    error="搜索查询词不能为空",
                    execution_time=0.0,
                    tool_name=self._metadata.name
                )
            
            logger.info(f"执行Web搜索: query={query}, engine={engine}")
            
            # 执行搜索
            search_result = web_search_service.search(
                query=query,
                engine=engine,
                safe_search=True,
                num_results=num_results
            )
            
            execution_time = time.time() - start_time
            
            if search_result.get("success"):
                return ToolExecutionResult(
                    success=True,
                    result=search_result.get("results", []),
                    execution_time=execution_time,
                    tool_name=self._metadata.name,
                    metadata={
                        "query": query,
                        "engine": engine,
                        "num_results": len(search_result.get("results", []))
                    }
                )
            else:
                return ToolExecutionResult(
                    success=False,
                    error=search_result.get("error", "搜索失败"),
                    execution_time=execution_time,
                    tool_name=self._metadata.name
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Web搜索执行失败: {str(e)}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )
