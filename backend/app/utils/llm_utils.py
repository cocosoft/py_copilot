"""LLM工具函数模块"""
from typing import Dict, Any, List, Optional
import re
# import tiktoken
import logging

logger = logging.getLogger(__name__)


class PromptTemplates:
    """提示模板管理类"""
    
    # 预定义的系统提示模板
    SYSTEM_TEMPLATES = {
        "general_assistant": "你是一个有帮助的AI助手，可以回答各种问题并提供有用的信息。请保持友好和专业的语气。",
        "code_assistant": "你是一个专业的编程助手，可以帮助编写、解释和调试代码。请提供清晰的代码示例和详细的解释。",
        "creative_writing": "你是一个有创造力的写作助手，可以帮助生成故事、诗歌、文章等内容。请发挥想象力，创作出有趣且独特的内容。",
        "data_analyst": "你是一个数据分析助手，可以帮助理解数据、生成分析报告和可视化建议。请以清晰、专业的方式呈现分析结果。",
        "teacher": "你是一个知识渊博的教师，可以帮助解释各种概念和回答问题。请用简单易懂的语言解释复杂的概念。"
    }
    
    @classmethod
    def get_template(cls, template_name: str, custom_instructions: Optional[str] = None) -> str:
        """获取系统提示模板"""
        base_template = cls.SYSTEM_TEMPLATES.get(template_name, cls.SYSTEM_TEMPLATES["general_assistant"])
        
        if custom_instructions:
            return f"{base_template}\n\n{custom_instructions}"
        
        return base_template
    
    @classmethod
    def format_prompt(cls, template: str, **kwargs) -> str:
        """格式化带变量的提示模板"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return template


def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    """计算文本的token数量"""
    try:
        # 回退方案：粗略估算（英文通常1token≈4字符，中文通常1token≈2字符）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        non_chinese = len(text) - chinese_chars
        estimated_tokens = chinese_chars + (non_chinese // 4)
        return estimated_tokens
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        # 简单回退：按字符数估算
        return len(text) // 2


def truncate_text(text: str, max_tokens: int, model_name: str = "gpt-3.5-turbo") -> str:
    """截断文本至指定的最大token数"""
    try:
        # 回退方案：粗略截断
        avg_token_length = 4  # 假设平均每个token 4个字符
        truncated_text = text[:max_tokens * avg_token_length]
        
        # 确保截断的文本不会在单词中间
        if len(truncated_text) < len(text) and not truncated_text.endswith(' '):
            last_space = truncated_text.rfind(' ')
            if last_space != -1:
                truncated_text = truncated_text[:last_space]
        
        return truncated_text + "..."
    except Exception as e:
        logger.error(f"Error truncating text: {str(e)}")
        # 简单回退：按字符数截断
        return text[:max_tokens * 4] + "..."


def prepare_conversation_history(
    messages: List[Dict[str, str]], 
    max_tokens: int = 4000, 
    model_name: str = "gpt-3.5-turbo"
) -> List[Dict[str, str]]:
    """准备对话历史，确保不超过最大token限制"""
    total_tokens = 0
    processed_messages = []
    
    # 从最新消息开始，向前添加直到达到token限制
    for msg in reversed(messages):
        msg_tokens = count_tokens(msg["content"], model_name)
        
        # 如果添加这个消息会超过限制，就停止
        if total_tokens + msg_tokens > max_tokens:
            # 如果是第一条消息就超限，需要截断
            if not processed_messages:
                msg["content"] = truncate_text(msg["content"], max_tokens, model_name)
                processed_messages.insert(0, msg)
            break
        
        total_tokens += msg_tokens
        processed_messages.insert(0, msg)
    
    return processed_messages


def extract_code_blocks(text: str) -> List[str]:
    """从文本中提取代码块"""
    # 匹配 ```language ... ``` 格式的代码块
    code_blocks = re.findall(r'```[a-zA-Z]*\n(.*?)```', text, re.DOTALL)
    return code_blocks


def detect_language(text: str) -> str:
    """简单检测文本语言（中文/英文）"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    if chinese_chars > english_words:
        return "chinese"
    elif english_words > chinese_chars:
        return "english"
    else:
        # 如果两种语言数量相近，返回混合
        return "mixed"


def format_response_for_api(response: Dict[str, Any]) -> Dict[str, Any]:
    """格式化LLM响应为API友好的格式"""
    return {
        "content": response.get("response", ""),
        "model": response.get("model", "unknown"),
        "response_time_ms": response.get("response_time_ms", 0),
        "success": response.get("success", False),
        "error": response.get("error", None)
    }