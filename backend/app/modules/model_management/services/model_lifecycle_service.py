"""
模型生命周期管理服务

提供模型生命周期管理功能，包括：
- 模型状态流转：开发中、测试中、已上线、已废弃
- 状态变更审批流程
- 模型上线和废弃管理
- 废弃预告机制
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON

from app.models.base import Base
from app.models.supplier_db import ModelDB

logger = logging.getLogger(__name__)


class ModelLifecycleStatus(Enum):
    """模型生命周期状态枚举"""
    DEVELOPMENT = "development"      # 开发中
    TESTING = "testing"              # 测试中
    STAGING = "staging"              # 预发布
    PRODUCTION = "production"        # 已上线
    DEPRECATED = "deprecated"        # 已废弃
    ARCHIVED = "archived"            # 已归档


class ApprovalStatus(Enum):
    """审批状态枚举"""
    PENDING = "pending"              # 待审批
    APPROVED = "approved"            # 已通过
    REJECTED = "rejected"            # 已拒绝
    CANCELLED = "cancelled"          # 已取消


@dataclass
class StatusTransition:
    """状态流转记录"""
    from_status: ModelLifecycleStatus
    to_status: ModelLifecycleStatus
    transitioned_by: int
    transitioned_at: datetime
    reason: Optional[str] = None
    approval_id: Optional[int] = None


class ModelLifecycle(Base):
    """模型生命周期数据库模型"""
    __tablename__ = "model_lifecycles"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, unique=True)
    current_status = Column(String(50), nullable=False, default="development")
    previous_status = Column(String(50))
    status_changed_at = Column(DateTime, default=datetime.utcnow)
    status_changed_by = Column(Integer)
    deprecation_date = Column(DateTime)  # 预计废弃日期
    deprecation_notice_days = Column(Integer, default=30)  # 废弃预告天数
    is_deprecated = Column(Boolean, default=False)
    deprecated_at = Column(DateTime)
    deprecated_by = Column(Integer)
    deprecation_reason = Column(Text)
    migration_guide = Column(Text)  # 迁移指南
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StatusTransitionHistory(Base):
    """状态流转历史数据库模型"""
    __tablename__ = "status_transition_history"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    transitioned_by = Column(Integer, nullable=False)
    transitioned_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text)
    approval_id = Column(Integer)


class StatusApproval(Base):
    """状态变更审批数据库模型"""
    __tablename__ = "status_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    requested_by = Column(Integer, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(Integer)
    approved_at = Column(DateTime)
    status = Column(String(50), nullable=False, default="pending")
    reason = Column(Text)
    rejection_reason = Column(Text)


class DeprecationNotice(Base):
    """废弃预告数据库模型"""
    __tablename__ = "deprecation_notices"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    notice_date = Column(DateTime, default=datetime.utcnow)
    effective_date = Column(DateTime, nullable=False)
    created_by = Column(Integer, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer)
    acknowledged_at = Column(DateTime)
    message = Column(Text)


class ModelLifecycleService:
    """
    模型生命周期服务类
    
    提供完整的模型生命周期管理功能，包括：
    - 状态流转管理
    - 审批流程
    - 废弃管理
    - 迁移指南
    """
    
    # 状态流转规则：定义允许的状态转换
    TRANSITION_RULES = {
        ModelLifecycleStatus.DEVELOPMENT: [
            ModelLifecycleStatus.TESTING,
            ModelLifecycleStatus.ARCHIVED
        ],
        ModelLifecycleStatus.TESTING: [
            ModelLifecycleStatus.STAGING,
            ModelLifecycleStatus.DEVELOPMENT,
            ModelLifecycleStatus.ARCHIVED
        ],
        ModelLifecycleStatus.STAGING: [
            ModelLifecycleStatus.PRODUCTION,
            ModelLifecycleStatus.TESTING,
            ModelLifecycleStatus.ARCHIVED
        ],
        ModelLifecycleStatus.PRODUCTION: [
            ModelLifecycleStatus.DEPRECATED,
            ModelLifecycleStatus.STAGING
        ],
        ModelLifecycleStatus.DEPRECATED: [
            ModelLifecycleStatus.ARCHIVED,
            ModelLifecycleStatus.PRODUCTION
        ],
        ModelLifecycleStatus.ARCHIVED: [
            ModelLifecycleStatus.DEVELOPMENT
        ]
    }
    
    # 需要审批的状态转换
    APPROVAL_REQUIRED_TRANSITIONS = [
        (ModelLifecycleStatus.TESTING, ModelLifecycleStatus.STAGING),
        (ModelLifecycleStatus.STAGING, ModelLifecycleStatus.PRODUCTION),
        (ModelLifecycleStatus.PRODUCTION, ModelLifecycleStatus.DEPRECATED),
    ]
    
    def __init__(self, db: Session):
        """
        初始化生命周期服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._status_change_callbacks: List[Callable] = []
    
    # ==================== 状态管理 ====================
    
    def get_lifecycle(self, model_id: int) -> Optional[ModelLifecycle]:
        """
        获取模型生命周期信息
        
        Args:
            model_id: 模型ID
        
        Returns:
            生命周期对象，不存在时返回None
        """
        return self.db.query(ModelLifecycle).filter(
            ModelLifecycle.model_id == model_id
        ).first()
    
    def create_lifecycle(
        self,
        model_id: int,
        initial_status: ModelLifecycleStatus = ModelLifecycleStatus.DEVELOPMENT,
        created_by: Optional[int] = None
    ) -> ModelLifecycle:
        """
        创建模型生命周期记录
        
        Args:
            model_id: 模型ID
            initial_status: 初始状态
            created_by: 创建者ID
        
        Returns:
            生命周期对象
        """
        lifecycle = ModelLifecycle(
            model_id=model_id,
            current_status=initial_status.value,
            status_changed_by=created_by
        )
        
        self.db.add(lifecycle)
        self.db.commit()
        self.db.refresh(lifecycle)
        
        logger.info(f"模型生命周期创建成功: Model={model_id}, Status={initial_status.value}")
        
        return lifecycle
    
    def can_transition(
        self,
        model_id: int,
        to_status: ModelLifecycleStatus
    ) -> tuple[bool, Optional[str]]:
        """
        检查是否可以进行状态转换
        
        Args:
            model_id: 模型ID
            to_status: 目标状态
        
        Returns:
            (是否可以转换, 原因)
        """
        lifecycle = self.get_lifecycle(model_id)
        
        if not lifecycle:
            return False, "模型生命周期记录不存在"
        
        current_status = ModelLifecycleStatus(lifecycle.current_status)
        
        # 检查是否已经是目标状态
        if current_status == to_status:
            return False, "已经是目标状态"
        
        # 检查是否允许转换
        allowed_transitions = self.TRANSITION_RULES.get(current_status, [])
        if to_status not in allowed_transitions:
            return False, f"不允许从 {current_status.value} 转换到 {to_status.value}"
        
        # 检查是否有待审批的请求
        pending_approval = self.db.query(StatusApproval).filter(
            StatusApproval.model_id == model_id,
            StatusApproval.status == ApprovalStatus.PENDING.value
        ).first()
        
        if pending_approval:
            return False, "存在待审批的状态变更请求"
        
        return True, None
    
    def request_status_transition(
        self,
        model_id: int,
        to_status: ModelLifecycleStatus,
        requested_by: int,
        reason: Optional[str] = None
    ) -> StatusApproval:
        """
        请求状态转换
        
        Args:
            model_id: 模型ID
            to_status: 目标状态
            requested_by: 请求者ID
            reason: 原因
        
        Returns:
            审批记录
        """
        lifecycle = self.get_lifecycle(model_id)
        
        if not lifecycle:
            lifecycle = self.create_lifecycle(model_id, created_by=requested_by)
        
        from_status = ModelLifecycleStatus(lifecycle.current_status)
        
        # 检查是否需要审批
        needs_approval = (from_status, to_status) in self.APPROVAL_REQUIRED_TRANSITIONS
        
        if needs_approval:
            # 创建审批记录
            approval = StatusApproval(
                model_id=model_id,
                from_status=from_status.value,
                to_status=to_status.value,
                requested_by=requested_by,
                reason=reason,
                status=ApprovalStatus.PENDING.value
            )
            
            self.db.add(approval)
            self.db.commit()
            self.db.refresh(approval)
            
            logger.info(
                f"状态变更审批请求创建: Model={model_id}, "
                f"From={from_status.value}, To={to_status.value}"
            )
            
            return approval
        else:
            # 直接执行状态转换
            self._execute_transition(
                model_id, from_status, to_status, requested_by, reason
            )
            
            # 返回已批准的记录
            approval = StatusApproval(
                model_id=model_id,
                from_status=from_status.value,
                to_status=to_status.value,
                requested_by=requested_by,
                approved_by=requested_by,
                approved_at=datetime.utcnow(),
                status=ApprovalStatus.APPROVED.value,
                reason=reason
            )
            
            self.db.add(approval)
            self.db.commit()
            self.db.refresh(approval)
            
            return approval
    
    def approve_transition(
        self,
        approval_id: int,
        approved_by: int,
        rejection_reason: Optional[str] = None
    ) -> Optional[StatusApproval]:
        """
        审批状态转换请求
        
        Args:
            approval_id: 审批记录ID
            approved_by: 审批者ID
            rejection_reason: 拒绝原因（拒绝时必填）
        
        Returns:
            审批记录，不存在时返回None
        """
        approval = self.db.query(StatusApproval).filter(
            StatusApproval.id == approval_id
        ).first()
        
        if not approval:
            return None
        
        if approval.status != ApprovalStatus.PENDING.value:
            raise ValueError("审批请求已处理")
        
        if rejection_reason:
            # 拒绝
            approval.status = ApprovalStatus.REJECTED.value
            approval.rejection_reason = rejection_reason
            
            logger.info(f"状态变更审批拒绝: Approval={approval_id}")
        else:
            # 批准
            approval.status = ApprovalStatus.APPROVED.value
            approval.approved_by = approved_by
            approval.approved_at = datetime.utcnow()
            
            # 执行状态转换
            self._execute_transition(
                approval.model_id,
                ModelLifecycleStatus(approval.from_status),
                ModelLifecycleStatus(approval.to_status),
                approved_by,
                approval.reason
            )
            
            logger.info(f"状态变更审批通过: Approval={approval_id}")
        
        self.db.commit()
        self.db.refresh(approval)
        
        return approval
    
    def _execute_transition(
        self,
        model_id: int,
        from_status: ModelLifecycleStatus,
        to_status: ModelLifecycleStatus,
        transitioned_by: int,
        reason: Optional[str] = None
    ) -> None:
        """
        执行状态转换
        
        Args:
            model_id: 模型ID
            from_status: 原状态
            to_status: 目标状态
            transitioned_by: 执行者ID
            reason: 原因
        """
        lifecycle = self.get_lifecycle(model_id)
        
        if not lifecycle:
            lifecycle = self.create_lifecycle(model_id, from_status, transitioned_by)
        
        # 更新生命周期状态
        lifecycle.previous_status = lifecycle.current_status
        lifecycle.current_status = to_status.value
        lifecycle.status_changed_at = datetime.utcnow()
        lifecycle.status_changed_by = transitioned_by
        
        # 如果是废弃状态，更新废弃信息
        if to_status == ModelLifecycleStatus.DEPRECATED:
            lifecycle.is_deprecated = True
            lifecycle.deprecated_at = datetime.utcnow()
            lifecycle.deprecated_by = transitioned_by
            lifecycle.deprecation_reason = reason
        
        self.db.commit()
        
        # 记录状态流转历史
        history = StatusTransitionHistory(
            model_id=model_id,
            from_status=from_status.value,
            to_status=to_status.value,
            transitioned_by=transitioned_by,
            reason=reason
        )
        self.db.add(history)
        self.db.commit()
        
        # 触发回调
        self._trigger_status_change_callbacks(
            model_id, from_status, to_status, transitioned_by
        )
        
        logger.info(
            f"状态转换执行成功: Model={model_id}, "
            f"From={from_status.value}, To={to_status.value}"
        )
    
    # ==================== 废弃管理 ====================
    
    def schedule_deprecation(
        self,
        model_id: int,
        effective_date: datetime,
        created_by: int,
        message: Optional[str] = None,
        migration_guide: Optional[str] = None
    ) -> DeprecationNotice:
        """
        创建废弃预告
        
        Args:
            model_id: 模型ID
            effective_date: 生效日期
            created_by: 创建者ID
            message: 预告消息
            migration_guide: 迁移指南
        
        Returns:
            废弃预告对象
        """
        lifecycle = self.get_lifecycle(model_id)
        
        if not lifecycle:
            lifecycle = self.create_lifecycle(model_id, created_by=created_by)
        
        # 更新生命周期信息
        lifecycle.deprecation_date = effective_date
        lifecycle.migration_guide = migration_guide
        
        # 创建废弃预告
        notice = DeprecationNotice(
            model_id=model_id,
            effective_date=effective_date,
            created_by=created_by,
            message=message or f"该模型将于 {effective_date.strftime('%Y-%m-%d')} 废弃"
        )
        
        self.db.add(notice)
        self.db.commit()
        self.db.refresh(notice)
        
        logger.info(f"废弃预告创建成功: Model={model_id}, Effective={effective_date}")
        
        return notice
    
    def acknowledge_deprecation(
        self,
        notice_id: int,
        acknowledged_by: int
    ) -> Optional[DeprecationNotice]:
        """
        确认废弃预告
        
        Args:
            notice_id: 预告ID
            acknowledged_by: 确认者ID
        
        Returns:
            废弃预告对象，不存在时返回None
        """
        notice = self.db.query(DeprecationNotice).filter(
            DeprecationNotice.id == notice_id
        ).first()
        
        if not notice:
            return None
        
        notice.is_acknowledged = True
        notice.acknowledged_by = acknowledged_by
        notice.acknowledged_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(notice)
        
        logger.info(f"废弃预告已确认: Notice={notice_id}")
        
        return notice
    
    def get_deprecation_notices(
        self,
        model_id: Optional[int] = None,
        acknowledged: Optional[bool] = None
    ) -> List[DeprecationNotice]:
        """
        获取废弃预告列表
        
        Args:
            model_id: 模型ID过滤器（可选）
            acknowledged: 确认状态过滤器（可选）
        
        Returns:
            废弃预告列表
        """
        query = self.db.query(DeprecationNotice)
        
        if model_id:
            query = query.filter(DeprecationNotice.model_id == model_id)
        
        if acknowledged is not None:
            query = query.filter(DeprecationNotice.is_acknowledged == acknowledged)
        
        return query.order_by(DeprecationNotice.effective_date.desc()).all()
    
    # ==================== 查询方法 ====================
    
    def get_transition_history(
        self,
        model_id: int,
        limit: int = 100
    ) -> List[StatusTransitionHistory]:
        """
        获取状态流转历史
        
        Args:
            model_id: 模型ID
            limit: 返回的最大数量
        
        Returns:
            状态流转历史列表
        """
        return self.db.query(StatusTransitionHistory).filter(
            StatusTransitionHistory.model_id == model_id
        ).order_by(
            StatusTransitionHistory.transitioned_at.desc()
        ).limit(limit).all()
    
    def get_pending_approvals(
        self,
        model_id: Optional[int] = None
    ) -> List[StatusApproval]:
        """
        获取待审批列表
        
        Args:
            model_id: 模型ID过滤器（可选）
        
        Returns:
            待审批列表
        """
        query = self.db.query(StatusApproval).filter(
            StatusApproval.status == ApprovalStatus.PENDING.value
        )
        
        if model_id:
            query = query.filter(StatusApproval.model_id == model_id)
        
        return query.order_by(StatusApproval.requested_at.desc()).all()
    
    def get_models_by_status(
        self,
        status: ModelLifecycleStatus
    ) -> List[int]:
        """
        获取指定状态的所有模型ID
        
        Args:
            status: 状态
        
        Returns:
            模型ID列表
        """
        lifecycles = self.db.query(ModelLifecycle).filter(
            ModelLifecycle.current_status == status.value
        ).all()
        
        return [lc.model_id for lc in lifecycles]
    
    # ==================== 回调机制 ====================
    
    def register_status_change_callback(
        self,
        callback: Callable[[int, ModelLifecycleStatus, ModelLifecycleStatus, int], None]
    ) -> None:
        """
        注册状态变更回调
        
        Args:
            callback: 回调函数，接收(model_id, from_status, to_status, user_id)参数
        """
        self._status_change_callbacks.append(callback)
    
    def _trigger_status_change_callbacks(
        self,
        model_id: int,
        from_status: ModelLifecycleStatus,
        to_status: ModelLifecycleStatus,
        user_id: int
    ) -> None:
        """
        触发状态变更回调
        
        Args:
            model_id: 模型ID
            from_status: 原状态
            to_status: 新状态
            user_id: 用户ID
        """
        for callback in self._status_change_callbacks:
            try:
                callback(model_id, from_status, to_status, user_id)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {str(e)}")
    
    # ==================== 批量操作 ====================
    
    def check_deprecation_schedule(self) -> List[DeprecationNotice]:
        """
        检查即将生效的废弃预告
        
        Returns:
            即将生效的废弃预告列表
        """
        # 获取7天内即将生效的废弃预告
        upcoming_date = datetime.utcnow() + timedelta(days=7)
        
        notices = self.db.query(DeprecationNotice).filter(
            DeprecationNotice.effective_date <= upcoming_date,
            DeprecationNotice.effective_date > datetime.utcnow(),
            DeprecationNotice.is_acknowledged == False
        ).all()
        
        return notices


# ==================== 依赖注入函数 ====================

def get_model_lifecycle_service(db: Session) -> ModelLifecycleService:
    """
    获取模型生命周期服务实例（用于依赖注入）
    
    Args:
        db: 数据库会话
    
    Returns:
        模型生命周期服务实例
    """
    return ModelLifecycleService(db)
