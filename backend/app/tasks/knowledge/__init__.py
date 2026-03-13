"""
知识库处理任务模块

包含文档处理、实体提取、实体对齐等Celery任务
"""

from .document_processing import (
    process_document_task,
    batch_process_documents_task,
    cleanup_old_processing_results
)

__all__ = [
    'process_document_task',
    'batch_process_documents_task',
    'cleanup_old_processing_results'
]
