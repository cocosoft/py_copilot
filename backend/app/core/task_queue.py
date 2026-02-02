"""任务队列管理器

提供任务队列功能，用于处理高并发请求
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum, IntEnum
import uuid
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskPriority(IntEnum):
    """任务优先级"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task(Generic[T]):
    """任务类"""
    func: Callable[..., T] = field(compare=False)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[T] = None
    error: Optional[Exception] = None
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """比较任务优先级"""
        return self.priority > other.priority  # 优先级高的排前面


class WorkerPool:
    """工作池"""
    
    def __init__(self, size: int):
        """
        初始化工作池
        
        Args:
            size: 工作池大小
        """
        self.size = size
        self.workers = []
        self.task_queue = asyncio.Queue()
        self.running = False
    
    async def start(self):
        """启动工作池"""
        if self.running:
            return
        
        self.running = True
        
        # 创建工作协程
        for i in range(self.size):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"工作池已启动，大小: {self.size}")
    
    async def stop(self):
        """停止工作池"""
        if not self.running:
            return
        
        self.running = False
        
        # 等待所有工作协程结束
        for worker in self.workers:
            worker.cancel()
        
        try:
            await asyncio.gather(*self.workers, return_exceptions=True)
        except Exception as e:
            logger.error(f"停止工作池时发生错误: {e}")
        
        self.workers.clear()
        logger.info("工作池已停止")
    
    async def _worker(self, worker_id: int):
        """工作协程"""
        logger.debug(f"工作协程 {worker_id} 已启动")
        
        while self.running:
            try:
                # 从队列获取任务
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=0.1
                )
                
                # 处理任务
                await self._process_task(task, worker_id)
                
                # 标记任务完成
                self.task_queue.task_done()
            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except asyncio.CancelledError:
                # 被取消
                break
            except Exception as e:
                logger.error(f"工作协程 {worker_id} 发生错误: {e}")
        
        logger.debug(f"工作协程 {worker_id} 已停止")
    
    async def _process_task(self, task: Task, worker_id: int):
        """处理任务"""
        logger.debug(f"工作协程 {worker_id} 开始处理任务 {task.id}")
        
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # 执行任务
            if task.timeout:
                # 带超时的执行
                task.result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                # 正常执行
                task.result = await task.func(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            logger.debug(f"任务 {task.id} 执行成功")
        except asyncio.TimeoutError as e:
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = time.time()
            logger.warning(f"任务 {task.id} 执行超时")
        except asyncio.CancelledError as e:
            task.status = TaskStatus.CANCELLED
            task.error = e
            task.completed_at = time.time()
            logger.debug(f"任务 {task.id} 被取消")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = time.time()
            logger.error(f"任务 {task.id} 执行失败: {e}")
    
    async def submit(self, task: Task):
        """
        提交任务
        
        Args:
            task: 任务对象
        """
        await self.task_queue.put(task)
    
    def qsize(self) -> int:
        """
        获取队列大小
        
        Returns:
            队列中的任务数
        """
        return self.task_queue.qsize()


class PriorityTaskQueue:
    """优先级任务队列"""
    
    def __init__(self):
        """初始化优先级队列"""
        # 使用字典存储不同优先级的队列
        self.queues: Dict[TaskPriority, deque] = defaultdict(deque)
        self.task_count: int = 0
    
    def put(self, task: Task):
        """
        添加任务
        
        Args:
            task: 任务对象
        """
        self.queues[task.priority].append(task)
        self.task_count += 1
    
    def get(self) -> Optional[Task]:
        """
        获取任务（按优先级）
        
        Returns:
            任务对象，如果队列为空返回None
        """
        # 按优先级从高到低获取任务
        for priority in sorted(TaskPriority, reverse=True):
            if self.queues[priority]:
                task = self.queues[priority].popleft()
                self.task_count -= 1
                return task
        return None
    
    def qsize(self) -> int:
        """
        获取队列大小
        
        Returns:
            队列中的任务数
        """
        return self.task_count
    
    def empty(self) -> bool:
        """
        检查队列是否为空
        
        Returns:
            是否为空
        """
        return self.task_count == 0


class TaskQueueManager:
    """任务队列管理器"""
    
    def __init__(
        self,
        worker_count: int = 4,
        max_pending_tasks: int = 10000,
        enable_priority: bool = True
    ):
        """
        初始化任务队列管理器
        
        Args:
            worker_count: 工作线程数
            max_pending_tasks: 最大待处理任务数
            enable_priority: 是否启用优先级
        """
        self.worker_count = worker_count
        self.max_pending_tasks = max_pending_tasks
        self.enable_priority = enable_priority
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        
        # 优先级队列
        if enable_priority:
            self.task_queue = PriorityTaskQueue()
        else:
            self.task_queue = deque()
        
        # 工作池
        self.worker_pool = WorkerPool(worker_count)
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        # 运行状态
        self.running = False
    
    async def start(self):
        """启动任务队列管理器"""
        if self.running:
            return
        
        self.running = True
        await self.worker_pool.start()
        
        # 启动任务处理协程
        self.process_task_task = asyncio.create_task(self._process_tasks())
        
        logger.info(f"任务队列管理器已启动，工作线程数: {self.worker_count}")
    
    async def stop(self):
        """停止任务队列管理器"""
        if not self.running:
            return
        
        self.running = False
        
        # 停止任务处理协程
        if hasattr(self, 'process_task_task'):
            self.process_task_task.cancel()
            try:
                await self.process_task_task
            except asyncio.CancelledError:
                pass
        
        # 停止工作池
        await self.worker_pool.stop()
        
        logger.info("任务队列管理器已停止")
    
    async def _process_tasks(self):
        """处理任务"""
        while self.running:
            try:
                # 检查队列大小
                if isinstance(self.task_queue, PriorityTaskQueue):
                    queue_size = self.task_queue.qsize()
                else:
                    queue_size = len(self.task_queue)
                
                if queue_size > 0:
                    # 获取任务
                    if isinstance(self.task_queue, PriorityTaskQueue):
                        task = self.task_queue.get()
                    else:
                        task = self.task_queue.popleft()
                    
                    # 提交到工作池
                    await self.worker_pool.submit(task)
                else:
                    # 队列为空，短暂休眠
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"处理任务时发生错误: {e}")
                await asyncio.sleep(0.1)
    
    async def submit_task(
        self,
        func: Callable[..., T],
        *args,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Task[T]:
        """
        提交任务
        
        Args:
            func: 任务函数
            *args: 位置参数
            priority: 优先级
            timeout: 超时时间
            metadata: 元数据
            **kwargs: 关键字参数
            
        Returns:
            任务对象
        """
        # 检查队列大小
        if isinstance(self.task_queue, PriorityTaskQueue):
            queue_size = self.task_queue.qsize()
        else:
            queue_size = len(self.task_queue)
        
        if queue_size >= self.max_pending_tasks:
            raise ValueError(f"任务队列已满，最大容量: {self.max_pending_tasks}")
        
        # 创建任务
        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        # 存储任务
        self.tasks[task.id] = task
        
        # 添加到队列
        if isinstance(self.task_queue, PriorityTaskQueue):
            self.task_queue.put(task)
        else:
            self.task_queue.append(task)
        
        # 更新统计信息
        self.stats["total_tasks"] += 1
        
        logger.debug(f"提交任务 {task.id}，优先级: {priority.name}")
        return task
    
    async def submit_high_priority(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> Task[T]:
        """
        提交高优先级任务
        
        Args:
            func: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务对象
        """
        return await self.submit_task(
            func,
            *args,
            priority=TaskPriority.HIGH,
            **kwargs
        )
    
    async def submit_critical(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> Task[T]:
        """
        提交关键任务
        
        Args:
            func: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务对象
        """
        return await self.submit_task(
            func,
            *args,
            priority=TaskPriority.CRITICAL,
            **kwargs
        )
    
    async def submit_low_priority(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> Task[T]:
        """
        提交低优先级任务
        
        Args:
            func: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务对象
        """
        return await self.submit_task(
            func,
            *args,
            priority=TaskPriority.LOW,
            **kwargs
        )
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在返回None
        """
        return self.tasks.get(task_id)
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Task:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            任务对象
            
        Raises:
            TimeoutError: 超时
            ValueError: 任务不存在
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 等待任务完成
        start_time = time.time()
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"等待任务超时: {task_id}")
            await asyncio.sleep(0.01)
        
        # 更新统计信息
        if task.status == TaskStatus.COMPLETED:
            self.stats["completed_tasks"] += 1
            if task.started_at and task.completed_at:
                execution_time = task.completed_at - task.started_at
                self.stats["total_execution_time"] += execution_time
                self.stats["average_execution_time"] = (
                    self.stats["total_execution_time"] / 
                    self.stats["completed_tasks"]
                )
        elif task.status == TaskStatus.FAILED:
            self.stats["failed_tasks"] += 1
        elif task.status == TaskStatus.CANCELLED:
            self.stats["cancelled_tasks"] += 1
        
        return task
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        # 只能取消未开始的任务
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
            self.stats["cancelled_tasks"] += 1
            logger.debug(f"任务 {task_id} 已取消")
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        # 计算当前队列大小
        if isinstance(self.task_queue, PriorityTaskQueue):
            queue_size = self.task_queue.qsize()
        else:
            queue_size = len(self.task_queue)
        
        # 计算当前运行中的任务数
        running_tasks = sum(1 for task in self.tasks.values() if task.status == TaskStatus.RUNNING)
        
        return {
            **self.stats,
            "queue_size": queue_size,
            "running_tasks": running_tasks,
            "worker_count": self.worker_count,
            "max_pending_tasks": self.max_pending_tasks,
            "enable_priority": self.enable_priority
        }
    
    def clear_completed_tasks(self):
        """
        清理已完成的任务
        """
        completed_task_ids = []
        for task_id, task in self.tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                completed_task_ids.append(task_id)
        
        for task_id in completed_task_ids:
            del self.tasks[task_id]
        
        logger.debug(f"清理了 {len(completed_task_ids)} 个已完成的任务")
    
    def reset_stats(self):
        """
        重置统计信息
        """
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        logger.info("重置了任务队列统计信息")


# 创建全局任务队列管理器实例
_default_manager: Optional[TaskQueueManager] = None


def get_task_queue_manager(
    worker_count: int = 4,
    max_pending_tasks: int = 10000
) -> TaskQueueManager:
    """
    获取全局任务队列管理器实例
    
    Args:
        worker_count: 工作线程数
        max_pending_tasks: 最大待处理任务数
        
    Returns:
        任务队列管理器实例
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = TaskQueueManager(
            worker_count=worker_count,
            max_pending_tasks=max_pending_tasks
        )
    return _default_manager


# 便捷函数
async def submit_task(
    func: Callable[..., T],
    *args,
    **kwargs
) -> Task[T]:
    """
    提交任务
    
    Args:
        func: 任务函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        任务对象
    """
    manager = get_task_queue_manager()
    return await manager.submit_task(func, *args, **kwargs)


async def submit_high_priority_task(
    func: Callable[..., T],
    *args,
    **kwargs
) -> Task[T]:
    """
    提交高优先级任务
    
    Args:
        func: 任务函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        任务对象
    """
    manager = get_task_queue_manager()
    return await manager.submit_high_priority(func, *args, **kwargs)


async def submit_critical_task(
    func: Callable[..., T],
    *args,
    **kwargs
) -> Task[T]:
    """
    提交关键任务
    
    Args:
        func: 任务函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        任务对象
    """
    manager = get_task_queue_manager()
    return await manager.submit_critical(func, *args, **kwargs)


async def submit_low_priority_task(
    func: Callable[..., T],
    *args,
    **kwargs
) -> Task[T]:
    """
    提交低优先级任务
    
    Args:
        func: 任务函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        任务对象
    """
    manager = get_task_queue_manager()
    return await manager.submit_low_priority(func, *args, **kwargs)


async def start_task_queue():
    """
    启动任务队列
    """
    manager = get_task_queue_manager()
    await manager.start()


async def stop_task_queue():
    """
    停止任务队列
    """
    manager = get_task_queue_manager()
    await manager.stop()
