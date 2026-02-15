"""
话题标题生成服务
"""
from typing import Dict, Any, Optional
import time
from sqlalchemy.orm import Session

from app.services.model_query_service import ModelQueryService
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
from app.models.parameter_template import ParameterTemplate


class TopicTitleService:
    """话题标题生成服务"""
    
    def __init__(self):
        pass
    
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
        
        # 1. 获取默认模型（用于标题生成）
        model = ModelQueryService.get_default_model(db, "chat")
        
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
        
        # 5. 调用增强的 LLM 服务生成标题
        try:
            messages = [{"role": "user", "content": prompt}]
            response = enhanced_llm_service.chat_completion(
                messages=messages,
                model_name=model.model_id,
                max_tokens=parameters.get('max_tokens', 100),
                temperature=parameters.get('temperature', 0.4),
                db=db
            )
            
            # 处理流式响应（生成器）
            if hasattr(response, '__iter__') and not isinstance(response, (list, dict)):
                title_text = ""
                for chunk in response:
                    if isinstance(chunk, dict):
                        if chunk.get("success", False):
                            title_text += chunk.get("generated_text", "")
                        elif chunk.get("type") == "content":
                            title_text += chunk.get("content", "")
                        elif "content" in chunk and chunk.get("type") != "thinking":
                            title_text += chunk.get("content", "")
                    elif isinstance(chunk, str):
                        title_text += chunk
            elif isinstance(response, dict) and response.get('success', False):
                title_text = response.get('generated_text', '')
                if not title_text and 'reasoning_content' in response:
                    pass
            else:
                error_msg = response.get('error', '未知错误') if isinstance(response, dict) else '响应格式错误'
                raise RuntimeError(f"LLM生成失败: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"调用LLM生成标题失败: {str(e)}")
        
        # 6. 处理响应
        title = self._extract_title(title_text)
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
        
        title = response.strip()
        
        thinking_keywords = [
            '首先，任务是', '现在，分析对话内容', '让我分析', '我需要', 
            '首先', '然后', '接下来', '根据', '分析如下', '思考过程',
            '好的，用户', '用户要求', '我来看', '让我看看'
        ]
        
        lines = title.split('\n')
        title_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            is_thinking_line = False
            for keyword in thinking_keywords:
                if line_stripped.startswith(keyword) or keyword in line_stripped[:30]:
                    is_thinking_line = True
                    break
            
            if not is_thinking_line:
                title_lines.append(line_stripped)
        
        if title_lines:
            title = title_lines[-1]
        else:
            title = lines[-1].strip() if lines else ""
        
        title = title.strip('"').strip("'").strip('"').strip("'")
        
        if title.startswith('标题：') or title.startswith('标题:'):
            title = title[3:].strip()
        
        punctuation_to_remove = '。，、；：？！""''（）【】《》\n'
        title = title.rstrip(punctuation_to_remove)
        
        if len(title) > 50:
            last_period_pos = max(
                title.rfind('。'),
                title.rfind('，'),
                title.rfind('：'),
                title.rfind(':')
            )
            if last_period_pos > 0:
                title = title[last_period_pos + 1:].strip()
        
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
