"""
性能集成系统
整合性能监控、分析和优化功能
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import uuid

from .skill_performance_monitor import skill_performance_monitor, ExecutionMetrics
from .performance_analyzer import performance_analyzer, BottleneckAnalysis
from .performance_optimizer import performance_optimizer, OptimizationResult

logger = logging.getLogger(__name__)


@dataclass
class PerformanceIntegrationResult:
    """性能集成结果"""
    execution_id: str
    skill_id: str
    success: bool
    execution_time: float
    bottlenecks: List[BottleneckAnalysis]
    optimizations_applied: List[Dict[str, Any]]
    improvement: float
    recommendations: List[Dict[str, Any]]


class PerformanceIntegrationSystem:
    """性能集成系统"""
    
    def __init__(self):
        """初始化性能集成系统"""
        self.integration_results: Dict[str, PerformanceIntegrationResult] = {}
        
        # 自动优化配置
        self.auto_optimization_config = {
            "enabled": True,
            "min_improvement_threshold": 10.0,  # 最小改进阈值（%）
            "max_optimizations_per_skill": 5,   # 每个技能最大优化次数
        }
        
        # 性能事件处理器
        self.performance_event_handlers: List[Callable] = []
    
    async def execute_with_performance_integration(self, skill_id: str, 
                                                 skill_executor: Callable,
                                                 input_data: Dict[str, Any]) -> PerformanceIntegrationResult:
        """执行技能并集成性能监控、分析和优化
        
        Args:
            skill_id: 技能ID
            skill_executor: 技能执行函数
            input_data: 输入数据
            
        Returns:
            性能集成结果
        """
        execution_id = str(uuid.uuid4())
        
        logger.info(f"开始性能集成执行: {skill_id} - {execution_id}")
        
        # 1. 开始性能监控
        metrics = skill_performance_monitor.start_monitoring_execution(
            skill_id, execution_id, input_data
        )
        
        # 2. 执行技能
        start_time = time.time()
        
        try:
            # 应用自动优化（如果启用）
            optimized_executor = self._apply_auto_optimizations(skill_id, skill_executor)
            
            # 执行技能
            result = await optimized_executor(input_data)
            
            execution_time = time.time() - start_time
            success = True
            error = None
            
        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error = str(e)
            result = None
            logger.error(f"技能执行失败: {skill_id}, 错误: {e}")
        
        # 3. 结束性能监控
        skill_performance_monitor.end_monitoring_execution(
            metrics, success, error, result
        )
        
        # 4. 性能分析
        execution_metrics = {
            "execution_time": execution_time,
            "cpu_usage_percent": metrics.cpu_usage_percent,
            "memory_usage_mb": metrics.memory_usage_mb,
            "input_size": metrics.input_size,
            "output_size": metrics.output_size if result else 0
        }
        
        bottlenecks = performance_analyzer.analyze_execution_performance(
            skill_id, execution_id, execution_metrics
        )
        
        # 5. 生成优化建议
        recommendations = self._generate_optimization_recommendations(skill_id, bottlenecks)
        
        # 6. 计算性能改进
        improvement = self._calculate_performance_improvement(skill_id, execution_time)
        
        # 7. 创建集成结果
        integration_result = PerformanceIntegrationResult(
            execution_id=execution_id,
            skill_id=skill_id,
            success=success,
            execution_time=execution_time,
            bottlenecks=bottlenecks,
            optimizations_applied=self._get_applied_optimizations(skill_id),
            improvement=improvement,
            recommendations=recommendations
        )
        
        # 8. 保存结果
        self.integration_results[execution_id] = integration_result
        
        # 9. 触发性能事件
        self._trigger_performance_events(integration_result)
        
        logger.info(f"性能集成执行完成: {skill_id} - {execution_id}, "
                   f"时间: {execution_time:.3f}s, 改进: {improvement:.1f}%")
        
        return integration_result
    
    def _apply_auto_optimizations(self, skill_id: str, skill_executor: Callable) -> Callable:
        """应用自动优化"""
        if not self.auto_optimization_config["enabled"]:
            return skill_executor
        
        # 检查优化次数限制
        optimization_history = performance_optimizer.get_optimization_history(skill_id)
        if len(optimization_history) >= self.auto_optimization_config["max_optimizations_per_skill"]:
            return skill_executor
        
        # 根据技能特性应用优化
        optimized_executor = skill_executor
        
        # 应用缓存优化（适用于纯函数）
        if self._is_pure_function(skill_executor):
            optimized_executor = performance_optimizer.apply_caching_optimization(
                skill_id, optimized_executor
            )
        
        # 应用异步优化（适用于IO密集型任务）
        if self._is_io_intensive(skill_executor):
            optimized_executor = performance_optimizer.apply_async_optimization(
                skill_id, optimized_executor
            )
        
        return optimized_executor
    
    def _is_pure_function(self, func: Callable) -> bool:
        """判断是否为纯函数"""
        # 简化判断：检查函数是否有副作用
        # 实际项目中需要更复杂的分析
        try:
            # 检查函数签名和文档
            func_name = func.__name__.lower()
            pure_keywords = ['calculate', 'compute', 'get', 'generate']
            
            return any(keyword in func_name for keyword in pure_keywords)
        except:
            return False
    
    def _is_io_intensive(self, func: Callable) -> bool:
        """判断是否为IO密集型函数"""
        # 简化判断：基于函数名和文档
        try:
            func_name = func.__name__.lower()
            io_keywords = ['read', 'write', 'load', 'save', 'fetch', 'download']
            
            return any(keyword in func_name for keyword in io_keywords)
        except:
            return False
    
    def _generate_optimization_recommendations(self, skill_id: str, 
                                             bottlenecks: List[BottleneckAnalysis]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        
        # 从性能分析器获取建议
        analyzer_suggestions = performance_analyzer.get_optimization_suggestions(skill_id)
        
        for suggestion in analyzer_suggestions:
            recommendations.append({
                "source": "analyzer",
                "title": suggestion.title,
                "description": suggestion.description,
                "expected_improvement": suggestion.expected_improvement,
                "priority": suggestion.priority
            })
        
        # 基于瓶颈分析生成建议
        for bottleneck in bottlenecks:
            if bottleneck.severity in ["high", "critical"]:
                recommendations.append({
                    "source": "bottleneck_analysis",
                    "title": f"解决{bottleneck.bottleneck_type.value}瓶颈",
                    "description": bottleneck.description,
                    "expected_improvement": "20-60%",
                    "priority": "high" if bottleneck.severity == "critical" else "medium"
                })
        
        return recommendations
    
    def _calculate_performance_improvement(self, skill_id: str, current_time: float) -> float:
        """计算性能改进"""
        # 获取基准数据
        benchmark_data = performance_optimizer.get_benchmark_data(skill_id)
        
        if "original_time" in benchmark_data and benchmark_data["original_time"] > 0:
            original_time = benchmark_data["original_time"]
            improvement = ((original_time - current_time) / original_time) * 100
            return max(improvement, 0)  # 确保非负
        
        return 0.0
    
    def _get_applied_optimizations(self, skill_id: str) -> List[Dict[str, Any]]:
        """获取已应用的优化"""
        optimization_history = performance_optimizer.get_optimization_history(skill_id)
        
        applied_optimizations = []
        for optimization in optimization_history:
            applied_optimizations.append({
                "type": optimization.optimization_type,
                "improvement": optimization.improvement,
                "success": optimization.success
            })
        
        return applied_optimizations
    
    def _trigger_performance_events(self, result: PerformanceIntegrationResult):
        """触发性能事件"""
        event_data = {
            "execution_id": result.execution_id,
            "skill_id": result.skill_id,
            "timestamp": time.time(),
            "execution_time": result.execution_time,
            "improvement": result.improvement,
            "bottlenecks_count": len(result.bottlenecks),
            "recommendations_count": len(result.recommendations)
        }
        
        for handler in self.performance_event_handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"性能事件处理失败: {e}")
    
    async def benchmark_skill_performance(self, skill_id: str, skill_executor: Callable,
                                        test_data: Any, iterations: int = 10) -> Dict[str, Any]:
        """基准测试技能性能
        
        Args:
            skill_id: 技能ID
            skill_executor: 技能执行函数
            test_data: 测试数据
            iterations: 测试迭代次数
            
        Returns:
            基准测试结果
        """
        logger.info(f"开始技能性能基准测试: {skill_id}")
        
        # 测试原始性能
        original_times = []
        
        for i in range(iterations):
            result = await self.execute_with_performance_integration(
                skill_id, skill_executor, test_data
            )
            original_times.append(result.execution_time)
        
        avg_original_time = sum(original_times) / len(original_times)
        
        # 测试优化后性能（应用所有优化）
        optimized_executor = self._apply_all_optimizations(skill_id, skill_executor)
        
        optimized_times = []
        
        for i in range(iterations):
            result = await self.execute_with_performance_integration(
                skill_id, optimized_executor, test_data
            )
            optimized_times.append(result.execution_time)
        
        avg_optimized_time = sum(optimized_times) / len(optimized_times)
        
        # 计算性能提升
        improvement = ((avg_original_time - avg_optimized_time) / avg_original_time) * 100
        
        benchmark_result = {
            "skill_id": skill_id,
            "iterations": iterations,
            "original_performance": {
                "avg_time": avg_original_time,
                "min_time": min(original_times),
                "max_time": max(original_times)
            },
            "optimized_performance": {
                "avg_time": avg_optimized_time,
                "min_time": min(optimized_times),
                "max_time": max(optimized_times)
            },
            "improvement": improvement,
            "improvement_achieved": improvement >= 30.0  # 验收标准
        }
        
        logger.info(f"技能性能基准测试完成: {skill_id}, 改进: {improvement:.1f}%")
        
        return benchmark_result
    
    def _apply_all_optimizations(self, skill_id: str, skill_executor: Callable) -> Callable:
        """应用所有优化"""
        optimized_executor = skill_executor
        
        # 应用缓存优化
        optimized_executor = performance_optimizer.apply_caching_optimization(
            skill_id, optimized_executor
        )
        
        # 应用异步优化
        optimized_executor = performance_optimizer.apply_async_optimization(
            skill_id, optimized_executor
        )
        
        return optimized_executor
    
    def get_integration_result(self, execution_id: str) -> Optional[PerformanceIntegrationResult]:
        """获取集成结果"""
        return self.integration_results.get(execution_id)
    
    def get_performance_report(self, skill_id: str) -> Dict[str, Any]:
        """获取性能报告"""
        # 获取性能统计数据
        performance_stats = skill_performance_monitor.get_performance_stats(skill_id)
        
        # 获取优化报告
        optimization_report = performance_optimizer.create_optimization_report(skill_id)
        
        # 获取分析历史
        analysis_history = performance_analyzer.get_analysis_history(skill_id)
        
        return {
            "skill_id": skill_id,
            "performance_stats": performance_stats.__dict__ if performance_stats else {},
            "optimization_report": optimization_report,
            "analysis_history": [analysis.__dict__ for analysis in analysis_history],
            "integration_results_count": len([r for r in self.integration_results.values() 
                                             if r.skill_id == skill_id])
        }
    
    def add_performance_event_handler(self, handler: Callable):
        """添加性能事件处理器"""
        self.performance_event_handlers.append(handler)
    
    def set_auto_optimization_config(self, config: Dict[str, Any]):
        """设置自动优化配置"""
        self.auto_optimization_config.update(config)
        logger.info(f"自动优化配置已更新: {config}")


# 创建全局性能集成系统实例
performance_integration_system = PerformanceIntegrationSystem()