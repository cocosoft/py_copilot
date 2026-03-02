"""
文本处理工具

复用服务：KnowledgeTextProcessor
提供文本清理、分块、格式化等功能
"""

from typing import Dict, Any, List
import time
import logging

from app.modules.function_calling.base_tool import ServiceTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)
from app.services.knowledge.text_processor import KnowledgeTextProcessor

logger = logging.getLogger(__name__)


class TextProcessingTool(ServiceTool):
    """
    文本处理工具
    
    复用服务：KnowledgeTextProcessor
    提供文本清理、分块、格式化等功能
    """
    
    def __init__(self):
        """初始化文本处理工具"""
        self._text_processor = None
        super().__init__()
    
    def _get_service(self):
        """
        获取文本处理服务实例
        
        Returns:
            KnowledgeTextProcessor: 文本处理服务实例
        """
        return KnowledgeTextProcessor()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="text_processing",
            display_name="文本处理",
            description="提供文本清理、分块、格式化等文本处理功能",
            category=ToolCategory.TEXT.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="📝",
            tags=["文本", "处理", "清理", "分块"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            List[ToolParameter]: 参数定义列表
        """
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=["clean", "chunk", "process", "count", "extract"]
            ),
            ToolParameter(
                name="text",
                type="string",
                description="输入文本",
                required=True
            ),
            ToolParameter(
                name="chunk_size",
                type="integer",
                description="分块大小（action=chunk或process时使用）",
                required=False,
                default=1000
            ),
            ToolParameter(
                name="preserve_newlines",
                type="boolean",
                description="是否保留换行符（action=clean时使用）",
                required=False,
                default=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行文本处理
        
        Args:
            **kwargs: 处理参数
                - action: 操作类型（必需）
                - text: 输入文本（必需）
                - chunk_size: 分块大小（可选）
                - preserve_newlines: 是否保留换行（可选）
        
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            # 验证参数
            validation_result = self.validate_parameters(**kwargs)
            if not validation_result.is_valid:
                errors = [e.message for e in validation_result.errors]
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"参数验证失败: {'; '.join(errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time=time.time() - start_time
                )
            
            action = kwargs.get("action")
            text = kwargs.get("text")
            
            logger.info(f"执行文本处理: action={action}, text_length={len(text)}")
            
            service = self.get_service()
            
            # 根据操作类型执行不同逻辑
            if action == "clean":
                return self._handle_clean(text, kwargs, start_time)
            elif action == "chunk":
                return self._handle_chunk(text, kwargs, start_time)
            elif action == "process":
                return self._handle_process(text, kwargs, start_time)
            elif action == "count":
                return self._handle_count(text, start_time)
            elif action == "extract":
                return self._handle_extract(text, start_time)
            else:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"不支持的操作类型: {action}",
                    error_code="INVALID_ACTION",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"文本处理失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"处理失败: {str(e)}",
                error_code="PROCESSING_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _handle_clean(self, text: str, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理清理操作"""
        preserve_newlines = kwargs.get("preserve_newlines", False)
        
        service = self.get_service()
        
        if preserve_newlines:
            # 保留换行符的清理
            cleaned = self._clean_text_preserve_newlines(text)
        else:
            cleaned = service.clean_text(text)
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "original_length": len(text),
                "cleaned_length": len(cleaned),
                "cleaned_text": cleaned,
                "reduction_percent": round((1 - len(cleaned) / len(text)) * 100, 2) if text else 0
            },
            execution_time=time.time() - start_time
        )
    
    def _handle_chunk(self, text: str, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理分块操作"""
        chunk_size = kwargs.get("chunk_size", 1000)
        
        service = self.get_service()
        chunks = service.chunk_text(text, chunk_size)
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "original_length": len(text),
                "chunk_count": len(chunks),
                "chunk_size": chunk_size,
                "chunks": chunks,
                "average_chunk_length": sum(len(c) for c in chunks) // len(chunks) if chunks else 0
            },
            execution_time=time.time() - start_time
        )
    
    def _handle_process(self, text: str, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理完整处理操作（清理+分块）"""
        chunk_size = kwargs.get("chunk_size", 1000)
        
        service = self.get_service()
        chunks = service.process_document_text(text, chunk_size)
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "original_length": len(text),
                "chunk_count": len(chunks),
                "chunks": chunks,
                "processing_steps": ["clean", "chunk"]
            },
            execution_time=time.time() - start_time
        )
    
    def _handle_count(self, text: str, start_time: float) -> ToolExecutionResult:
        """处理统计操作"""
        # 字符统计
        char_count = len(text)
        char_count_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        
        # 单词统计（中英文）
        import re
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        # 行数统计
        line_count = len(text.split('\n'))
        
        # 段落统计
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "character_count": char_count,
                "character_count_no_spaces": char_count_no_spaces,
                "english_words": english_words,
                "chinese_characters": chinese_chars,
                "line_count": line_count,
                "paragraph_count": paragraph_count,
                "estimated_reading_time_minutes": round(char_count / 500, 2)  # 假设每分钟500字
            },
            execution_time=time.time() - start_time
        )
    
    def _handle_extract(self, text: str, start_time: float) -> ToolExecutionResult:
        """处理提取操作"""
        import re
        
        # 提取URL
        urls = re.findall(r'https?://[^\s<>"{}|\\^`[\]]+', text)
        
        # 提取邮箱
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        
        # 提取数字
        numbers = re.findall(r'\b\d+\b', text)
        
        # 提取中文字符
        chinese_text = re.findall(r'[\u4e00-\u9fff]+', text)
        
        # 提取英文单词
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        
        return ToolExecutionResult.success_result(
            tool_name=self._metadata.name,
            result={
                "urls": urls,
                "emails": emails,
                "numbers": numbers,
                "chinese_segments": chinese_text,
                "english_words": list(set(english_words)),  # 去重
                "extracted_counts": {
                    "urls": len(urls),
                    "emails": len(emails),
                    "numbers": len(numbers),
                    "chinese_segments": len(chinese_text),
                    "unique_english_words": len(set(english_words))
                }
            },
            execution_time=time.time() - start_time
        )
    
    def _clean_text_preserve_newlines(self, text: str) -> str:
        """
        清理文本但保留换行符
        
        Args:
            text: 输入文本
            
        Returns:
            str: 清理后的文本
        """
        import re
        # 只移除多余的空格，保留换行
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 移除行内多余空格
            cleaned_line = re.sub(r'\s+', ' ', line).strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return '\n'.join(cleaned_lines)
