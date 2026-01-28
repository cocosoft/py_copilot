"""
多模态响应格式定义
统一管理各种媒体类型的响应格式
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class MediaType(Enum):
    """媒体类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    CODE = "code"
    TABLE = "table"
    CHART = "chart"


class ResponseFormat(Enum):
    """响应格式枚举"""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PLAIN_TEXT = "plain_text"


class ResponsePriority(Enum):
    """响应优先级枚举"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class MediaContent(BaseModel):
    """媒体内容模型"""
    type: MediaType
    content: Union[str, bytes, Dict[str, Any]]
    format: Optional[str] = None  # 如: jpg, png, mp3, mp4
    size: Optional[int] = None  # 字节大小
    duration: Optional[float] = None  # 音频/视频时长（秒）
    resolution: Optional[str] = None  # 图像/视频分辨率
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RichTextContent(BaseModel):
    """富文本内容模型"""
    text: str
    format: ResponseFormat = ResponseFormat.MARKDOWN
    sections: Optional[List[Dict[str, Any]]] = None  # 结构化内容
    entities: Optional[List[Dict[str, Any]]] = None  # 实体信息


class InteractiveElement(BaseModel):
    """交互元素模型"""
    type: str  # button, dropdown, slider, etc.
    label: str
    action: str
    options: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    response_time_ms: float
    processing_time_ms: float
    memory_usage_mb: float
    token_count: Optional[int] = None
    model_name: Optional[str] = None
    cache_hit: bool = False


class MultimodalResponse(BaseModel):
    """多模态响应模型"""
    # 基础信息
    response_id: str
    timestamp: datetime
    priority: ResponsePriority = ResponsePriority.NORMAL
    
    # 内容部分
    text_content: Optional[RichTextContent] = None
    media_contents: List[MediaContent] = Field(default_factory=list)
    interactive_elements: List[InteractiveElement] = Field(default_factory=list)
    
    # 上下文信息
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # 性能指标
    performance: Optional[PerformanceMetrics] = None
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_text_content(self, text: str, format: ResponseFormat = ResponseFormat.MARKDOWN) -> None:
        """添加文本内容"""
        self.text_content = RichTextContent(text=text, format=format)
    
    def add_media_content(self, media_type: MediaType, content: Union[str, bytes, Dict], 
                         **kwargs) -> None:
        """添加媒体内容"""
        media_content = MediaContent(type=media_type, content=content, **kwargs)
        self.media_contents.append(media_content)
    
    def add_interactive_element(self, element_type: str, label: str, action: str, 
                               **kwargs) -> None:
        """添加交互元素"""
        element = InteractiveElement(type=element_type, label=label, action=action, **kwargs)
        self.interactive_elements.append(element)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "response_id": self.response_id,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "text_content": self.text_content.dict() if self.text_content else None,
            "media_contents": [content.dict() for content in self.media_contents],
            "interactive_elements": [element.dict() for element in self.interactive_elements],
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "performance": self.performance.dict() if self.performance else None,
            "metadata": self.metadata
        }


class BatchMultimodalResponse(BaseModel):
    """批量多模态响应模型"""
    responses: List[MultimodalResponse]
    total_count: int
    batch_id: str
    processing_time_ms: float
    success_rate: float
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        successful_responses = [r for r in self.responses if r.performance]
        
        return {
            "total_responses": len(self.responses),
            "successful_responses": len(successful_responses),
            "average_response_time": (
                sum(r.performance.response_time_ms for r in successful_responses) / 
                len(successful_responses) if successful_responses else 0
            ),
            "total_processing_time": self.processing_time_ms,
            "success_rate": self.success_rate
        }


class ResponseOptimizationConfig(BaseModel):
    """响应优化配置"""
    # 性能配置
    max_response_time_ms: int = 5000
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    
    # 内容配置
    max_text_length: int = 4000
    max_media_size_mb: int = 10
    enable_compression: bool = True
    
    # 格式配置
    default_format: ResponseFormat = ResponseFormat.MARKDOWN
    enable_rich_formatting: bool = True
    
    # 多媒体配置
    supported_media_types: List[MediaType] = Field(default_factory=list)
    max_media_items: int = 5


class ResponseOptimizationResult(BaseModel):
    """响应优化结果"""
    optimized: bool
    original_size: int
    optimized_size: int
    compression_ratio: float
    optimization_time_ms: float
    applied_techniques: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)