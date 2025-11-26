"""文本摘要工具模块"""
from typing import Dict, List, Optional, Union

from transformers import pipeline


class TextSummarizer:
    """文本摘要器类，用于生成文本摘要"""

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        初始化文本摘要器

        Args:
            model_name: 摘要模型名称
        """
        self.model_name = model_name
        self.summarizer_pipeline = pipeline("summarization", model=model_name)

    def summarize(self,
                  text: str,
                  max_length: int = 150,
                  min_length: int = 30,
                  do_sample: bool = False) -> str:
        """
        生成文本摘要

        Args:
            text: 要摘要的文本
            max_length: 摘要的最大长度
            min_length: 摘要的最小长度
            do_sample: 是否使用采样生成摘要

        Returns:
            生成的摘要文本
        """
        result = self.summarizer_pipeline(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=do_sample
        )[0]
        return result["summary_text"]

    def summarize_with_options(
        self,
        text: str,
        options: Optional[Dict] = None
    ) -> Dict[str, Union[str, Dict]]:
        """
        带选项的文本摘要

        Args:
            text: 要摘要的文本
            options: 摘要选项

        Returns:
            包含摘要和选项的字典
        """
        if options is None:
            options = {}
        
        # 默认选项
        default_options = {
            "max_length": 150,
            "min_length": 30,
            "do_sample": False
        }
        
        # 合并选项
        merged_options = {**default_options, **options}
        
        # 生成摘要
        summary = self.summarize(
            text=text,
            **merged_options
        )
        
        return {
            "summary": summary,
            "options": merged_options
        }

    def batch_summarize(
        self,
        texts: List[str],
        max_length: int = 150,
        min_length: int = 30,
        do_sample: bool = False
    ) -> List[str]:
        """
        批量生成文本摘要

        Args:
            texts: 要摘要的文本列表
            max_length: 摘要的最大长度
            min_length: 摘要的最小长度
            do_sample: 是否使用采样生成摘要

        Returns:
            摘要文本列表
        """
        results = self.summarizer_pipeline(
            texts,
            max_length=max_length,
            min_length=min_length,
            do_sample=do_sample
        )
        return [result["summary_text"] for result in results]

    def generate_multiple_summaries(
        self,
        text: str,
        variations: List[Dict[str, int]]
    ) -> List[Dict[str, Union[str, Dict]]]:
        """
        生成多个不同参数的摘要变体

        Args:
            text: 要摘要的文本
            variations: 参数变体列表

        Returns:
            多个摘要结果列表
        """
        summaries = []
        
        for variation in variations:
            summary = self.summarize_with_options(text, variation)
            summaries.append(summary)
        
        return summaries


# 创建全局文本摘要器实例
text_summarizer = TextSummarizer()