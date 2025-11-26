"""情感分析工具模块"""
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from transformers import pipeline


class SentimentAnalyzer:
    """情感分析器类，用于分析文本情感"""

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        初始化情感分析器

        Args:
            model_name: 情感分析模型名称
        """
        self.model_name = model_name
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)

    def analyze_sentiment(self, text: str) -> Dict[str, Union[str, float]]:
        """
        分析单个文本的情感

        Args:
            text: 要分析的文本

        Returns:
            包含情感标签和置信度的字典
        """
        result = self.sentiment_pipeline(text)[0]
        return {
            "label": result["label"],
            "score": result["score"]
        }

    def batch_analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """
        批量分析文本情感

        Args:
            texts: 要分析的文本列表

        Returns:
            情感分析结果列表
        """
        results = self.sentiment_pipeline(texts)
        return [
            {
                "label": result["label"],
                "score": result["score"]
            }
            for result in results
        ]

    def analyze_sentiment_with_threshold(self, text: str, threshold: float = 0.7) -> Dict[str, Union[str, float, bool]]:
        """
        带阈值的情感分析

        Args:
            text: 要分析的文本
            threshold: 置信度阈值

        Returns:
            包含情感标签、置信度和是否置信的字典
        """
        result = self.analyze_sentiment(text)
        result["confident"] = result["score"] >= threshold
        return result

    def get_sentiment_summary(self, texts: List[str]) -> Dict[str, Union[int, float, List[Tuple[str, float]]]]:
        """
        获取多个文本的情感汇总统计

        Args:
            texts: 文本列表

        Returns:
            情感汇总统计信息
        """
        results = self.batch_analyze_sentiment(texts)
        
        # 计算统计信息
        positive_count = sum(1 for r in results if r["label"] == "POSITIVE")
        negative_count = sum(1 for r in results if r["label"] == "NEGATIVE")
        scores = [r["score"] for r in results]
        
        # 按置信度排序的结果
        sorted_results = sorted(zip(texts, results), key=lambda x: x[1]["score"], reverse=True)
        
        return {
            "total_texts": len(texts),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "positive_ratio": positive_count / len(texts) if texts else 0,
            "average_confidence": np.mean(scores) if scores else 0,
            "top_results": [(text, result["label"], result["score"]) for text, result in sorted_results[:5]]
        }


# 创建全局情感分析器实例
sentiment_analyzer = SentimentAnalyzer()