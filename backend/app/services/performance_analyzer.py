"""
性能瓶颈分析器
分析技能执行性能瓶颈，提供优化建议
"""

import time
import cProfile
import pstats
import io
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import tracemalloc
import line_profiler

logger = logging.getLogger(__name__)


class BottleneckType(Enum):
    """瓶颈类型枚举"""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    NETWORK_BOUND = "network_bound"
    DATABASE_BOUND = "database_bound"
    LOCK_CONTENTION = "lock_contention"
    ALGORITHMIC = "algorithmic"


@dataclass
class BottleneckAnalysis:
    """瓶颈分析结果"""
    skill_id: str
    execution_id: str
    bottleneck_type: BottleneckType
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0 - 1.0
    description: str
    location: str  # 函数/模块位置
    impact: str  # 对性能的影响描述
    suggestions: List[str]
    metrics: Dict[str, Any]


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    title: str
    description: str
    expected_improvement: str  # 预期改进程度
    implementation_difficulty: str  # low, medium, high
    priority: str  # low, medium, high, critical
    code_examples: List[str]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        """初始化性能分析器"""
        self.analysis_history: Dict[str, List[BottleneckAnalysis]] = {}
        self.optimization_suggestions: Dict[str, List[OptimizationSuggestion]] = {}
        
        # 分析配置
        self.analysis_config = {
            "cpu_threshold": 80.0,  # CPU使用率阈值
            "memory_threshold": 500.0,  # 内存使用阈值(MB)
            "execution_time_threshold": 5.0,  # 执行时间阈值(秒)
            "io_wait_threshold": 0.5,  # IO等待时间阈值(秒)
            "network_latency_threshold": 1.0,  # 网络延迟阈值(秒)
        }
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 性能分析器状态
        self.profiling_enabled = False
        self.memory_profiling_enabled = False
    
    def analyze_execution_performance(self, skill_id: str, execution_id: str,
                                    execution_metrics: Dict[str, Any]) -> List[BottleneckAnalysis]:
        """分析执行性能
        
        Args:
            skill_id: 技能ID
            execution_id: 执行ID
            execution_metrics: 执行指标
            
        Returns:
            瓶颈分析结果列表
        """
        analyses = []
        
        # 分析CPU瓶颈
        cpu_analysis = self._analyze_cpu_bottleneck(skill_id, execution_id, execution_metrics)
        if cpu_analysis:
            analyses.append(cpu_analysis)
        
        # 分析内存瓶颈
        memory_analysis = self._analyze_memory_bottleneck(skill_id, execution_id, execution_metrics)
        if memory_analysis:
            analyses.append(memory_analysis)
        
        # 分析IO瓶颈
        io_analysis = self._analyze_io_bottleneck(skill_id, execution_id, execution_metrics)
        if io_analysis:
            analyses.append(io_analysis)
        
        # 分析网络瓶颈
        network_analysis = self._analyze_network_bottleneck(skill_id, execution_id, execution_metrics)
        if network_analysis:
            analyses.append(network_analysis)
        
        # 分析算法瓶颈
        algorithmic_analysis = self._analyze_algorithmic_bottleneck(skill_id, execution_id, execution_metrics)
        if algorithmic_analysis:
            analyses.append(algorithmic_analysis)
        
        # 保存分析结果
        self._save_analysis_results(skill_id, analyses)
        
        # 生成优化建议
        self._generate_optimization_suggestions(skill_id, analyses)
        
        logger.info(f"性能分析完成: {skill_id}, 发现 {len(analyses)} 个瓶颈")
        
        return analyses
    
    def _analyze_cpu_bottleneck(self, skill_id: str, execution_id: str,
                              metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """分析CPU瓶颈"""
        cpu_usage = metrics.get("cpu_usage_percent", 0.0)
        execution_time = metrics.get("execution_time", 0.0)
        
        if cpu_usage > self.analysis_config["cpu_threshold"] and execution_time > 1.0:
            severity = self._calculate_severity(cpu_usage, self.analysis_config["cpu_threshold"])
            confidence = min(cpu_usage / 100, 0.95)  # 置信度基于CPU使用率
            
            return BottleneckAnalysis(
                skill_id=skill_id,
                execution_id=execution_id,
                bottleneck_type=BottleneckType.CPU_BOUND,
                severity=severity,
                confidence=confidence,
                description=f"CPU使用率过高: {cpu_usage:.1f}%",
                location="技能执行主循环",
                impact=f"导致执行时间延长 {execution_time:.2f}秒",
                suggestions=[
                    "优化算法复杂度，减少计算量",
                    "使用缓存避免重复计算",
                    "考虑使用异步处理",
                    "优化数据结构和算法"
                ],
                metrics={
                    "cpu_usage": cpu_usage,
                    "execution_time": execution_time,
                    "threshold": self.analysis_config["cpu_threshold"]
                }
            )
        
        return None
    
    def _analyze_memory_bottleneck(self, skill_id: str, execution_id: str,
                                 metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """分析内存瓶颈"""
        memory_usage = metrics.get("memory_usage_mb", 0.0)
        
        if memory_usage > self.analysis_config["memory_threshold"]:
            severity = self._calculate_severity(memory_usage, self.analysis_config["memory_threshold"])
            confidence = min(memory_usage / 1000, 0.95)  # 置信度基于内存使用量
            
            return BottleneckAnalysis(
                skill_id=skill_id,
                execution_id=execution_id,
                bottleneck_type=BottleneckType.MEMORY_BOUND,
                severity=severity,
                confidence=confidence,
                description=f"内存使用过高: {memory_usage:.1f}MB",
                location="数据加载和处理",
                impact="可能导致内存不足和性能下降",
                suggestions=[
                    "使用流式处理替代批量加载",
                    "及时释放不再使用的对象",
                    "使用更高效的数据结构",
                    "考虑数据分片处理"
                ],
                metrics={
                    "memory_usage": memory_usage,
                    "threshold": self.analysis_config["memory_threshold"]
                }
            )
        
        return None
    
    def _analyze_io_bottleneck(self, skill_id: str, execution_id: str,
                             metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """分析IO瓶颈"""
        # 这里需要实际的IO等待时间数据
        # 暂时使用执行时间作为代理指标
        execution_time = metrics.get("execution_time", 0.0)
        
        # 假设IO密集型任务执行时间较长但CPU使用率较低
        cpu_usage = metrics.get("cpu_usage_percent", 0.0)
        
        if execution_time > self.analysis_config["execution_time_threshold"] and cpu_usage < 30.0:
            severity = self._calculate_severity(execution_time, self.analysis_config["execution_time_threshold"])
            confidence = 0.7  # 中等置信度
            
            return BottleneckAnalysis(
                skill_id=skill_id,
                execution_id=execution_id,
                bottleneck_type=BottleneckType.IO_BOUND,
                severity=severity,
                confidence=confidence,
                description=f"疑似IO瓶颈，执行时间: {execution_time:.2f}秒",
                location="文件读写或数据库操作",
                impact="执行时间主要消耗在等待IO操作上",
                suggestions=[
                    "使用异步IO操作",
                    "批量处理文件读写",
                    "使用缓存减少IO次数",
                    "优化数据库查询"
                ],
                metrics={
                    "execution_time": execution_time,
                    "cpu_usage": cpu_usage,
                    "threshold": self.analysis_config["execution_time_threshold"]
                }
            )
        
        return None
    
    def _analyze_network_bottleneck(self, skill_id: str, execution_id: str,
                                  metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """分析网络瓶颈"""
        # 这里需要实际的网络延迟数据
        # 暂时使用执行时间作为代理指标
        execution_time = metrics.get("execution_time", 0.0)
        
        # 假设网络请求密集型任务
        if execution_time > self.analysis_config["network_latency_threshold"]:
            severity = self._calculate_severity(execution_time, self.analysis_config["network_latency_threshold"])
            confidence = 0.6  # 较低置信度，需要更多数据
            
            return BottleneckAnalysis(
                skill_id=skill_id,
                execution_id=execution_id,
                bottleneck_type=BottleneckType.NETWORK_BOUND,
                severity=severity,
                confidence=confidence,
                description=f"疑似网络瓶颈，执行时间: {execution_time:.2f}秒",
                location="网络请求处理",
                impact="执行时间主要消耗在网络等待上",
                suggestions=[
                    "使用连接池复用连接",
                    "批量发送网络请求",
                    "使用异步网络操作",
                    "增加超时和重试机制"
                ],
                metrics={
                    "execution_time": execution_time,
                    "threshold": self.analysis_config["network_latency_threshold"]
                }
            )
        
        return None
    
    def _analyze_algorithmic_bottleneck(self, skill_id: str, execution_id: str,
                                      metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """分析算法瓶颈"""
        execution_time = metrics.get("execution_time", 0.0)
        input_size = metrics.get("input_size", 0)
        
        # 检测算法复杂度问题
        # 如果输入数据量不大但执行时间很长，可能是算法效率问题
        if input_size < 1000 and execution_time > 2.0:
            severity = "high"
            confidence = 0.8
            
            return BottleneckAnalysis(
                skill_id=skill_id,
                execution_id=execution_id,
                bottleneck_type=BottleneckType.ALGORITHMIC,
                severity=severity,
                confidence=confidence,
                description=f"疑似算法瓶颈，小数据量长时间执行",
                location="核心算法实现",
                impact="算法效率低下，需要优化",
                suggestions=[
                    "分析算法时间复杂度",
                    "使用更高效的算法",
                    "优化循环和递归",
                    "使用内置高效函数"
                ],
                metrics={
                    "execution_time": execution_time,
                    "input_size": input_size
                }
            )
        
        return None
    
    def _calculate_severity(self, actual_value: float, threshold: float) -> str:
        """计算严重程度"""
        ratio = actual_value / threshold
        
        if ratio > 3.0:
            return "critical"
        elif ratio > 2.0:
            return "high"
        elif ratio > 1.5:
            return "medium"
        else:
            return "low"
    
    def _save_analysis_results(self, skill_id: str, analyses: List[BottleneckAnalysis]):
        """保存分析结果"""
        with self._lock:
            if skill_id not in self.analysis_history:
                self.analysis_history[skill_id] = []
            
            self.analysis_history[skill_id].extend(analyses)
            
            # 限制历史记录大小
            if len(self.analysis_history[skill_id]) > 100:
                self.analysis_history[skill_id] = self.analysis_history[skill_id][-50:]
    
    def _generate_optimization_suggestions(self, skill_id: str, analyses: List[BottleneckAnalysis]):
        """生成优化建议"""
        suggestions = []
        
        for analysis in analyses:
            if analysis.bottleneck_type == BottleneckType.CPU_BOUND:
                suggestions.extend(self._generate_cpu_optimizations(analysis))
            elif analysis.bottleneck_type == BottleneckType.MEMORY_BOUND:
                suggestions.extend(self._generate_memory_optimizations(analysis))
            elif analysis.bottleneck_type == BottleneckType.IO_BOUND:
                suggestions.extend(self._generate_io_optimizations(analysis))
            elif analysis.bottleneck_type == BottleneckType.NETWORK_BOUND:
                suggestions.extend(self._generate_network_optimizations(analysis))
            elif analysis.bottleneck_type == BottleneckType.ALGORITHMIC:
                suggestions.extend(self._generate_algorithmic_optimizations(analysis))
        
        with self._lock:
            if skill_id not in self.optimization_suggestions:
                self.optimization_suggestions[skill_id] = []
            
            self.optimization_suggestions[skill_id].extend(suggestions)
    
    def _generate_cpu_optimizations(self, analysis: BottleneckAnalysis) -> List[OptimizationSuggestion]:
        """生成CPU优化建议"""
        return [
            OptimizationSuggestion(
                title="算法复杂度优化",
                description="分析并优化核心算法的时间复杂度",
                expected_improvement="30-70%",
                implementation_difficulty="medium",
                priority="high",
                code_examples=[
                    "# 优化前: O(n²)复杂度\nfor i in range(n):\n    for j in range(n):\n        process(i, j)",
                    "# 优化后: O(n)复杂度\nfor i in range(n):\n    process_optimized(i)"
                ]
            ),
            OptimizationSuggestion(
                title="使用缓存",
                description="缓存计算结果避免重复计算",
                expected_improvement="50-90%",
                implementation_difficulty="low",
                priority="medium",
                code_examples=[
                    "from functools import lru_cache\n\n@lru_cache(maxsize=1000)\ndef expensive_calculation(x):\n    return x * x"
                ]
            )
        ]
    
    def _generate_memory_optimizations(self, analysis: BottleneckAnalysis) -> List[OptimizationSuggestion]:
        """生成内存优化建议"""
        return [
            OptimizationSuggestion(
                title="流式处理",
                description="使用流式处理替代批量加载",
                expected_improvement="60-80%内存减少",
                implementation_difficulty="medium",
                priority="high",
                code_examples=[
                    "# 优化前: 批量加载\ndata = load_all_data()\nprocess(data)",
                    "# 优化后: 流式处理\nfor chunk in stream_data():\n    process_chunk(chunk)"
                ]
            ),
            OptimizationSuggestion(
                title="及时释放内存",
                description="及时释放不再使用的大对象",
                expected_improvement="20-40%内存减少",
                implementation_difficulty="low",
                priority="medium",
                code_examples=[
                    "# 及时释放大对象\nlarge_data = load_large_data()\nresult = process(large_data)\ndel large_data  # 及时释放"
                ]
            )
        ]
    
    def _generate_io_optimizations(self, analysis: BottleneckAnalysis) -> List[OptimizationSuggestion]:
        """生成IO优化建议"""
        return [
            OptimizationSuggestion(
                title="异步IO操作",
                description="使用异步IO避免阻塞",
                expected_improvement="50-80%",
                implementation_difficulty="medium",
                priority="high",
                code_examples=[
                    "import asyncio\nimport aiofiles\n\nasync def read_file_async(path):\n    async with aiofiles.open(path, 'r') as f:\n        return await f.read()"
                ]
            ),
            OptimizationSuggestion(
                title="批量处理",
                description="批量处理文件读写操作",
                expected_improvement="30-60%",
                implementation_difficulty="low",
                priority="medium",
                code_examples=[
                    "# 优化前: 单次处理\nfor file in files:\n    data = read_file(file)\n    process(data)",
                    "# 优化后: 批量处理\nbatch_data = [read_file(file) for file in files]\nprocess_batch(batch_data)"
                ]
            )
        ]
    
    def _generate_network_optimizations(self, analysis: BottleneckAnalysis) -> List[OptimizationSuggestion]:
        """生成网络优化建议"""
        return [
            OptimizationSuggestion(
                title="连接池",
                description="使用连接池复用网络连接",
                expected_improvement="40-70%",
                implementation_difficulty="medium",
                priority="high",
                code_examples=[
                    "import requests\nfrom requests.adapters import HTTPAdapter\n\nsession = requests.Session()\nadapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)\nsession.mount('http://', adapter)"
                ]
            ),
            OptimizationSuggestion(
                title="异步网络请求",
                description="使用异步方式发送网络请求",
                expected_improvement="60-90%",
                implementation_difficulty="high",
                priority="high",
                code_examples=[
                    "import aiohttp\nimport asyncio\n\nasync def fetch_urls(urls):\n    async with aiohttp.ClientSession() as session:\n        tasks = [session.get(url) for url in urls]\n        return await asyncio.gather(*tasks)"
                ]
            )
        ]
    
    def _generate_algorithmic_optimizations(self, analysis: BottleneckAnalysis) -> List[OptimizationSuggestion]:
        """生成算法优化建议"""
        return [
            OptimizationSuggestion(
                title="算法分析",
                description="分析算法时间复杂度并优化",
                expected_improvement="50-90%",
                implementation_difficulty="high",
                priority="critical",
                code_examples=[
                    "# 优化前: O(n²)\nfor i in range(n):\n    for j in range(n):\n        if condition(i, j):\n            result.append((i, j))",
                    "# 优化后: O(n)\nfor i in range(n):\n    if optimized_condition(i):\n        result.append(i)"
                ]
            )
        ]
    
    def profile_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """性能分析函数"""
        if not self.profiling_enabled:
            return {"error": "性能分析未启用"}
        
        # 使用cProfile进行性能分析
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
        
        # 分析性能数据
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # 显示前10个最耗时的函数
        
        profile_output = s.getvalue()
        
        return {
            "result": result,
            "profile_output": profile_output,
            "success": True
        }
    
    def memory_profile_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """内存分析函数"""
        if not self.memory_profiling_enabled:
            return {"error": "内存分析未启用"}
        
        # 使用tracemalloc进行内存分析
        tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
            
            # 获取内存快照
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            memory_info = []
            for stat in top_stats[:10]:  # 显示前10个内存使用最多的位置
                memory_info.append({
                    "file": stat.traceback[0].filename,
                    "line": stat.traceback[0].lineno,
                    "size": stat.size,
                    "count": stat.count
                })
            
            return {
                "result": result,
                "memory_info": memory_info,
                "success": True
            }
            
        finally:
            tracemalloc.stop()
    
    def get_analysis_history(self, skill_id: str) -> List[BottleneckAnalysis]:
        """获取分析历史"""
        return self.analysis_history.get(skill_id, [])
    
    def get_optimization_suggestions(self, skill_id: str) -> List[OptimizationSuggestion]:
        """获取优化建议"""
        return self.optimization_suggestions.get(skill_id, [])
    
    def enable_profiling(self):
        """启用性能分析"""
        self.profiling_enabled = True
        logger.info("性能分析已启用")
    
    def disable_profiling(self):
        """禁用性能分析"""
        self.profiling_enabled = False
        logger.info("性能分析已禁用")
    
    def enable_memory_profiling(self):
        """启用内存分析"""
        self.memory_profiling_enabled = True
        logger.info("内存分析已启用")
    
    def disable_memory_profiling(self):
        """禁用内存分析"""
        self.memory_profiling_enabled = False
        logger.info("内存分析已禁用")


# 创建全局性能分析器实例
performance_analyzer = PerformanceAnalyzer()