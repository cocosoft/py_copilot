"""
多模态响应管理器
统一管理和优化多模态响应
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.schemas.multimodal_response import (
    MultimodalResponse, MediaType, ResponseFormat, ResponsePriority,
    MediaContent, RichTextContent, InteractiveElement, PerformanceMetrics,
    ResponseOptimizationConfig, ResponseOptimizationResult
)


class ResponseOptimizationStrategy(Enum):
    """响应优化策略枚举"""
    COMPRESSION = "compression"
    CACHING = "caching"
    PRIORITIZATION = "prioritization"
    STREAMING = "streaming"
    LAZY_LOADING = "lazy_loading"


@dataclass
class ResponseCacheEntry:
    """响应缓存条目"""
    response: MultimodalResponse
    timestamp: float
    ttl: int


class MultimodalResponseManager:
    """多模态响应管理器"""
    
    def __init__(self, config: Optional[ResponseOptimizationConfig] = None):
        self.config = config or ResponseOptimizationConfig()
        self.response_cache: Dict[str, ResponseCacheEntry] = {}
        self.performance_stats: Dict[str, List[float]] = {
            'response_times': [],
            'processing_times': [],
            'cache_hits': []
        }
    
    async def create_response(self, 
                            text_content: Optional[str] = None,
                            media_contents: Optional[List[Dict]] = None,
                            conversation_id: Optional[str] = None,
                            user_id: Optional[str] = None,
                            agent_id: Optional[str] = None,
                            priority: ResponsePriority = ResponsePriority.NORMAL,
                            format: ResponseFormat = ResponseFormat.MARKDOWN) -> MultimodalResponse:
        """创建多模态响应"""
        start_time = time.time()
        
        response = MultimodalResponse(
            response_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            priority=priority,
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id
        )
        
        # 添加文本内容
        if text_content:
            response.add_text_content(text_content, format)
        
        # 添加媒体内容
        if media_contents:
            for media in media_contents:
                response.add_media_content(
                    media_type=MediaType(media.get('type', 'text')),
                    content=media.get('content', ''),
                    format=media.get('format'),
                    size=media.get('size'),
                    duration=media.get('duration'),
                    resolution=media.get('resolution'),
                    metadata=media.get('metadata', {})
                )
        
        # 优化响应
        optimized_response = await self.optimize_response(response)
        
        # 记录性能指标
        processing_time = (time.time() - start_time) * 1000
        optimized_response.performance = PerformanceMetrics(
            response_time_ms=processing_time,
            processing_time_ms=processing_time,
            memory_usage_mb=0.0,  # 实际应用中需要测量内存使用
            cache_hit=False
        )
        
        # 更新统计信息
        self._update_performance_stats(processing_time)
        
        return optimized_response
    
    async def optimize_response(self, response: MultimodalResponse) -> MultimodalResponse:
        """优化响应"""
        optimization_start = time.time()
        applied_techniques = []
        
        # 文本压缩
        if response.text_content and len(response.text_content.text) > self.config.max_text_length:
            response = await self._compress_text(response)
            applied_techniques.append("text_compression")
        
        # 媒体优化
        if response.media_contents:
            response = await self._optimize_media(response)
            applied_techniques.append("media_optimization")
        
        # 缓存策略
        if self.config.enable_caching:
            cache_key = self._generate_cache_key(response)
            self.response_cache[cache_key] = ResponseCacheEntry(
                response=response,
                timestamp=time.time(),
                ttl=self.config.cache_ttl_seconds
            )
            applied_techniques.append("caching")
        
        optimization_time = (time.time() - optimization_start) * 1000
        
        # 添加优化元数据
        response.metadata.update({
            "optimization_applied": True,
            "optimization_techniques": applied_techniques,
            "optimization_time_ms": optimization_time
        })
        
        return response
    
    async def _compress_text(self, response: MultimodalResponse) -> MultimodalResponse:
        """压缩文本内容"""
        if not response.text_content:
            return response
        
        text = response.text_content.text
        
        # 简单的文本压缩策略
        if len(text) > self.config.max_text_length:
            # 截断并添加省略号
            compressed_text = text[:self.config.max_text_length - 100] + "..."
            
            # 创建新的富文本内容
            response.text_content = RichTextContent(
                text=compressed_text,
                format=response.text_content.format,
                sections=response.text_content.sections,
                entities=response.text_content.entities
            )
        
        return response
    
    async def _optimize_media(self, response: MultimodalResponse) -> MultimodalResponse:
        """优化媒体内容"""
        optimized_media = []
        
        for media in response.media_contents:
            # 检查媒体大小
            if media.size and media.size > self.config.max_media_size_mb * 1024 * 1024:
                # 对于大文件，可以添加懒加载标记
                media.metadata["lazy_loading"] = True
                media.metadata["original_size"] = media.size
            
            # 添加压缩标记
            if self.config.enable_compression:
                media.metadata["compressed"] = True
            
            optimized_media.append(media)
        
        # 限制媒体数量
        if len(optimized_media) > self.config.max_media_items:
            optimized_media = optimized_media[:self.config.max_media_items]
            response.metadata["media_truncated"] = True
        
        response.media_contents = optimized_media
        return response
    
    def _generate_cache_key(self, response: MultimodalResponse) -> str:
        """生成缓存键"""
        key_parts = []
        
        if response.text_content:
            key_parts.append(response.text_content.text[:100])
        
        for media in response.media_contents:
            key_parts.append(str(media.type))
            if isinstance(media.content, str):
                key_parts.append(media.content[:50])
        
        return "|".join(key_parts)
    
    def _update_performance_stats(self, processing_time: float):
        """更新性能统计"""
        self.performance_stats['response_times'].append(processing_time)
        
        # 保持最近1000个记录
        if len(self.performance_stats['response_times']) > 1000:
            self.performance_stats['response_times'] = self.performance_stats['response_times'][-1000:]
    
    async def get_cached_response(self, cache_key: str) -> Optional[MultimodalResponse]:
        """获取缓存的响应"""
        if not self.config.enable_caching:
            return None
        
        entry = self.response_cache.get(cache_key)
        if entry and time.time() - entry.timestamp < entry.ttl:
            # 更新缓存命中统计
            self.performance_stats['cache_hits'].append(time.time())
            return entry.response
        
        # 清理过期缓存
        self._clean_expired_cache()
        return None
    
    def _clean_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.response_cache.items():
            if current_time - entry.timestamp > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.response_cache[key]
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        response_times = self.performance_stats['response_times']
        
        if not response_times:
            return {}
        
        return {
            "total_responses": len(response_times),
            "average_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "cache_size": len(self.response_cache),
            "cache_hit_count": len(self.performance_stats['cache_hits'])
        }
    
    async def batch_create_responses(self, 
                                   response_data_list: List[Dict[str, Any]]) -> List[MultimodalResponse]:
        """批量创建响应"""
        start_time = time.time()
        
        tasks = []
        for data in response_data_list:
            task = self.create_response(**data)
            tasks.append(task)
        
        # 并行处理
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        successful_responses = []
        for response in responses:
            if isinstance(response, MultimodalResponse):
                successful_responses.append(response)
        
        processing_time = (time.time() - start_time) * 1000
        success_rate = len(successful_responses) / len(response_data_list) if response_data_list else 0
        
        return successful_responses
    
    def export_response(self, response: MultimodalResponse, 
                       export_format: str = 'json') -> Union[str, Dict[str, Any]]:
        """导出响应"""
        if export_format == 'json':
            return response.to_dict()
        elif export_format == 'text':
            return self._format_as_text(response)
        else:
            raise ValueError(f"不支持的导出格式: {export_format}")
    
    def _format_as_text(self, response: MultimodalResponse) -> str:
        """格式化为文本"""
        lines = []
        
        lines.append(f"响应ID: {response.response_id}")
        lines.append(f"时间: {response.timestamp}")
        lines.append(f"优先级: {response.priority.value}")
        
        if response.text_content:
            lines.append("\n文本内容:")
            lines.append(response.text_content.text)
        
        if response.media_contents:
            lines.append("\n媒体内容:")
            for i, media in enumerate(response.media_contents, 1):
                lines.append(f"  {i}. 类型: {media.type.value}")
                if media.format:
                    lines.append(f"     格式: {media.format}")
                if media.size:
                    lines.append(f"     大小: {media.size} 字节")
        
        if response.performance:
            lines.append("\n性能指标:")
            lines.append(f"  响应时间: {response.performance.response_time_ms:.2f}ms")
            lines.append(f"  处理时间: {response.performance.processing_time_ms:.2f}ms")
        
        return "\n".join(lines)