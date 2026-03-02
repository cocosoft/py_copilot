"""
随机数生成工具

提供随机数、随机字符串、随机选择等功能
"""

from typing import Dict, Any, List
import time
import logging
import random
import string
import secrets

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class RandomGeneratorTool(BaseTool):
    """
    随机数生成工具
    
    提供随机数、随机字符串、随机选择等功能
    """
    
    def __init__(self):
        """初始化随机数生成工具"""
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="random_generator",
            display_name="随机数生成",
            description="生成随机数、随机字符串、随机选择等",
            category=ToolCategory.UTILITY.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="🎲",
            tags=["随机", "生成", "工具"],
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
                    "number", "integer", "float",
                    "string", "password", "uuid",
                    "choice", "shuffle", "sample"
                ]
            ),
            ToolParameter(
                name="min_value",
                type="number",
                description="最小值（用于number、integer、float）",
                required=False,
                default=0
            ),
            ToolParameter(
                name="max_value",
                type="number",
                description="最大值（用于number、integer、float）",
                required=False,
                default=100
            ),
            ToolParameter(
                name="length",
                type="integer",
                description="长度（用于string、password）",
                required=False,
                default=10
            ),
            ToolParameter(
                name="count",
                type="integer",
                description="数量",
                required=False,
                default=1
            ),
            ToolParameter(
                name="choices",
                type="array",
                description="选项列表（用于choice、shuffle、sample）",
                required=False
            ),
            ToolParameter(
                name="include_uppercase",
                type="boolean",
                description="包含大写字母（用于string、password）",
                required=False,
                default=True
            ),
            ToolParameter(
                name="include_lowercase",
                type="boolean",
                description="包含小写字母（用于string、password）",
                required=False,
                default=True
            ),
            ToolParameter(
                name="include_digits",
                type="boolean",
                description="包含数字（用于string、password）",
                required=False,
                default=True
            ),
            ToolParameter(
                name="include_special",
                type="boolean",
                description="包含特殊字符（用于password）",
                required=False,
                default=False
            ),
            ToolParameter(
                name="seed",
                type="integer",
                description="随机种子（用于可重复的结果）",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行随机数生成
        
        Args:
            **kwargs: 生成参数
                - action: 操作类型（必需）
                - 其他参数根据action不同而不同
        
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
            seed = kwargs.get("seed")
            
            # 设置随机种子（如果提供）
            if seed is not None:
                random.seed(seed)
            
            logger.info(f"执行随机数生成: action={action}")
            
            # 根据操作类型执行不同逻辑
            if action == "number":
                result = self._generate_number(kwargs)
            elif action == "integer":
                result = self._generate_integer(kwargs)
            elif action == "float":
                result = self._generate_float(kwargs)
            elif action == "string":
                result = self._generate_string(kwargs)
            elif action == "password":
                result = self._generate_password(kwargs)
            elif action == "uuid":
                result = self._generate_uuid(kwargs)
            elif action == "choice":
                result = self._generate_choice(kwargs)
            elif action == "shuffle":
                result = self._generate_shuffle(kwargs)
            elif action == "sample":
                result = self._generate_sample(kwargs)
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
                metadata={"action": action}
            )
            
        except Exception as e:
            logger.error(f"随机数生成失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"生成失败: {str(e)}",
                error_code="GENERATION_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _generate_number(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """生成随机数（整数或浮点数）"""
        min_val = kwargs.get("min_value", 0)
        max_val = kwargs.get("max_value", 100)
        count = kwargs.get("count", 1)
        
        # 根据范围决定生成整数还是浮点数
        if isinstance(min_val, int) and isinstance(max_val, int):
            if count == 1:
                value = random.randint(min_val, max_val)
            else:
                value = [random.randint(min_val, max_val) for _ in range(count)]
        else:
            if count == 1:
                value = random.uniform(min_val, max_val)
            else:
                value = [random.uniform(min_val, max_val) for _ in range(count)]
        
        return {
            "value": value,
            "min": min_val,
            "max": max_val,
            "count": count
        }
    
    def _generate_integer(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """生成随机整数"""
        min_val = int(kwargs.get("min_value", 0))
        max_val = int(kwargs.get("max_value", 100))
        count = kwargs.get("count", 1)
        
        if count == 1:
            value = random.randint(min_val, max_val)
        else:
            value = [random.randint(min_val, max_val) for _ in range(count)]
        
        return {
            "value": value,
            "min": min_val,
            "max": max_val,
            "count": count,
            "type": "integer"
        }
    
    def _generate_float(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """生成随机浮点数"""
        min_val = float(kwargs.get("min_value", 0))
        max_val = float(kwargs.get("max_value", 1))
        count = kwargs.get("count", 1)
        
        if count == 1:
            value = random.uniform(min_val, max_val)
        else:
            value = [random.uniform(min_val, max_val) for _ in range(count)]
        
        return {
            "value": value,
            "min": min_val,
            "max": max_val,
            "count": count,
            "type": "float"
        }
    
    def _generate_string(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """生成随机字符串"""
        length = kwargs.get("length", 10)
        include_upper = kwargs.get("include_uppercase", True)
        include_lower = kwargs.get("include_lowercase", True)
        include_digits = kwargs.get("include_digits", True)
        count = kwargs.get("count", 1)
        
        # 构建字符集
        chars = ""
        if include_upper:
            chars += string.ascii_uppercase
        if include_lower:
            chars += string.ascii_lowercase
        if include_digits:
            chars += string.digits
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        if count == 1:
            value = ''.join(random.choices(chars, k=length))
        else:
            value = [''.join(random.choices(chars, k=length)) for _ in range(count)]
        
        return {
            "value": value,
            "length": length,
            "character_set": {
                "uppercase": include_upper,
                "lowercase": include_lower,
                "digits": include_digits
            },
            "count": count
        }
    
    def _generate_password(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """生成安全密码"""
        length = kwargs.get("length", 16)
        include_upper = kwargs.get("include_uppercase", True)
        include_lower = kwargs.get("include_lowercase", True)
        include_digits = kwargs.get("include_digits", True)
        include_special = kwargs.get("include_special", True)
        count = kwargs.get("count", 1)
        
        # 构建字符集
        chars = ""
        if include_upper:
            chars += string.ascii_uppercase
        if include_lower:
            chars += string.ascii_lowercase
        if include_digits:
            chars += string.digits
        if include_special:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        passwords = []
        for _ in range(count):
            # 使用secrets生成安全密码
            password = ''.join(secrets.choice(chars) for _ in range(length))
            passwords.append(password)
        
        return {
            "value": passwords[0] if count == 1 else passwords,
            "length": length,
            "character_set": {
                "uppercase": include_upper,
                "lowercase": include_lower,
                "digits": include_digits,
                "special": include_special
            },
            "count": count,
            "secure": True
        }
    
    def _generate_uuid(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """生成UUID"""
        import uuid
        
        count = kwargs.get("count", 1)
        
        if count == 1:
            value = str(uuid.uuid4())
        else:
            value = [str(uuid.uuid4()) for _ in range(count)]
        
        return {
            "value": value,
            "version": "4",
            "count": count
        }
    
    def _generate_choice(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """随机选择"""
        choices = kwargs.get("choices", [])
        count = kwargs.get("count", 1)
        
        if not choices:
            raise ValueError("需要提供choices参数")
        
        if count == 1:
            value = random.choice(choices)
        else:
            value = random.choices(choices, k=count)
        
        return {
            "value": value,
            "choices": choices,
            "count": count
        }
    
    def _generate_shuffle(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """随机打乱"""
        choices = kwargs.get("choices", [])
        
        if not choices:
            raise ValueError("需要提供choices参数")
        
        # 创建副本并打乱
        shuffled = choices.copy()
        random.shuffle(shuffled)
        
        return {
            "value": shuffled,
            "original": choices,
            "count": len(shuffled)
        }
    
    def _generate_sample(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """随机抽样"""
        choices = kwargs.get("choices", [])
        count = kwargs.get("count", 1)
        
        if not choices:
            raise ValueError("需要提供choices参数")
        
        if count > len(choices):
            raise ValueError(f"抽样数量({count})不能大于选项数量({len(choices)})")
        
        value = random.sample(choices, count)
        
        return {
            "value": value,
            "choices": choices,
            "sample_size": count,
            "population_size": len(choices)
        }
