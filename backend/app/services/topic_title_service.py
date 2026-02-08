"""
话题标题生成服务
"""
from typing import Dict, Any, Optional
import time
from sqlalchemy.orm import Session

from app.services.default_model_cache_service import DefaultModelCacheService
from app.services.llm_service import LLMService
from app.models.parameter_template import ParameterTemplate


class TopicTitleService:
    """话题标题生成服务"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.cache_service = DefaultModelCacheService()
    
    def generate_title(
        self,
        conversation_content: str,
        db: Session,
        style: str = "concise",
        max_length: int = 20
    ) -> Dict[str, Any]:
        """
        生成话题标题
        
        Args:
            conversation_content: 对话内容
            db: 数据库会话
            style: 标题风格（concise, descriptive, creative）
            max_length: 标题最大长度
        
        Returns:
            生成的标题及相关信息
        """
        start_time = time.time()
        
        # 1. 获取 topic_title 场景的默认模型
        model = self.cache_service.get_default_model_for_scene('topic_title', db)
        
        if not model:
            raise ValueError("未找到话题标题生成的默认模型")
        
        # 2. 获取参数模板
        parameter_template = db.query(ParameterTemplate).filter(
            ParameterTemplate.name == 'topic_title_generation'
        ).first()
        
        # 3. 构建提示词
        prompt = self._build_prompt(conversation_content, style, max_length)
        
        # 4. 获取参数
        parameters = {}
        if parameter_template:
            for param in parameter_template.parameters:
                try:
                    param_value = param.parameter_value
                    # 根据参数类型转换值
                    if param.parameter_type == 'float':
                        parameters[param.parameter_name] = float(param_value)
                    elif param.parameter_type == 'integer':
                        parameters[param.parameter_name] = int(param_value)
                    else:
                        parameters[param.parameter_name] = param_value
                except (ValueError, TypeError):
                    pass
        
        # 根据风格调整参数
        if style == 'creative':
            parameters['temperature'] = 0.5
        elif style == 'descriptive':
            parameters['temperature'] = 0.4
            parameters['max_tokens'] = int(max_length * 1.5)
        
        # 5. 调用 LLM 生成标题
        try:
            response = self.llm_service.generate_response(
                model_name=model.model_name,
                prompt=prompt,
                parameters=parameters
            )
        except Exception as e:
            raise RuntimeError(f"调用LLM生成标题失败: {str(e)}")
        
        # 6. 处理响应
        title = self._extract_title(response)
        generation_time = time.time() - start_time
        
        # 7. 质量评估
        quality_score = self._evaluate_quality(title, conversation_content)
        
        return {
            'title': title,
            'model_id': model.id,
            'model_name': model.model_name,
            'generation_time': generation_time,
            'quality_score': quality_score
        }
    
    def _build_prompt(self, content: str, style: str, max_length: int) -> str:
        """构建提示词"""
        style_instructions = {
            'concise': '请生成一个简洁明了的标题，直接点明对话主题。',
            'descriptive': '请生成一个描述性的标题，包含更多细节信息。',
            'creative': '请生成一个富有创意的标题，吸引注意力。'
        }
        
        prompt = f"""你是一个专业的标题生成助手。请根据以下对话内容生成一个标题。

对话内容：
{content}

要求：
1. 标题长度不超过 {max_length} 个字
2. {style_instructions.get(style, style_instructions['concise'])}
3. 标题应该准确反映对话的核心主题
4. 避免使用过于抽象或模糊的表达
5. 只返回标题，不要包含其他解释或说明

请生成标题："""
        
        return prompt
    
    def _extract_title(self, response: str) -> str:
        """从响应中提取标题"""
        if not response:
            return ""
        
        title = response.strip().strip('"').strip("'").strip('"').strip("'")
        
        if title.startswith('标题：') or title.startswith('标题:'):
            title = title[3:].strip()
        
        return title
    
    def _evaluate_quality(self, title: str, content: str) -> float:
        """评估标题质量"""
        if not title:
            return 0.0
        
        score = 0.0
        
        # 长度评分（20%）
        length = len(title)
        if 5 <= length <= 20:
            score += 0.2
        elif 3 <= length < 5 or 20 < length <= 30:
            score += 0.16
        else:
            score += 0.1
        
        # 相关性评分（30%）
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())
        
        if title_words:
            intersection = title_words & content_words
            relevance = len(intersection) / len(title_words)
            score += min(relevance * 2, 1) * 0.3
        
        # 清晰度评分（25%）
        vague_words = ['一些', '某些', '关于', '相关', '等']
        clarity = 1.0
        for word in vague_words:
            if word in title:
                clarity = 0.6
                break
        score += clarity * 0.25
        
        # 独特性评分（25%）
        score += 0.9 * 0.25
        
        return round(score * 100, 2)
