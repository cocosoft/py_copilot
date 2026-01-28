"""
响应性能优化器
提升多模态响应的性能和效率
"""

import asyncio
import time
import gzip
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

from app.schemas.multimodal_response import (
    MultimodalResponse, MediaContent, PerformanceMetrics,
    ResponseOptimizationResult
)


class OptimizationTechnique(Enum):
    """优化技术枚举"""
    COMPRESSION = "compression"
    CACHING = "caching"
    STREAMING = "streaming"
    LAZY_LOADING = "lazy_loading"
    PRIORITIZATION = "prioritization"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""
    max_response_time_ms: int = 3000
    max_memory_usage_mb: int = 100
    max_network_usage_kb: int = 500
    acceptable_cache_hit_rate: float = 0.8


class ResponsePerformanceOptimizer:
    """响应性能优化器"""
    
    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.optimization_cache: Dict[str, Tuple[MultimodalResponse, float]] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.technique_success_rates: Dict[str, List[bool]] = {}
    
    async def optimize_response_performance(self, 
                                          response: MultimodalResponse,
                                          enable_techniques: List[OptimizationTechnique] = None) -> ResponseOptimizationResult:
        """优化响应性能"""
        start_time = time.time()
        original_size = self._calculate_response_size(response)
        
        if enable_techniques is None:
            enable_techniques = list(OptimizationTechnique)
        
        optimized_response = response
        applied_techniques = []
        
        # 应用优化技术
        for technique in enable_techniques:
            try:
                if technique == OptimizationTechnique.COMPRESSION:
                    optimized_response = await self._apply_compression(optimized_response)
                    applied_techniques.append(technique.value)
                
                elif technique == OptimizationTechnique.CACHING:
                    optimized_response = await self._apply_caching(optimized_response)
                    applied_techniques.append(technique.value)
                
                elif technique == OptimizationTechnique.STREAMING:
                    optimized_response = await self._apply_streaming(optimized_response)
                    applied_techniques.append(technique.value)
                
                elif technique == OptimizationTechnique.LAZY_LOADING:
                    optimized_response = await self._apply_lazy_loading(optimized_response)
                    applied_techniques.append(technique.value)
                
                elif technique == OptimizationTechnique.PRIORITIZATION:
                    optimized_response = await self._apply_prioritization(optimized_response)
                    applied_techniques.append(technique.value)
                
                # 记录技术成功率
                self._record_technique_success(technique.value, True)
                
            except Exception as e:
                # 记录技术失败
                self._record_technique_success(technique.value, False)
                print(f"优化技术 {technique.value} 失败: {e}")
        
        optimized_size = self._calculate_response_size(optimized_response)
        optimization_time = (time.time() - start_time) * 1000
        compression_ratio = optimized_size / original_size if original_size > 0 else 1.0
        
        # 更新性能历史
        self._update_performance_history({
            'timestamp': time.time(),
            'original_size': original_size,
            'optimized_size': optimized_size,
            'compression_ratio': compression_ratio,
            'optimization_time': optimization_time,
            'applied_techniques': applied_techniques
        })
        
        return ResponseOptimizationResult(
            optimized=len(applied_techniques) > 0,
            original_size=original_size,
            optimized_size=optimized_size,
            compression_ratio=compression_ratio,
            optimization_time_ms=optimization_time,
            applied_techniques=applied_techniques
        )
    
    async def _apply_compression(self, response: MultimodalResponse) -> MultimodalResponse:
        """应用压缩技术"""
        # 文本内容压缩
        if response.text_content:
            compressed_text = await self._compress_text(response.text_content.text)
            response.text_content.text = compressed_text
        
        # 媒体内容压缩（标记）
        for media in response.media_contents:
            if media.size and media.size > 1024 * 1024:  # 大于1MB
                media.metadata["compression_recommended"] = True
        
        return response
    
    async def _apply_caching(self, response: MultimodalResponse) -> MultimodalResponse:
        """应用缓存技术"""
        cache_key = self._generate_cache_key(response)
        
        # 检查是否已缓存
        if cache_key in self.optimization_cache:
            cached_response, timestamp = self.optimization_cache[cache_key]
            
            # 检查缓存是否过期（5分钟）
            if time.time() - timestamp < 300:
                # 更新性能指标
                if response.performance:
                    response.performance.cache_hit = True
                return cached_response
        
        # 缓存响应
        self.optimization_cache[cache_key] = (response, time.time())
        
        # 清理过期缓存
        self._clean_expired_cache()
        
        return response
    
    async def _apply_streaming(self, response: MultimodalResponse) -> MultimodalResponse:
        """应用流式传输技术"""
        # 标记大媒体内容为流式传输
        for media in response.media_contents:
            if media.size and media.size > 512 * 1024:  # 大于512KB
                media.metadata["streaming_enabled"] = True
        
        # 添加流式传输标记
        response.metadata["streaming_supported"] = True
        
        return response
    
    async def _apply_lazy_loading(self, response: MultimodalResponse) -> MultimodalResponse:
        """应用懒加载技术"""
        # 标记媒体内容为懒加载
        for media in response.media_contents:
            if media.size and media.size > 256 * 1024:  # 大于256KB
                media.metadata["lazy_loading"] = True
        
        return response
    
    async def _apply_prioritization(self, response: MultimodalResponse) -> MultimodalResponse:
        """应用优先级技术"""
        # 根据内容类型设置优先级
        if response.media_contents:
            # 如果有媒体内容，降低文本优先级
            response.metadata["content_priority"] = "media_first"
        else:
            response.metadata["content_priority"] = "text_first"
        
        return response
    
    def _calculate_response_size(self, response: MultimodalResponse) -> int:
        """计算响应大小"""
        size = 0
        
        # 文本内容大小
        if response.text_content:
            size += len(response.text_content.text.encode('utf-8'))
        
        # 媒体内容大小
        for media in response.media_contents:
            if media.size:
                size += media.size
            elif isinstance(media.content, bytes):
                size += len(media.content)
            elif isinstance(media.content, str):
                size += len(media.content.encode('utf-8'))
        
        return size
    
    def _generate_cache_key(self, response: MultimodalResponse) -> str:
        """生成缓存键"""
        key_data = {
            'text': response.text_content.text if response.text_content else '',
            'media_count': len(response.media_contents),
            'conversation_id': response.conversation_id,
            'user_id': response.user_id
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    async def _compress_text(self, text: str) -> str:
        """压缩文本"""
        # 简单的文本压缩策略
        if len(text) > 1000:
            # 移除多余的空格和换行
            compressed = ' '.join(text.split())
            
            # 如果压缩后仍然很大，进行进一步处理
            if len(compressed) > 2000:
                # 截断并添加省略号
                compressed = compressed[:1900] + '...'
            
            return compressed
        
        return text
    
    def _clean_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self.optimization_cache.items():
            if current_time - timestamp > 300:  # 5分钟过期
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.optimization_cache[key]
    
    def _record_technique_success(self, technique: str, success: bool):
        """记录技术成功率"""
        if technique not in self.technique_success_rates:
            self.technique_success_rates[technique] = []
        
        self.technique_success_rates[technique].append(success)
        
        # 保持最近100个记录
        if len(self.technique_success_rates[technique]) > 100:
            self.technique_success_rates[technique] = self.technique_success_rates[technique][-100:]
    
    def _update_performance_history(self, record: Dict[str, Any]):
        """更新性能历史"""
        self.performance_history.append(record)
        
        # 保持最近1000个记录
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        if not self.performance_history:
            return {}
        
        # 计算基本统计
        compression_ratios = [r['compression_ratio'] for r in self.performance_history]
        optimization_times = [r['optimization_time'] for r in self.performance_history]
        
        stats = {
            'total_optimizations': len(self.performance_history),
            'average_compression_ratio': sum(compression_ratios) / len(compression_ratios),
            'average_optimization_time_ms': sum(optimization_times) / len(optimization_times),
            'cache_size': len(self.optimization_cache)
        }
        
        # 计算技术成功率
        technique_stats = {}
        for technique, results in self.technique_success_rates.items():
            success_count = sum(1 for r in results if r)
            total_count = len(results)
            success_rate = success_count / total_count if total_count > 0 else 0
            
            technique_stats[technique] = {
                'success_rate': success_rate,
                'total_applications': total_count
            }
        
        stats['technique_success_rates'] = technique_stats
        
        return stats
    
    async def batch_optimize_performance(self, 
                                       responses: List[MultimodalResponse]) -> List[ResponseOptimizationResult]:
        """批量优化性能"""
        tasks = []
        for response in responses:
            task = self.optimize_response_performance(response)
            tasks.append(task)
        
        # 并行处理
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        successful_results = []
        for result in results:
            if isinstance(result, ResponseOptimizationResult):
                successful_results.append(result)
        
        return successful_results
    
    def get_optimization_recommendations(self, response: MultimodalResponse) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        # 检查响应大小
        response_size = self._calculate_response_size(response)
        if response_size > self.thresholds.max_network_usage_kb * 1024:
            recommendations.append("响应过大，建议启用压缩")
        
        # 检查媒体内容
        if len(response.media_contents) > 3:
            recommendations.append("媒体内容过多，建议启用懒加载")
        
        # 检查文本长度
        if response.text_content and len(response.text_content.text) > 2000:
            recommendations.append("文本内容过长，建议启用流式传输")
        
        return recommendations
    
    def clear_cache(self):
        """清空缓存"""
        self.optimization_cache.clear()
        self.performance_history.clear()
        self.technique_success_rates.clear()