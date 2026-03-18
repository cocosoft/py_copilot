"""
文档处理进度追踪服务

提供实时的文档处理进度反馈，支持WebSocket或轮询查询
"""
import time
import threading
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__)


class ProcessingProgressService:
    """文档处理进度追踪服务"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._progress_map: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._initialized = True

        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        logger.info("文档处理进度追踪服务初始化完成")

    def start_processing(self, document_id: str, total_steps: int = 6, document_name: str = None) -> None:
        """
        开始处理文档，初始化进度

        @param document_id: 文档ID
        @param total_steps: 总处理步骤数
        @param document_name: 文档名称
        """
        with self._lock:
            self._progress_map[document_id] = {
                "document_id": document_id,
                "document_name": document_name or f"文档 {document_id}",
                "status": "processing",
                "current_step": 0,
                "total_steps": total_steps,
                "step_name": "初始化",
                "progress_percent": 0,
                "start_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat(),
                "message": "开始处理文档",
                "details": {}
            }
        logger.info(f"文档处理进度初始化: {document_id} - {document_name}")

    def _broadcast_progress_via_websocket(self, document_id: str, progress: Dict[str, Any]):
        """
        通过WebSocket广播进度更新

        @param document_id: 文档ID
        @param progress: 进度信息
        """
        try:
            # 导入WebSocket消息处理器
            from app.websocket.message_handler import message_handler

            # 检查是否有订阅者，避免不必要的广播
            subscriber_count = len(message_handler.document_progress_subscriptions.get(int(document_id), set()))
            if subscriber_count == 0:
                logger.debug(f"文档 {document_id} 没有WebSocket订阅者，跳过广播")
                return

            # 获取文档名称
            document_name = progress.get("document_name", f"文档 {document_id}")

            # 获取当前事件循环
            try:
                loop = asyncio.get_running_loop()
                # 在主进程中，使用asyncio创建任务
                asyncio.create_task(message_handler.broadcast_document_progress(
                    document_id=int(document_id),
                    status=progress["status"],
                    progress_percent=progress["progress_percent"],
                    step_name=progress["step_name"],
                    message=progress["message"],
                    document_name=document_name,
                    details=progress.get("details")
                ))
                logger.debug(f"已广播文档 {document_id} 进度到 {subscriber_count} 个订阅者")
            except RuntimeError:
                # 没有运行的事件循环（可能在Celery任务中）
                # 使用线程来运行异步任务
                def run_async_broadcast():
                    try:
                        # 创建新的事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # 运行异步广播
                        loop.run_until_complete(message_handler.broadcast_document_progress(
                            document_id=int(document_id),
                            status=progress["status"],
                            progress_percent=progress["progress_percent"],
                            step_name=progress["step_name"],
                            message=progress["message"],
                            document_name=document_name,
                            details=progress.get("details")
                        ))
                        loop.close()
                        logger.debug(f"已在后台线程广播文档 {document_id} 进度")
                    except Exception as e:
                        logger.debug(f"后台线程广播进度失败: {e}")

                # 启动后台线程
                thread = threading.Thread(target=run_async_broadcast, daemon=True)
                thread.start()
                logger.debug(f"已启动后台线程广播文档 {document_id} 进度")
        except Exception as e:
            logger.debug(f"WebSocket广播进度失败（可能无订阅者）: {e}")

    def update_progress(self, document_id: str, step: int, step_name: str,
                       message: str, details: Optional[Dict] = None) -> None:
        """
        更新处理进度

        @param document_id: 文档ID
        @param step: 当前步骤（从1开始）
        @param step_name: 步骤名称
        @param message: 进度消息
        @param details: 详细信息
        """
        with self._lock:
            if document_id not in self._progress_map:
                return

            progress = self._progress_map[document_id]
            progress["current_step"] = step
            progress["step_name"] = step_name
            progress["message"] = message
            progress["update_time"] = datetime.now().isoformat()

            # 计算进度百分比
            # 优先使用传入的details中的progress_percent，否则使用步骤进度
            total_steps = progress.get("total_steps", 6)
            if details and "progress_percent" in details:
                progress["progress_percent"] = details["progress_percent"]
            else:
                progress["progress_percent"] = min(int((step / total_steps) * 100), 99)

            if details:
                progress["details"].update(details)

            # 复制进度信息用于WebSocket广播
            progress_copy = progress.copy()

        logger.info(f"文档处理进度更新: {document_id} - 步骤 {step}/{total_steps}: {step_name}")

        # 通过WebSocket广播进度
        self._broadcast_progress_via_websocket(document_id, progress_copy)

    def complete_processing(self, document_id: str, success: bool = True,
                           result: Optional[Dict] = None) -> None:
        """
        完成文档处理

        @param document_id: 文档ID
        @param success: 是否成功
        @param result: 处理结果
        """
        with self._lock:
            if document_id not in self._progress_map:
                return

            progress = self._progress_map[document_id]
            progress["status"] = "completed" if success else "failed"
            progress["progress_percent"] = 100
            progress["current_step"] = progress.get("total_steps", 6)
            progress["step_name"] = "完成" if success else "失败"
            progress["message"] = "文档处理完成" if success else f"处理失败: {result.get('error', '未知错误') if result else '未知错误'}"
            progress["end_time"] = datetime.now().isoformat()
            progress["update_time"] = datetime.now().isoformat()

            if result:
                progress["result"] = result

            # 复制进度信息用于WebSocket广播
            progress_copy = progress.copy()

        logger.info(f"文档处理完成: {document_id} - {'成功' if success else '失败'}")

        # 通过WebSocket广播完成状态
        self._broadcast_progress_via_websocket(document_id, progress_copy)

    def get_progress(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档处理进度

        @param document_id: 文档ID
        @returns: 进度信息，如果不存在返回None
        """
        with self._lock:
            progress = self._progress_map.get(document_id)
            if progress:
                return progress.copy()
            return None

    def _cleanup_loop(self):
        """清理过期的进度记录"""
        while True:
            try:
                time.sleep(300)  # 每5分钟清理一次
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"清理进度记录失败: {e}")

    def _cleanup_expired(self):
        """清理超过1小时的过期记录"""
        expired_time = datetime.now() - timedelta(hours=1)
        with self._lock:
            expired_ids = [
                doc_id for doc_id, progress in self._progress_map.items()
                if datetime.fromisoformat(progress["update_time"]) < expired_time
            ]
            for doc_id in expired_ids:
                del self._progress_map[doc_id]

        if expired_ids:
            logger.info(f"清理了 {len(expired_ids)} 条过期的进度记录")


# 全局实例
processing_progress_service = ProcessingProgressService()
