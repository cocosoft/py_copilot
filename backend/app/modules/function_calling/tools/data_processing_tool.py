"""数据处理工具"""
from typing import List, Optional
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
import logging

logger = logging.getLogger(__name__)


class DataProcessingTool(BaseTool):
    """数据处理工具"""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="data_processing",
            display_name="数据处理工具",
            description="提供数据处理功能，包括JSON解析、数据转换、排序、过滤等操作",
            category="data_processing",
            version="1.0.0",
            icon="📊",
            tags=["data", "processing", "json", "conversion", "filtering"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="处理动作：parse_json, stringify_json, sort_array, filter_array, get_keys, get_values, merge_objects",
                required=True,
                default="parse_json"
            ),
            ToolParameter(
                name="data",
                type="string",
                description="要处理的数据（JSON字符串或文本）",
                required=True
            ),
            ToolParameter(
                name="key",
                type="string",
                description="用于过滤或排序的键名（可选）",
                required=False
            ),
            ToolParameter(
                name="value",
                type="string",
                description="用于过滤的值（可选）",
                required=False
            )
        ]
    
    async def execute(self, parameters: dict) -> ToolExecutionResult:
        """
        执行数据处理
        
        Args:
            parameters: 工具参数
                - action: 处理动作
                - data: 要处理的数据
                - key: 键名（可选）
                - value: 值（可选）
                
        Returns:
            工具执行结果
        """
        import time
        import json
        start_time = time.time()
        
        try:
            action = parameters.get("action", "parse_json")
            data_str = parameters.get("data", "")
            key = parameters.get("key")
            value = parameters.get("value")
            
            if not data_str:
                return ToolExecutionResult(
                    success=False,
                    error="数据不能为空",
                    error_code="DATA_001",
                    execution_time=time.time() - start_time,
                    tool_name=self._metadata.name
                )
            
            result = {}
            
            if action == "parse_json":
                try:
                    data = json.loads(data_str)
                    result = {
                        "parsed_data": data,
                        "data_type": type(data).__name__,
                        "action": "parse_json"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            elif action == "stringify_json":
                try:
                    data = json.loads(data_str)
                    json_str = json.dumps(data, ensure_ascii=False, indent=2)
                    result = {
                        "json_string": json_str,
                        "action": "stringify_json"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            elif action == "sort_array":
                try:
                    data = json.loads(data_str)
                    if not isinstance(data, list):
                        return ToolExecutionResult(
                            success=False,
                            error="数据必须是数组类型",
                            error_code="DATA_003",
                            execution_time=time.time() - start_time,
                            tool_name=self._metadata.name
                        )
                    
                    if key and all(isinstance(item, dict) and key in item for item in data):
                        sorted_data = sorted(data, key=lambda x: x[key])
                    else:
                        sorted_data = sorted(data)
                    
                    result = {
                        "original_data": data,
                        "sorted_data": sorted_data,
                        "action": "sort_array"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            elif action == "filter_array":
                try:
                    data = json.loads(data_str)
                    if not isinstance(data, list):
                        return ToolExecutionResult(
                            success=False,
                            error="数据必须是数组类型",
                            error_code="DATA_003",
                            execution_time=time.time() - start_time,
                            tool_name=self._metadata.name
                        )
                    
                    if key and value is not None:
                        filtered_data = [item for item in data if isinstance(item, dict) and item.get(key) == value]
                    else:
                        filtered_data = data
                    
                    result = {
                        "original_data": data,
                        "filtered_data": filtered_data,
                        "filter_count": len(filtered_data),
                        "action": "filter_array"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            elif action == "get_keys":
                try:
                    data = json.loads(data_str)
                    if not isinstance(data, dict):
                        return ToolExecutionResult(
                            success=False,
                            error="数据必须是对象类型",
                            error_code="DATA_004",
                            execution_time=time.time() - start_time,
                            tool_name=self._metadata.name
                        )
                    
                    result = {
                        "keys": list(data.keys()),
                        "key_count": len(data),
                        "action": "get_keys"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            elif action == "get_values":
                try:
                    data = json.loads(data_str)
                    if not isinstance(data, dict):
                        return ToolExecutionResult(
                            success=False,
                            error="数据必须是对象类型",
                            error_code="DATA_004",
                            execution_time=time.time() - start_time,
                            tool_name=self._metadata.name
                        )
                    
                    result = {
                        "values": list(data.values()),
                        "value_count": len(data),
                        "action": "get_values"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            elif action == "merge_objects":
                try:
                    data = json.loads(data_str)
                    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                        return ToolExecutionResult(
                            success=False,
                            error="数据必须是对象数组",
                            error_code="DATA_005",
                            execution_time=time.time() - start_time,
                            tool_name=self._metadata.name
                        )
                    
                    merged = {}
                    for item in data:
                        merged.update(item)
                    
                    result = {
                        "merged_object": merged,
                        "action": "merge_objects"
                    }
                except json.JSONDecodeError as e:
                    return ToolExecutionResult(
                        success=False,
                        error=f"JSON解析失败: {str(e)}",
                        error_code="DATA_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"不支持的动作: {action}",
                    error_code="DATA_006",
                    execution_time=time.time() - start_time,
                    tool_name=self._metadata.name
                )
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time,
                tool_name=self._metadata.name
            )
            
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            return ToolExecutionResult(
                success=False,
                error=f"数据处理失败: {str(e)}",
                error_code="DATA_007",
                execution_time=time.time() - start_time,
                tool_name=self._metadata.name
            )
