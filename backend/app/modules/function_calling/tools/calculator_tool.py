"""计算器工具"""
from typing import List, Optional
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
import logging

logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """计算器工具"""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator",
            display_name="计算器工具",
            description="提供基本数学计算功能，包括加减乘除、幂运算、平方根等",
            category="utility",
            version="1.0.0",
            icon="🧮",
            tags=["calculator", "math", "computation", "arithmetic"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type="string",
                description="运算操作：add, subtract, multiply, divide, power, sqrt, abs, round",
                required=True,
                default="add"
            ),
            ToolParameter(
                name="a",
                type="number",
                description="第一个数字",
                required=True
            ),
            ToolParameter(
                name="b",
                type="number",
                description="第二个数字（对于sqrt、abs、round操作不需要）",
                required=False
            ),
            ToolParameter(
                name="precision",
                type="integer",
                description="小数位数（仅用于round操作）",
                required=False,
                default=2
            )
        ]
    
    async def execute(self, parameters: dict) -> ToolExecutionResult:
        """
        执行计算
        
        Args:
            parameters: 工具参数
                - operation: 运算操作
                - a: 第一个数字
                - b: 第二个数字（可选）
                - precision: 小数位数（可选）
                
        Returns:
            工具执行结果
        """
        import time
        import math
        start_time = time.time()
        
        try:
            operation = parameters.get("operation", "add")
            a = parameters.get("a")
            b = parameters.get("b")
            precision = parameters.get("precision", 2)
            
            if a is None:
                return ToolExecutionResult(
                    success=False,
                    error="参数a不能为空",
                    error_code="CALC_001",
                    execution_time=time.time() - start_time,
                    tool_name=self._metadata.name
                )
            
            try:
                a = float(a)
            except (ValueError, TypeError):
                return ToolExecutionResult(
                    success=False,
                    error=f"参数a必须是数字: {a}",
                    error_code="CALC_002",
                    execution_time=time.time() - start_time,
                    tool_name=self._metadata.name
                )
            
            result = {}
            
            if operation == "add":
                if b is None:
                    return ToolExecutionResult(
                        success=False,
                        error="加法操作需要两个数字",
                        error_code="CALC_003",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                try:
                    b = float(b)
                except (ValueError, TypeError):
                    return ToolExecutionResult(
                        success=False,
                        error=f"参数b必须是数字: {b}",
                        error_code="CALC_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                result = {
                    "operation": "addition",
                    "a": a,
                    "b": b,
                    "result": a + b,
                    "formula": f"{a} + {b} = {a + b}"
                }
            elif operation == "subtract":
                if b is None:
                    return ToolExecutionResult(
                        success=False,
                        error="减法操作需要两个数字",
                        error_code="CALC_003",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                try:
                    b = float(b)
                except (ValueError, TypeError):
                    return ToolExecutionResult(
                        success=False,
                        error=f"参数b必须是数字: {b}",
                        error_code="CALC_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                result = {
                    "operation": "subtraction",
                    "a": a,
                    "b": b,
                    "result": a - b,
                    "formula": f"{a} - {b} = {a - b}"
                }
            elif operation == "multiply":
                if b is None:
                    return ToolExecutionResult(
                        success=False,
                        error="乘法操作需要两个数字",
                        error_code="CALC_003",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                try:
                    b = float(b)
                except (ValueError, TypeError):
                    return ToolExecutionResult(
                        success=False,
                        error=f"参数b必须是数字: {b}",
                        error_code="CALC_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                result = {
                    "operation": "multiplication",
                    "a": a,
                    "b": b,
                    "result": a * b,
                    "formula": f"{a} × {b} = {a * b}"
                }
            elif operation == "divide":
                if b is None:
                    return ToolExecutionResult(
                        success=False,
                        error="除法操作需要两个数字",
                        error_code="CALC_003",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                try:
                    b = float(b)
                except (ValueError, TypeError):
                    return ToolExecutionResult(
                        success=False,
                        error=f"参数b必须是数字: {b}",
                        error_code="CALC_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                if b == 0:
                    return ToolExecutionResult(
                        success=False,
                        error="除数不能为零",
                        error_code="CALC_004",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                result = {
                    "operation": "division",
                    "a": a,
                    "b": b,
                    "result": a / b,
                    "formula": f"{a} ÷ {b} = {a / b}"
                }
            elif operation == "power":
                if b is None:
                    return ToolExecutionResult(
                        success=False,
                        error="幂运算需要两个数字",
                        error_code="CALC_003",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                try:
                    b = float(b)
                except (ValueError, TypeError):
                    return ToolExecutionResult(
                        success=False,
                        error=f"参数b必须是数字: {b}",
                        error_code="CALC_002",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                result = {
                    "operation": "power",
                    "base": a,
                    "exponent": b,
                    "result": a ** b,
                    "formula": f"{a}^{b} = {a ** b}"
                }
            elif operation == "sqrt":
                if a < 0:
                    return ToolExecutionResult(
                        success=False,
                        error="不能对负数求平方根",
                        error_code="CALC_005",
                        execution_time=time.time() - start_time,
                        tool_name=self._metadata.name
                    )
                result = {
                    "operation": "square_root",
                    "number": a,
                    "result": math.sqrt(a),
                    "formula": f"√{a} = {math.sqrt(a)}"
                }
            elif operation == "abs":
                result = {
                    "operation": "absolute_value",
                    "number": a,
                    "result": abs(a),
                    "formula": f"|{a}| = {abs(a)}"
                }
            elif operation == "round":
                try:
                    precision = int(precision)
                except (ValueError, TypeError):
                    precision = 2
                result = {
                    "operation": "round",
                    "number": a,
                    "precision": precision,
                    "result": round(a, precision),
                    "formula": f"round({a}, {precision}) = {round(a, precision)}"
                }
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"不支持的操作: {operation}",
                    error_code="CALC_006",
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
            logger.error(f"计算失败: {e}")
            return ToolExecutionResult(
                success=False,
                error=f"计算失败: {str(e)}",
                error_code="CALC_007",
                execution_time=time.time() - start_time,
                tool_name=self._metadata.name
            )
