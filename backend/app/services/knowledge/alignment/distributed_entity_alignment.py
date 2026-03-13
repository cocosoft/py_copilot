#!/usr/bin/env python3
"""
分布式实体对齐服务

支持大规模实体对齐的分布式处理，包括：
- 数据分片与并行处理
- 分布式相似度计算
- 结果聚合与去重
- 负载均衡与故障恢复
"""

import asyncio
import logging
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

logger = logging.getLogger(__name__)


class PartitionStrategy(Enum):
    """数据分片策略"""
    HASH = "hash"           # 基于哈希的分片
    RANGE = "range"         # 基于范围的分片
    ROUND_ROBIN = "round_robin"  # 轮询分片


@dataclass
class EntityPartition:
    """实体数据分片"""
    partition_id: str
    shard_index: int
    total_shards: int
    entities: List[Dict[str, Any]] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None


@dataclass
class AlignmentTask:
    """对齐任务"""
    task_id: str
    partition_id: str
    source_entities: List[Dict[str, Any]]
    target_entities: List[Dict[str, Any]]
    threshold: float = 0.85
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class DistributedAlignmentResult:
    """分布式对齐结果"""
    task_id: str
    total_partitions: int
    completed_partitions: int
    aligned_pairs: List[Dict[str, Any]] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


class DistributedEntityAligner:
    """
    分布式实体对齐器
    
    支持大规模实体对齐的分布式处理
    """
    
    def __init__(self, 
                 num_workers: int = None,
                 partition_strategy: PartitionStrategy = PartitionStrategy.HASH,
                 batch_size: int = 1000):
        """
        初始化分布式对齐器
        
        Args:
            num_workers: 工作进程数，默认使用CPU核心数
            partition_strategy: 数据分片策略
            batch_size: 批处理大小
        """
        self.num_workers = num_workers or mp.cpu_count()
        self.partition_strategy = partition_strategy
        self.batch_size = batch_size
        
        # 线程池用于I/O密集型任务
        self.thread_pool = ThreadPoolExecutor(max_workers=self.num_workers * 2)
        # 进程池用于CPU密集型任务
        self.process_pool = ProcessPoolExecutor(max_workers=self.num_workers)
        
        # 任务管理
        self.tasks: Dict[str, AlignmentTask] = {}
        
        logger.info(f"分布式实体对齐器初始化完成 (工作进程: {self.num_workers})")
    
    def partition_entities(self, 
                          entities: List[Dict[str, Any]], 
                          num_shards: int = None) -> List[EntityPartition]:
        """
        将实体数据分片
        
        Args:
            entities: 实体列表
            num_shards: 分片数量
        
        Returns:
            分片列表
        """
        num_shards = num_shards or self.num_workers
        
        if self.partition_strategy == PartitionStrategy.HASH:
            return self._hash_partition(entities, num_shards)
        elif self.partition_strategy == PartitionStrategy.RANGE:
            return self._range_partition(entities, num_shards)
        else:
            return self._round_robin_partition(entities, num_shards)
    
    def _hash_partition(self, 
                       entities: List[Dict[str, Any]], 
                       num_shards: int) -> List[EntityPartition]:
        """基于哈希的分片"""
        shards = [[] for _ in range(num_shards)]
        
        for entity in entities:
            # 使用实体ID的哈希值确定分片
            entity_id = str(entity.get('id', entity.get('entity_id', '')))
            hash_value = int(hashlib.md5(entity_id.encode()).hexdigest(), 16)
            shard_index = hash_value % num_shards
            shards[shard_index].append(entity)
        
        partitions = []
        for i, shard_entities in enumerate(shards):
            partition = EntityPartition(
                partition_id=f"partition_{i}",
                shard_index=i,
                total_shards=num_shards,
                entities=shard_entities
            )
            partitions.append(partition)
        
        logger.info(f"哈希分片完成: {len(entities)} 个实体 -> {num_shards} 个分片")
        return partitions
    
    def _range_partition(self, 
                        entities: List[Dict[str, Any]], 
                        num_shards: int) -> List[EntityPartition]:
        """基于范围的分片"""
        # 按实体ID排序
        sorted_entities = sorted(entities, 
                                key=lambda e: str(e.get('id', e.get('entity_id', ''))))
        
        shard_size = len(sorted_entities) // num_shards
        partitions = []
        
        for i in range(num_shards):
            start_idx = i * shard_size
            end_idx = start_idx + shard_size if i < num_shards - 1 else len(sorted_entities)
            
            partition = EntityPartition(
                partition_id=f"partition_{i}",
                shard_index=i,
                total_shards=num_shards,
                entities=sorted_entities[start_idx:end_idx]
            )
            partitions.append(partition)
        
        logger.info(f"范围分片完成: {len(entities)} 个实体 -> {num_shards} 个分片")
        return partitions
    
    def _round_robin_partition(self, 
                              entities: List[Dict[str, Any]], 
                              num_shards: int) -> List[EntityPartition]:
        """轮询分片"""
        shards = [[] for _ in range(num_shards)]
        
        for i, entity in enumerate(entities):
            shard_index = i % num_shards
            shards[shard_index].append(entity)
        
        partitions = []
        for i, shard_entities in enumerate(shards):
            partition = EntityPartition(
                partition_id=f"partition_{i}",
                shard_index=i,
                total_shards=num_shards,
                entities=shard_entities
            )
            partitions.append(partition)
        
        logger.info(f"轮询分片完成: {len(entities)} 个实体 -> {num_shards} 个分片")
        return partitions
    
    async def align_distributed(self,
                               source_entities: List[Dict[str, Any]],
                               target_entities: List[Dict[str, Any]],
                               threshold: float = 0.85,
                               use_embeddings: bool = True) -> DistributedAlignmentResult:
        """
        执行分布式实体对齐
        
        Args:
            source_entities: 源实体列表
            target_entities: 目标实体列表
            threshold: 相似度阈值
            use_embeddings: 是否使用向量嵌入
        
        Returns:
            分布式对齐结果
        """
        import uuid
        import time
        
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"开始分布式对齐任务: {task_id}")
        logger.info(f"源实体: {len(source_entities)}, 目标实体: {len(target_entities)}")
        
        # 1. 数据分片
        source_partitions = self.partition_entities(source_entities, self.num_workers)
        target_partitions = self.partition_entities(target_entities, self.num_workers)
        
        # 2. 创建对齐任务
        alignment_tasks = []
        for i, (src_part, tgt_part) in enumerate(zip(source_partitions, target_partitions)):
            task = AlignmentTask(
                task_id=f"{task_id}_{i}",
                partition_id=src_part.partition_id,
                source_entities=src_part.entities,
                target_entities=tgt_part.entities,
                threshold=threshold
            )
            alignment_tasks.append(task)
            self.tasks[task.task_id] = task
        
        # 3. 并行执行对齐任务
        logger.info(f"启动 {len(alignment_tasks)} 个并行对齐任务")
        
        # 使用线程池并行处理
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                self.thread_pool,
                self._align_partition,
                task,
                use_embeddings
            )
            for task in alignment_tasks
        ]
        
        # 等待所有任务完成
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        # 4. 聚合结果
        all_aligned_pairs = []
        completed_count = 0
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"分区 {i} 对齐失败: {result}")
                alignment_tasks[i].status = "failed"
                alignment_tasks[i].error = str(result)
                failed_count += 1
            else:
                alignment_tasks[i].result = result
                alignment_tasks[i].status = "completed"
                all_aligned_pairs.extend(result)
                completed_count += 1
        
        # 5. 去重和排序
        unique_pairs = self._deduplicate_and_sort(all_aligned_pairs)
        
        execution_time = (time.time() - start_time) * 1000
        
        # 6. 构建结果
        result = DistributedAlignmentResult(
            task_id=task_id,
            total_partitions=len(alignment_tasks),
            completed_partitions=completed_count,
            aligned_pairs=unique_pairs,
            statistics={
                'source_entities': len(source_entities),
                'target_entities': len(target_entities),
                'total_partitions': len(alignment_tasks),
                'completed_partitions': completed_count,
                'failed_partitions': failed_count,
                'aligned_pairs': len(unique_pairs),
                'avg_pairs_per_partition': len(unique_pairs) / completed_count if completed_count > 0 else 0
            },
            execution_time_ms=execution_time
        )
        
        logger.info(f"分布式对齐完成: {len(unique_pairs)} 对实体 ({execution_time:.0f}ms)")
        
        return result
    
    def _align_partition(self, 
                        task: AlignmentTask, 
                        use_embeddings: bool = True) -> List[Dict[str, Any]]:
        """
        对齐单个分区的实体
        
        Args:
            task: 对齐任务
            use_embeddings: 是否使用向量嵌入
        
        Returns:
            对齐结果列表
        """
        task.start_time = datetime.now()
        task.status = "running"
        
        try:
            aligned_pairs = []
            
            # 简化的对齐逻辑（实际应该使用BERT等模型）
            for src_entity in task.source_entities:
                src_name = str(src_entity.get('name', src_entity.get('text', '')))
                src_id = str(src_entity.get('id', src_entity.get('entity_id', '')))
                
                best_match = None
                best_score = 0.0
                
                for tgt_entity in task.target_entities:
                    tgt_name = str(tgt_entity.get('name', tgt_entity.get('text', '')))
                    tgt_id = str(tgt_entity.get('id', tgt_entity.get('entity_id', '')))
                    
                    # 计算相似度（使用简单的字符串相似度）
                    score = self._calculate_similarity(src_name, tgt_name)
                    
                    if score > best_score and score >= task.threshold:
                        best_score = score
                        best_match = {
                            'source_id': src_id,
                            'source_name': src_name,
                            'target_id': tgt_id,
                            'target_name': tgt_name,
                            'similarity': score,
                            'partition_id': task.partition_id
                        }
                
                if best_match:
                    aligned_pairs.append(best_match)
            
            task.end_time = datetime.now()
            task.status = "completed"
            
            return aligned_pairs
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            raise
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度分数 (0-1)
        """
        # 使用Jaccard相似度作为示例
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _deduplicate_and_sort(self, pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重并排序对齐结果
        
        Args:
            pairs: 对齐结果列表
        
        Returns:
            去重排序后的结果
        """
        # 使用source_id + target_id作为唯一键
        seen = set()
        unique_pairs = []
        
        for pair in pairs:
            key = (pair['source_id'], pair['target_id'])
            if key not in seen:
                seen.add(key)
                unique_pairs.append(pair)
        
        # 按相似度降序排序
        unique_pairs.sort(key=lambda x: x['similarity'], reverse=True)
        
        return unique_pairs
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态信息
        """
        # 查找主任务的所有子任务
        sub_tasks = [
            task for task_id_key, task in self.tasks.items()
            if task_id_key.startswith(task_id)
        ]
        
        if not sub_tasks:
            return None
        
        total = len(sub_tasks)
        completed = sum(1 for t in sub_tasks if t.status == "completed")
        failed = sum(1 for t in sub_tasks if t.status == "failed")
        running = sum(1 for t in sub_tasks if t.status == "running")
        pending = sum(1 for t in sub_tasks if t.status == "pending")
        
        return {
            'task_id': task_id,
            'total_subtasks': total,
            'completed': completed,
            'failed': failed,
            'running': running,
            'pending': pending,
            'progress': completed / total if total > 0 else 0
        }
    
    def shutdown(self):
        """关闭资源"""
        logger.info("关闭分布式对齐器...")
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("分布式对齐器已关闭")


# 便捷函数
async def align_entities_distributed(
    source_entities: List[Dict[str, Any]],
    target_entities: List[Dict[str, Any]],
    threshold: float = 0.85
) -> DistributedAlignmentResult:
    """便捷函数：分布式对齐实体"""
    aligner = DistributedEntityAligner()
    try:
        result = await aligner.align_distributed(source_entities, target_entities, threshold)
        return result
    finally:
        aligner.shutdown()


if __name__ == '__main__':
    # 测试分布式对齐
    import asyncio
    
    # 创建测试数据
    source = [
        {'id': f'src_{i}', 'name': f'实体{i}', 'type': 'PERSON'}
        for i in range(100)
    ]
    
    target = [
        {'id': f'tgt_{i}', 'name': f'实体{i}', 'type': 'PERSON'}
        for i in range(100)
    ]
    
    # 执行对齐
    async def test():
        aligner = DistributedEntityAligner(num_workers=4)
        result = await aligner.align_distributed(source, target, threshold=0.5)
        
        print(f"\n对齐结果:")
        print(f"  任务ID: {result.task_id}")
        print(f"  总分片: {result.total_partitions}")
        print(f"  完成分片: {result.completed_partitions}")
        print(f"  对齐对数: {len(result.aligned_pairs)}")
        print(f"  执行时间: {result.execution_time_ms:.0f}ms")
        print(f"\n统计信息:")
        for key, value in result.statistics.items():
            print(f"  {key}: {value}")
        
        aligner.shutdown()
    
    asyncio.run(test())
