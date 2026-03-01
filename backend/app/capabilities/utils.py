"""
能力中心工具函数

本模块提供能力中心的通用工具函数
"""

import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


def generate_capability_id(name: str, version: str = "1.0.0") -> str:
    """
    生成能力唯一标识

    Args:
        name: 能力名称
        version: 版本号

    Returns:
        str: 能力ID
    """
    content = f"{name}:{version}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def generate_execution_id() -> str:
    """
    生成执行唯一标识

    Returns:
        str: 执行ID
    """
    import uuid
    return str(uuid.uuid4())


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个字典

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        Dict[str, Any]: 合并后的字典
    """
    result = base.copy()
    result.update(override)
    return result


def safe_json_loads(data: str, default: Any = None) -> Any:
    """
    安全地解析JSON

    Args:
        data: JSON字符串
        default: 解析失败时的默认值

    Returns:
        Any: 解析结果
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """
    安全地序列化JSON

    Args:
        data: 待序列化的数据
        default: 序列化失败时的默认值

    Returns:
        str: JSON字符串
    """
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        str: 截断后的字符串
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_execution_time(milliseconds: int) -> str:
    """
    格式化执行时间

    Args:
        milliseconds: 毫秒数

    Returns:
        str: 格式化后的时间字符串
    """
    if milliseconds < 1000:
        return f"{milliseconds}ms"

    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.2f}s"

    minutes = seconds / 60
    return f"{minutes:.2f}min"


def calculate_success_rate(success: int, total: int) -> float:
    """
    计算成功率

    Args:
        success: 成功次数
        total: 总次数

    Returns:
        float: 成功率（0-1）
    """
    if total == 0:
        return 1.0

    return round(success / total, 4)


def parse_tags(tags_input) -> List[str]:
    """
    解析标签输入

    Args:
        tags_input: 可能是字符串、列表或其他类型

    Returns:
        List[str]: 标签列表
    """
    if tags_input is None:
        return []

    if isinstance(tags_input, list):
        return [str(tag).strip() for tag in tags_input if tag]

    if isinstance(tags_input, str):
        # 尝试解析JSON
        try:
            parsed = json.loads(tags_input)
            if isinstance(parsed, list):
                return [str(tag).strip() for tag in parsed if tag]
        except json.JSONDecodeError:
            pass

        # 按逗号分割
        if "," in tags_input:
            return [tag.strip() for tag in tags_input.split(",") if tag.strip()]

        return [tags_input.strip()] if tags_input.strip() else []

    return []


def log_execution(func: Callable) -> Callable:
    """
    执行日志装饰器

    自动记录函数的执行时间和结果
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        func_name = func.__name__

        logger.debug(f"开始执行: {func_name}")

        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            logger.debug(f"执行完成: {func_name}, 耗时: {execution_time:.2f}ms")

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"执行失败: {func_name}, 耗时: {execution_time:.2f}ms, 错误: {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        func_name = func.__name__

        logger.debug(f"开始执行: {func_name}")

        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            logger.debug(f"执行完成: {func_name}, 耗时: {execution_time:.2f}ms")

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"执行失败: {func_name}, 耗时: {execution_time:.2f}ms, 错误: {e}")
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    异常重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio

            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay}秒后重试: {e}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 重试{max_retries}次后仍失败: {e}")

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay}秒后重试: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 重试{max_retries}次后仍失败: {e}")

            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class Timer:
    """
    计时器上下文管理器
    """

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed_ms = 0

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed_ms = (time.time() - self.start_time) * 1000

        if exc_type is None:
            logger.debug(f"{self.name} 完成，耗时: {self.elapsed_ms:.2f}ms")
        else:
            logger.error(f"{self.name} 失败，耗时: {self.elapsed_ms:.2f}ms, 错误: {exc_val}")

    async def __aenter__(self):
        import time
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed_ms = (time.time() - self.start_time) * 1000

        if exc_type is None:
            logger.debug(f"{self.name} 完成，耗时: {self.elapsed_ms:.2f}ms")
        else:
            logger.error(f"{self.name} 失败，耗时: {self.elapsed_ms:.2f}ms, 错误: {exc_val}")


class RateLimiter:
    """
    速率限制器
    """

    def __init__(self, max_calls: int, period: float):
        """
        初始化速率限制器

        Args:
            max_calls: 周期内最大调用次数
            period: 周期（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def can_call(self) -> bool:
        """
        检查是否可以调用

        Returns:
            bool: 是否可以调用
        """
        import time

        now = time.time()
        # 清理过期的调用记录
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

        return len(self.calls) < self.max_calls

    def record_call(self):
        """记录一次调用"""
        import time
        self.calls.append(time.time())

    def wait_time(self) -> float:
        """
        获取需要等待的时间

        Returns:
            float: 等待时间（秒）
        """
        import time

        if self.can_call():
            return 0

        now = time.time()
        oldest_call = min(self.calls)
        return max(0, self.period - (now - oldest_call))


# 导入 asyncio 用于检查协程函数
import asyncio
