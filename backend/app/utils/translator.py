"""语言翻译工具模块"""
from typing import Dict, List, Optional, Union


class Translator:
    """文本翻译器类，用于文本翻译"""

    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-zh-en"):
        """
        初始化翻译器

        Args:
            model_name: 翻译模型名称，默认使用中文到英文的翻译模型
        """
        self.model_name = model_name
        # 临时注释掉需要下载大型模型的代码，使用简单实现
        # self.translator_pipeline = pipeline("translation", model=model_name)
        self.current_model_direction = self._extract_language_direction(model_name)

    def _extract_language_direction(self, model_name: str) -> str:
        """
        从模型名称中提取语言方向

        Args:
            model_name: 模型名称

        Returns:
            语言方向字符串，如'zh-en'
        """
        # 尝试从模型名称中提取语言方向
        import re
        match = re.search(r'opus-mt-([a-z]+-[a-z]+)', model_name)
        if match:
            return match.group(1)
        return "unknown-unknown"

    def translate(self, text: str) -> str:
        """
        翻译单个文本

        Args:
            text: 要翻译的文本

        Returns:
            翻译后的文本
        """
        # 临时使用简单实现，直接返回原文
        # result = self.translator_pipeline(text)[0]
        # return result["translation_text"]
        return text

    def batch_translate(self, texts: List[str]) -> List[str]:
        """
        批量翻译文本

        Args:
            texts: 要翻译的文本列表

        Returns:
            翻译后的文本列表
        """
        # 临时注释掉翻译功能，直接返回原文列表
        # results = self.translator_pipeline(texts)
        # return [result["translation_text"] for result in results]
        return texts

    def translate_with_metadata(self, text: str) -> Dict[str, Union[str, str]]:
        """
        翻译文本并返回元数据

        Args:
            text: 要翻译的文本

        Returns:
            包含翻译结果和元数据的字典
        """
        translation = self.translate(text)
        return {
            "original_text": text,
            "translated_text": translation,
            "model_used": self.model_name,
            "language_direction": self.current_model_direction
        }

    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言方向列表（常用）

        Returns:
            支持的语言方向列表
        """
        return [
            "zh-en",  # 中文到英文
            "en-zh",  # 英文到中文
            "zh-fr",  # 中文到法文
            "en-fr",  # 英文到法文
            "en-de",  # 英文到德文
            "en-es",  # 英文到西班牙文
            "en-ja",  # 英文到日文
            "en-ko"   # 英文到韩文
        ]

    def switch_model(self, model_name: str) -> None:
        """
        切换翻译模型

        Args:
            model_name: 新的翻译模型名称
        """
        self.model_name = model_name
        # 临时注释掉模型加载代码
        # self.translator_pipeline = pipeline("translation", model=model_name)
        self.current_model_direction = self._extract_language_direction(model_name)


# 创建全局翻译器实例
# 默认使用中文到英文的翻译模型
translator = Translator()

# 创建英文到中文的翻译器实例
translator_en_to_zh = Translator(model_name="Helsinki-NLP/opus-mt-en-zh")