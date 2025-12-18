"""断路器模式实现"""
import time
from enum import Enum, auto
from typing import Callable, TypeVar, Dict, Any


T = TypeVar('T')


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = auto()      # 正常工作
    OPEN = auto()        # 断开，拒绝请求
    HALF_OPEN = auto()   # 半开，测试恢复


class CircuitBreaker:
    """断路器模式实现"""
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """使用断路器执行异步函数"""
        if self.state == CircuitState.OPEN:
            # 检查是否可以尝试恢复
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception("Circuit breaker is open")
            else:
                # 尝试半开状态
                self.state = CircuitState.HALF_OPEN
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """处理成功情况"""
        if self.state == CircuitState.CLOSED:
            # 正常状态，重置失败计数
            self.failure_count = 0
        elif self.state == CircuitState.HALF_OPEN:
            # 半开状态，增加成功计数
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # 成功次数达到阈值，恢复闭合状态
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
    
    def _on_failure(self):
        """处理失败情况"""
        if self.state == CircuitState.CLOSED:
            # 正常状态，增加失败计数
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                # 失败次数达到阈值，打开断路器
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
        elif self.state == CircuitState.HALF_OPEN:
            # 半开状态测试失败，重新打开断路器
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            self.success_count = 0
