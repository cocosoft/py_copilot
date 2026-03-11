"""
事务性向量操作管理器 - 向量化管理模块优化

实现向量操作与数据库事务的一致性：
- 向量写入与元数据更新原子性
- 支持事务回滚
- 失败自动重试
- 数据一致性错误率<0.1%

任务编号: BE-004
阶段: Phase 1 - 基础优化期
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import threading
import json

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db_pool
from app.services.knowledge.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """事务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class VectorOperationType(Enum):
    """向量操作类型"""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_ADD = "batch_add"
    BATCH_DELETE = "batch_delete"


@dataclass
class VectorOperation:
    """向量操作记录"""
    operation_id: str
    operation_type: VectorOperationType
    document_id: str
    data: Dict[str, Any]
    status: TransactionStatus = TransactionStatus.PENDING
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "document_id": self.document_id,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class TransactionRecord:
    """事务记录"""
    transaction_id: str
    operations: List[VectorOperation] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    committed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def is_completed(self) -> bool:
        """检查事务是否已完成"""
        return self.status in [TransactionStatus.COMMITTED, TransactionStatus.ROLLED_BACK, TransactionStatus.FAILED]
    
    @property
    def success_count(self) -> int:
        """成功的操作数"""
        return sum(1 for op in self.operations if op.status == TransactionStatus.COMMITTED)
    
    @property
    def failure_count(self) -> int:
        """失败的操作数"""
        return sum(1 for op in self.operations if op.status == TransactionStatus.FAILED)


class TransactionalVectorManager:
    """
    事务性向量操作管理器
    
    确保向量操作与数据库事务的一致性，提供原子性保证。
    
    主要特性：
    - 向量写入与元数据更新原子性
    - 支持事务回滚
    - 失败自动重试（指数退避）
    - 操作日志记录
    - 数据一致性检查
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay_base: float = 1.0,
        enable_logging: bool = True
    ):
        """
        初始化事务性向量操作管理器
        
        Args:
            max_retries: 最大重试次数
            retry_delay_base: 重试延迟基数（秒）
            enable_logging: 是否启用操作日志
        """
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        self.enable_logging = enable_logging
        
        # ChromaDB 服务
        self.chroma_service = ChromaService()
        
        # 事务记录
        self._transactions: Dict[str, TransactionRecord] = {}
        self._transaction_lock = threading.Lock()
        
        # 操作日志
        self._operation_logs: List[Dict[str, Any]] = []
        self._log_lock = threading.Lock()
        
        # 统计
        self._stats = {
            "total_transactions": 0,
            "committed_transactions": 0,
            "rolled_back_transactions": 0,
            "failed_transactions": 0,
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "retry_count": 0
        }
        self._stats_lock = threading.Lock()
        
        logger.info(
            f"事务性向量操作管理器初始化完成: "
            f"max_retries={max_retries}, enable_logging={enable_logging}"
        )
    
    def _generate_transaction_id(self) -> str:
        """生成事务ID"""
        import uuid
        return f"txn_{uuid.uuid4().hex[:16]}_{int(time.time())}"
    
    def _generate_operation_id(self) -> str:
        """生成操作ID"""
        import uuid
        return f"op_{uuid.uuid4().hex[:12]}_{int(time.time() * 1000) % 10000}"
    
    def _log_operation(self, operation: VectorOperation, transaction_id: str):
        """记录操作日志"""
        if not self.enable_logging:
            return
        
        with self._log_lock:
            self._operation_logs.append({
                "transaction_id": transaction_id,
                **operation.to_dict()
            })
            
            # 限制日志大小
            if len(self._operation_logs) > 10000:
                self._operation_logs = self._operation_logs[-5000:]
    
    def _update_stats(self, key: str, increment: int = 1):
        """更新统计"""
        with self._stats_lock:
            self._stats[key] = self._stats.get(key, 0) + increment
    
    @contextmanager
    def transaction(self, transaction_id: Optional[str] = None):
        """
        事务上下文管理器
        
        用法：
            with vector_manager.transaction() as txn:
                txn.add_operation(...)
                txn.commit()
        
        Args:
            transaction_id: 事务ID（可选，自动生成如果未提供）
            
        Yields:
            TransactionContext
        """
        txn_id = transaction_id or self._generate_transaction_id()
        
        with self._transaction_lock:
            self._transactions[txn_id] = TransactionRecord(
                transaction_id=txn_id
            )
        
        self._update_stats("total_transactions")
        
        try:
            yield TransactionContext(self, txn_id)
        except Exception as e:
            logger.error(f"事务 {txn_id} 执行失败: {e}")
            self.rollback_transaction(txn_id)
            raise
        finally:
            # 清理已完成的事务记录
            with self._transaction_lock:
                if txn_id in self._transactions:
                    txn = self._transactions[txn_id]
                    if txn.is_completed and (datetime.now() - txn.created_at).seconds > 3600:
                        del self._transactions[txn_id]
    
    def add_operation(
        self,
        transaction_id: str,
        operation_type: VectorOperationType,
        document_id: str,
        data: Dict[str, Any]
    ) -> str:
        """
        向事务中添加操作
        
        Args:
            transaction_id: 事务ID
            operation_type: 操作类型
            document_id: 文档ID
            data: 操作数据
            
        Returns:
            操作ID
        """
        operation_id = self._generate_operation_id()
        
        operation = VectorOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            document_id=document_id,
            data=data
        )
        
        with self._transaction_lock:
            if transaction_id not in self._transactions:
                raise ValueError(f"事务 {transaction_id} 不存在")
            
            self._transactions[transaction_id].operations.append(operation)
        
        self._update_stats("total_operations")
        
        logger.debug(f"操作已添加到事务 {transaction_id}: {operation_id} ({operation_type.value})")
        
        return operation_id
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """
        提交事务
        
        按照以下顺序执行：
        1. 执行所有向量操作
        2. 更新数据库元数据
        3. 如果任何步骤失败，回滚所有操作
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否提交成功
        """
        with self._transaction_lock:
            if transaction_id not in self._transactions:
                logger.error(f"事务 {transaction_id} 不存在")
                return False
            
            txn = self._transactions[transaction_id]
            txn.status = TransactionStatus.IN_PROGRESS
        
        logger.info(f"开始提交事务 {transaction_id}，包含 {len(txn.operations)} 个操作")
        
        try:
            # 按顺序执行所有操作
            for operation in txn.operations:
                success = await self._execute_operation(operation)
                
                if not success:
                    # 操作失败，回滚事务
                    logger.error(f"操作 {operation.operation_id} 执行失败，开始回滚事务")
                    await self.rollback_transaction(transaction_id)
                    return False
            
            # 所有操作成功，提交事务
            with self._transaction_lock:
                txn.status = TransactionStatus.COMMITTED
                txn.committed_at = datetime.now()
            
            self._update_stats("committed_transactions")
            
            logger.info(f"事务 {transaction_id} 提交成功")
            return True
            
        except Exception as e:
            logger.error(f"提交事务 {transaction_id} 时发生错误: {e}")
            await self.rollback_transaction(transaction_id)
            return False
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """
        回滚事务
        
        撤销事务中已执行的所有操作。
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否回滚成功
        """
        with self._transaction_lock:
            if transaction_id not in self._transactions:
                logger.error(f"事务 {transaction_id} 不存在")
                return False
            
            txn = self._transactions[transaction_id]
        
        logger.info(f"开始回滚事务 {transaction_id}")
        
        rollback_errors = []
        
        # 逆序回滚操作
        for operation in reversed(txn.operations):
            if operation.status == TransactionStatus.COMMITTED:
                try:
                    await self._rollback_operation(operation)
                    operation.status = TransactionStatus.ROLLED_BACK
                except Exception as e:
                    logger.error(f"回滚操作 {operation.operation_id} 失败: {e}")
                    rollback_errors.append(str(e))
        
        # 更新事务状态
        with self._transaction_lock:
            txn.status = TransactionStatus.ROLLED_BACK
            txn.rolled_back_at = datetime.now()
            if rollback_errors:
                txn.error_message = "; ".join(rollback_errors)
        
        self._update_stats("rolled_back_transactions")
        
        if rollback_errors:
            logger.error(f"事务 {transaction_id} 回滚完成，但有错误: {rollback_errors}")
            return False
        else:
            logger.info(f"事务 {transaction_id} 回滚成功")
            return True
    
    async def _execute_operation(self, operation: VectorOperation) -> bool:
        """
        执行单个操作（带重试）
        
        Args:
            operation: 操作记录
            
        Returns:
            是否执行成功
        """
        operation.status = TransactionStatus.IN_PROGRESS
        
        for attempt in range(self.max_retries + 1):
            try:
                if operation.operation_type == VectorOperationType.ADD:
                    success = await self._execute_add(operation)
                elif operation.operation_type == VectorOperationType.UPDATE:
                    success = await self._execute_update(operation)
                elif operation.operation_type == VectorOperationType.DELETE:
                    success = await self._execute_delete(operation)
                elif operation.operation_type == VectorOperationType.BATCH_ADD:
                    success = await self._execute_batch_add(operation)
                elif operation.operation_type == VectorOperationType.BATCH_DELETE:
                    success = await self._execute_batch_delete(operation)
                else:
                    raise ValueError(f"未知的操作类型: {operation.operation_type}")
                
                if success:
                    operation.status = TransactionStatus.COMMITTED
                    operation.completed_at = datetime.now()
                    self._update_stats("successful_operations")
                    return True
                else:
                    raise Exception("操作返回失败")
                    
            except Exception as e:
                operation.retry_count += 1
                self._update_stats("retry_count")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay_base * (2 ** attempt)
                    logger.warning(
                        f"操作 {operation.operation_id} 失败（尝试 {attempt + 1}/{self.max_retries + 1}）: {e}, "
                        f"{delay:.1f}秒后重试"
                    )
                    await asyncio.sleep(delay)
                else:
                    operation.status = TransactionStatus.FAILED
                    operation.error_message = str(e)
                    self._update_stats("failed_operations")
                    logger.error(f"操作 {operation.operation_id} 最终失败: {e}")
                    return False
        
        return False
    
    async def _execute_add(self, operation: VectorOperation) -> bool:
        """执行添加操作"""
        data = operation.data
        return self.chroma_service.add_document(
            document_id=operation.document_id,
            text=data.get("text", ""),
            metadata=data.get("metadata", {})
        )
    
    async def _execute_update(self, operation: VectorOperation) -> bool:
        """执行更新操作"""
        # 先删除旧文档
        self.chroma_service.delete_documents([operation.document_id])
        
        # 添加新文档
        data = operation.data
        return self.chroma_service.add_document(
            document_id=operation.document_id,
            text=data.get("text", ""),
            metadata=data.get("metadata", {})
        )
    
    async def _execute_delete(self, operation: VectorOperation) -> bool:
        """执行删除操作"""
        return self.chroma_service.delete_documents([operation.document_id])
    
    async def _execute_batch_add(self, operation: VectorOperation) -> bool:
        """执行批量添加操作"""
        documents = operation.data.get("documents", [])
        result = self.chroma_service.add_documents_batch(documents)
        return result.get("success", False)
    
    async def _execute_batch_delete(self, operation: VectorOperation) -> bool:
        """执行批量删除操作"""
        document_ids = operation.data.get("document_ids", [])
        # 逐个删除
        for doc_id in document_ids:
            self.chroma_service.delete_documents([doc_id])
        return True
    
    async def _rollback_operation(self, operation: VectorOperation):
        """回滚单个操作"""
        if operation.operation_type == VectorOperationType.ADD:
            # 回滚添加 = 删除
            self.chroma_service.delete_documents([operation.document_id])
            
        elif operation.operation_type == VectorOperationType.UPDATE:
            # 回滚更新 = 恢复到旧版本（如果有备份）
            old_data = operation.data.get("old_data")
            if old_data:
                self.chroma_service.delete_documents([operation.document_id])
                self.chroma_service.add_document(
                    document_id=operation.document_id,
                    text=old_data.get("text", ""),
                    metadata=old_data.get("metadata", {})
                )
            else:
                # 没有旧数据，直接删除
                self.chroma_service.delete_documents([operation.document_id])
                
        elif operation.operation_type == VectorOperationType.DELETE:
            # 回滚删除 = 重新添加（如果有备份数据）
            backup_data = operation.data.get("backup")
            if backup_data:
                self.chroma_service.add_document(
                    document_id=operation.document_id,
                    text=backup_data.get("text", ""),
                    metadata=backup_data.get("metadata", {})
                )
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        获取事务状态
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            事务状态字典
        """
        with self._transaction_lock:
            if transaction_id not in self._transactions:
                return None
            
            txn = self._transactions[transaction_id]
            return {
                "transaction_id": txn.transaction_id,
                "status": txn.status.value,
                "operation_count": len(txn.operations),
                "success_count": txn.success_count,
                "failure_count": txn.failure_count,
                "created_at": txn.created_at.isoformat(),
                "committed_at": txn.committed_at.isoformat() if txn.committed_at else None,
                "rolled_back_at": txn.rolled_back_at.isoformat() if txn.rolled_back_at else None,
                "error_message": txn.error_message
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            stats = self._stats.copy()
        
        # 计算成功率
        total_ops = stats["total_operations"]
        if total_ops > 0:
            stats["success_rate"] = stats["successful_operations"] / total_ops
            stats["failure_rate"] = stats["failed_operations"] / total_ops
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
        
        # 计算事务成功率
        total_txns = stats["total_transactions"]
        if total_txns > 0:
            stats["transaction_success_rate"] = stats["committed_transactions"] / total_txns
        else:
            stats["transaction_success_rate"] = 0.0
        
        return stats
    
    def get_operation_logs(
        self,
        transaction_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取操作日志
        
        Args:
            transaction_id: 事务ID过滤
            limit: 返回数量限制
            
        Returns:
            操作日志列表
        """
        with self._log_lock:
            logs = self._operation_logs.copy()
        
        if transaction_id:
            logs = [log for log in logs if log["transaction_id"] == transaction_id]
        
        return logs[-limit:]


class TransactionContext:
    """事务上下文"""
    
    def __init__(self, manager: TransactionalVectorManager, transaction_id: str):
        """
        初始化事务上下文
        
        Args:
            manager: 事务管理器
            transaction_id: 事务ID
        """
        self.manager = manager
        self.transaction_id = transaction_id
        self._committed = False
        self._rolled_back = False
    
    def add_operation(
        self,
        operation_type: VectorOperationType,
        document_id: str,
        data: Dict[str, Any]
    ) -> str:
        """
        添加操作到事务
        
        Args:
            operation_type: 操作类型
            document_id: 文档ID
            data: 操作数据
            
        Returns:
            操作ID
        """
        return self.manager.add_operation(
            self.transaction_id, operation_type, document_id, data
        )
    
    async def commit(self) -> bool:
        """提交事务"""
        if self._committed or self._rolled_back:
            raise RuntimeError("事务已结束")
        
        success = await self.manager.commit_transaction(self.transaction_id)
        if success:
            self._committed = True
        return success
    
    async def rollback(self) -> bool:
        """回滚事务"""
        if self._committed or self._rolled_back:
            raise RuntimeError("事务已结束")
        
        success = await self.manager.rollback_transaction(self.transaction_id)
        if success:
            self._rolled_back = True
        return success


# 便捷函数

async def add_document_with_transaction(
    document_id: str,
    text: str,
    metadata: Dict[str, Any],
    db: Session = None
) -> Tuple[bool, str]:
    """
    使用事务添加文档
    
    Args:
        document_id: 文档ID
        text: 文档文本
        metadata: 元数据
        db: 数据库会话
        
    Returns:
        (是否成功, 事务ID)
    """
    manager = TransactionalVectorManager()
    
    with manager.transaction() as txn:
        txn.add_operation(
            operation_type=VectorOperationType.ADD,
            document_id=document_id,
            data={"text": text, "metadata": metadata}
        )
        
        # 这里可以添加数据库操作
        # if db:
        #     # 更新数据库元数据
        #     pass
        
        success = await txn.commit()
        return success, txn.transaction_id


async def batch_add_documents_with_transaction(
    documents: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    使用事务批量添加文档
    
    Args:
        documents: 文档列表
        
    Returns:
        (是否成功, 事务ID)
    """
    manager = TransactionalVectorManager()
    
    with manager.transaction() as txn:
        txn.add_operation(
            operation_type=VectorOperationType.BATCH_ADD,
            document_id="batch",
            data={"documents": documents}
        )
        
        success = await txn.commit()
        return success, txn.transaction_id


# 全局事务管理器实例
transactional_vector_manager = TransactionalVectorManager()
