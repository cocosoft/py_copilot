"""流式响应优化器

提供动态调整chunk_size和发送频率的功能
"""
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from enum import Enum
import json


class StreamingStrategy(Enum):
    """流式响应策略"""
    FAST = "fast"              # 快速：大chunk，短延迟
    BALANCED = "balanced"      # 平衡：中等chunk，中等延迟
    SMOOTH = "smooth"          # 平滑：小chunk，长延迟
    ADAPTIVE = "adaptive"      # 自适应：根据内容动态调整


class StreamingConfig:
    """流式响应配置"""
    
    def __init__(
        self,
        strategy: StreamingStrategy = StreamingStrategy.BALANCED,
        initial_chunk_size: int = 50,
        min_chunk_size: int = 10,
        max_chunk_size: int = 200,
        initial_delay: float = 0.05,
        min_delay: float = 0.01,
        max_delay: float = 0.2,
        enable_adaptive: bool = True
    ):
        """
        初始化流式响应配置
        
        Args:
            strategy: 流式响应策略
            initial_chunk_size: 初始chunk大小
            min_chunk_size: 最小chunk大小
            max_chunk_size: 最大chunk大小
            initial_delay: 初始延迟（秒）
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            enable_adaptive: 是否启用自适应调整
        """
        self.strategy = strategy
        self.initial_chunk_size = initial_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.initial_delay = initial_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.enable_adaptive = enable_adaptive


class StreamingOptimizer:
    """流式响应优化器"""
    
    # 预定义的策略配置
    STRATEGY_CONFIGS = {
        StreamingStrategy.FAST: {
            "chunk_size": 100,
            "delay": 0.02,
            "description": "快速响应，适合短对话"
        },
        StreamingStrategy.BALANCED: {
            "chunk_size": 50,
            "delay": 0.05,
            "description": "平衡响应，适合一般对话"
        },
        StreamingStrategy.SMOOTH: {
            "chunk_size": 20,
            "delay": 0.1,
            "description": "平滑响应，适合长对话"
        },
        StreamingStrategy.ADAPTIVE: {
            "chunk_size": 50,
            "delay": 0.05,
            "description": "自适应响应，根据内容动态调整"
        }
    }
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        """
        初始化流式响应优化器
        
        Args:
            config: 流式响应配置
        """
        self.config = config or StreamingConfig()
        self.current_chunk_size = self.config.initial_chunk_size
        self.current_delay = self.config.initial_delay
        self.performance_metrics = {
            "total_chunks": 0,
            "total_time": 0.0,
            "average_chunk_time": 0.0,
            "client_feedback": []
        }
    
    def _get_strategy_config(self) -> Dict[str, Any]:
        """
        获取策略配置
        
        Returns:
            策略配置字典
        """
        return self.STRATEGY_CONFIGS.get(
            self.config.strategy,
            self.STRATEGY_CONFIGS[StreamingStrategy.BALANCED]
        )
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """
        分析内容特征
        
        Args:
            content: 内容文本
            
        Returns:
            内容特征字典
        """
        return {
            "length": len(content),
            "word_count": len(content.split()),
            "sentence_count": content.count('.') + content.count('!') + content.count('?'),
            "has_code": '```' in content or '`' in content,
            "has_list": content.count('\n-') > 0 or content.count('\n*') > 0,
            "has_numbering": any(f'\n{i}.' in content for i in range(1, 11))
        }
    
    def _adjust_chunk_size(self, content: str, chunk_index: int, total_chunks: int) -> int:
        """
        调整chunk大小
        
        Args:
            content: 内容文本
            chunk_index: 当前chunk索引
            total_chunks: 总chunk数
            
        Returns:
            调整后的chunk大小
        """
        if not self.config.enable_adaptive or self.config.strategy != StreamingStrategy.ADAPTIVE:
            return self.current_chunk_size
        
        # 分析内容特征
        content_features = self._analyze_content(content)
        
        # 根据内容特征调整chunk大小
        chunk_size = self.current_chunk_size
        
        # 如果内容包含代码块，使用较大的chunk
        if content_features["has_code"]:
            chunk_size = min(chunk_size * 2, self.config.max_chunk_size)
        
        # 如果内容包含列表，使用中等chunk
        if content_features["has_list"] or content_features["has_numbering"]:
            chunk_size = min(int(chunk_size * 1.5), self.config.max_chunk_size)
        
        # 根据chunk位置调整
        if chunk_index == 0:
            # 第一个chunk可以稍大
            chunk_size = min(int(chunk_size * 1.2), self.config.max_chunk_size)
        elif chunk_index == total_chunks - 1:
            # 最后一个chunk可以稍小
            chunk_size = max(int(chunk_size * 0.8), self.config.min_chunk_size)
        
        # 确保chunk大小在合理范围内
        chunk_size = max(self.config.min_chunk_size, min(chunk_size, self.config.max_chunk_size))
        
        return chunk_size
    
    def _adjust_delay(self, content: str, chunk_index: int, total_chunks: int) -> float:
        """
        调整发送延迟
        
        Args:
            content: 内容文本
            chunk_index: 当前chunk索引
            total_chunks: 总chunk数
            
        Returns:
            调整后的延迟时间（秒）
        """
        if not self.config.enable_adaptive or self.config.strategy != StreamingStrategy.ADAPTIVE:
            return self.current_delay
        
        # 分析内容特征
        content_features = self._analyze_content(content)
        
        # 根据内容特征调整延迟
        delay = self.current_delay
        
        # 如果内容包含代码块，使用较短的延迟
        if content_features["has_code"]:
            delay = max(delay * 0.7, self.config.min_delay)
        
        # 如果内容包含列表，使用较短的延迟
        if content_features["has_list"] or content_features["has_numbering"]:
            delay = max(delay * 0.8, self.config.min_delay)
        
        # 根据chunk位置调整
        if chunk_index == 0:
            # 第一个chunk使用较短的延迟
            delay = max(delay * 0.5, self.config.min_delay)
        elif chunk_index == total_chunks - 1:
            # 最后一个chunk使用较长的延迟
            delay = min(delay * 1.5, self.config.max_delay)
        
        # 确保延迟在合理范围内
        delay = max(self.config.min_delay, min(delay, self.config.max_delay))
        
        return delay
    
    def split_into_chunks(
        self,
        text: str,
        chunk_size: Optional[int] = None
    ) -> List[str]:
        """
        将文本分割成块
        
        Args:
            text: 文本内容
            chunk_size: chunk大小（可选，如果不提供则使用当前配置）
            
        Returns:
            chunk列表
        """
        if chunk_size is None:
            chunk_size = self.current_chunk_size
        
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        
        return chunks
    
    async def generate_streaming_chunks(
        self,
        content: str,
        chunk_type: str = "content",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成流式响应块
        
        Args:
            content: 内容文本
            chunk_type: chunk类型
            metadata: 元数据
            
        Yields:
            流式响应块字典
        """
        # 获取策略配置
        strategy_config = self._get_strategy_config()
        
        # 使用策略配置的chunk大小和延迟
        chunk_size = strategy_config["chunk_size"]
        delay = strategy_config["delay"]
        
        # 分割内容
        chunks = self.split_into_chunks(content, chunk_size)
        total_chunks = len(chunks)
        
        # 生成流式响应
        for i, chunk in enumerate(chunks):
            # 自适应调整
            if self.config.enable_adaptive and self.config.strategy == StreamingStrategy.ADAPTIVE:
                chunk_size = self._adjust_chunk_size(content, i, total_chunks)
                delay = self._adjust_delay(content, i, total_chunks)
            
            # 构建chunk数据
            chunk_data = {
                "type": chunk_type,
                "content": chunk,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "is_final": (i == total_chunks - 1),
                "chunk_size": len(chunk),
                "timestamp": datetime.now().isoformat()
            }
            
            # 添加元数据
            if metadata:
                chunk_data["metadata"] = metadata
            
            # 更新性能指标
            self.performance_metrics["total_chunks"] += 1
            
            # 发送chunk
            yield chunk_data
            
            # 控制发送速度
            await asyncio.sleep(delay)
    
    async def generate_character_streaming(
        self,
        content: str,
        chunk_type: str = "content",
        metadata: Optional[Dict[str, Any]] = None,
        skip_short: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成逐字符流式响应
        
        Args:
            content: 内容文本
            chunk_type: chunk类型
            metadata: 元数据
            skip_short: 是否跳过短文本的逐字符发送
            
        Yields:
            流式响应块字典
        """
        # 获取策略配置
        strategy_config = self._get_strategy_config()
        delay = strategy_config["delay"]
        
        # 如果内容很短且启用了跳过，直接发送完整内容
        if skip_short and len(content) < 10:
            chunk_data = {
                "type": chunk_type,
                "content": content,
                "chunk_index": 0,
                "total_chunks": 1,
                "is_final": True,
                "chunk_size": len(content),
                "timestamp": datetime.now().isoformat()
            }
            
            if metadata:
                chunk_data["metadata"] = metadata
            
            self.performance_metrics["total_chunks"] += 1
            yield chunk_data
            await asyncio.sleep(delay * 4)
            return
        
        # 逐字符发送
        total_chunks = len(content)
        for i in range(1, total_chunks + 1):
            current_text = content[:i]
            
            # 自适应调整延迟
            current_delay = delay
            if self.config.enable_adaptive and self.config.strategy == StreamingStrategy.ADAPTIVE:
                # 根据字符位置调整延迟
                if i == 1:
                    current_delay = max(delay * 0.5, self.config.min_delay)
                elif i == total_chunks:
                    current_delay = min(delay * 1.5, self.config.max_delay)
            
            # 构建chunk数据
            chunk_data = {
                "type": chunk_type,
                "content": current_text,
                "chunk_index": i - 1,
                "total_chunks": total_chunks,
                "is_final": (i == total_chunks),
                "chunk_size": i,
                "timestamp": datetime.now().isoformat()
            }
            
            if metadata:
                chunk_data["metadata"] = metadata
            
            # 更新性能指标
            self.performance_metrics["total_chunks"] += 1
            
            # 发送chunk
            yield chunk_data
            
            # 控制发送速度
            await asyncio.sleep(current_delay)
    
    def update_performance_metrics(self, chunk_time: float):
        """
        更新性能指标
        
        Args:
            chunk_time: chunk处理时间（秒）
        """
        self.performance_metrics["total_time"] += chunk_time
        self.performance_metrics["average_chunk_time"] = (
            self.performance_metrics["total_time"] / 
            max(1, self.performance_metrics["total_chunks"])
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            性能指标字典
        """
        return self.performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            "total_chunks": 0,
            "total_time": 0.0,
            "average_chunk_time": 0.0,
            "client_feedback": []
        }
    
    def set_strategy(self, strategy: StreamingStrategy):
        """
        设置流式响应策略
        
        Args:
            strategy: 流式响应策略
        """
        self.config.strategy = strategy
        strategy_config = self._get_strategy_config()
        self.current_chunk_size = strategy_config["chunk_size"]
        self.current_delay = strategy_config["delay"]
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            策略信息字典
        """
        strategy_config = self._get_strategy_config()
        return {
            "strategy": self.config.strategy.value,
            "chunk_size": strategy_config["chunk_size"],
            "delay": strategy_config["delay"],
            "description": strategy_config["description"],
            "enable_adaptive": self.config.enable_adaptive
        }


# 创建全局优化器实例
_default_optimizer: Optional[StreamingOptimizer] = None


def get_streaming_optimizer(config: Optional[StreamingConfig] = None) -> StreamingOptimizer:
    """
    获取流式响应优化器实例
    
    Args:
        config: 流式响应配置
        
    Returns:
        流式响应优化器实例
    """
    global _default_optimizer
    if _default_optimizer is None:
        _default_optimizer = StreamingOptimizer(config)
    return _default_optimizer


# 便捷函数
async def generate_fast_streaming(
    content: str,
    chunk_type: str = "content",
    metadata: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    生成快速流式响应
    
    Args:
        content: 内容文本
        chunk_type: chunk类型
        metadata: 元数据
        
    Yields:
        流式响应块字典
    """
    config = StreamingConfig(strategy=StreamingStrategy.FAST)
    optimizer = StreamingOptimizer(config)
    async for chunk in optimizer.generate_streaming_chunks(content, chunk_type, metadata):
        yield chunk


async def generate_balanced_streaming(
    content: str,
    chunk_type: str = "content",
    metadata: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    生成平衡流式响应
    
    Args:
        content: 内容文本
        chunk_type: chunk类型
        metadata: 元数据
        
    Yields:
        流式响应块字典
    """
    config = StreamingConfig(strategy=StreamingStrategy.BALANCED)
    optimizer = StreamingOptimizer(config)
    async for chunk in optimizer.generate_streaming_chunks(content, chunk_type, metadata):
        yield chunk


async def generate_smooth_streaming(
    content: str,
    chunk_type: str = "content",
    metadata: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    生成平滑流式响应
    
    Args:
        content: 内容文本
        chunk_type: chunk类型
        metadata: 元数据
        
    Yields:
        流式响应块字典
    """
    config = StreamingConfig(strategy=StreamingStrategy.SMOOTH)
    optimizer = StreamingOptimizer(config)
    async for chunk in optimizer.generate_streaming_chunks(content, chunk_type, metadata):
        yield chunk


async def generate_adaptive_streaming(
    content: str,
    chunk_type: str = "content",
    metadata: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    生成自适应流式响应
    
    Args:
        content: 内容文本
        chunk_type: chunk类型
        metadata: 元数据
        
    Yields:
        流式响应块字典
    """
    config = StreamingConfig(strategy=StreamingStrategy.ADAPTIVE)
    optimizer = StreamingOptimizer(config)
    async for chunk in optimizer.generate_streaming_chunks(content, chunk_type, metadata):
        yield chunk
