"""文本处理工具"""
from typing import List, Optional
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
import logging

logger = logging.getLogger(__name__)


class TextProcessingTool(BaseTool):
    """文本处理工具"""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="text_processing",
            display_name="文本处理工具",
            description="提供文本处理功能，包括文本统计、格式化、转换等操作",
            category="text_processing",
            version="1.0.0",
            icon="📝",
            tags=["text", "processing", "formatting", "conversion"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="处理动作：count_chars, count_words, count_lines, to_upper, to_lower, reverse, remove_spaces, trim",
                required=True,
                default="count_words"
            ),
            ToolParameter(
                name="text",
                type="string",
                description="要处理的文本内容",
                required=True
            )
        ]
    
    async def execute(self, parameters: dict) -> ToolExecutionResult:
        """
        执行文本处理
        
        Args:
            parameters: 工具参数
                - action: 处理动作
                - text: 要处理的文本
                
        Returns:
            工具执行结果
        """
        import time
        start_time = time.time()
        
        try:
            action = parameters.get("action", "count_words")
            text = parameters.get("text", "")
            
            if not text:
                return ToolExecutionResult(
                    success=False,
                    error="文本内容不能为空",
                    error_code="TEXT_001",
                    execution_time=time.time() - start_time,
                    tool_name=self._metadata.name
                )
            
            result = {}
            
            if action == "count_chars":
                result = {
                    "char_count": len(text),
                    "char_count_no_spaces": len(text.replace(" ", "")),
                    "action": "count_chars"
                }
            elif action == "count_words":
                words = text.split()
                result = {
                    "word_count": len(words),
                    "unique_words": len(set(words)),
                    "action": "count_words"
                }
            elif action == "count_lines":
                lines = text.split("\n")
                result = {
                    "line_count": len(lines),
                    "non_empty_lines": len([line for line in lines if line.strip()]),
                    "action": "count_lines"
                }
            elif action == "to_upper":
                result = {
                    "original_text": text,
                    "processed_text": text.upper(),
                    "action": "to_upper"
                }
            elif action == "to_lower":
                result = {
                    "original_text": text,
                    "processed_text": text.lower(),
                    "action": "to_lower"
                }
            elif action == "reverse":
                result = {
                    "original_text": text,
                    "processed_text": text[::-1],
                    "action": "reverse"
                }
            elif action == "remove_spaces":
                result = {
                    "original_text": text,
                    "processed_text": text.replace(" ", ""),
                    "action": "remove_spaces"
                }
            elif action == "trim":
                result = {
                    "original_text": text,
                    "processed_text": text.strip(),
                    "action": "trim"
                }
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"不支持的动作: {action}",
                    error_code="TEXT_002",
                    execution_time=time.time() - start_time,
                    tool_name=self._metadata.name
                )
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time,
                tool_name=self._metadata.name
            )
            
        except Exception as e:
            logger.error(f"文本处理失败: {e}")
            return ToolExecutionResult(
                success=False,
                error=f"文本处理失败: {str(e)}",
                error_code="TEXT_003",
                execution_time=time.time() - start_time,
                tool_name=self._metadata.name
            )
