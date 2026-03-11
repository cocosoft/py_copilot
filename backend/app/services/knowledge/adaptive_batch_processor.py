"""
自适应批次处理器 - 向量化管理模块优化

根据系统负载动态调整批次大小，支持流式处理大文件，提供失败重试机制。
实现性能优化目标：批量处理性能提升50%以上。

任务编号: BE-001
阶段: Phase 1 - 基础优化期
"""

import logging
import asyncio
import psutil
import time
import gc
from typing import List, Dict, Any, Optional, Callable, Tuple, Iterator, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class BatchSizeStrategy(Enum):
    """批次大小调整策略"""
    CONSERVATIVE = "conservative"  # 保守策略，优先稳定性
    BALANCED = "balanced"          # 平衡策略，兼顾性能和稳定性
    AGGRESSIVE = "aggressive"      # 激进策略，最大化吞吐量


class ProcessingStatus(Enum):
    """处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class BatchConfig:
    """批次配置"""
    # 基础批次大小
    base_batch_size: int = 50
    
    # 最小/最大批次大小
    min_batch_size: int = 10
    max_batch_size: int = 200
    
    # 内存阈值（百分比）
    memory_threshold_low: float = 60.0
    memory_threshold_high: float = 80.0
    memory_threshold_critical: float = 90.0
    
    # 调整策略
    strategy: BatchSizeStrategy = BatchSizeStrategy.BALANCED
    
    # 重试配置
    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_max: float = 30.0
    
    # 流式处理配置
    stream_chunk_size: int = 1000
    stream_buffer_size: int = 5000
    
    # 并发控制
    max_concurrent_batches: int = 3
    
    def __post_init__(self):
        """验证配置"""
        if self.min_batch_size > self.max_batch_size:
            raise ValueError("min_batch_size 不能大于 max_batch_size")
        if self.base_batch_size < self.min_batch_size:
            self.base_batch_size = self.min_batch_size
        if self.base_batch_size > self.max_batch_size:
            self.base_batch_size = self.max_batch_size


@dataclass
class BatchItem:
    """批次中的单个项目"""
    id: str
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: ProcessingStatus = ProcessingStatus.PENDING
    retry_count: int = 0
    error_message: Optional[str] = None
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None


@dataclass
class BatchResult:
    """批次处理结果"""
    batch_id: str
    success: bool
    items_processed: int
    items_failed: int
    items: List[BatchItem]
    processing_time: float
    batch_size: int
    memory_usage_percent: float
    error_message: Optional[str] = None


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    total_processing_time: float = 0.0
    avg_batch_size: float = 0.0
    avg_processing_time: float = 0.0
    current_batch_size: int = 0
    current_memory_usage: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_items == 0:
            return 0.0
        return self.processed_items / self.total_items
    
    @property
    def throughput(self) -> float:
        """计算吞吐量（项目/秒）"""
        if self.total_processing_time == 0:
            return 0.0
        return self.processed_items / self.total_processing_time


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._history: List[Tuple[float, float]] = []  # (timestamp, memory_percent)
        self._max_history_size = 100
    
    def get_memory_usage(self) -> float:
        """
        获取当前内存使用率
        
        Returns:
            内存使用百分比 (0-100)
        """
        try:
            memory = psutil.virtual_memory()
            usage = memory.percent
            
            with self._lock:
                self._history.append((time.time(), usage))
                if len(self._history) > self._max_history_size:
                    self._history.pop(0)
            
            return usage
        except Exception as e:
            logger.warning(f"获取内存使用率失败: {e}")
            return 50.0  # 默认返回中等值
    
    def get_memory_trend(self, window_seconds: float = 10.0) -> float:
        """
        获取内存使用趋势
        
        Args:
            window_seconds: 时间窗口（秒）
            
        Returns:
            内存变化率（正数表示上升，负数表示下降）
        """
        with self._lock:
            if len(self._history) < 2:
                return 0.0
            
            now = time.time()
            recent = [(t, m) for t, m in self._history if now - t <= window_seconds]
            
            if len(recent) < 2:
                return 0.0
            
            first = recent[0][1]
            last = recent[-1][1]
            return last - first
    
    def is_memory_pressure(self, threshold: float = 85.0) -> bool:
        """检查是否存在内存压力"""
        return self.get_memory_usage() > threshold


class AdaptiveBatchProcessor:
    """
    自适应批次处理器
    
    根据系统负载动态调整批次大小，优化向量化处理性能。
    主要特性：
    - 基于内存使用率动态调整批次大小
    - 支持流式处理大文件
    - 自动失败重试机制
    - 详细的性能指标收集
    """
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """
        初始化自适应批次处理器
        
        Args:
            config: 批次配置，使用默认配置如果未提供
        """
        self.config = config or BatchConfig()
        self.memory_monitor = MemoryMonitor()
        self.stats = ProcessingStats()
        
        # 当前批次大小（会根据负载动态调整）
        self._current_batch_size = self.config.base_batch_size
        
        # 并发控制
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)
        
        # 性能历史记录
        self._performance_history: List[Dict[str, Any]] = []
        self._max_history_size = 50
        
        logger.info(
            f"自适应批次处理器初始化完成: "
            f"base_batch_size={self.config.base_batch_size}, "
            f"strategy={self.config.strategy.value}"
        )
    
    def _calculate_optimal_batch_size(self) -> int:
        """
        根据系统负载计算最优批次大小
        
        Returns:
            最优批次大小
        """
        memory_usage = self.memory_monitor.get_memory_usage()
        memory_trend = self.memory_monitor.get_memory_trend()
        
        # 基础调整系数
        adjustment_factor = 1.0
        
        # 根据内存使用率调整
        if memory_usage >= self.config.memory_threshold_critical:
            # 临界状态，大幅减小批次
            adjustment_factor = 0.3
            logger.warning(f"内存使用临界 ({memory_usage:.1f}%), 大幅减小批次大小")
        elif memory_usage >= self.config.memory_threshold_high:
            # 高负载状态，减小批次
            adjustment_factor = 0.6
            logger.info(f"内存使用较高 ({memory_usage:.1f}%), 减小批次大小")
        elif memory_usage >= self.config.memory_threshold_low:
            # 中等负载，略微减小批次
            adjustment_factor = 0.85
        else:
            # 低负载，可以增加批次
            adjustment_factor = 1.2
        
        # 根据内存趋势调整
        if memory_trend > 5.0:  # 内存快速上升
            adjustment_factor *= 0.8
            logger.info(f"内存快速上升 (趋势: {memory_trend:+.1f}%), 进一步减小批次")
        elif memory_trend < -3.0:  # 内存下降
            adjustment_factor *= 1.1
        
        # 根据策略调整
        if self.config.strategy == BatchSizeStrategy.CONSERVATIVE:
            adjustment_factor *= 0.8
        elif self.config.strategy == BatchSizeStrategy.AGGRESSIVE:
            adjustment_factor *= 1.2
        
        # 计算新的批次大小
        new_batch_size = int(self._current_batch_size * adjustment_factor)
        
        # 限制在合理范围内
        new_batch_size = max(
            self.config.min_batch_size,
            min(self.config.max_batch_size, new_batch_size)
        )
        
        # 更新当前批次大小
        self._current_batch_size = new_batch_size
        
        logger.debug(
            f"批次大小调整: {self._current_batch_size} -> {new_batch_size} "
            f"(内存: {memory_usage:.1f}%, 趋势: {memory_trend:+.1f}%)"
        )
        
        return new_batch_size
    
    def _create_batches(self, items: List[Any]) -> Iterator[List[BatchItem]]:
        """
        将项目列表分割成批次
        
        Args:
            items: 项目列表
            
        Yields:
            批次项目列表
        """
        batch_size = self._calculate_optimal_batch_size()
        batch_id = 0
        
        for i in range(0, len(items), batch_size):
            batch_items = items[i:i + batch_size]
            
            # 包装为 BatchItem
            wrapped_items = []
            for idx, item_data in enumerate(batch_items):
                item_id = f"item_{batch_id}_{idx}"
                wrapped_items.append(BatchItem(
                    id=item_id,
                    data=item_data,
                    metadata={"batch_id": batch_id, "index": i + idx}
                ))
            
            yield wrapped_items
            batch_id += 1
    
    async def _process_batch_with_retry(
        self,
        batch: List[BatchItem],
        processor: Callable[[Any], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult:
        """
        处理单个批次，支持重试
        
        Args:
            batch: 批次项目列表
            processor: 处理函数
            progress_callback: 进度回调函数
            
        Returns:
            批次处理结果
        """
        batch_id = batch[0].metadata.get("batch_id", 0) if batch else 0
        start_time = time.time()
        memory_before = self.memory_monitor.get_memory_usage()
        
        logger.info(f"开始处理批次 {batch_id}, 大小: {len(batch)}")
        
        # 更新项目状态
        for item in batch:
            item.status = ProcessingStatus.PROCESSING
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.max_retries:
            try:
                # 使用信号量控制并发
                async with self._semaphore:
                    # 处理批次中的每个项目
                    for idx, item in enumerate(batch):
                        item_start = time.time()
                        
                        try:
                            # 执行处理
                            result = await self._execute_processor(processor, item.data)
                            
                            # 更新项目状态
                            item.status = ProcessingStatus.SUCCESS
                            item.processed_at = datetime.now()
                            item.processing_time = time.time() - item_start
                            
                            # 将结果存入 metadata
                            item.metadata["result"] = result
                            
                        except Exception as e:
                            item.error_message = str(e)
                            item.retry_count += 1
                            
                            if item.retry_count <= self.config.max_retries:
                                item.status = ProcessingStatus.RETRYING
                                # 指数退避重试
                                delay = min(
                                    self.config.retry_delay_base * (2 ** item.retry_count),
                                    self.config.retry_delay_max
                                )
                                logger.warning(
                                    f"项目 {item.id} 处理失败，{delay:.1f}秒后重试 "
                                    f"(第{item.retry_count}次): {e}"
                                )
                                await asyncio.sleep(delay)
                                
                                # 重试
                                result = await self._execute_processor(processor, item.data)
                                item.status = ProcessingStatus.SUCCESS
                                item.processed_at = datetime.now()
                                item.processing_time = time.time() - item_start
                                item.metadata["result"] = result
                            else:
                                item.status = ProcessingStatus.FAILED
                                logger.error(f"项目 {item.id} 处理失败，已达最大重试次数: {e}")
                        
                        # 进度回调
                        if progress_callback:
                            progress_callback(idx + 1, len(batch))
                
                # 计算结果
                processing_time = time.time() - start_time
                memory_after = self.memory_monitor.get_memory_usage()
                
                success_count = sum(1 for item in batch if item.status == ProcessingStatus.SUCCESS)
                failed_count = len(batch) - success_count
                
                result = BatchResult(
                    batch_id=str(batch_id),
                    success=failed_count == 0,
                    items_processed=success_count,
                    items_failed=failed_count,
                    items=batch,
                    processing_time=processing_time,
                    batch_size=len(batch),
                    memory_usage_percent=memory_after
                )
                
                # 记录性能数据
                self._record_performance(batch_id, len(batch), processing_time, memory_after)
                
                logger.info(
                    f"批次 {batch_id} 处理完成: {success_count}/{len(batch)} 成功, "
                    f"耗时 {processing_time:.2f}s, 内存 {memory_before:.1f}% -> {memory_after:.1f}%"
                )
                
                return result
                
            except Exception as e:
                retry_count += 1
                last_error = e
                
                if retry_count <= self.config.max_retries:
                    delay = min(
                        self.config.retry_delay_base * (2 ** retry_count),
                        self.config.retry_delay_max
                    )
                    logger.warning(
                        f"批次 {batch_id} 处理失败，{delay:.1f}秒后重试 "
                        f"(第{retry_count}次): {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"批次 {batch_id} 处理失败，已达最大重试次数: {e}")
        
        # 所有重试都失败
        processing_time = time.time() - start_time
        for item in batch:
            if item.status == ProcessingStatus.PROCESSING:
                item.status = ProcessingStatus.FAILED
                item.error_message = str(last_error)
        
        return BatchResult(
            batch_id=str(batch_id),
            success=False,
            items_processed=0,
            items_failed=len(batch),
            items=batch,
            processing_time=processing_time,
            batch_size=len(batch),
            memory_usage_percent=self.memory_monitor.get_memory_usage(),
            error_message=str(last_error)
        )
    
    async def _execute_processor(
        self,
        processor: Callable[[Any], Any],
        data: Any
    ) -> Any:
        """
        执行处理器函数
        
        Args:
            processor: 处理函数
            data: 输入数据
            
        Returns:
            处理结果
        """
        # 如果处理器是协程函数，直接调用
        if asyncio.iscoroutinefunction(processor):
            return await processor(data)
        else:
            # 如果是普通函数，在线程池中执行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, processor, data)
    
    def _record_performance(
        self,
        batch_id: int,
        batch_size: int,
        processing_time: float,
        memory_usage: float
    ):
        """记录性能数据"""
        self._performance_history.append({
            "batch_id": batch_id,
            "batch_size": batch_size,
            "processing_time": processing_time,
            "memory_usage": memory_usage,
            "throughput": batch_size / processing_time if processing_time > 0 else 0,
            "timestamp": time.time()
        })
        
        if len(self._performance_history) > self._max_history_size:
            self._performance_history.pop(0)
    
    async def process_items(
        self,
        items: List[Any],
        processor: Callable[[Any], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[BatchResult], ProcessingStats]:
        """
        处理项目列表
        
        Args:
            items: 要处理的项目列表
            processor: 处理函数
            progress_callback: 进度回调函数，接收 (current, total) 参数
            
        Returns:
            (批次结果列表, 处理统计信息)
        """
        self.stats = ProcessingStats(
            total_items=len(items),
            start_time=datetime.now()
        )
        
        logger.info(f"开始处理 {len(items)} 个项目")
        
        # 创建批次
        batches = list(self._create_batches(items))
        self.stats.total_batches = len(batches)
        
        logger.info(f"分成 {len(batches)} 个批次处理")
        
        # 处理所有批次
        results = []
        total_processed = 0
        
        for batch_idx, batch in enumerate(batches):
            # 更新当前批次大小统计
            self.stats.current_batch_size = len(batch)
            self.stats.current_memory_usage = self.memory_monitor.get_memory_usage()
            
            # 处理批次
            batch_result = await self._process_batch_with_retry(
                batch,
                processor,
                progress_callback=lambda c, t: progress_callback(
                    total_processed + c, len(items)
                ) if progress_callback else None
            )
            
            results.append(batch_result)
            total_processed += batch_result.items_processed
            
            # 更新统计
            self.stats.processed_items += batch_result.items_processed
            self.stats.failed_items += batch_result.items_failed
            self.stats.total_processing_time += batch_result.processing_time
            
            if batch_result.success:
                self.stats.successful_batches += 1
            else:
                self.stats.failed_batches += 1
            
            # 触发垃圾回收
            if batch_idx % 5 == 0:
                gc.collect()
            
            # 批次间短暂延迟，让系统有时间处理其他请求
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(0.1)
        
        # 计算平均值
        if self.stats.total_batches > 0:
            self.stats.avg_batch_size = self.stats.total_items / self.stats.total_batches
            self.stats.avg_processing_time = self.stats.total_processing_time / self.stats.total_batches
        
        self.stats.end_time = datetime.now()
        
        logger.info(
            f"处理完成: {self.stats.processed_items}/{self.stats.total_items} 成功 "
            f"({self.stats.success_rate:.1%}), "
            f"吞吐量: {self.stats.throughput:.2f} items/s"
        )
        
        return results, self.stats
    
    async def process_stream(
        self,
        item_stream: Iterator[Any],
        processor: Callable[[Any], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[BatchResult], ProcessingStats]:
        """
        流式处理项目
        
        适用于大文件处理，可以边读取边处理，减少内存占用。
        
        Args:
            item_stream: 项目流（迭代器）
            processor: 处理函数
            progress_callback: 进度回调函数
            
        Returns:
            (批次结果列表, 处理统计信息)
        """
        self.stats = ProcessingStats(start_time=datetime.now())
        
        logger.info("开始流式处理")
        
        results = []
        buffer = []
        total_processed = 0
        total_items = 0  # 流式处理时总数未知
        
        for item in item_stream:
            total_items += 1
            buffer.append(item)
            
            # 当缓冲区达到批次大小时处理
            current_batch_size = self._calculate_optimal_batch_size()
            
            if len(buffer) >= current_batch_size:
                # 创建批次
                batch_items = []
                for idx, item_data in enumerate(buffer[:current_batch_size]):
                    item_id = f"stream_item_{total_processed + idx}"
                    batch_items.append(BatchItem(
                        id=item_id,
                        data=item_data,
                        metadata={"stream_index": total_processed + idx}
                    ))
                
                # 处理批次
                batch_result = await self._process_batch_with_retry(
                    batch_items,
                    processor,
                    progress_callback
                )
                
                results.append(batch_result)
                total_processed += len(batch_items)
                
                # 更新统计
                self.stats.processed_items += batch_result.items_processed
                self.stats.failed_items += batch_result.items_failed
                self.stats.total_processing_time += batch_result.processing_time
                self.stats.total_batches += 1
                
                if batch_result.success:
                    self.stats.successful_batches += 1
                else:
                    self.stats.failed_batches += 1
                
                # 清空已处理的缓冲区
                buffer = buffer[current_batch_size:]
                
                # 触发垃圾回收
                if self.stats.total_batches % 5 == 0:
                    gc.collect()
        
        # 处理剩余的项目
        if buffer:
            batch_items = []
            for idx, item_data in enumerate(buffer):
                item_id = f"stream_item_{total_processed + idx}"
                batch_items.append(BatchItem(
                    id=item_id,
                    data=item_data,
                    metadata={"stream_index": total_processed + idx}
                ))
            
            batch_result = await self._process_batch_with_retry(
                batch_items,
                processor,
                progress_callback
            )
            
            results.append(batch_result)
            self.stats.processed_items += batch_result.items_processed
            self.stats.failed_items += batch_result.items_failed
            self.stats.total_processing_time += batch_result.processing_time
            self.stats.total_batches += 1
        
        self.stats.total_items = total_items
        
        # 计算平均值
        if self.stats.total_batches > 0:
            self.stats.avg_batch_size = self.stats.total_items / self.stats.total_batches
            self.stats.avg_processing_time = self.stats.total_processing_time / self.stats.total_batches
        
        self.stats.end_time = datetime.now()
        
        logger.info(
            f"流式处理完成: {self.stats.processed_items}/{self.stats.total_items} 成功 "
            f"({self.stats.success_rate:.1%}), "
            f"吞吐量: {self.stats.throughput:.2f} items/s"
        )
        
        return results, self.stats
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        获取性能报告
        
        Returns:
            性能报告字典
        """
        if not self._performance_history:
            return {"message": "暂无性能数据"}
        
        # 计算统计数据
        throughputs = [p["throughput"] for p in self._performance_history]
        batch_sizes = [p["batch_size"] for p in self._performance_history]
        processing_times = [p["processing_time"] for p in self._performance_history]
        memory_usages = [p["memory_usage"] for p in self._performance_history]
        
        return {
            "total_batches": len(self._performance_history),
            "throughput": {
                "avg": sum(throughputs) / len(throughputs),
                "min": min(throughputs),
                "max": max(throughputs)
            },
            "batch_size": {
                "avg": sum(batch_sizes) / len(batch_sizes),
                "min": min(batch_sizes),
                "max": max(batch_sizes),
                "current": self._current_batch_size
            },
            "processing_time": {
                "avg": sum(processing_times) / len(processing_times),
                "min": min(processing_times),
                "max": max(processing_times)
            },
            "memory_usage": {
                "avg": sum(memory_usages) / len(memory_usages),
                "min": min(memory_usages),
                "max": max(memory_usages),
                "current": self.memory_monitor.get_memory_usage()
            },
            "current_stats": {
                "total_items": self.stats.total_items,
                "processed_items": self.stats.processed_items,
                "failed_items": self.stats.failed_items,
                "success_rate": self.stats.success_rate,
                "overall_throughput": self.stats.throughput
            }
        }


# 便捷函数

async def process_with_adaptive_batching(
    items: List[Any],
    processor: Callable[[Any], Any],
    config: Optional[BatchConfig] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Tuple[List[BatchResult], ProcessingStats]:
    """
    使用自适应批次处理项目
    
    Args:
        items: 要处理的项目列表
        processor: 处理函数
        config: 批次配置
        progress_callback: 进度回调函数
        
    Returns:
        (批次结果列表, 处理统计信息)
    """
    processor_instance = AdaptiveBatchProcessor(config)
    return await processor_instance.process_items(items, processor, progress_callback)


async def process_stream_with_adaptive_batching(
    item_stream: Iterator[Any],
    processor: Callable[[Any], Any],
    config: Optional[BatchConfig] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Tuple[List[BatchResult], ProcessingStats]:
    """
    使用自适应批次流式处理项目
    
    Args:
        item_stream: 项目流
        processor: 处理函数
        config: 批次配置
        progress_callback: 进度回调函数
        
    Returns:
        (批次结果列表, 处理统计信息)
    """
    processor_instance = AdaptiveBatchProcessor(config)
    return await processor_instance.process_stream(item_stream, processor, progress_callback)
