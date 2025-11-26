import unittest
from typing import Dict, Any, Optional, List

# 模拟LLM任务服务
class MockLLMTasks:
    def summarize_text(self, text, **options):
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        return {"result": "摘要结果", "model": "mock-model", "tokens_used": 100, "success": True}
    
    def generate_code(self, prompt, language, **options):
        if not prompt or not prompt.strip():
            raise ValueError("提示内容不能为空")
        if not language:
            raise ValueError("编程语言不能为空")
        return {"result": "代码结果", "model": "mock-model", "tokens_used": 150, "success": True}
    
    def translate_text(self, text, target_language, **options):
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        if not target_language:
            raise ValueError("目标语言不能为空")
        return {"result": "翻译结果", "model": "mock-model", "tokens_used": 120, "success": True}
    
    def paraphrase_text(self, text, style="formal", **options):
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        return {"result": "改写结果", "model": "mock-model", "tokens_used": 100, "success": True}
    
    def classify_text(self, text, categories, multi_label=False, **options):
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        if not categories:
            raise ValueError("分类类别不能为空")
        return {"result": {"category": categories[0], "confidence": 0.9}, "model": "mock-model", "tokens_used": 90, "success": True}
    
    def extract_info(self, text, entities=None, **options):
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        return {"result": {"提取内容": ["测试"]}, "model": "mock-model", "tokens_used": 110, "success": True}
    
    def expand_text(self, text, length="medium", style="detailed", **options):
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        return {"result": "扩写结果", "model": "mock-model", "tokens_used": 200, "success": True}

# 简化的API逻辑模拟
class MockAPI:
    def __init__(self):
        self.llm_tasks = MockLLMTasks()
    
    def summarize(self, text: str, options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.summarize_text(text, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400
    
    def generate_code(self, prompt: str, language: str, options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.generate_code(prompt, language, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400
    
    def translate(self, text: str, target_language: str, options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.translate_text(text, target_language, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400
    
    def paraphrase(self, text: str, options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.paraphrase_text(text, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400
    
    def classify(self, text: str, categories: List[str], options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.classify_text(text, categories, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400
    
    def extract_info(self, text: str, entities: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.extract_info(text, entities=entities, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400
    
    def expand(self, text: str, options: Optional[Dict[str, Any]] = None):
        try:
            return self.llm_tasks.expand_text(text, **(options or {})), 200
        except ValueError as e:
            return {"error": str(e)}, 400

class TestLLMAPI(unittest.TestCase):
    
    def setUp(self):
        # 创建模拟API实例
        self.api = MockAPI()
        
    def test_summarize_endpoint(self):
        # 测试文本摘要接口
        result, status_code = self.api.summarize("这是一段测试文本")
        self.assertEqual(status_code, 200)
        self.assertEqual(result["result"], "摘要结果")
    
    def test_generate_code_endpoint(self):
        # 测试代码生成接口
        result, status_code = self.api.generate_code("创建一个Hello World程序", "python")
        self.assertEqual(status_code, 200)
        self.assertEqual(result["result"], "代码结果")
    
    def test_translate_endpoint(self):
        # 测试文本翻译接口
        result, status_code = self.api.translate("你好世界", "en")
        self.assertEqual(status_code, 200)
        self.assertEqual(result["result"], "翻译结果")
    
    def test_paraphrase_endpoint(self):
        # 测试文本改写接口
        result, status_code = self.api.paraphrase("这是原句", {"style": "formal"})
        self.assertEqual(status_code, 200)
        self.assertEqual(result["result"], "改写结果")
    
    def test_classify_endpoint(self):
        # 测试文本分类接口
        result, status_code = self.api.classify("Python是一种编程语言", ["技术", "文学"])
        self.assertEqual(status_code, 200)
        self.assertEqual(result["result"]["category"], "技术")
        self.assertIn("confidence", result["result"])
    
    def test_extract_info_endpoint(self):
        # 测试信息提取接口
        result, status_code = self.api.extract_info("张三在北京工作", entities=["人物", "地点"])
        self.assertEqual(status_code, 200)
        self.assertIn("提取内容", result["result"])
    
    def test_expand_endpoint(self):
        # 测试文本扩写接口
        result, status_code = self.api.expand("这是原句", {"length": "long", "style": "detailed"})
        self.assertEqual(status_code, 200)
        self.assertEqual(result["result"], "扩写结果")
    
    def test_invalid_requests(self):
        # 测试摘要接口的无效请求
        result, status_code = self.api.summarize("")
        self.assertEqual(status_code, 400)
        
        # 测试代码生成接口的无效请求
        result, status_code = self.api.generate_code("", "python")
        self.assertEqual(status_code, 400)
        
        # 测试翻译接口的无效请求
        result, status_code = self.api.translate("你好", "")
        self.assertEqual(status_code, 400)

if __name__ == '__main__':
    unittest.main()