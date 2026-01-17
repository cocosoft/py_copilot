"""异步LLM任务处理服务模块"""
import asyncio
import logging
from typing import Dict, Any, Optional

from app.services.llm_tasks import LLMTasks
from app.services.task_queue_service import get_task_queue_service, TaskQueueService

logger = logging.getLogger(__name__)


class AsyncLLMTasks:
    """异步LLM任务处理服务类"""
    
    def __init__(self, llm_service=None):
        """
        初始化异步LLM任务处理服务
        
        Args:
            llm_service: LLM服务实例
        """
        self.llm_tasks = LLMTasks(llm_service)
        self.task_queue_service: TaskQueueService = get_task_queue_service()
        
        # 注册任务处理器
        self._register_task_handlers()
    
    def _register_task_handlers(self):
        """
        注册任务处理器
        """
        self.task_queue_service.register_task_handler("summarize_text", self._handle_summarize_text)
        self.task_queue_service.register_task_handler("generate_code", self._handle_generate_code)
        self.task_queue_service.register_task_handler("translate_text", self._handle_translate_text)
        self.task_queue_service.register_task_handler("analyze_sentiment", self._handle_analyze_sentiment)
        self.task_queue_service.register_task_handler("generate_ideas", self._handle_generate_ideas)
    
    async def submit_summarize_task(self, text: str, **options) -> str:
        """
        提交文本摘要任务
        
        Args:
            text: 需要摘要的文本
            options: 可选参数
            
        Returns:
            任务ID
        """
        task_data = {
            "text": text,
            "options": options
        }
        
        return await self.task_queue_service.submit_task("summarize_text", task_data)
    
    async def submit_code_generation_task(self, text: str, **options) -> str:
        """
        提交代码生成任务
        
        Args:
            text: 代码生成的描述
            options: 可选参数
            
        Returns:
            任务ID
        """
        task_data = {
            "text": text,
            "options": options
        }
        
        return await self.task_queue_service.submit_task("generate_code", task_data)
    
    async def submit_translation_task(self, text: str, **options) -> str:
        """
        提交文本翻译任务
        
        Args:
            text: 需要翻译的文本
            options: 可选参数
            
        Returns:
            任务ID
        """
        task_data = {
            "text": text,
            "options": options
        }
        
        return await self.task_queue_service.submit_task("translate_text", task_data)
    
    async def submit_sentiment_analysis_task(self, text: str, **options) -> str:
        """
        提交情感分析任务
        
        Args:
            text: 需要分析情感的文本
            options: 可选参数
            
        Returns:
            任务ID
        """
        task_data = {
            "text": text,
            "options": options
        }
        
        return await self.task_queue_service.submit_task("analyze_sentiment", task_data)
    
    async def submit_ideas_generation_task(self, topic: str, **options) -> str:
        """
        提交创意生成任务
        
        Args:
            topic: 创意生成的主题
            options: 可选参数
            
        Returns:
            任务ID
        """
        task_data = {
            "topic": topic,
            "options": options
        }
        
        return await self.task_queue_service.submit_task("generate_ideas", task_data)
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        return await self.task_queue_service.get_task_result(task_id)
    
    async def _handle_summarize_text(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理文本摘要任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            任务结果
        """
        text = task_data.get("text", "")
        options = task_data.get("options", {})
        
        # 异步执行任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm_tasks.summarize_text(text, **options)
        )
        
        return result
    
    async def _handle_generate_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理代码生成任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            任务结果
        """
        text = task_data.get("text", "")
        options = task_data.get("options", {})
        
        # 异步执行任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm_tasks.generate_code(text, **options)
        )
        
        return result
    
    async def _handle_translate_text(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理文本翻译任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            任务结果
        """
        text = task_data.get("text", "")
        options = task_data.get("options", {})
        
        # 异步执行任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm_tasks.translate_text(text, **options)
        )
        
        return result
    
    async def _handle_analyze_sentiment(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理情感分析任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            任务结果
        """
        text = task_data.get("text", "")
        options = task_data.get("options", {})
        
        # 异步执行任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm_tasks.analyze_sentiment(text, **options)
        )
        
        return result
    
    async def _handle_generate_ideas(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理创意生成任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            任务结果
        """
        topic = task_data.get("topic", "")
        options = task_data.get("options", {})
        
        # 异步执行任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm_tasks.generate_ideas(topic, **options)
        )
        
        return result


# 创建全局异步LLM任务服务实例
async_llm_tasks_service = AsyncLLMTasks()
