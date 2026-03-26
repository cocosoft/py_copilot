"""
异步工具模块

提供统一的异步方法执行工具，解决事件循环冲突问题
"""
import asyncio
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def run_async_safely(coro: Any) -> T:
    """安全地运行异步协程

    修复：统一处理异步方法调用，避免事件循环冲突

    处理以下情况：
    1. 没有事件循环：使用 asyncio.run
    2. 有运行中的事件循环：使用 nest_asyncio 或线程池
    3. 有未运行的事件循环：使用 run_until_complete

    Args:
        coro: 异步协程对象

    Returns:
        协程执行结果
    """
    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 没有事件循环，使用 asyncio.run
            return asyncio.run(coro)

        # 检查事件循环是否正在运行
        if loop.is_running():
            # 事件循环正在运行，使用 nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(coro)
            except ImportError:
                # 如果没有 nest_asyncio，使用线程池
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
        else:
            # 事件循环未运行，使用 run_until_complete
            return loop.run_until_complete(coro)

    except Exception as e:
        logger.error(f"运行异步协程失败: {e}")
        raise


def run_async_in_new_loop(coro: Any) -> T:
    """在新的事件循环中运行异步协程

    适用于需要完全隔离的场景

    Args:
        coro: 异步协程对象

    Returns:
        协程执行结果
    """
    import concurrent.futures

    def run_in_thread():
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result()


def ensure_event_loop():
    """确保有可用的事件循环

    如果当前没有事件循环，创建一个新的
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
