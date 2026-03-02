"""
计算器工具

提供数学计算、表达式求值、单位转换等功能
"""

from typing import Dict, Any, List
import time
import logging
import math
import re

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """
    计算器工具
    
    提供数学计算、表达式求值、单位转换等功能
    """
    
    def __init__(self):
        """初始化计算器工具"""
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="calculator",
            display_name="计算器",
            description="提供数学计算、表达式求值、单位转换等功能",
            category=ToolCategory.CALCULATION.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="🧮",
            tags=["计算", "数学", "表达式"],
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
                name="expression",
                type="string",
                description="数学表达式",
                required=True
            ),
            ToolParameter(
                name="precision",
                type="integer",
                description="结果精度（小数位数）",
                required=False,
                default=10
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="操作类型（可选，用于特定计算）",
                required=False,
                enum=["basic", "scientific", "statistical", "conversion"]
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行计算
        
        Args:
            **kwargs: 计算参数
                - expression: 数学表达式（必需）
                - precision: 结果精度（可选）
                - operation: 操作类型（可选）
        
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
            
            expression = kwargs.get("expression")
            precision = kwargs.get("precision", 10)
            operation = kwargs.get("operation", "basic")
            
            logger.info(f"执行计算: expression={expression}, operation={operation}")
            
            # 根据操作类型执行不同计算
            if operation == "statistical":
                result = self._calculate_statistical(expression)
            elif operation == "conversion":
                result = self._calculate_conversion(expression)
            else:
                result = self._evaluate_expression(expression, precision)
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "expression": expression,
                    "operation": operation
                }
            )
            
        except Exception as e:
            logger.error(f"计算失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"计算失败: {str(e)}",
                error_code="CALCULATION_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _evaluate_expression(self, expression: str, precision: int) -> Dict[str, Any]:
        """
        求值数学表达式
        
        Args:
            expression: 数学表达式
            precision: 精度
            
        Returns:
            Dict[str, Any]: 计算结果
        """
        # 清理表达式
        cleaned_expr = self._sanitize_expression(expression)
        
        # 定义安全的数学函数和常量
        safe_dict = {
            'abs': abs,
            'round': round,
            'max': max,
            'min': min,
            'sum': sum,
            'pow': pow,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'log': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'exp': math.exp,
            'ceil': math.ceil,
            'floor': math.floor,
            'pi': math.pi,
            'e': math.e,
            'degrees': math.degrees,
            'radians': math.radians,
            'factorial': math.factorial
        }
        
        try:
            # 使用eval计算（在安全环境下）
            result = eval(cleaned_expr, {"__builtins__": {}}, safe_dict)
            
            # 格式化结果
            if isinstance(result, float):
                formatted_result = round(result, precision)
            else:
                formatted_result = result
            
            return {
                "expression": expression,
                "cleaned_expression": cleaned_expr,
                "result": formatted_result,
                "type": type(result).__name__,
                "precision": precision
            }
            
        except Exception as e:
            raise ValueError(f"表达式求值失败: {str(e)}")
    
    def _sanitize_expression(self, expression: str) -> str:
        """
        清理和验证表达式
        
        Args:
            expression: 原始表达式
            
        Returns:
            str: 清理后的表达式
        """
        # 移除潜在危险字符
        # 只允许数字、运算符、括号、数学函数名和常量
        allowed_pattern = r'[^0-9a-zA-Z_+\-*/().,\s\[\]\^%]'
        cleaned = re.sub(allowed_pattern, '', expression)
        
        # 替换 ^ 为 **（幂运算）
        cleaned = cleaned.replace('^', '**')
        
        return cleaned.strip()
    
    def _calculate_statistical(self, expression: str) -> Dict[str, Any]:
        """
        计算统计信息
        
        Args:
            expression: 逗号分隔的数字列表
            
        Returns:
            Dict[str, Any]: 统计结果
        """
        try:
            # 解析数字列表
            numbers = [float(x.strip()) for x in expression.split(',')]
            
            if not numbers:
                raise ValueError("数字列表为空")
            
            n = len(numbers)
            mean = sum(numbers) / n
            
            # 方差
            variance = sum((x - mean) ** 2 for x in numbers) / n
            std_dev = math.sqrt(variance)
            
            # 中位数
            sorted_nums = sorted(numbers)
            if n % 2 == 0:
                median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
            else:
                median = sorted_nums[n//2]
            
            return {
                "operation": "statistical",
                "data": numbers,
                "count": n,
                "sum": sum(numbers),
                "mean": round(mean, 6),
                "median": round(median, 6),
                "variance": round(variance, 6),
                "std_dev": round(std_dev, 6),
                "min": min(numbers),
                "max": max(numbers),
                "range": max(numbers) - min(numbers)
            }
            
        except Exception as e:
            raise ValueError(f"统计计算失败: {str(e)}")
    
    def _calculate_conversion(self, expression: str) -> Dict[str, Any]:
        """
        单位转换
        
        Args:
            expression: 转换表达式，格式如 "100 km to miles" 或 "25 C to F"
            
        Returns:
            Dict[str, Any]: 转换结果
        """
        # 解析转换表达式
        match = re.match(r'([\d.]+)\s*(\w+)\s+(?:to|in)\s+(\w+)', expression.lower())
        
        if not match:
            raise ValueError("转换表达式格式错误，请使用格式: '100 km to miles'")
        
        value = float(match.group(1))
        from_unit = match.group(2)
        to_unit = match.group(3)
        
        # 定义转换因子
        conversions = {
            # 长度
            ('km', 'miles'): 0.621371,
            ('miles', 'km'): 1.60934,
            ('m', 'ft'): 3.28084,
            ('ft', 'm'): 0.3048,
            ('cm', 'in'): 0.393701,
            ('in', 'cm'): 2.54,
            # 重量
            ('kg', 'lbs'): 2.20462,
            ('lbs', 'kg'): 0.453592,
            ('g', 'oz'): 0.035274,
            ('oz', 'g'): 28.3495,
            # 温度
            ('c', 'f'): lambda c: c * 9/5 + 32,
            ('f', 'c'): lambda f: (f - 32) * 5/9,
            ('c', 'k'): lambda c: c + 273.15,
            ('k', 'c'): lambda k: k - 273.15,
            # 体积
            ('l', 'gal'): 0.264172,
            ('gal', 'l'): 3.78541,
            ('ml', 'fl_oz'): 0.033814,
            ('fl_oz', 'ml'): 29.5735
        }
        
        key = (from_unit, to_unit)
        
        if key not in conversions:
            raise ValueError(f"不支持的转换: {from_unit} to {to_unit}")
        
        converter = conversions[key]
        
        if callable(converter):
            result = converter(value)
        else:
            result = value * converter
        
        return {
            "operation": "conversion",
            "original_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": round(result, 6),
            "expression": expression
        }
