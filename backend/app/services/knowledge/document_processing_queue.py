"""
文档处理队列服务

提供文档处理的并发控制和队列管理，避免同时处理过多文档导致系统资源耗尽
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProcessingTask:
    """处理任务"""
    document_id: int
    knowledge_base_id: int
    document_name: str
    priority: int = 0  # 优先级，数字越小优先级越高
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3

    def __lt__(self, other):
        """
        实现小于比较，用于优先级队列排序

        @param other: 另一个ProcessingTask对象
        @return: 如果当前任务优先级更高则返回True
        """
        if not isinstance(other, ProcessingTask):
            return NotImplemented
        # 优先级数字小的先处理
        if self.priority != other.priority:
            return self.priority < other.priority
        # 优先级相同则先创建的先处理
        return self.created_at < other.created_at


class DocumentProcessingQueue:
    """
    文档处理队列

    功能：
    1. 控制并发处理数量
    2. 管理处理队列
    3. 支持优先级处理
    4. 提供任务状态查询
    5. 修复U03：增强并发控制健壮性
    """

    def __init__(self, max_concurrent: int = 2, max_queue_size: int = 100, timeout: int = 300):
        """
        初始化处理队列

        修复U03：添加队列大小限制和超时控制

        @param max_concurrent: 最大并发处理数量，默认2个
        @param max_queue_size: 最大队列大小，默认100
        @param timeout: 单个文档处理超时时间（秒），默认300
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.timeout = timeout
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._processing: Dict[int, ProcessingTask] = {}
        self._completed: Dict[int, Dict[str, Any]] = {}
        self._failed: Dict[int, Dict[str, Any]] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
        self._processor_func: Optional[Callable] = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        # 修复U03：添加处理超时控制
        self._processing_start_times: Dict[int, datetime] = {}

        logger.info(f"文档处理队列初始化完成，最大并发数: {max_concurrent}, "
                   f"最大队列大小: {max_queue_size}, 超时: {timeout}秒")

    def set_processor(self, processor_func: Callable):
        """
        设置文档处理函数

        @param processor_func: 处理函数，接收(document_id, knowledge_base_id)参数
        """
        self._processor_func = processor_func

    async def start(self):
        """启动队列处理器"""
        if self._running:
            return

        self._running = True
        logger.info("文档处理队列已启动")

        # 启动队列处理器任务
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """停止队列处理器"""
        self._running = False
        logger.info("文档处理队列已停止")

    async def add_document(self, document_id: int, knowledge_base_id: int,
                          document_name: str, priority: int = 0) -> bool:
        """
        添加文档到处理队列

        修复U03：添加队列大小检查和重复处理控制

        @param document_id: 文档ID
        @param knowledge_base_id: 知识库ID
        @param document_name: 文档名称
        @param priority: 优先级（数字越小优先级越高）
        @return: 是否成功添加
        """
        async with self._lock:
            # 修复U03：检查队列是否已满
            if self._queue.qsize() >= self.max_queue_size:
                logger.warning(f"队列已满 ({self._queue.qsize()}/{self.max_queue_size})，无法添加文档 {document_id}")
                return False

            # 检查是否已在处理中
            if document_id in self._processing:
                logger.warning(f"文档 {document_id} 正在处理中，跳过")
                return False

            # 检查是否已在队列中
            # 注意：由于PriorityQueue不支持遍历，这里使用额外的跟踪机制
            if hasattr(self, '_queued_document_ids') and document_id in self._queued_document_ids:
                logger.warning(f"文档 {document_id} 已在队列中，跳过")
                return False

            # 检查是否已完成（成功的文档不需要重新处理）
            if document_id in self._completed:
                logger.warning(f"文档 {document_id} 已处理完成，跳过")
                return False

            # 如果文档之前处理失败了，允许重新处理
            if document_id in self._failed:
                logger.info(f"文档 {document_id} 之前处理失败，允许重新处理")
                del self._failed[document_id]

        # 创建任务并添加到队列
        task = ProcessingTask(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            document_name=document_name,
            priority=priority
        )

        # 修复U03：跟踪队列中的文档ID
        if not hasattr(self, '_queued_document_ids'):
            self._queued_document_ids = set()

        async with self._lock:
            self._queued_document_ids.add(document_id)

        # 使用优先级队列（Python的PriorityQueue是最小堆，所以用负数实现高优先级先出）
        await self._queue.put((priority, task))
        logger.info(f"文档 {document_id} ({document_name}) 已添加到处理队列，优先级: {priority}")

        return True

    async def _process_queue(self):
        """处理队列中的文档"""
        while self._running:
            try:
                # 获取队列中的任务（带超时，以便检查_running状态）
                try:
                    priority, task = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # 使用信号量控制并发
                asyncio.create_task(self._process_with_semaphore(task))

            except Exception as e:
                logger.error(f"队列处理异常: {e}")
                await asyncio.sleep(1)

    async def _process_with_semaphore(self, task: ProcessingTask):
        """
        使用信号量控制并发处理

        @param task: 处理任务
        """
        async with self._semaphore:
            await self._process_document(task)

    async def _process_document(self, task: ProcessingTask):
        """
        处理单个文档

        修复U03：添加超时控制和异常处理

        @param task: 处理任务
        """
        document_id = task.document_id
        knowledge_base_id = task.knowledge_base_id

        # 标记为处理中
        async with self._lock:
            self._processing[document_id] = task
            self._processing_start_times[document_id] = datetime.now()

            # 从队列跟踪中移除
            if hasattr(self, '_queued_document_ids') and document_id in self._queued_document_ids:
                self._queued_document_ids.remove(document_id)

        logger.info(f"开始处理文档 {document_id} ({task.document_name})，"
                   f"当前并发数: {len(self._processing)}/{self.max_concurrent}")

        try:
            if self._processor_func:
                # 修复U03：添加超时控制
                await asyncio.wait_for(
                    self._processor_func(document_id, knowledge_base_id),
                    timeout=self.timeout
                )

                # 标记为完成
                async with self._lock:
                    self._completed[document_id] = {
                        "task": task,
                        "completed_at": datetime.now(),
                        "status": "success"
                    }
                    del self._processing[document_id]
                    if document_id in self._processing_start_times:
                        del self._processing_start_times[document_id]

                logger.info(f"文档 {document_id} 处理完成")
            else:
                raise Exception("未设置处理器函数")

        except asyncio.TimeoutError:
            logger.error(f"文档 {document_id} 处理超时（超过 {self.timeout} 秒）")

            # 标记为失败
            async with self._lock:
                self._failed[document_id] = {
                    "task": task,
                    "failed_at": datetime.now(),
                    "error": f"处理超时（超过 {self.timeout} 秒）",
                    "retry_count": task.retry_count
                }
                del self._processing[document_id]
                if document_id in self._processing_start_times:
                    del self._processing_start_times[document_id]

        except Exception as e:
            logger.error(f"文档 {document_id} 处理失败: {e}")

            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"文档 {document_id} 将在 {task.retry_count} 秒后重试 (第 {task.retry_count}/{task.max_retries} 次)")
                await asyncio.sleep(task.retry_count * 2)  # 指数退避
                await self._queue.put((task.priority, task))

                # 从处理中移除
                async with self._lock:
                    del self._processing[document_id]
                    if document_id in self._processing_start_times:
                        del self._processing_start_times[document_id]
            else:
                # 标记为失败
                async with self._lock:
                    self._failed[document_id] = {
                        "task": task,
                        "failed_at": datetime.now(),
                        "error": str(e),
                        "retry_count": task.retry_count
                    }
                    del self._processing[document_id]
                    if document_id in self._processing_start_times:
                        del self._processing_start_times[document_id]

    def get_status(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        获取文档处理状态

        @param document_id: 文档ID
        @return: 状态信息
        """
        if document_id in self._processing:
            task = self._processing[document_id]
            return {
                "status": "processing",
                "document_id": document_id,
                "document_name": task.document_name,
                "started_at": task.created_at.isoformat()
            }

        if document_id in self._completed:
            info = self._completed[document_id]
            return {
                "status": "completed",
                "document_id": document_id,
                "document_name": info["task"].document_name,
                "completed_at": info["completed_at"].isoformat()
            }

        if document_id in self._failed:
            info = self._failed[document_id]
            return {
                "status": "failed",
                "document_id": document_id,
                "document_name": info["task"].document_name,
                "failed_at": info["failed_at"].isoformat(),
                "error": info.get("error"),
                "retry_count": info.get("retry_count", 0)
            }

        return None

    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列整体状态

        修复U03：添加超时监控和处理时间统计

        @return: 队列状态信息
        """
        # 计算处理时间
        processing_times = {}
        now = datetime.now()
        for doc_id, start_time in self._processing_start_times.items():
            processing_times[doc_id] = (now - start_time).total_seconds()

        # 检查是否有超时的任务
        timeout_warnings = []
        for doc_id, elapsed in processing_times.items():
            if elapsed > self.timeout * 0.8:  # 超过80%超时时间发出警告
                timeout_warnings.append({
                    "document_id": doc_id,
                    "elapsed_seconds": elapsed,
                    "timeout_seconds": self.timeout,
                    "warning": "接近超时"
                })

        return {
            "queue_size": self._queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "processing_count": len(self._processing),
            "completed_count": len(self._completed),
            "failed_count": len(self._failed),
            "max_concurrent": self.max_concurrent,
            "timeout_seconds": self.timeout,
            "timeout_warnings": timeout_warnings,
            "processing_documents": [
                {
                    "document_id": task.document_id,
                    "document_name": task.document_name,
                    "started_at": task.created_at.isoformat(),
                    "elapsed_seconds": processing_times.get(task.document_id, 0)
                }
                for task in self._processing.values()
            ]
        }

    async def check_timeouts(self):
        """
        检查并处理超时任务

        修复U03：定期检查处理中的任务是否超时
        """
        now = datetime.now()
        timeout_tasks = []

        async with self._lock:
            for doc_id, start_time in list(self._processing_start_times.items()):
                elapsed = (now - start_time).total_seconds()
                if elapsed > self.timeout:
                    timeout_tasks.append(doc_id)

        for doc_id in timeout_tasks:
            logger.warning(f"文档 {doc_id} 处理超时，强制终止")
            # 这里可以添加强制终止逻辑
            # 注意：由于Python的asyncio无法强制取消任务，这里只是记录

        return len(timeout_tasks)

    def clear_completed(self, before_hours: int = 24):
        """
        清理已完成的任务记录

        @param before_hours: 清理几小时前的记录
        """
        cutoff_time = datetime.now() - __import__('datetime').timedelta(hours=before_hours)

        # 清理已完成的记录
        completed_to_remove = [
            doc_id for doc_id, info in self._completed.items()
            if info["completed_at"] < cutoff_time
        ]
        for doc_id in completed_to_remove:
            del self._completed[doc_id]

        # 清理失败的记录
        failed_to_remove = [
            doc_id for doc_id, info in self._failed.items()
            if info["failed_at"] < cutoff_time
        ]
        for doc_id in failed_to_remove:
            del self._failed[doc_id]

        if completed_to_remove or failed_to_remove:
            logger.info(f"清理了 {len(completed_to_remove)} 条完成记录和 {len(failed_to_remove)} 条失败记录")


# 全局队列实例
document_processing_queue = DocumentProcessingQueue(max_concurrent=2)
