"""
Skill能力适配器

本模块将现有Skill系统适配为统一Capability接口
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.capabilities.validators import InputValidator
from app.capabilities.utils import parse_tags
from app.models.skill import Skill, SkillExecutionLog, SkillArtifact
from app.services.skill_execution_engine import SkillExecutionEngine
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SkillCapability(BaseCapability):
    """
    Skill能力适配器

    将现有Skill系统适配为统一Capability接口。

    适配映射关系：
    - Skill.name → CapabilityMetadata.name
    - Skill.display_name → CapabilityMetadata.display_name
    - Skill.description → CapabilityMetadata.description
    - Skill.parameters_schema → CapabilityMetadata.input_schema
    - Skill.tags → CapabilityMetadata.tags
    - Skill.dependencies → CapabilityMetadata.dependencies

    Attributes:
        skill: 原始Skill模型实例
        execution_engine: Skill执行引擎
    """

    def __init__(self, skill: Skill):
        """
        初始化Skill能力适配器

        Args:
            skill: Skill模型实例
        """
        # 处理tags字段（可能是JSON字符串或列表）
        tags = parse_tags(skill.tags)

        # 构建依赖列表
        dependencies = []
        if skill.dependencies:
            for dep in skill.dependencies:
                if dep.dependency_skill:
                    dependencies.append(dep.dependency_skill.name)

        # 构建元数据
        metadata = CapabilityMetadata(
            name=skill.name,
            display_name=skill.display_name or skill.name,
            description=skill.description or "",
            capability_type=CapabilityType.SKILL,
            level=self._determine_level(skill),
            category="skill",
            tags=tags,
            input_schema=self._build_input_schema(skill),
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "artifacts": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            },
            dependencies=dependencies,
            timeout_seconds=300,  # Skill默认5分钟超时
            max_retries=skill.config.get("max_retries", 3) if skill.config else 3,
            version=skill.version or "1.0.0",
            author=skill.author or "system"
        )

        super().__init__(metadata)
        self.skill = skill
        self._execution_engine: Optional[SkillExecutionEngine] = None

    def _determine_level(self, skill: Skill) -> CapabilityLevel:
        """
        确定能力级别

        根据Skill的复杂度判断：
        - 有execution_flow的视为WORKFLOW
        - 有依赖的视为COMPOSITE
        - 否则为ATOMIC

        Args:
            skill: Skill模型

        Returns:
            CapabilityLevel: 能力级别
        """
        if skill.execution_flow and len(skill.execution_flow) > 0:
            return CapabilityLevel.WORKFLOW

        if skill.dependencies and len(skill.dependencies) > 0:
            return CapabilityLevel.COMPOSITE

        return CapabilityLevel.ATOMIC

    def _build_input_schema(self, skill: Skill) -> Dict[str, Any]:
        """
        构建输入Schema

        Args:
            skill: Skill模型

        Returns:
            Dict[str, Any]: 输入Schema
        """
        if not skill.parameters_schema:
            return {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "任务描述"
                    }
                }
            }

        # 转换Skill的参数schema为标准JSON Schema
        properties = {}
        required = []

        for param_name, param_def in skill.parameters_schema.items():
            prop = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", "")
            }

            # 添加其他属性
            if "default" in param_def:
                prop["default"] = param_def["default"]
            if "enum" in param_def:
                prop["enum"] = param_def["enum"]
            if "minimum" in param_def:
                prop["minimum"] = param_def["minimum"]
            if "maximum" in param_def:
                prop["maximum"] = param_def["maximum"]
            if "minLength" in param_def:
                prop["minLength"] = param_def["minLength"]
            if "maxLength" in param_def:
                prop["maxLength"] = param_def["maxLength"]
            if "pattern" in param_def:
                prop["pattern"] = param_def["pattern"]

            properties[param_name] = prop

            # 检查是否必填
            if param_def.get("required", False):
                required.append(param_name)

        schema = {
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    async def initialize(self) -> bool:
        """
        初始化Skill适配器

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建数据库会话
            db = SessionLocal()
            self._execution_engine = SkillExecutionEngine(db)
            self._is_initialized = True

            logger.info(f"Skill适配器 '{self.name}' 初始化完成")
            return True

        except Exception as e:
            logger.error(f"Skill适配器 '{self.name}' 初始化失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        if self._execution_engine and hasattr(self._execution_engine, 'db'):
            self._execution_engine.db.close()
        self._execution_engine = None
        self._is_initialized = False

        logger.info(f"Skill适配器 '{self.name}' 资源已清理")

    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        执行Skill

        完整的执行流程：
        1. 准备执行参数
        2. 调用Skill执行引擎
        3. 处理执行结果
        4. 处理Artifacts

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        try:
            # 准备执行参数
            task = input_data.get("task", "")
            params = {k: v for k, v in input_data.items() if k != "task"}

            # 调用执行引擎
            logger.info(f"开始执行Skill: {self.skill.name}")

            result = await self._execution_engine.execute(
                skill_id=self.skill.id,
                task=task,
                params=params,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                context=context.context_data
            )

            # 解析结果
            success = result.get("success", False)
            output = result.get("result", "")
            error = result.get("error")

            # 处理Artifacts
            artifacts = []
            if success:
                for artifact_data in result.get("artifacts", []):
                    artifacts.append({
                        "type": artifact_data.get("type", "unknown"),
                        "name": artifact_data.get("name", ""),
                        "content": "",  # 内容需要单独获取
                        "id": artifact_data.get("id")
                    })

            logger.info(f"Skill执行完成: {self.skill.name}, success={success}")

            return CapabilityResult(
                success=success,
                output=output if success else None,
                error=error if not success else None,
                artifacts=artifacts,
                metadata={
                    "skill_id": self.skill.id,
                    "skill_name": self.skill.name,
                    "execution_id": result.get("execution_id")
                }
            )

        except Exception as e:
            logger.error(f"Skill执行异常: {self.skill.name}, error={e}", exc_info=True)

            return CapabilityResult(
                success=False,
                error=f"Skill执行异常: {str(e)}",
                metadata={
                    "skill_id": self.skill.id,
                    "skill_name": self.skill.name,
                    "exception_type": type(e).__name__
                }
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据

        使用Skill的parameters_schema进行验证

        Args:
            input_data: 输入数据

        Returns:
            ValidationResult: 验证结果
        """
        if not self.metadata.input_schema:
            return ValidationResult(valid=True)

        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)

    def get_skill_info(self) -> Dict[str, Any]:
        """
        获取Skill详细信息

        Returns:
            Dict: Skill信息
        """
        return {
            "id": self.skill.id,
            "name": self.skill.name,
            "display_name": self.skill.display_name,
            "description": self.skill.description,
            "version": self.skill.version,
            "status": self.skill.status,
            "is_official": self.skill.is_official,
            "is_builtin": self.skill.is_builtin,
            "author": self.skill.author,
            "tags": self.skill.tags,
            "dependencies_count": len(self.skill.dependencies) if self.skill.dependencies else 0,
            "usage_count": self.skill.usage_count,
            "last_used_at": self.skill.last_used_at.isoformat() if self.skill.last_used_at else None,
            "created_at": self.skill.created_at.isoformat() if self.skill.created_at else None
        }
