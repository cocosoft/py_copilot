"""
性能优化器
实施性能优化方案，提供自动优化功能
"""

import asyncio
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from functools import lru_cache, wraps
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """优化结果"""
    skill_id: str
    optimization_type: str
    success: bool
    improvement: float  # 性能提升百分比
    execution_time_before: float
    execution_time_after: float
    memory_usage_before: float
    memory_usage_after: float
    details: Dict[str, Any]


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, max_threads: int = 10, max_processes: int = 4):
        """初始化性能优化器
        
        Args:
            max_threads: 最大线程数
            max_processes: 最大进程数
        """
        self.max_threads = max_threads
        self.max_processes = max_processes
        
        # 线程池和进程池
        self.thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        self.process_pool = ProcessPoolExecutor(max_workers=max_processes)
        
        # 优化结果记录
        self.optimization_results: Dict[str, List[OptimizationResult]] = {}
        
        # 缓存配置
        self.cache_config = {
            "maxsize": 1000,
            "ttl": 300  # 5分钟
        }
        
        # 批量处理配置
        self.batch_config = {
            "batch_size": 100,
            "max_concurrent_batches": 5
        }
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 性能基准数据
        self.benchmark_data: Dict[str, Dict[str, float]] = {}
    
    def apply_caching_optimization(self, skill_id: str, func: Callable) -> Callable:
        """应用缓存优化
        
        Args:
            skill_id: 技能ID
            func: 需要优化的函数
            
        Returns:
            优化后的函数
        """
        @lru_cache(maxsize=self.cache_config["maxsize"])
        @wraps(func)
        def cached_function(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 记录优化应用
        self._record_optimization(skill_id, "caching", "应用函数缓存优化")
        
        return cached_function
    
    def apply_async_optimization(self, skill_id: str, func: Callable) -> Callable:
        """应用异步优化
        
        Args:
            skill_id: 技能ID
            func: 需要优化的函数
            
        Returns:
            优化后的异步函数
        """
        @wraps(func)
        async def async_function(*args, **kwargs):
            # 在线程池中执行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
        
        # 记录优化应用
        self._record_optimization(skill_id, "async", "应用异步执行优化")
        
        return async_function
    
    def apply_batch_optimization(self, skill_id: str, process_single: Callable) -> Callable:
        """应用批量处理优化
        
        Args:
            skill_id: 技能ID
            process_single: 单条数据处理函数
            
        Returns:
            批量处理函数
        """
        @wraps(process_single)
        def batch_process(items: List[Any]) -> List[Any]:
            """批量处理函数"""
            batch_size = self.batch_config["batch_size"]
            results = []
            
            # 分批处理
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                # 并行处理批次
                with ThreadPoolExecutor(max_workers=self.batch_config["max_concurrent_batches"]) as executor:
                    batch_results = list(executor.map(process_single, batch))
                    results.extend(batch_results)
            
            return results
        
        # 记录优化应用
        self._record_optimization(skill_id, "batch", "应用批量处理优化")
        
        return batch_process
    
    def apply_memory_optimization(self, skill_id: str, data_processor: Callable) -> Callable:
        """应用内存优化
        
        Args:
            skill_id: 技能ID
            data_processor: 数据处理函数
            
        Returns:
            内存优化后的函数
        """
        @wraps(data_processor)
        def memory_optimized_processor(data):
            """内存优化版本"""
            # 使用生成器避免一次性加载所有数据
            if isinstance(data, (list, tuple)) and len(data) > 1000:
                # 流式处理大数据集
                for chunk in self._chunk_data(data, 100):
                    yield from data_processor(chunk)
            else:
                yield from data_processor(data)
        
        # 记录优化应用
        self._record_optimization(skill_id, "memory", "应用内存优化")
        
        return memory_optimized_processor
    
    def apply_algorithm_optimization(self, skill_id: str, original_algorithm: Callable, 
                                   optimized_algorithm: Callable) -> Callable:
        """应用算法优化
        
        Args:
            skill_id: 技能ID
            original_algorithm: 原始算法
            optimized_algorithm: 优化后的算法
            
        Returns:
            优化后的算法函数
        """
        @wraps(original_algorithm)
        def optimized_function(*args, **kwargs):
            # 验证优化算法的正确性
            try:
                result = optimized_algorithm(*args, **kwargs)
                
                # 验证结果一致性（可选）
                if self._validate_algorithm_optimization(original_algorithm, optimized_algorithm, *args, **kwargs):
                    return result
                else:
                    logger.warning(f"算法优化验证失败，使用原始算法: {skill_id}")
                    return original_algorithm(*args, **kwargs)
                    
            except Exception as e:
                logger.error(f"优化算法执行失败: {e}")
                return original_algorithm(*args, **kwargs)
        
        # 记录优化应用
        self._record_optimization(skill_id, "algorithm", "应用算法优化")
        
        return optimized_function
    
    def _validate_algorithm_optimization(self, original: Callable, optimized: Callable, 
                                       *args, **kwargs) -> bool:
        """验证算法优化结果一致性"""
        try:
            # 对小规模数据进行验证
            original_result = original(*args, **kwargs)
            optimized_result = optimized(*args, **kwargs)
            
            # 简单的结果比较（可根据具体需求调整）
            return original_result == optimized_result
            
        except Exception as e:
            logger.warning(f"算法验证失败: {e}")
            return False
    
    def _chunk_data(self, data: List[Any], chunk_size: int):
        """数据分块"""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
    
    def _record_optimization(self, skill_id: str, optimization_type: str, description: str):
        """记录优化应用"""
        logger.info(f"应用优化: {skill_id} - {optimization_type} - {description}")
    
    async def benchmark_optimization(self, skill_id: str, original_func: Callable, 
                                   optimized_func: Callable, test_data: Any, 
                                   iterations: int = 10) -> OptimizationResult:
        """基准测试优化效果
        
        Args:
            skill_id: 技能ID
            original_func: 原始函数
            optimized_func: 优化后的函数
            test_data: 测试数据
            iterations: 测试迭代次数
            
        Returns:
            优化结果
        """
        # 测试原始函数性能
        original_times = []
        original_memory = []
        
        for _ in range(iterations):
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            if asyncio.iscoroutinefunction(original_func):
                await original_func(test_data)
            else:
                original_func(test_data)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            original_times.append(end_time - start_time)
            original_memory.append(end_memory - start_memory)
        
        # 测试优化后函数性能
        optimized_times = []
        optimized_memory = []
        
        for _ in range(iterations):
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            if asyncio.iscoroutinefunction(optimized_func):
                await optimized_func(test_data)
            else:
                optimized_func(test_data)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            optimized_times.append(end_time - start_time)
            optimized_memory.append(end_memory - start_memory)
        
        # 计算性能提升
        avg_original_time = sum(original_times) / len(original_times)
        avg_optimized_time = sum(optimized_times) / len(optimized_times)
        
        avg_original_memory = sum(original_memory) / len(original_memory)
        avg_optimized_memory = sum(optimized_memory) / len(optimized_memory)
        
        time_improvement = ((avg_original_time - avg_optimized_time) / avg_original_time) * 100
        memory_improvement = ((avg_original_memory - avg_optimized_memory) / avg_original_memory) * 100
        
        # 创建优化结果
        result = OptimizationResult(
            skill_id=skill_id,
            optimization_type="benchmark",
            success=time_improvement > 0 or memory_improvement > 0,
            improvement=max(time_improvement, memory_improvement),
            execution_time_before=avg_original_time,
            execution_time_after=avg_optimized_time,
            memory_usage_before=avg_original_memory,
            memory_usage_after=avg_optimized_memory,
            details={
                "iterations": iterations,
                "time_improvement": time_improvement,
                "memory_improvement": memory_improvement,
                "original_times": original_times,
                "optimized_times": optimized_times
            }
        )
        
        # 保存基准数据
        self._save_benchmark_data(skill_id, "original", avg_original_time, avg_original_memory)
        self._save_benchmark_data(skill_id, "optimized", avg_optimized_time, avg_optimized_memory)
        
        # 记录优化结果
        self._save_optimization_result(skill_id, result)
        
        logger.info(f"基准测试完成: {skill_id}, 时间提升: {time_improvement:.1f}%, "
                   f"内存提升: {memory_improvement:.1f}%")
        
        return result
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _save_benchmark_data(self, skill_id: str, version: str, execution_time: float, memory_usage: float):
        """保存基准数据"""
        with self._lock:
            if skill_id not in self.benchmark_data:
                self.benchmark_data[skill_id] = {}
            
            self.benchmark_data[skill_id][f"{version}_time"] = execution_time
            self.benchmark_data[skill_id][f"{version}_memory"] = memory_usage
    
    def _save_optimization_result(self, skill_id: str, result: OptimizationResult):
        """保存优化结果"""
        with self._lock:
            if skill_id not in self.optimization_results:
                self.optimization_results[skill_id] = []
            
            self.optimization_results[skill_id].append(result)
    
    def get_optimization_history(self, skill_id: str) -> List[OptimizationResult]:
        """获取优化历史"""
        return self.optimization_results.get(skill_id, [])
    
    def get_benchmark_data(self, skill_id: str) -> Dict[str, float]:
        """获取基准数据"""
        return self.benchmark_data.get(skill_id, {})
    
    def create_optimization_report(self, skill_id: str) -> Dict[str, Any]:
        """创建优化报告"""
        optimization_history = self.get_optimization_history(skill_id)
        benchmark_data = self.get_benchmark_data(skill_id)
        
        if not optimization_history:
            return {"error": "无优化历史数据"}
        
        # 计算总体优化效果
        total_improvement = sum(result.improvement for result in optimization_history) / len(optimization_history)
        
        # 分析优化类型分布
        optimization_types = {}
        for result in optimization_history:
            opt_type = result.optimization_type
            optimization_types[opt_type] = optimization_types.get(opt_type, 0) + 1
        
        # 生成优化建议
        recommendations = self._generate_recommendations(optimization_history, benchmark_data)
        
        return {
            "skill_id": skill_id,
            "total_improvement": total_improvement,
            "optimization_count": len(optimization_history),
            "optimization_types": optimization_types,
            "benchmark_data": benchmark_data,
            "recommendations": recommendations,
            "successful_optimizations": [r for r in optimization_history if r.success],
            "failed_optimizations": [r for r in optimization_history if not r.success]
        }
    
    def _generate_recommendations(self, optimization_history: List[OptimizationResult], 
                                benchmark_data: Dict[str, float]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        
        # 分析优化效果
        successful_optimizations = [r for r in optimization_history if r.success]
        
        if not successful_optimizations:
            recommendations.append({
                "type": "general",
                "priority": "high",
                "message": "尚未实施有效的性能优化",
                "suggestion": "建议先进行性能分析，识别主要瓶颈"
            })
            return recommendations
        
        # 分析优化类型效果
        type_effectiveness = {}
        for result in successful_optimizations:
            opt_type = result.optimization_type
            if opt_type not in type_effectiveness:
                type_effectiveness[opt_type] = []
            type_effectiveness[opt_type].append(result.improvement)
        
        # 生成基于效果的推荐
        for opt_type, improvements in type_effectiveness.items():
            avg_improvement = sum(improvements) / len(improvements)
            
            if avg_improvement > 50:
                recommendations.append({
                    "type": opt_type,
                    "priority": "high",
                    "message": f"{opt_type}优化效果显著（平均提升{avg_improvement:.1f}%）",
                    "suggestion": "建议在其他类似场景中推广应用"
                })
            elif avg_improvement > 20:
                recommendations.append({
                    "type": opt_type,
                    "priority": "medium",
                    "message": f"{opt_type}优化效果良好（平均提升{avg_improvement:.1f}%）",
                    "suggestion": "可以考虑进一步优化"
                })
            else:
                recommendations.append({
                    "type": opt_type,
                    "priority": "low",
                    "message": f"{opt_type}优化效果有限（平均提升{avg_improvement:.1f}%）",
                    "suggestion": "可能需要尝试其他优化策略"
                })
        
        return recommendations
    
    def cleanup(self):
        """清理资源"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("性能优化器资源已清理")


# 创建全局性能优化器实例
performance_optimizer = PerformanceOptimizer()