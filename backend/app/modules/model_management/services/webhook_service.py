"""
Webhooks回调服务

提供模型管理相关的Webhooks回调功能，包括：
- 事件类型定义：模型创建、更新、删除、状态变更等
- 回调配置管理：支持多个回调URL
- 回调签名验证：确保回调安全性
- 回调失败重试：指数退避重试机制
"""

import logging
import hmac
import hashlib
import json
import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
import aiohttp

from app.models.base import Base
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Webhook事件类型枚举"""
    MODEL_CREATED = "model.created"           # 模型创建
    MODEL_UPDATED = "model.updated"           # 模型更新
    MODEL_DELETED = "model.deleted"           # 模型删除
    MODEL_STATUS_CHANGED = "model.status.changed"  # 模型状态变更
    PARAMETER_CREATED = "parameter.created"   # 参数创建
    PARAMETER_UPDATED = "parameter.updated"   # 参数更新
    PARAMETER_DELETED = "parameter.deleted"   # 参数删除
    PARAMETER_VERSION_CHANGED = "parameter.version.changed"  # 参数版本变更


@dataclass
class WebhookEvent:
    """Webhook事件"""
    event_type: WebhookEventType
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    model_id: Optional[int] = None
    user_id: Optional[int] = None


@dataclass
class WebhookDelivery:
    """Webhook投递记录"""
    delivery_id: str
    event_id: str
    webhook_id: int
    url: str
    status: str  # pending, delivered, failed
    http_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class WebhookConfig(Base):
    """Webhook配置数据库模型"""
    __tablename__ = "webhook_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255))  # 用于签名验证
    event_types = Column(JSON)  # 监听的事件类型列表
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=3)  # 最大重试次数
    retry_interval = Column(Integer, default=60)  # 重试间隔（秒）
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookDeliveryRecord(Base):
    """Webhook投递记录数据库模型"""
    __tablename__ = "webhook_delivery_records"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), nullable=False, index=True)
    webhook_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(Text)
    status = Column(String(20), nullable=False)  # pending, delivered, failed
    http_status = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)


class WebhookService:
    """
    Webhook服务类
    
    提供完整的Webhook管理功能，包括：
    - Webhook配置管理
    - 事件触发和分发
    - 回调签名验证
    - 失败重试机制
    """
    
    # 重试配置
    RETRY_CONFIG = {
        "max_attempts": 5,
        "base_delay": 60,  # 基础延迟（秒）
        "max_delay": 3600,  # 最大延迟（秒）
        "backoff_factor": 2,  # 退避因子
    }
    
    def __init__(self, db: Session):
        """
        初始化Webhook服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.redis_client = get_redis()
    
    # ==================== Webhook配置管理 ====================
    
    def create_webhook(
        self,
        name: str,
        url: str,
        event_types: List[str],
        created_by: int,
        secret: Optional[str] = None,
        retry_count: int = 3,
        retry_interval: int = 60
    ) -> WebhookConfig:
        """
        创建Webhook配置
        
        Args:
            name: Webhook名称
            url: 回调URL
            event_types: 监听的事件类型列表
            created_by: 创建者ID
            secret: 签名密钥（可选）
            retry_count: 最大重试次数
            retry_interval: 重试间隔（秒）
        
        Returns:
            Webhook配置对象
        """
        webhook = WebhookConfig(
            name=name,
            url=url,
            event_types=event_types,
            created_by=created_by,
            secret=secret,
            retry_count=retry_count,
            retry_interval=retry_interval,
            is_active=True
        )
        
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)
        
        logger.info(f"Webhook配置创建成功: ID={webhook.id}, Name={name}")
        
        return webhook
    
    def update_webhook(
        self,
        webhook_id: int,
        **kwargs
    ) -> Optional[WebhookConfig]:
        """
        更新Webhook配置
        
        Args:
            webhook_id: Webhook ID
            **kwargs: 更新字段
        
        Returns:
            更新后的Webhook配置，不存在时返回None
        """
        webhook = self.db.query(WebhookConfig).filter(
            WebhookConfig.id == webhook_id
        ).first()
        
        if not webhook:
            return None
        
        for key, value in kwargs.items():
            if hasattr(webhook, key):
                setattr(webhook, key, value)
        
        webhook.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(webhook)
        
        logger.info(f"Webhook配置更新成功: ID={webhook_id}")
        
        return webhook
    
    def delete_webhook(self, webhook_id: int) -> bool:
        """
        删除Webhook配置
        
        Args:
            webhook_id: Webhook ID
        
        Returns:
            是否删除成功
        """
        webhook = self.db.query(WebhookConfig).filter(
            WebhookConfig.id == webhook_id
        ).first()
        
        if not webhook:
            return False
        
        self.db.delete(webhook)
        self.db.commit()
        
        logger.info(f"Webhook配置删除成功: ID={webhook_id}")
        
        return True
    
    def get_webhook(self, webhook_id: int) -> Optional[WebhookConfig]:
        """
        获取Webhook配置
        
        Args:
            webhook_id: Webhook ID
        
        Returns:
            Webhook配置对象，不存在时返回None
        """
        return self.db.query(WebhookConfig).filter(
            WebhookConfig.id == webhook_id
        ).first()
    
    def get_active_webhooks(
        self,
        event_type: Optional[WebhookEventType] = None
    ) -> List[WebhookConfig]:
        """
        获取活动的Webhook配置列表
        
        Args:
            event_type: 事件类型过滤器（可选）
        
        Returns:
            Webhook配置列表
        """
        query = self.db.query(WebhookConfig).filter(
            WebhookConfig.is_active == True
        )
        
        if event_type:
            # 过滤监听指定事件类型的Webhook
            query = query.filter(
                WebhookConfig.event_types.contains([event_type.value])
            )
        
        return query.all()
    
    # ==================== 事件触发和分发 ====================
    
    async def trigger_event(
        self,
        event_type: WebhookEventType,
        data: Dict[str, Any],
        model_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List[WebhookDelivery]:
        """
        触发Webhook事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            model_id: 模型ID（可选）
            user_id: 用户ID（可选）
        
        Returns:
            投递记录列表
        """
        # 生成事件ID
        event_id = self._generate_event_id()
        
        # 创建事件对象
        event = WebhookEvent(
            event_type=event_type,
            event_id=event_id,
            timestamp=datetime.utcnow(),
            data=data,
            model_id=model_id,
            user_id=user_id
        )
        
        # 获取监听该事件的Webhook
        webhooks = self.get_active_webhooks(event_type)
        
        if not webhooks:
            logger.debug(f"没有Webhook监听事件: {event_type.value}")
            return []
        
        # 分发事件到所有监听的Webhook
        deliveries = []
        for webhook in webhooks:
            delivery = await self._deliver_event(event, webhook)
            deliveries.append(delivery)
        
        return deliveries
    
    async def _deliver_event(
        self,
        event: WebhookEvent,
        webhook: WebhookConfig
    ) -> WebhookDelivery:
        """
        投递事件到指定Webhook
        
        Args:
            event: 事件对象
            webhook: Webhook配置
        
        Returns:
            投递记录
        """
        # 生成投递ID
        delivery_id = self._generate_delivery_id()
        
        # 构建payload
        payload = self._build_payload(event)
        
        # 创建投递记录
        record = WebhookDeliveryRecord(
            event_id=event.event_id,
            webhook_id=webhook.id,
            event_type=event.event_type.value,
            payload=json.dumps(payload),
            status="pending",
            attempt_count=0
        )
        self.db.add(record)
        self.db.commit()
        
        # 构建签名
        signature = self._generate_signature(payload, webhook.secret)
        
        # 发送HTTP请求
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Event": event.event_type.value,
                    "X-Webhook-Event-ID": event.event_id,
                    "X-Webhook-Delivery-ID": delivery_id,
                    "X-Webhook-Signature": signature
                }
                
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_body = await response.text()
                    
                    # 更新投递记录
                    record.status = "delivered" if response.status < 400 else "failed"
                    record.http_status = response.status
                    record.response_body = response_body
                    record.delivered_at = datetime.utcnow()
                    record.attempt_count += 1
                    
                    self.db.commit()
                    
                    logger.info(
                        f"Webhook投递成功: Event={event.event_type.value}, "
                        f"Webhook={webhook.id}, Status={response.status}"
                    )
        
        except Exception as e:
            error_message = str(e)
            record.status = "failed"
            record.error_message = error_message
            record.attempt_count += 1
            
            self.db.commit()
            
            logger.error(
                f"Webhook投递失败: Event={event.event_type.value}, "
                f"Webhook={webhook.id}, Error={error_message}"
            )
            
            # 触发重试
            if record.attempt_count < webhook.retry_count:
                await self._schedule_retry(record.id)
        
        # 构建返回对象
        return WebhookDelivery(
            delivery_id=delivery_id,
            event_id=event.event_id,
            webhook_id=webhook.id,
            url=webhook.url,
            status=record.status,
            http_status=record.http_status,
            response_body=record.response_body,
            error_message=record.error_message,
            attempt_count=record.attempt_count,
            created_at=record.created_at,
            delivered_at=record.delivered_at
        )
    
    # ==================== 签名验证 ====================
    
    def _generate_signature(
        self,
        payload: Dict[str, Any],
        secret: Optional[str]
    ) -> str:
        """
        生成Webhook签名
        
        Args:
            payload: 请求体
            secret: 签名密钥
        
        Returns:
            签名字符串
        """
        if not secret:
            return ""
        
        payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        signature = hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def verify_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        验证Webhook签名
        
        Args:
            payload: 请求体字符串
            signature: 收到的签名
            secret: 签名密钥
        
        Returns:
            签名是否有效
        """
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(
            signature.replace("sha256=", ""),
            expected_signature
        )
    
    # ==================== 重试机制 ====================
    
    async def _schedule_retry(self, record_id: int) -> None:
        """
        调度重试任务
        
        Args:
            record_id: 投递记录ID
        """
        # 计算延迟时间（指数退避）
        record = self.db.query(WebhookDeliveryRecord).filter(
            WebhookDeliveryRecord.id == record_id
        ).first()
        
        if not record:
            return
        
        delay = min(
            self.RETRY_CONFIG["base_delay"] * (
                self.RETRY_CONFIG["backoff_factor"] ** record.attempt_count
            ),
            self.RETRY_CONFIG["max_delay"]
        )
        
        logger.info(f"调度Webhook重试: Record={record_id}, Delay={delay}s")
        
        # 使用异步任务调度重试
        asyncio.create_task(self._retry_delivery(record_id, delay))
    
    async def _retry_delivery(
        self,
        record_id: int,
        delay: float
    ) -> None:
        """
        执行重试投递
        
        Args:
            record_id: 投递记录ID
            delay: 延迟时间（秒）
        """
        await asyncio.sleep(delay)
        
        record = self.db.query(WebhookDeliveryRecord).filter(
            WebhookDeliveryRecord.id == record_id
        ).first()
        
        if not record or record.status == "delivered":
            return
        
        webhook = self.db.query(WebhookConfig).filter(
            WebhookConfig.id == record.webhook_id
        ).first()
        
        if not webhook:
            return
        
        # 重新构建事件对象
        event = WebhookEvent(
            event_type=WebhookEventType(record.event_type),
            event_id=record.event_id,
            timestamp=record.created_at,
            data=json.loads(record.payload)
        )
        
        # 重新投递
        await self._deliver_event(event, webhook)
    
    # ==================== 辅助方法 ====================
    
    def _build_payload(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        构建Webhook请求体
        
        Args:
            event: 事件对象
        
        Returns:
            请求体字典
        """
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "model_id": event.model_id,
            "user_id": event.user_id,
            "data": event.data
        }
    
    def _generate_event_id(self) -> str:
        """生成事件ID"""
        import uuid
        return f"evt_{uuid.uuid4().hex[:16]}"
    
    def _generate_delivery_id(self) -> str:
        """生成投递ID"""
        import uuid
        return f"del_{uuid.uuid4().hex[:16]}"
    
    # ==================== 投递记录查询 ====================
    
    def get_delivery_records(
        self,
        webhook_id: Optional[int] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookDeliveryRecord]:
        """
        获取投递记录
        
        Args:
            webhook_id: Webhook ID过滤器（可选）
            event_type: 事件类型过滤器（可选）
            status: 状态过滤器（可选）
            limit: 返回的最大数量
        
        Returns:
            投递记录列表
        """
        query = self.db.query(WebhookDeliveryRecord)
        
        if webhook_id:
            query = query.filter(WebhookDeliveryRecord.webhook_id == webhook_id)
        
        if event_type:
            query = query.filter(WebhookDeliveryRecord.event_type == event_type)
        
        if status:
            query = query.filter(WebhookDeliveryRecord.status == status)
        
        return query.order_by(
            WebhookDeliveryRecord.created_at.desc()
        ).limit(limit).all()


# ==================== 依赖注入函数 ====================

def get_webhook_service(db: Session) -> WebhookService:
    """
    获取Webhook服务实例（用于依赖注入）
    
    Args:
        db: 数据库会话
    
    Returns:
        Webhook服务实例
    """
    return WebhookService(db)
