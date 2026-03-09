"""
模型容错和降级服务

提供模型调用相关的容错机制，包括：
- 熔断器模式：处理模型服务故障
- 模型降级策略：主模型不可用时自动切换备用模型
- 超时和重试：指数退避重试策略
- 降级通知：降级事件通知
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.core.circuit_breaker import CircuitBreaker, CircuitState
from app.core.retry import RetryPolicy
from app.core.exceptions import TransientError
from app.models.supplier_db import ModelDB

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ModelStatus(Enum):
    """模型状态枚举"""
    AVAILABLE = "available"       # 可用
    DEGRADED = "degraded"         # 降级
    UNAVAILABLE = "unavailable"   # 不可用
    UNKNOWN = "unknown"           # 未知


@dataclass
class ModelHealthInfo:
    """模型健康信息"""
    model_id: int
    model_name: str
    status: ModelStatus
    last_check_time: datetime
    failure_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    fallback_model_id: Optional[int] = None


@dataclass
class DegradationEvent:
    """降级事件"""
    timestamp: datetime
    original_model_id: int
    original_model_name: str
    fallback_model_id: Optional[int]
    fallback_model_name: Optional[str]
    reason: str
    recovered: bool = False


class ModelCircuitBreaker:
    """
    模型熔断器
    
    为每个模型维护独立的熔断器实例，实现模型级别的故障隔离。
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3
    ):
        """
        初始化模型熔断器
        
        Args:
            failure_threshold: 失败阈值，超过后触发熔断
            recovery_timeout: 恢复超时时间（秒）
            success_threshold: 成功阈值，半开状态下连续成功次数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        # 模型ID到熔断器实例的映射
        self._circuit_breakers: Dict[int, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, model_id: int) -> CircuitBreaker:
        """
        获取指定模型的熔断器实例
        
        Args:
            model_id: 模型ID
        
        Returns:
            熔断器实例
        """
        if model_id not in self._circuit_breakers:
            self._circuit_breakers[model_id] = CircuitBreaker(
                failure_threshold=self.failure_threshold,
                recovery_timeout=self.recovery_timeout,
                success_threshold=self.success_threshold
            )
        
        return self._circuit_breakers[model_id]
    
    def is_available(self, model_id: int) -> bool:
        """
        检查模型是否可用
        
        Args:
            model_id: 模型ID
        
        Returns:
            是否可用
        """
        cb = self.get_circuit_breaker(model_id)
        return cb.state != CircuitState.OPEN
    
    def get_state(self, model_id: int) -> CircuitState:
        """
        获取模型熔断器状态
        
        Args:
            model_id: 模型ID
        
        Returns:
            熔断器状态
        """
        cb = self.get_circuit_breaker(model_id)
        return cb.state
    
    def reset(self, model_id: int) -> None:
        """
        重置模型熔断器
        
        Args:
            model_id: 模型ID
        """
        if model_id in self._circuit_breakers:
            del self._circuit_breakers[model_id]


class ModelDegradationService:
    """
    模型降级服务
    
    管理模型的降级策略，包括：
    - 备用模型配置
    - 自动降级切换
    - 降级事件通知
    - 健康状态监控
    """
    
    def __init__(self, db: Session):
        """
        初始化模型降级服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
        # 熔断器管理器
        self.circuit_breaker = ModelCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=3
        )
        
        # 重试策略
        self.retry_policy = RetryPolicy(
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            max_delay=30.0,
            jitter=True
        )
        
        # 模型健康信息缓存
        self._health_info: Dict[int, ModelHealthInfo] = {}
        
        # 降级事件历史
        self._degradation_events: List[DegradationEvent] = []
        
        # 降级通知回调
        self._degradation_callbacks: List[Callable] = []
    
    # ==================== 备用模型配置 ====================
    
    def get_fallback_model(
        self,
        model_id: int
    ) -> Optional[ModelDB]:
        """
        获取备用模型
        
        Args:
            model_id: 主模型ID
        
        Returns:
            备用模型对象，不存在时返回None
        """
        # 查找主模型
        primary_model = self.db.query(ModelDB).filter(
            ModelDB.id == model_id
        ).first()
        
        if not primary_model:
            return None
        
        # 查找同一供应商的其他可用模型
        fallback_model = self.db.query(ModelDB).filter(
            ModelDB.supplier_id == primary_model.supplier_id,
            ModelDB.id != model_id,
            ModelDB.is_active == True
        ).order_by(
            ModelDB.is_default.desc(),
            ModelDB.id.asc()
        ).first()
        
        return fallback_model
    
    def get_fallback_chain(
        self,
        model_id: int,
        max_depth: int = 3
    ) -> List[ModelDB]:
        """
        获取降级链
        
        Args:
            model_id: 主模型ID
            max_depth: 最大降级深度
        
        Returns:
            降级链（模型列表）
        """
        chain = []
        current_id = model_id
        visited = set()
        
        while len(chain) < max_depth and current_id not in visited:
            visited.add(current_id)
            
            fallback = self.get_fallback_model(current_id)
            if fallback:
                chain.append(fallback)
                current_id = fallback.id
            else:
                break
        
        return chain
    
    # ==================== 健康状态监控 ====================
    
    def update_health_info(
        self,
        model_id: int,
        model_name: str,
        success: bool,
        response_time: float = 0.0,
        error: Optional[str] = None
    ) -> ModelHealthInfo:
        """
        更新模型健康信息
        
        Args:
            model_id: 模型ID
            model_name: 模型名称
            success: 是否成功
            response_time: 响应时间（毫秒）
            error: 错误信息（可选）
        
        Returns:
            更新后的健康信息
        """
        if model_id not in self._health_info:
            self._health_info[model_id] = ModelHealthInfo(
                model_id=model_id,
                model_name=model_name,
                status=ModelStatus.UNKNOWN,
                last_check_time=datetime.now()
            )
        
        info = self._health_info[model_id]
        info.last_check_time = datetime.now()
        
        if success:
            info.success_count += 1
            info.failure_count = 0
            info.last_error = None
            
            # 更新平均响应时间
            if response_time > 0:
                total_count = info.success_count
                info.avg_response_time = (
                    (info.avg_response_time * (total_count - 1) + response_time) 
                    / total_count
                )
            
            # 更新状态
            if self.circuit_breaker.is_available(model_id):
                info.status = ModelStatus.AVAILABLE
        else:
            info.failure_count += 1
            info.last_error = error
            
            # 更新状态
            if not self.circuit_breaker.is_available(model_id):
                info.status = ModelStatus.UNAVAILABLE
        
        return info
    
    def get_health_info(self, model_id: int) -> Optional[ModelHealthInfo]:
        """
        获取模型健康信息
        
        Args:
            model_id: 模型ID
        
        Returns:
            健康信息，不存在时返回None
        """
        return self._health_info.get(model_id)
    
    def get_all_health_info(self) -> List[ModelHealthInfo]:
        """
        获取所有模型的健康信息
        
        Returns:
            健康信息列表
        """
        return list(self._health_info.values())
    
    # ==================== 降级执行 ====================
    
    async def execute_with_fallback(
        self,
        model_id: int,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        带降级策略执行模型调用
        
        Args:
            model_id: 模型ID
            func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            执行结果
        
        Raises:
            Exception: 所有降级尝试都失败时抛出
        """
        # 获取模型信息
        model = self.db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型不存在: {model_id}")
        
        model_name = model.model_name or model.model_id or str(model_id)
        
        # 检查熔断器状态
        if not self.circuit_breaker.is_available(model_id):
            logger.warning(f"模型 {model_name} 熔断器已打开，尝试降级")
            return await self._execute_fallback(model_id, func, *args, **kwargs)
        
        # 尝试执行主模型
        try:
            start_time = datetime.now()
            
            result = await self.circuit_breaker.get_circuit_breaker(model_id).execute(
                func, *args, **kwargs
            )
            
            # 记录成功
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self.update_health_info(
                model_id, model_name, True, response_time
            )
            
            return result
            
        except Exception as e:
            # 记录失败
            self.update_health_info(
                model_id, model_name, False, error=str(e)
            )
            
            logger.warning(f"模型 {model_name} 执行失败: {str(e)}，尝试降级")
            
            # 尝试降级
            return await self._execute_fallback(model_id, func, *args, **kwargs)
    
    async def _execute_fallback(
        self,
        model_id: int,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        执行降级调用
        
        Args:
            model_id: 主模型ID
            func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            执行结果
        
        Raises:
            Exception: 所有降级尝试都失败时抛出
        """
        # 获取降级链
        fallback_chain = self.get_fallback_chain(model_id)
        
        if not fallback_chain:
            # 没有备用模型，抛出异常
            raise Exception(f"模型 {model_id} 不可用且无备用模型")
        
        # 获取主模型信息
        primary_model = self.db.query(ModelDB).filter(
            ModelDB.id == model_id
        ).first()
        primary_name = primary_model.model_name if primary_model else str(model_id)
        
        # 尝试降级链中的模型
        last_error = None
        for fallback_model in fallback_chain:
            fallback_name = fallback_model.model_name or fallback_model.model_id
            
            try:
                logger.info(f"尝试降级到模型: {fallback_name}")
                
                # 更新kwargs中的模型ID
                kwargs['model_id'] = fallback_model.id
                
                result = await func(*args, **kwargs)
                
                # 记录降级事件
                event = DegradationEvent(
                    timestamp=datetime.now(),
                    original_model_id=model_id,
                    original_model_name=primary_name,
                    fallback_model_id=fallback_model.id,
                    fallback_model_name=fallback_name,
                    reason="主模型不可用"
                )
                self._degradation_events.append(event)
                
                # 发送降级通知
                await self._notify_degradation(event)
                
                # 更新健康信息
                self.update_health_info(
                    fallback_model.id, fallback_name, True
                )
                
                logger.info(f"降级成功: {primary_name} -> {fallback_name}")
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"降级模型 {fallback_name} 执行失败: {str(e)}")
                
                # 更新健康信息
                self.update_health_info(
                    fallback_model.id, fallback_name, False, error=str(e)
                )
        
        # 所有降级尝试都失败
        raise Exception(f"所有降级尝试都失败: {str(last_error)}")
    
    # ==================== 降级通知 ====================
    
    def register_degradation_callback(
        self,
        callback: Callable[[DegradationEvent], None]
    ) -> None:
        """
        注册降级通知回调
        
        Args:
            callback: 回调函数
        """
        self._degradation_callbacks.append(callback)
    
    async def _notify_degradation(self, event: DegradationEvent) -> None:
        """
        发送降级通知
        
        Args:
            event: 降级事件
        """
        for callback in self._degradation_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"降级通知回调执行失败: {str(e)}")
    
    def get_degradation_events(
        self,
        limit: int = 100
    ) -> List[DegradationEvent]:
        """
        获取降级事件历史
        
        Args:
            limit: 返回的最大数量
        
        Returns:
            降级事件列表
        """
        return self._degradation_events[-limit:]
    
    # ==================== 重试策略 ====================
    
    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        带重试策略执行函数
        
        Args:
            func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            执行结果
        """
        return await self.retry_policy.execute_with_retry(func, *args, **kwargs)


# ==================== 依赖注入函数 ====================

def get_model_degradation_service(db: Session) -> ModelDegradationService:
    """
    获取模型降级服务实例（用于依赖注入）
    
    Args:
        db: 数据库会话
    
    Returns:
        模型降级服务实例
    """
    return ModelDegradationService(db)
