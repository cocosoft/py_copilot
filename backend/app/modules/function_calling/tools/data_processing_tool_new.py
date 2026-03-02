"""
数据处理工具

提供数据转换、格式化、验证、分析等功能
"""

from typing import Dict, Any, List, Optional
import time
import logging
import json
import csv
import io
import re

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class DataProcessingTool(BaseTool):
    """
    数据处理工具
    
    提供数据转换、格式化、验证、分析等功能
    """
    
    def __init__(self):
        """初始化数据处理工具"""
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="data_processing",
            display_name="数据处理",
            description="提供数据转换、格式化、验证、分析等功能",
            category=ToolCategory.DATA.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="📊",
            tags=["数据", "处理", "转换", "分析"],
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
                enum=[
                    "json_to_csv", "csv_to_json",
                    "format_json", "validate_json",
                    "extract_fields", "filter_data",
                    "sort_data", "aggregate"
                ]
            ),
            ToolParameter(
                name="data",
                type="string",
                description="输入数据",
                required=True
            ),
            ToolParameter(
                name="options",
                type="object",
                description="操作选项",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行数据处理
        
        Args:
            **kwargs: 处理参数
                - action: 操作类型（必需）
                - data: 输入数据（必需）
                - options: 操作选项（可选）
        
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
            data = kwargs.get("data")
            options = kwargs.get("options", {})
            
            logger.info(f"执行数据处理: action={action}")
            
            # 根据操作类型执行不同逻辑
            if action == "json_to_csv":
                result = self._json_to_csv(data, options)
            elif action == "csv_to_json":
                result = self._csv_to_json(data, options)
            elif action == "format_json":
                result = self._format_json(data, options)
            elif action == "validate_json":
                result = self._validate_json(data)
            elif action == "extract_fields":
                result = self._extract_fields(data, options)
            elif action == "filter_data":
                result = self._filter_data(data, options)
            elif action == "sort_data":
                result = self._sort_data(data, options)
            elif action == "aggregate":
                result = self._aggregate(data, options)
            else:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"不支持的操作类型: {action}",
                    error_code="INVALID_ACTION",
                    execution_time=time.time() - start_time
                )
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "action": action,
                    "input_size": len(str(data))
                }
            )
            
        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"处理失败: {str(e)}",
                error_code="PROCESSING_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _json_to_csv(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """JSON转CSV"""
        try:
            json_data = json.loads(data)
            
            if not isinstance(json_data, list):
                raise ValueError("JSON数据必须是数组格式")
            
            if not json_data:
                raise ValueError("JSON数据为空")
            
            # 获取所有字段
            headers = list(json_data[0].keys())
            
            # 创建CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerows(json_data)
            
            csv_content = output.getvalue()
            
            return {
                "csv": csv_content,
                "row_count": len(json_data),
                "column_count": len(headers),
                "headers": headers
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def _csv_to_json(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """CSV转JSON"""
        try:
            input_stream = io.StringIO(data)
            reader = csv.DictReader(input_stream)
            
            rows = list(reader)
            
            # 尝试转换数字类型
            for row in rows:
                for key, value in row.items():
                    try:
                        if '.' in value:
                            row[key] = float(value)
                        else:
                            row[key] = int(value)
                    except (ValueError, TypeError):
                        pass
            
            return {
                "json": rows,
                "row_count": len(rows),
                "column_count": len(rows[0].keys()) if rows else 0,
                "headers": list(rows[0].keys()) if rows else []
            }
            
        except Exception as e:
            raise ValueError(f"CSV解析失败: {str(e)}")
    
    def _format_json(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """格式化JSON"""
        try:
            json_data = json.loads(data)
            indent = options.get("indent", 2)
            sort_keys = options.get("sort_keys", False)
            
            formatted = json.dumps(
                json_data,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=False
            )
            
            return {
                "formatted": formatted,
                "original_size": len(data),
                "formatted_size": len(formatted)
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def _validate_json(self, data: str) -> Dict[str, Any]:
        """验证JSON"""
        try:
            json_data = json.loads(data)
            
            # 分析JSON结构
            def analyze_structure(obj, path=""):
                structure = {}
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if isinstance(value, (dict, list)):
                            structure[current_path] = analyze_structure(value, current_path)
                        else:
                            structure[current_path] = type(value).__name__
                elif isinstance(obj, list):
                    if obj:
                        structure[path + "[]"] = analyze_structure(obj[0], path + "[]")
                    else:
                        structure[path + "[]"] = "empty_array"
                return structure
            
            structure = analyze_structure(json_data)
            
            return {
                "valid": True,
                "type": type(json_data).__name__,
                "structure": structure,
                "size": len(data)
            }
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "column": e.colno
            }
    
    def _extract_fields(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """提取字段"""
        try:
            json_data = json.loads(data)
            fields = options.get("fields", [])
            
            if not fields:
                raise ValueError("需要提供fields选项")
            
            def extract(obj, field_path):
                """递归提取字段"""
                parts = field_path.split(".")
                current = obj
                
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list) and part.isdigit():
                        idx = int(part)
                        if idx < len(current):
                            current = current[idx]
                        else:
                            return None
                    else:
                        return None
                
                return current
            
            if isinstance(json_data, list):
                extracted = []
                for item in json_data:
                    item_data = {}
                    for field in fields:
                        item_data[field] = extract(item, field)
                    extracted.append(item_data)
            else:
                extracted = {}
                for field in fields:
                    extracted[field] = extract(json_data, field)
            
            return {
                "extracted": extracted,
                "fields": fields
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def _filter_data(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """过滤数据"""
        try:
            json_data = json.loads(data)
            condition = options.get("condition")
            field = options.get("field")
            value = options.get("value")
            operator = options.get("operator", "equals")
            
            if not isinstance(json_data, list):
                raise ValueError("数据必须是数组格式")
            
            def matches(item):
                if field:
                    item_value = item.get(field) if isinstance(item, dict) else item
                else:
                    item_value = item
                
                if operator == "equals":
                    return item_value == value
                elif operator == "contains":
                    return value in str(item_value)
                elif operator == "starts_with":
                    return str(item_value).startswith(str(value))
                elif operator == "ends_with":
                    return str(item_value).endswith(str(value))
                elif operator == "greater_than":
                    return float(item_value) > float(value)
                elif operator == "less_than":
                    return float(item_value) < float(value)
                elif operator == "regex":
                    return bool(re.search(value, str(item_value)))
                
                return False
            
            filtered = [item for item in json_data if matches(item)]
            
            return {
                "filtered": filtered,
                "original_count": len(json_data),
                "filtered_count": len(filtered)
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def _sort_data(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """排序数据"""
        try:
            json_data = json.loads(data)
            sort_by = options.get("sort_by")
            reverse = options.get("reverse", False)
            
            if not isinstance(json_data, list):
                raise ValueError("数据必须是数组格式")
            
            if sort_by:
                sorted_data = sorted(
                    json_data,
                    key=lambda x: x.get(sort_by) if isinstance(x, dict) else x,
                    reverse=reverse
                )
            else:
                sorted_data = sorted(json_data, reverse=reverse)
            
            return {
                "sorted": sorted_data,
                "count": len(sorted_data),
                "sort_by": sort_by,
                "reverse": reverse
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def _aggregate(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """聚合数据"""
        try:
            json_data = json.loads(data)
            group_by = options.get("group_by")
            aggregate_field = options.get("aggregate_field")
            aggregate_func = options.get("aggregate_func", "count")
            
            if not isinstance(json_data, list):
                raise ValueError("数据必须是数组格式")
            
            if not group_by:
                # 全局聚合
                if aggregate_field:
                    values = [item.get(aggregate_field, 0) for item in json_data if isinstance(item, dict)]
                else:
                    values = json_data
                
                return self._calculate_aggregate(values, aggregate_func, "total")
            
            # 分组聚合
            groups = {}
            for item in json_data:
                if isinstance(item, dict):
                    key = item.get(group_by)
                    if key not in groups:
                        groups[key] = []
                    if aggregate_field:
                        groups[key].append(item.get(aggregate_field, 0))
            
            results = {}
            for key, values in groups.items():
                results[key] = self._calculate_aggregate(values, aggregate_func, key)
            
            return {
                "aggregated": results,
                "group_by": group_by,
                "aggregate_field": aggregate_field,
                "aggregate_func": aggregate_func
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def _calculate_aggregate(self, values: List, func: str, name: str) -> Dict[str, Any]:
        """计算聚合值"""
        if not values:
            return {"count": 0}
        
        numeric_values = [v for v in values if isinstance(v, (int, float))]
        
        if func == "count":
            return {"count": len(values)}
        elif func == "sum":
            return {"sum": sum(numeric_values)} if numeric_values else {"sum": 0}
        elif func == "avg":
            return {"avg": sum(numeric_values) / len(numeric_values)} if numeric_values else {"avg": 0}
        elif func == "min":
            return {"min": min(numeric_values)} if numeric_values else {"min": None}
        elif func == "max":
            return {"max": max(numeric_values)} if numeric_values else {"max": None}
        
        return {"count": len(values)}
