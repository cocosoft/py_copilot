"""审计日志服务层"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditLogService:
    """审计日志服务类"""
    
    @staticmethod
    def create_log(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        创建审计日志
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 操作类型（create, update, delete, restore等）
            resource_type: 资源类型（agent, category等）
            resource_id: 资源ID
            old_values: 旧值（更新操作时使用）
            new_values: 新值（创建或更新操作时使用）
            ip_address: IP地址
            user_agent: 用户代理字符串
        
        Returns:
            创建的审计日志
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def get_logs(
        db: Session,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[AuditLog], int]:
        """
        获取审计日志列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID（可选）
            resource_type: 资源类型（可选）
            resource_id: 资源ID（可选）
            action: 操作类型（可选）
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            审计日志列表和总数
        """
        query = db.query(AuditLog)
        
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        
        if resource_type is not None:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if resource_id is not None:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        if action is not None:
            query = query.filter(AuditLog.action == action)
        
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return logs, total
