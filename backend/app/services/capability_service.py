"""
能力服务

本模块提供能力管理的业务逻辑服务
"""

import logging
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.capabilities.center.unified_center import UnifiedCapabilityCenter
from app.capabilities.types import CapabilityMetadata, CapabilityResult, ExecutionContext

logger = logging.getLogger(__name__)


class CapabilityService:
    """
    能力服务

    提供能力管理的业务逻辑，包括：
    - 能力发现
    - 能力执行
    - 能力监控
    - 能力统计

    Attributes:
        _center: 统一能力中心
        _db: 数据库会话
    """

    def __init__(self, center: UnifiedCapabilityCenter, db: Session):
        """
        初始化能力服务

        Args:
            center: 统一能力中心
            db: 数据库会话
        """
        self._center = center
        self._db = db

        logger.info("能力服务已创建")

    async def discover_capabilities(self,
                                   query: str,
                                   tags: Optional[List[str]] = None,
                                   capability_type: Optional[str] = None,
                                   limit: int = 10) -> List[CapabilityMetadata]:
        """
        发现能力

        Args:
            query: 查询字符串
            tags: 标签过滤
            capability_type: 能力类型过滤
            limit: 返回数量限制

        Returns:
            List[CapabilityMetadata]: 能力元数据列表
        """
        return await self._center.discover(
            query=query,
            tags=tags,
            capability_type=capability_type,
            limit=limit
        )

    async def execute_capability(self,
                                capability_name: str,
                                parameters: Dict[str, Any],
                                context: Optional[ExecutionContext] = None) -> CapabilityResult:
        """
        执行能力

        Args:
            capability_name: 能力名称
            parameters: 执行参数
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        return await self._center.execute(
            capability_name=capability_name,
            parameters=parameters,
            context=context
        )

    async def execute_batch(self,
                           requests: List[Dict[str, Any]],
                           context: Optional[ExecutionContext] = None) -> List[CapabilityResult]:
        """
        批量执行能力

        Args:
            requests: 执行请求列表
            context: 执行上下文

        Returns:
            List[CapabilityResult]: 执行结果列表
        """
        return await self._center.execute_batch(requests, context)

    async def execute_pipeline(self,
                              pipeline: List[Dict[str, Any]],
                              initial_input: Any,
                              context: Optional[ExecutionContext] = None) -> CapabilityResult:
        """
        执行管道

        Args:
            pipeline: 管道定义
            initial_input: 初始输入
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        return await self._center.execute_pipeline(
            pipeline=pipeline,
            initial_input=initial_input,
            context=context
        )

    def get_capability_info(self, capability_name: str) -> Optional[Dict[str, Any]]:
        """
        获取能力信息

        Args:
            capability_name: 能力名称

        Returns:
            Optional[Dict[str, Any]]: 能力信息
        """
        capability = self._center.get_capability(capability_name)
        if capability:
            return capability.metadata.to_dict()
        return None

    def list_capabilities(self,
                         capability_type: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        列出所有能力

        Args:
            capability_type: 能力类型过滤
            tags: 标签过滤

        Returns:
            List[Dict[str, Any]]: 能力信息列表
        """
        capabilities = self._center.list_capabilities(
            capability_type=capability_type,
            tags=tags
        )
        return [cap.metadata.to_dict() for cap in capabilities]

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        return self._center.get_execution_stats()

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            Dict[str, Any]: 健康状态
        """
        return self._center.get_health_status()
