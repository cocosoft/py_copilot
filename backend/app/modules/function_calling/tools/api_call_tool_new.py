"""
API调用工具

提供HTTP请求功能，支持GET、POST等方法
"""

from typing import Dict, Any, List, Optional
import time
import logging
import json

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class APICallTool(BaseTool):
    """
    API调用工具
    
    提供HTTP请求功能，支持GET、POST、PUT、DELETE等方法
    """
    
    def __init__(self):
        """初始化API调用工具"""
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="api_call",
            display_name="API调用",
            description="发送HTTP请求，支持GET、POST、PUT、DELETE等方法",
            category=ToolCategory.API.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="🌐",
            tags=["API", "HTTP", "请求"],
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
                name="url",
                type="string",
                description="请求URL",
                required=True
            ),
            ToolParameter(
                name="method",
                type="string",
                description="HTTP方法",
                required=False,
                default="GET",
                enum=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="请求头",
                required=False
            ),
            ToolParameter(
                name="params",
                type="object",
                description="URL参数",
                required=False
            ),
            ToolParameter(
                name="data",
                type="object",
                description="请求体数据（JSON对象）",
                required=False
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="超时时间（秒）",
                required=False,
                default=30
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行API调用
        
        Args:
            **kwargs: 请求参数
                - url: 请求URL（必需）
                - method: HTTP方法（可选，默认GET）
                - headers: 请求头（可选）
                - params: URL参数（可选）
                - data: 请求体数据（可选）
                - timeout: 超时时间（可选，默认30）
        
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
            
            url = kwargs.get("url")
            method = kwargs.get("method", "GET")
            headers = kwargs.get("headers", {})
            params = kwargs.get("params", {})
            data = kwargs.get("data")
            timeout = kwargs.get("timeout", 30)
            
            logger.info(f"执行API调用: {method} {url}")
            
            # 执行请求
            result = await self._make_request(
                url=url,
                method=method,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout
            )
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "url": url,
                    "method": method,
                    "status_code": result.get("status_code")
                }
            )
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"请求失败: {str(e)}",
                error_code="REQUEST_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _make_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            method: HTTP方法
            headers: 请求头
            params: URL参数
            data: 请求体数据
            timeout: 超时时间
            
        Returns:
            Dict[str, Any]: 响应结果
        """
        import aiohttp
        
        # 设置默认请求头
        default_headers = {
            "User-Agent": "PyCopilot-API-Tool/1.0"
        }
        
        # 合并请求头
        merged_headers = {**default_headers, **headers}
        
        # 如果有数据且没有Content-Type，设置为JSON
        if data and "Content-Type" not in merged_headers:
            merged_headers["Content-Type"] = "application/json"
        
        async with aiohttp.ClientSession() as session:
            request_kwargs = {
                "headers": merged_headers,
                "params": params,
                "timeout": aiohttp.ClientTimeout(total=timeout)
            }
            
            # 添加请求体
            if data:
                request_kwargs["json"] = data
            
            async with session.request(method, url, **request_kwargs) as response:
                # 读取响应内容
                content_type = response.headers.get("Content-Type", "")
                
                if "application/json" in content_type:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                else:
                    response_data = await response.text()
                
                # 构建响应头字典
                response_headers = dict(response.headers)
                
                return {
                    "status_code": response.status,
                    "status": f"{response.status} {response.reason}",
                    "headers": response_headers,
                    "data": response_data,
                    "url": str(response.url),
                    "method": method,
                    "success": 200 <= response.status < 300
                }
