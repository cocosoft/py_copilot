"""
多媒体内容展示器
优化多媒体内容的展示效果和性能
"""

import asyncio
import base64
import io
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from PIL import Image

from app.schemas.multimodal_response import MediaType, MediaContent


class DisplayStrategy(Enum):
    """展示策略枚举"""
    IMMEDIATE = "immediate"  # 立即显示
    LAZY_LOAD = "lazy_load"  # 懒加载
    PROGRESSIVE = "progressive"  # 渐进式加载
    THUMBNAIL_FIRST = "thumbnail_first"  # 缩略图优先


class MediaQuality(Enum):
    """媒体质量枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ORIGINAL = "original"


@dataclass
class DisplayConfig:
    """展示配置"""
    max_width: int = 800
    max_height: int = 600
    quality: MediaQuality = MediaQuality.MEDIUM
    strategy: DisplayStrategy = DisplayStrategy.IMMEDIATE
    enable_compression: bool = True
    thumbnail_size: Tuple[int, int] = (200, 150)


class MediaContentDisplay:
    """多媒体内容展示器"""
    
    def __init__(self, config: Optional[DisplayConfig] = None):
        self.config = config or DisplayConfig()
        self.image_cache: Dict[str, bytes] = {}
        self.performance_stats: Dict[str, List[float]] = {
            'image_processing_times': [],
            'compression_ratios': []
        }
    
    async def optimize_media_display(self, media_content: MediaContent) -> MediaContent:
        """优化媒体内容展示"""
        start_time = time.time()
        
        optimized_content = media_content
        
        if media_content.type == MediaType.IMAGE:
            optimized_content = await self._optimize_image_display(media_content)
        elif media_content.type == MediaType.AUDIO:
            optimized_content = await self._optimize_audio_display(media_content)
        elif media_content.type == MediaType.VIDEO:
            optimized_content = await self._optimize_video_display(media_content)
        
        processing_time = (time.time() - start_time) * 1000
        self._update_performance_stats(processing_time)
        
        # 添加展示元数据
        optimized_content.metadata.update({
            "display_optimized": True,
            "display_strategy": str(self.config.strategy),
            "processing_time_ms": processing_time
        })
        
        return optimized_content
    
    async def _optimize_image_display(self, media_content: MediaContent) -> MediaContent:
        """优化图片展示"""
        try:
            if isinstance(media_content.content, bytes):
                # 处理二进制图像数据
                image_data = media_content.content
                
                # 根据策略优化
                if self.config.strategy == DisplayStrategy.THUMBNAIL_FIRST:
                    # 生成缩略图
                    thumbnail_data = await self._create_thumbnail(image_data)
                    media_content.metadata["thumbnail"] = base64.b64encode(thumbnail_data).decode('utf-8')
                    media_content.metadata["lazy_loading"] = True
                
                elif self.config.enable_compression:
                    # 压缩图像
                    compressed_data = await self._compress_image(image_data)
                    if compressed_data:
                        media_content.content = compressed_data
                        media_content.size = len(compressed_data)
                        media_content.metadata["compressed"] = True
                        
                        # 记录压缩率
                        original_size = len(image_data)
                        compressed_size = len(compressed_data)
                        compression_ratio = compressed_size / original_size if original_size > 0 else 0
                        self.performance_stats['compression_ratios'].append(compression_ratio)
            
            return media_content
            
        except Exception as e:
            # 如果优化失败，返回原始内容
            media_content.metadata["optimization_error"] = str(e)
            return media_content
    
    async def _optimize_audio_display(self, media_content: MediaContent) -> MediaContent:
        """优化音频展示"""
        # 音频优化策略
        if self.config.strategy == DisplayStrategy.LAZY_LOAD:
            media_content.metadata["lazy_loading"] = True
        
        # 添加音频播放器配置
        media_content.metadata.update({
            "audio_player": {
                "autoplay": False,
                "controls": True,
                "loop": False
            }
        })
        
        return media_content
    
    async def _optimize_video_display(self, media_content: MediaContent) -> MediaContent:
        """优化视频展示"""
        # 视频优化策略
        if self.config.strategy in [DisplayStrategy.LAZY_LOAD, DisplayStrategy.THUMBNAIL_FIRST]:
            media_content.metadata["lazy_loading"] = True
        
        # 添加视频播放器配置
        media_content.metadata.update({
            "video_player": {
                "autoplay": False,
                "controls": True,
                "muted": True,
                "poster": "auto"  # 自动生成海报帧
            }
        })
        
        return media_content
    
    async def _create_thumbnail(self, image_data: bytes) -> bytes:
        """创建缩略图"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # 调整尺寸
            thumbnail_size = self.config.thumbnail_size
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            
            return output.getvalue()
            
        except Exception as e:
            # 如果缩略图创建失败，返回空数据
            return b''
    
    async def _compress_image(self, image_data: bytes) -> Optional[bytes]:
        """压缩图像"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # 调整尺寸（如果太大）
            if image.width > self.config.max_width or image.height > self.config.max_height:
                image.thumbnail((self.config.max_width, self.config.max_height), Image.Resampling.LANCZOS)
            
            # 根据质量设置选择压缩参数
            quality = 85  # 默认质量
            if self.config.quality == MediaQuality.LOW:
                quality = 60
            elif self.config.quality == MediaQuality.HIGH:
                quality = 95
            elif self.config.quality == MediaQuality.ORIGINAL:
                quality = 100
            
            # 保存为JPEG格式
            output = io.BytesIO()
            
            # 处理不同格式
            if image.mode in ('RGBA', 'LA', 'P'):
                # 转换为RGB
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                rgb_image.save(output, format='JPEG', quality=quality, optimize=True)
            else:
                image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            # 如果压缩失败，返回None
            return None
    
    def _update_performance_stats(self, processing_time: float):
        """更新性能统计"""
        self.performance_stats['image_processing_times'].append(processing_time)
        
        # 保持最近1000个记录
        if len(self.performance_stats['image_processing_times']) > 1000:
            self.performance_stats['image_processing_times'] = \
                self.performance_stats['image_processing_times'][-1000:]
    
    def get_display_statistics(self) -> Dict[str, Any]:
        """获取展示统计信息"""
        processing_times = self.performance_stats['image_processing_times']
        compression_ratios = self.performance_stats['compression_ratios']
        
        stats = {
            "total_processed": len(processing_times),
            "cache_size": len(self.image_cache)
        }
        
        if processing_times:
            stats.update({
                "average_processing_time_ms": sum(processing_times) / len(processing_times),
                "min_processing_time_ms": min(processing_times),
                "max_processing_time_ms": max(processing_times)
            })
        
        if compression_ratios:
            avg_ratio = sum(compression_ratios) / len(compression_ratios)
            stats["average_compression_ratio"] = f"{avg_ratio:.2%}"
        
        return stats
    
    async def batch_optimize_display(self, 
                                   media_contents: List[MediaContent]) -> List[MediaContent]:
        """批量优化展示"""
        tasks = []
        for media in media_contents:
            task = self.optimize_media_display(media)
            tasks.append(task)
        
        # 并行处理
        optimized_contents = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        successful_contents = []
        for content in optimized_contents:
            if isinstance(content, MediaContent):
                successful_contents.append(content)
        
        return successful_contents
    
    def generate_html_display(self, media_content: MediaContent) -> str:
        """生成HTML展示代码"""
        if media_content.type == MediaType.IMAGE:
            return self._generate_image_html(media_content)
        elif media_content.type == MediaType.AUDIO:
            return self._generate_audio_html(media_content)
        elif media_content.type == MediaType.VIDEO:
            return self._generate_video_html(media_content)
        else:
            return f"<p>不支持的类型: {media_content.type.value}</p>"
    
    def _generate_image_html(self, media_content: MediaContent) -> str:
        """生成图片HTML"""
        if isinstance(media_content.content, bytes):
            # 转换为base64
            image_base64 = base64.b64encode(media_content.content).decode('utf-8')
            
            html = f'''
            <div class="media-container image-container">
                <img src="data:image/jpeg;base64,{image_base64}" 
                     alt="图片" 
                     loading="lazy"
                     style="max-width: 100%; height: auto;">
            </div>
            '''
            return html
        
        return f"<p>图片数据格式错误</p>"
    
    def _generate_audio_html(self, media_content: MediaContent) -> str:
        """生成音频HTML"""
        if isinstance(media_content.content, bytes):
            audio_base64 = base64.b64encode(media_content.content).decode('utf-8')
            
            html = f'''
            <div class="media-container audio-container">
                <audio controls style="width: 100%;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    您的浏览器不支持音频播放。
                </audio>
            </div>
            '''
            return html
        
        return f"<p>音频数据格式错误</p>"
    
    def _generate_video_html(self, media_content: MediaContent) -> str:
        """生成视频HTML"""
        if isinstance(media_content.content, bytes):
            video_base64 = base64.b64encode(media_content.content).decode('utf-8')
            
            html = f'''
            <div class="media-container video-container">
                <video controls style="max-width: 100%; height: auto;" muted>
                    <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                    您的浏览器不支持视频播放。
                </video>
            </div>
            '''
            return html
        
        return f"<p>视频数据格式错误</p>"
    
    def clear_cache(self):
        """清空缓存"""
        self.image_cache.clear()
        self.performance_stats = {
            'image_processing_times': [],
            'compression_ratios': []
        }