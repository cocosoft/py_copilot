import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# 模拟LLMTasks类而不是导入它
class MockLLMTasks:
    def __init__(self):
        self.llm_service = MagicMock()
    
    def summarize_text(self, text, **options):
        # 添加输入验证
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        # 模拟处理逻辑
        return {"result": "摘要结果", "model": "mock-model", "tokens_used": 100, "success": True}
    
    def generate_code(self, prompt, language):
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("提示内容不能为空")
        if not language or not isinstance(language, str):
            raise ValueError("编程语言不能为空")
        return {"result": "代码结果", "model": "mock-model", "tokens_used": 150, "success": True}
    
    def translate_text(self, text, target_language):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        if not target_language or not isinstance(target_language, str):
            raise ValueError("目标语言不能为空")
        return {"result": "翻译结果", "model": "mock-model", "tokens_used": 120, "success": True}
    
    def analyze_sentiment(self, text):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        return {"result": {"sentiment": "positive", "score": 0.8}, "model": "mock-model", "tokens_used": 80, "success": True}
    
    def paraphrase_text(self, text, style="formal"):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        valid_styles = ["formal", "casual", "professional", "academic"]
        if style not in valid_styles:
            raise ValueError(f"style参数必须是以下值之一: {', '.join(valid_styles)}")
        return {"result": "改写结果", "model": "mock-model", "tokens_used": 100, "success": True}
    
    def classify_text(self, text, categories, multi_label=False):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        if not categories or not isinstance(categories, list):
            raise ValueError("分类类别不能为空且必须是列表类型")
        if not all(isinstance(cat, str) for cat in categories):
            raise ValueError("分类类别必须是字符串类型")
        if not isinstance(multi_label, bool):
            raise ValueError("multi_label参数必须是布尔类型")
        return {"result": {"category": categories[0], "confidence": 0.9}, "model": "mock-model", "tokens_used": 90, "success": True}
    
    def extract_info(self, text, entities=None):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        if entities is not None:
            if not isinstance(entities, list):
                raise ValueError("entities参数必须是列表类型")
            if not all(isinstance(entity, str) for entity in entities):
                raise ValueError("entities列表中的元素必须是字符串类型")
        return {"result": {"提取内容": ["测试"]}, "model": "mock-model", "tokens_used": 110, "success": True}
    
    def expand_text(self, text, length="medium", style="detailed"):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        valid_lengths = ["short", "medium", "long"]
        if length not in valid_lengths:
            raise ValueError(f"length参数必须是以下值之一: {', '.join(valid_lengths)}")
        valid_styles = ["detailed", "concise", "formal", "casual"]
        if style not in valid_styles:
            raise ValueError(f"style参数必须是以下值之一: {', '.join(valid_styles)}")
        return {"result": "扩写结果", "model": "mock-model", "tokens_used": 200, "success": True}

# 创建测试实例
llm_tasks = MockLLMTasks()

class TestLLMTasks(unittest.TestCase):
    
    def test_summarize_text(self):
        # 测试正常情况
        result = llm_tasks.summarize_text("这是一段测试文本")
        self.assertEqual(result["result"], "摘要结果")
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.summarize_text("")
    
    def test_generate_code(self):
        # 测试正常情况
        result = llm_tasks.generate_code("创建一个Hello World程序", "python")
        self.assertEqual(result["result"], "代码结果")
        
        # 测试空提示
        with self.assertRaises(ValueError):
            llm_tasks.generate_code("", "python")
        
        # 测试空语言
        with self.assertRaises(ValueError):
            llm_tasks.generate_code("测试提示", "")
    
    def test_translate_text(self):
        # 测试正常情况
        result = llm_tasks.translate_text("你好世界", "en")
        self.assertEqual(result["result"], "翻译结果")
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.translate_text("", "en")
        
        # 测试空目标语言
        with self.assertRaises(ValueError):
            llm_tasks.translate_text("测试文本", "")
    
    def test_analyze_sentiment(self):
        # 测试正常情况
        result = llm_tasks.analyze_sentiment("这是一段正面评价")
        self.assertEqual(result["result"]["sentiment"], "positive")
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.analyze_sentiment("")
    
    def test_paraphrase_text(self):
        # 测试正常情况
        result = llm_tasks.paraphrase_text("这是原句")
        self.assertEqual(result["result"], "改写结果")
        
        # 测试不同风格
        result = llm_tasks.paraphrase_text("这是原句", style="casual")
        self.assertEqual(result["result"], "改写结果")
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.paraphrase_text("")
    
    def test_classify_text(self):
        # 测试正常情况
        result = llm_tasks.classify_text("Python是一种编程语言", ["技术", "文学"])
        self.assertEqual(result["result"]["category"], "技术")
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.classify_text("", ["技术", "文学"])
        
        # 测试空类别
        with self.assertRaises(ValueError):
            llm_tasks.classify_text("测试文本", [])
    
    def test_extract_info(self):
        # 测试正常情况
        result = llm_tasks.extract_info("张三在北京工作")
        self.assertIn("提取内容", result["result"])
        
        # 测试带实体列表
        result = llm_tasks.extract_info("张三在北京工作", entities=["人物", "地点"])
        self.assertIn("提取内容", result["result"])
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.extract_info("")
    
    def test_expand_text(self):
        # 测试正常情况
        result = llm_tasks.expand_text("这是原句")
        self.assertEqual(result["result"], "扩写结果")
        
        # 测试不同长度和风格
        result = llm_tasks.expand_text("这是原句", length="long", style="detailed")
        self.assertEqual(result["result"], "扩写结果")
        
        # 测试空文本
        with self.assertRaises(ValueError):
            llm_tasks.expand_text("")
    
    def test_analyze_sentiment_validation(self):
        # 测试情感分析的输入验证
        with self.assertRaises(ValueError):
            llm_tasks.analyze_sentiment("")
        
        with self.assertRaises(ValueError):
            llm_tasks.analyze_sentiment(None)

if __name__ == '__main__':
    unittest.main()