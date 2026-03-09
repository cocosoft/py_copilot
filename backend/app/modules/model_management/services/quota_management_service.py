"""
用户配额管理服务

提供用户调用配额管理功能，包括：
- 配额设置和查询
- 配额使用统计
- 配额接近和用尽通知
- 配额管理API
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text
from sqlalchemy.ext.declarative import declarative_base

from app.models.base import Base
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class QuotaPeriod(Enum):
    """配额周期枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class QuotaStatus(Enum):
    """配额状态枚举"""
    NORMAL = "normal"           # 正常
    WARNING = "warning"         # 接近用尽
    EXHAUSTED = "exhausted"     # 已用尽
    UNLIMITED = "unlimited"     # 无限制


@dataclass
class QuotaConfig:
    """配额配置"""
    user_id: int
    period: QuotaPeriod
    max_calls: int
    warning_threshold: float = 0.8  # 警告阈值（80%）
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuotaUsage:
    """配额使用情况"""
    user_id: int
    period: QuotaPeriod
    period_start: date
    period_end: date
    used_calls: int
    max_calls: int
    status: QuotaStatus
    remaining_calls: int
    usage_percentage: float


class UserQuota(Base):
    """用户配额数据库模型"""
    __tablename__ = "user_quotas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    period = Column(String(20), nullable=False)  # daily, weekly, monthly
    max_calls = Column(Integer, nullable=False, default=1000)
    warning_threshold = Column(Integer, default=80)  # 百分比
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuotaUsageRecord(Base):
    """配额使用记录数据库模型"""
    __tablename__ = "quota_usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    period = Column(String(20), nullable=False)
    period_date = Column(Date, nullable=False, index=True)  # 周期开始日期
    used_calls = Column(Integer, default=0)
    last_call_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuotaNotification(Base):
    """配额通知数据库模型"""
    __tablename__ = "quota_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)  # warning, exhausted
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuotaManagementService:
    """
    配额管理服务类
    
    提供用户配额的完整管理功能，包括：
    - 配额设置和查询
    - 使用量统计和追踪
    - 配额警告和通知
    - 配额重置
    """
    
    # 默认配额配置
    DEFAULT_QUOTAS = {
        QuotaPeriod.DAILY: 1000,
        QuotaPeriod.WEEKLY: 5000,
        QuotaPeriod.MONTHLY: 20000,
    }
    
    # Redis缓存键前缀
    CACHE_PREFIX = "quota"
    
    def __init__(self, db: Session):
        """
        初始化配额管理服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.redis_client = get_redis()
    
    # ==================== 配额配置管理 ====================
    
    def set_user_quota(
        self,
        user_id: int,
        period: QuotaPeriod,
        max_calls: int,
        warning_threshold: int = 80
    ) -> UserQuota:
        """
        设置用户配额
        
        Args:
            user_id: 用户ID
            period: 配额周期
            max_calls: 最大调用次数
            warning_threshold: 警告阈值（百分比）
        
        Returns:
            配额配置对象
        """
        # 查找现有配额配置
        quota = self.db.query(UserQuota).filter(
            UserQuota.user_id == user_id,
            UserQuota.period == period.value
        ).first()
        
        if quota:
            # 更新现有配置
            quota.max_calls = max_calls
            quota.warning_threshold = warning_threshold
            quota.updated_at = datetime.utcnow()
        else:
            # 创建新配置
            quota = UserQuota(
                user_id=user_id,
                period=period.value,
                max_calls=max_calls,
                warning_threshold=warning_threshold
            )
            self.db.add(quota)
        
        self.db.commit()
        self.db.refresh(quota)
        
        # 清除缓存
        self._clear_quota_cache(user_id, period)
        
        logger.info(f"用户 {user_id} 配额已设置: {period.value}={max_calls}")
        
        return quota
    
    def get_user_quota(
        self,
        user_id: int,
        period: QuotaPeriod
    ) -> Optional[UserQuota]:
        """
        获取用户配额配置
        
        Args:
            user_id: 用户ID
            period: 配额周期
        
        Returns:
            配额配置对象，不存在时返回None
        """
        return self.db.query(UserQuota).filter(
            UserQuota.user_id == user_id,
            UserQuota.period == period.value,
            UserQuota.is_active == True
        ).first()
    
    def get_user_all_quotas(self, user_id: int) -> List[UserQuota]:
        """
        获取用户所有配额配置
        
        Args:
            user_id: 用户ID
        
        Returns:
            配额配置列表
        """
        return self.db.query(UserQuota).filter(
            UserQuota.user_id == user_id,
            UserQuota.is_active == True
        ).all()
    
    # ==================== 配额使用统计 ====================
    
    def record_usage(
        self,
        user_id: int,
        period: QuotaPeriod = QuotaPeriod.DAILY
    ) -> QuotaUsage:
        """
        记录配额使用
        
        Args:
            user_id: 用户ID
            period: 配额周期
        
        Returns:
            更新后的配额使用情况
        """
        # 获取当前周期日期范围
        period_start, period_end = self._get_period_range(period)
        
        # 查找或创建使用记录
        record = self.db.query(QuotaUsageRecord).filter(
            QuotaUsageRecord.user_id == user_id,
            QuotaUsageRecord.period == period.value,
            QuotaUsageRecord.period_date == period_start
        ).first()
        
        if not record:
            record = QuotaUsageRecord(
                user_id=user_id,
                period=period.value,
                period_date=period_start,
                used_calls=0
            )
            self.db.add(record)
        
        # 增加使用次数
        record.used_calls += 1
        record.last_call_time = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        
        # 清除缓存
        self._clear_usage_cache(user_id, period)
        
        # 获取使用情况并检查是否需要通知
        usage = self.get_quota_usage(user_id, period)
        
        # 检查是否需要发送警告通知
        self._check_and_notify(user_id, usage)
        
        return usage
    
    def get_quota_usage(
        self,
        user_id: int,
        period: QuotaPeriod = QuotaPeriod.DAILY
    ) -> QuotaUsage:
        """
        获取配额使用情况
        
        Args:
            user_id: 用户ID
            period: 配额周期
        
        Returns:
            配额使用情况
        """
        # 尝试从缓存获取
        cached = self._get_cached_usage(user_id, period)
        if cached:
            return cached
        
        # 获取配额配置
        quota = self.get_user_quota(user_id, period)
        max_calls = quota.max_calls if quota else self.DEFAULT_QUOTAS.get(period, 1000)
        
        # 获取当前周期日期范围
        period_start, period_end = self._get_period_range(period)
        
        # 获取使用记录
        record = self.db.query(QuotaUsageRecord).filter(
            QuotaUsageRecord.user_id == user_id,
            QuotaUsageRecord.period == period.value,
            QuotaUsageRecord.period_date == period_start
        ).first()
        
        used_calls = record.used_calls if record else 0
        
        # 计算使用百分比
        usage_percentage = (used_calls / max_calls * 100) if max_calls > 0 else 0
        
        # 确定状态
        warning_threshold = quota.warning_threshold if quota else 80
        if max_calls == -1:  # 无限制
            status = QuotaStatus.UNLIMITED
        elif used_calls >= max_calls:
            status = QuotaStatus.EXHAUSTED
        elif usage_percentage >= warning_threshold:
            status = QuotaStatus.WARNING
        else:
            status = QuotaStatus.NORMAL
        
        usage = QuotaUsage(
            user_id=user_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            used_calls=used_calls,
            max_calls=max_calls,
            status=status,
            remaining_calls=max(0, max_calls - used_calls) if max_calls > 0 else -1,
            usage_percentage=usage_percentage
        )
        
        # 缓存结果
        self._cache_usage(user_id, period, usage)
        
        return usage
    
    def check_quota_available(
        self,
        user_id: int,
        period: QuotaPeriod = QuotaPeriod.DAILY
    ) -> bool:
        """
        检查配额是否可用
        
        Args:
            user_id: 用户ID
            period: 配额周期
        
        Returns:
            是否有可用配额
        """
        usage = self.get_quota_usage(user_id, period)
        
        if usage.status == QuotaStatus.UNLIMITED:
            return True
        
        return usage.status != QuotaStatus.EXHAUSTED
    
    # ==================== 配额通知 ====================
    
    def get_unread_notifications(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[QuotaNotification]:
        """
        获取未读通知
        
        Args:
            user_id: 用户ID
            limit: 返回的最大数量
        
        Returns:
            通知列表
        """
        return self.db.query(QuotaNotification).filter(
            QuotaNotification.user_id == user_id,
            QuotaNotification.is_read == False
        ).order_by(
            QuotaNotification.created_at.desc()
        ).limit(limit).all()
    
    def mark_notification_read(self, notification_id: int) -> None:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知ID
        """
        notification = self.db.query(QuotaNotification).filter(
            QuotaNotification.id == notification_id
        ).first()
        
        if notification:
            notification.is_read = True
            self.db.commit()
    
    def _check_and_notify(
        self,
        user_id: int,
        usage: QuotaUsage
    ) -> None:
        """
        检查并发送配额通知
        
        Args:
            user_id: 用户ID
            usage: 配额使用情况
        """
        # 检查是否已发送过相同类型的通知
        today = date.today()
        
        if usage.status == QuotaStatus.EXHAUSTED:
            # 检查今天是否已发送过用尽通知
            existing = self.db.query(QuotaNotification).filter(
                QuotaNotification.user_id == user_id,
                QuotaNotification.notification_type == "exhausted",
                QuotaNotification.created_at >= today
            ).first()
            
            if not existing:
                notification = QuotaNotification(
                    user_id=user_id,
                    notification_type="exhausted",
                    message=f"您的{usage.period.value}配额已用尽，请升级套餐或等待配额重置。"
                )
                self.db.add(notification)
                self.db.commit()
                
                logger.warning(f"用户 {user_id} 配额已用尽")
        
        elif usage.status == QuotaStatus.WARNING:
            # 检查今天是否已发送过警告通知
            existing = self.db.query(QuotaNotification).filter(
                QuotaNotification.user_id == user_id,
                QuotaNotification.notification_type == "warning",
                QuotaNotification.created_at >= today
            ).first()
            
            if not existing:
                notification = QuotaNotification(
                    user_id=user_id,
                    notification_type="warning",
                    message=f"您的{usage.period.value}配额已使用{usage.usage_percentage:.1f}%，请注意控制使用量。"
                )
                self.db.add(notification)
                self.db.commit()
                
                logger.info(f"用户 {user_id} 配额接近用尽: {usage.usage_percentage:.1f}%")
    
    # ==================== 辅助方法 ====================
    
    def _get_period_range(
        self,
        period: QuotaPeriod
    ) -> tuple[date, date]:
        """
        获取配额周期的日期范围
        
        Args:
            period: 配额周期
        
        Returns:
            (周期开始日期, 周期结束日期)
        """
        today = date.today()
        
        if period == QuotaPeriod.DAILY:
            return today, today
        elif period == QuotaPeriod.WEEKLY:
            # 本周一到本周日
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif period == QuotaPeriod.MONTHLY:
            # 本月第一天到最后一天
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
        
        return today, today
    
    def _get_cache_key(
        self,
        user_id: int,
        period: QuotaPeriod,
        key_type: str
    ) -> str:
        """
        获取缓存键
        
        Args:
            user_id: 用户ID
            period: 配额周期
            key_type: 键类型
        
        Returns:
            缓存键
        """
        return f"{self.CACHE_PREFIX}:{key_type}:{user_id}:{period.value}"
    
    def _cache_usage(
        self,
        user_id: int,
        period: QuotaPeriod,
        usage: QuotaUsage
    ) -> None:
        """
        缓存使用情况
        
        Args:
            user_id: 用户ID
            period: 配额周期
            usage: 使用情况
        """
        if self.redis_client:
            key = self._get_cache_key(user_id, period, "usage")
            # 缓存5分钟
            self.redis_client.setex(key, 300, str(usage.used_calls))
    
    def _get_cached_usage(
        self,
        user_id: int,
        period: QuotaPeriod
    ) -> Optional[QuotaUsage]:
        """
        获取缓存的使用情况
        
        Args:
            user_id: 用户ID
            period: 配额周期
        
        Returns:
            使用情况，不存在时返回None
        """
        return None  # 暂不使用缓存，直接查询数据库
    
    def _clear_quota_cache(
        self,
        user_id: int,
        period: QuotaPeriod
    ) -> None:
        """
        清除配额缓存
        
        Args:
            user_id: 用户ID
            period: 配额周期
        """
        if self.redis_client:
            key = self._get_cache_key(user_id, period, "quota")
            self.redis_client.delete(key)
    
    def _clear_usage_cache(
        self,
        user_id: int,
        period: QuotaPeriod
    ) -> None:
        """
        清除使用情况缓存
        
        Args:
            user_id: 用户ID
            period: 配额周期
        """
        if self.redis_client:
            key = self._get_cache_key(user_id, period, "usage")
            self.redis_client.delete(key)


# ==================== 依赖注入函数 ====================

def get_quota_management_service(db: Session) -> QuotaManagementService:
    """
    获取配额管理服务实例（用于依赖注入）
    
    Args:
        db: 数据库会话
    
    Returns:
        配额管理服务实例
    """
    return QuotaManagementService(db)
