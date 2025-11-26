"""文本处理工具模块"""
import re
import string
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """基础文本清洗"""
    try:
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白
        text = text.strip()
        return text
    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        return text


def remove_punctuation(text: str, keep: Optional[str] = None) -> str:
    """移除标点符号"""
    try:
        if keep:
            # 创建一个包含所有标点符号但排除要保留的字符的字符串
            punct_to_remove = ''.join([p for p in string.punctuation if p not in keep])
            return text.translate(str.maketrans('', '', punct_to_remove))
        else:
            return text.translate(str.maketrans('', '', string.punctuation))
    except Exception as e:
        logger.error(f"Error removing punctuation: {str(e)}")
        return text


def normalize_text(text: str, lowercase: bool = True, remove_extra_spaces: bool = True) -> str:
    """文本规范化"""
    try:
        if lowercase:
            text = text.lower()
        if remove_extra_spaces:
            text = re.sub(r'\s+', ' ', text)
        return text.strip()
    except Exception as e:
        logger.error(f"Error normalizing text: {str(e)}")
        return text


def split_text(text: str, separator: str = '\n', max_length: Optional[int] = None) -> List[str]:
    """文本分割"""
    try:
        parts = text.split(separator)
        
        # 如果指定了最大长度，进一步分割过长的部分
        if max_length:
            result = []
            for part in parts:
                if len(part) > max_length:
                    # 按最大长度分割
                    for i in range(0, len(part), max_length):
                        result.append(part[i:i+max_length])
                else:
                    result.append(part)
            return result
        
        return parts
    except Exception as e:
        logger.error(f"Error splitting text: {str(e)}")
        return [text]


def extract_keywords(text: str, method: str = 'simple', top_n: int = 10) -> List[str]:
    """简单关键词提取"""
    try:
        # 简单方法：基于词频（排除停用词）
        if method == 'simple':
            # 基础停用词列表（可以扩展）
            stop_words = {
                '的', '了', '和', '是', '在', '有', '我', '他', '她', '它', '们',
                '这', '那', '个', '一', '不', '也', '很', '都', '要', '与', '而',
                'with', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'for', 'and',
                'is', 'are', 'was', 'were', 'be', 'been', 'being'
            }
            
            # 清理文本
            text = normalize_text(text)
            text = remove_punctuation(text)
            
            # 分词并统计词频
            words = text.split()
            word_freq = {}
            
            for word in words:
                if word not in stop_words and len(word) > 1:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按词频排序并返回前N个
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:top_n]]
        
        return []
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return []


def count_words(text: str) -> Dict[str, int]:
    """统计文本中的单词数量和字符数量"""
    try:
        # 清理文本
        cleaned_text = clean_text(text)
        
        # 统计字符数（包括空格）
        char_count = len(cleaned_text)
        
        # 统计字符数（不包括空格）
        char_count_no_spaces = len(cleaned_text.replace(' ', ''))
        
        # 统计单词数
        word_count = len(cleaned_text.split())
        
        # 统计句子数（简单方法）
        sentences = re.split(r'[.!?。！？]+', cleaned_text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "char_count_no_spaces": char_count_no_spaces,
            "sentence_count": sentence_count
        }
    except Exception as e:
        logger.error(f"Error counting words: {str(e)}")
        return {"word_count": 0, "char_count": 0, "char_count_no_spaces": 0, "sentence_count": 0}


def truncate_text_by_sentences(text: str, max_sentences: int = 5) -> str:
    """按句子截断文本"""
    try:
        # 分割句子
        sentences = re.split(r'([.!?。！？]+)', text)
        
        # 重组句子（保留标点符号）
        combined_sentences = []
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # 添加标点符号
            if sentence.strip():
                combined_sentences.append(sentence)
        
        # 返回前N个句子
        if len(combined_sentences) <= max_sentences:
            return ''.join(combined_sentences)
        else:
            return ''.join(combined_sentences[:max_sentences]) + "..."
    except Exception as e:
        logger.error(f"Error truncating text by sentences: {str(e)}")
        return text


def detect_text_language(text: str) -> str:
    """检测文本语言（简单实现）"""
    try:
        # 统计中文和英文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # 基于字符数量判断
        if chinese_chars > english_chars * 2:
            return "chinese"
        elif english_chars > chinese_chars * 2:
            return "english"
        else:
            return "mixed"
    except Exception as e:
        logger.error(f"Error detecting text language: {str(e)}")
        return "unknown"