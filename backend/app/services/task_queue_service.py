"""任务队列服务模块"""
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from uuid import uuid4

from app.core.microservices import get_message_queue, MessageQueue
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class TaskQueueService:
    """任务队列服务类"""
    
    def __init__(self, message_queue: Optional[MessageQueue] = None):
        """
        初始化任务队列服务
        
        Args:
            message_queue: 消息队列实例
        """
        self.message_queue = message_queue or get_message_queue()
        self.task_handlers: Dict[str, Callable] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}
    
    async def submit_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        提交任务到队列
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            
        Returns:
            任务ID
        """
        task_id = str(uuid4())
        
        # 构建任务消息
        task_message = {
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data,
            "status": "pending",
            "created_at": asyncio.get_event_loop().time()
        }
        
        # 发布任务到消息队列
        success = await self.message_queue.publish_message("task_queue", task_message)
        
        if success:
            logger.info(f"任务提交成功，任务ID: {task_id}, 任务类型: {task_type}")
            return task_id
        else:
            logger.error(f"任务提交失败，任务ID: {task_id}, 任务类型: {task_type}")
            raise Exception("任务提交失败")
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        if task_id in self.task_results:
            return self.task_results[task_id]
        else:
            # 从Redis获取任务结果
            redis_client = get_redis()
            result_key = f"task_result:{task_id}"
            result_data = await redis_client.get(result_key)
            
            if result_data:
                result = json.loads(result_data)
                self.task_results[task_id] = result
                return result
            else:
                return {
                    "task_id": task_id,
                    "status": "pending",
                    "result": None,
                    "error": None
                }
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 任务处理函数
        """
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器，任务类型: {task_type}")
    
    async def process_task(self, task_data: Dict[str, Any]):
        """
        处理任务
        
        Args:
            task_data: 任务数据
        """
        task_id = task_data["task_id"]
        task_type = task_data["task_type"]
        task_payload = task_data["task_data"]
        
        logger.info(f"开始处理任务，任务ID: {task_id}, 任务类型: {task_type}")
        
        # 更新任务状态
        redis_client = get_redis()
        result_key = f"task_result:{task_id}"
        
        # 保存任务状态
        await redis_client.set(
            result_key,
            json.dumps({
                "task_id": task_id,
                "task_type": task_type,
                "status": "processing",
                "result": None,
                "error": None,
                "started_at": asyncio.get_event_loop().time()
            })
        )
        
        try:
            # 检查任务处理器是否存在
            if task_type not in self.task_handlers:
                raise Exception(f"未知的任务类型: {task_type}")
            
            # 执行任务处理
            handler = self.task_handlers[task_type]
            result = await handler(task_payload)
            
            # 更新任务结果
            final_result = {
                "task_id": task_id,
                "task_type": task_type,
                "status": "completed",
                "result": result,
                "error": None,
                "started_at": asyncio.get_event_loop().time(),
                "completed_at": asyncio.get_event_loop().time()
            }
            
            # 保存任务结果
            await redis_client.set(result_key, json.dumps(final_result))
            self.task_results[task_id] = final_result
            
            logger.info(f"任务处理完成，任务ID: {task_id}, 任务类型: {task_type}")
            
        except Exception as e:
            logger.error(f"任务处理失败，任务ID: {task_id}, 错误: {str(e)}")
            
            # 更新任务错误信息
            error_result = {
                "task_id": task_id,
                "task_type": task_type,
                "status": "failed",
                "result": None,
                "error": str(e),
                "started_at": asyncio.get_event_loop().time(),
                "completed_at": asyncio.get_event_loop().time()
            }
            
            # 保存任务错误信息
            await redis_client.set(result_key, json.dumps(error_result))
            self.task_results[task_id] = error_result
    
    async def start_worker(self):
        """
        启动任务处理工作器
        """
        logger.info("启动任务处理工作器")
        
        # 订阅任务队列
        await self.message_queue.subscribe_to_channel("task_queue", self.process_task)


# 创建全局任务队列服务实例
_task_queue_service: Optional[TaskQueueService] = None

def get_task_queue_service() -> TaskQueueService:
    """获取任务队列服务实例"""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()
    return _task_queue_service
