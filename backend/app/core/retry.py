"""重试策略实现"""
import random
import asyncio
from typing import Callable, TypeVar, Union, Dict, Any

from app.core.exceptions import TransientError

T = TypeVar('T')


class RetryPolicy:
    """重试策略实现"""
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (TransientError,)
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def get_delay(self, attempt: int) -> float:
        """计算重试延迟，支持指数退避和抖动"""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # 添加抖动，避免请求峰值
            delay = delay * (0.5 + random.random())

        return delay

    async def execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """使用重试策略执行异步函数"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except self.retryable_exceptions as e:
                if attempt == self.max_retries - 1:
                    # 最后一次重试失败，抛出异常
                    raise

                delay = self.get_delay(attempt)
                # 可以在这里添加日志记录
                await asyncio.sleep(delay)
            except Exception as e:
                # 非重试able异常，直接抛出
                raise
