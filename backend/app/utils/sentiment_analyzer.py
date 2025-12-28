"""简化的情感分析工具模块（仅提供默认结果）"""
from typing import Dict, List, Optional, Tuple, Union


class SentimentAnalyzer:
    """简化的情感分析器类，仅提供默认情感分析结果"""

    def __init__(self):
        """初始化情感分析器"""
        self.is_available = False
        self.available = False

    def analyze_sentiment(self, text: str) -> Dict[str, Union[str, float]]:
        """
        返回默认的情感分析结果

        Args:
            text: 要分析的文本

        Returns:
            包含情感标签和置信度的字典
        """
        return {
            "label": "NEUTRAL",
            "score": 0.5
        }

    def batch_analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """
        批量返回默认的情感分析结果

        Args:
            texts: 要分析的文本列表

        Returns:
            情感分析结果列表
        """
        return [
            {
                "label": "NEUTRAL",
                "score": 0.5
            }
            for _ in texts
        ]

    def analyze_sentiment_with_threshold(self, text: str, threshold: float = 0.7) -> Dict[str, Union[str, float, bool]]:
        """
        返回带阈值的默认情感分析结果

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
        返回默认的情感汇总统计信息

        Args:
            texts: 文本列表

        Returns:
            情感汇总统计信息
        """
        return {
            "total_texts": len(texts),
            "positive_count": 0,
            "negative_count": 0,
            "positive_ratio": 0,
            "average_confidence": 0.5,
            "top_results": []
        }


# 创建全局情感分析器实例
sentiment_analyzer = SentimentAnalyzer()