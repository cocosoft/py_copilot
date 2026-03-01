"""
输入验证器

本模块提供输入数据的验证功能
"""

import json
from typing import Dict, Any, List, Optional

from app.capabilities.types import ValidationResult


class InputValidator:
    """
    输入验证器

    基于JSON Schema验证输入数据
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        初始化验证器

        Args:
            schema: JSON Schema定义
        """
        self.schema = schema

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据

        Args:
            data: 待验证的数据

        Returns:
            ValidationResult: 验证结果
        """
        if not self.schema:
            return ValidationResult(valid=True)

        errors = []

        # 验证类型
        if "type" in self.schema:
            type_error = self._validate_type(data, self.schema["type"], "root")
            if type_error:
                errors.append(type_error)

        # 验证必填字段
        if "required" in self.schema:
            for field in self.schema["required"]:
                if field not in data:
                    errors.append(f"缺少必填字段: {field}")

        # 验证属性
        if "properties" in self.schema and isinstance(data, dict):
            for prop_name, prop_schema in self.schema["properties"].items():
                if prop_name in data:
                    prop_errors = self._validate_property(
                        data[prop_name], prop_schema, prop_name
                    )
                    errors.extend(prop_errors)

        # 验证额外属性
        if "additionalProperties" in self.schema:
            additional = self.schema["additionalProperties"]
            if additional is False:
                allowed_props = set(self.schema.get("properties", {}).keys())
                for key in data.keys():
                    if key not in allowed_props:
                        errors.append(f"不允许的字段: {key}")

        if errors:
            return ValidationResult(
                valid=False,
                error=f"验证失败: {'; '.join(errors[:3])}",
                errors=errors
            )

        return ValidationResult(valid=True)

    def _validate_type(self, value: Any, expected_type: str, path: str) -> Optional[str]:
        """
        验证数据类型

        Args:
            value: 待验证的值
            expected_type: 期望的类型
            path: 字段路径

        Returns:
            Optional[str]: 错误信息，无错误返回None
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        if expected_type not in type_mapping:
            return None

        expected_python_type = type_mapping[expected_type]

        if expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                return f"字段 '{path}' 应该是整数类型"
        elif expected_type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return f"字段 '{path}' 应该是数字类型"
        elif not isinstance(value, expected_python_type):
            return f"字段 '{path}' 应该是 {expected_type} 类型"

        return None

    def _validate_property(self, value: Any, schema: Dict[str, Any], path: str) -> List[str]:
        """
        验证单个属性

        Args:
            value: 属性值
            schema: 属性schema
            path: 属性路径

        Returns:
            List[str]: 错误列表
        """
        errors = []

        # 验证类型
        if "type" in schema:
            type_error = self._validate_type(value, schema["type"], path)
            if type_error:
                errors.append(type_error)
                return errors

        # 验证字符串
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                errors.append(f"字段 '{path}' 长度至少为 {schema['minLength']}")

            if "maxLength" in schema and len(value) > schema["maxLength"]:
                errors.append(f"字段 '{path}' 长度不能超过 {schema['maxLength']}")

            if "pattern" in schema:
                import re
                if not re.match(schema["pattern"], value):
                    errors.append(f"字段 '{path}' 格式不符合要求")

            if "enum" in schema and value not in schema["enum"]:
                errors.append(f"字段 '{path}' 必须是以下值之一: {schema['enum']}")

        # 验证数字
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                errors.append(f"字段 '{path}' 最小值为 {schema['minimum']}")

            if "maximum" in schema and value > schema["maximum"]:
                errors.append(f"字段 '{path}' 最大值为 {schema['maximum']}")

        # 验证数组
        elif isinstance(value, list):
            if "minItems" in schema and len(value) < schema["minItems"]:
                errors.append(f"字段 '{path}' 至少包含 {schema['minItems']} 个元素")

            if "maxItems" in schema and len(value) > schema["maxItems"]:
                errors.append(f"字段 '{path}' 最多包含 {schema['maxItems']} 个元素")

            if "items" in schema:
                for i, item in enumerate(value):
                    item_errors = self._validate_property(
                        item, schema["items"], f"{path}[{i}]"
                    )
                    errors.extend(item_errors)

        # 验证对象
        elif isinstance(value, dict):
            if "properties" in schema:
                for prop_name, prop_schema in schema["properties"].items():
                    if prop_name in value:
                        prop_errors = self._validate_property(
                            value[prop_name], prop_schema, f"{path}.{prop_name}"
                        )
                        errors.extend(prop_errors)

            if "required" in schema:
                for field in schema["required"]:
                    if field not in value:
                        errors.append(f"字段 '{path}' 缺少必填项: {field}")

        return errors


class SchemaBuilder:
    """
    Schema构建器

    辅助构建JSON Schema
    """

    @staticmethod
    def string(description: str = "",
               min_length: int = None,
               max_length: int = None,
               pattern: str = None,
               enum: List[str] = None,
               default: str = None) -> Dict[str, Any]:
        """构建字符串schema"""
        schema = {"type": "string", "description": description}

        if min_length is not None:
            schema["minLength"] = min_length
        if max_length is not None:
            schema["maxLength"] = max_length
        if pattern is not None:
            schema["pattern"] = pattern
        if enum is not None:
            schema["enum"] = enum
        if default is not None:
            schema["default"] = default

        return schema

    @staticmethod
    def integer(description: str = "",
                minimum: int = None,
                maximum: int = None,
                default: int = None) -> Dict[str, Any]:
        """构建整数schema"""
        schema = {"type": "integer", "description": description}

        if minimum is not None:
            schema["minimum"] = minimum
        if maximum is not None:
            schema["maximum"] = maximum
        if default is not None:
            schema["default"] = default

        return schema

    @staticmethod
    def number(description: str = "",
               minimum: float = None,
               maximum: float = None,
               default: float = None) -> Dict[str, Any]:
        """构建数字schema"""
        schema = {"type": "number", "description": description}

        if minimum is not None:
            schema["minimum"] = minimum
        if maximum is not None:
            schema["maximum"] = maximum
        if default is not None:
            schema["default"] = default

        return schema

    @staticmethod
    def boolean(description: str = "", default: bool = None) -> Dict[str, Any]:
        """构建布尔schema"""
        schema = {"type": "boolean", "description": description}

        if default is not None:
            schema["default"] = default

        return schema

    @staticmethod
    def array(items: Dict[str, Any],
              description: str = "",
              min_items: int = None,
              max_items: int = None) -> Dict[str, Any]:
        """构建数组schema"""
        schema = {"type": "array", "items": items, "description": description}

        if min_items is not None:
            schema["minItems"] = min_items
        if max_items is not None:
            schema["maxItems"] = max_items

        return schema

    @staticmethod
    def object(properties: Dict[str, Any],
               description: str = "",
               required: List[str] = None,
               additional_properties: bool = True) -> Dict[str, Any]:
        """构建对象schema"""
        schema = {
            "type": "object",
            "properties": properties,
            "description": description
        }

        if required:
            schema["required"] = required
        if not additional_properties:
            schema["additionalProperties"] = False

        return schema

    @staticmethod
    def build_object_schema(properties: Dict[str, Any],
                           required: List[str] = None,
                           description: str = "") -> Dict[str, Any]:
        """
        构建完整的对象schema

        Args:
            properties: 属性定义
            required: 必填字段列表
            description: 描述

        Returns:
            Dict[str, Any]: 完整的schema
        """
        schema = {
            "type": "object",
            "properties": properties,
            "description": description
        }

        if required:
            schema["required"] = required

        return schema
