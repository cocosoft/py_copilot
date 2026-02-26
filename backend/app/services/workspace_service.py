"""
工作空间服务

提供工作空间的创建、查询、更新、删除等功能
支持多用户独立工作空间管理
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.workspace import Workspace
from app.models.user import User


class WorkspaceService:
    """
    工作空间服务类

    处理工作空间相关的业务逻辑，包括CRUD操作和权限验证
    """

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def create_workspace(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        max_storage_bytes: int = 1073741824
    ) -> Workspace:
        """
        创建工作空间

        Args:
            user_id: 用户ID
            name: 工作空间名称
            description: 工作空间描述
            max_storage_bytes: 最大存储空间（字节）

        Returns:
            Workspace: 创建的工作空间对象

        Raises:
            HTTPException: 当工作空间数量超过限制或名称重复时
        """
        # 检查用户工作空间数量限制
        existing_count = self.db.query(Workspace).filter(
            Workspace.user_id == user_id
        ).count()

        if existing_count >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每个用户最多只能创建10个工作空间"
            )

        # 检查名称是否重复
        if self.db.query(Workspace).filter(
            Workspace.user_id == user_id,
            Workspace.name == name
        ).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="工作空间名称已存在"
            )

        # 创建新工作空间
        workspace = Workspace(
            user_id=user_id,
            name=name,
            description=description,
            max_storage_bytes=max_storage_bytes,
            is_default=(existing_count == 0)  # 第一个工作空间设为默认
        )

        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)

        return workspace

    def get_workspace(self, workspace_id: int, user_id: int) -> Workspace:
        """
        获取工作空间详情

        Args:
            workspace_id: 工作空间ID
            user_id: 用户ID（用于权限验证）

        Returns:
            Workspace: 工作空间对象

        Raises:
            HTTPException: 当工作空间不存在或无权限访问时
        """
        workspace = self.db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.user_id == user_id
        ).first()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作空间不存在"
            )

        return workspace

    def get_user_workspaces(self, user_id: int) -> List[Workspace]:
        """
        获取用户的所有工作空间

        Args:
            user_id: 用户ID

        Returns:
            List[Workspace]: 工作空间列表
        """
        return self.db.query(Workspace).filter(
            Workspace.user_id == user_id,
            Workspace.is_active == True
        ).order_by(Workspace.is_default.desc(), Workspace.created_at.desc()).all()

    def update_workspace(
        self,
        workspace_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        max_storage_bytes: Optional[int] = None
    ) -> Workspace:
        """
        更新工作空间信息

        Args:
            workspace_id: 工作空间ID
            user_id: 用户ID
            name: 新名称
            description: 新描述
            max_storage_bytes: 新存储配额

        Returns:
            Workspace: 更新后的工作空间对象
        """
        workspace = self.get_workspace(workspace_id, user_id)

        if name is not None:
            # 检查新名称是否与其他工作空间重复
            existing = self.db.query(Workspace).filter(
                Workspace.user_id == user_id,
                Workspace.name == name,
                Workspace.id != workspace_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="工作空间名称已存在"
                )

            workspace.name = name

        if description is not None:
            workspace.description = description

        if max_storage_bytes is not None:
            workspace.max_storage_bytes = max_storage_bytes

        self.db.commit()
        self.db.refresh(workspace)

        return workspace

    def delete_workspace(self, workspace_id: int, user_id: int) -> bool:
        """
        删除工作空间

        Args:
            workspace_id: 工作空间ID
            user_id: 用户ID

        Returns:
            bool: 是否删除成功

        Raises:
            HTTPException: 当尝试删除默认工作空间时
        """
        workspace = self.get_workspace(workspace_id, user_id)

        if workspace.is_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除默认工作空间"
            )

        # 软删除
        workspace.is_active = False
        self.db.commit()

        return True

    def set_default_workspace(self, workspace_id: int, user_id: int) -> Workspace:
        """
        设置默认工作空间

        Args:
            workspace_id: 工作空间ID
            user_id: 用户ID

        Returns:
            Workspace: 新的默认工作空间
        """
        # 取消当前默认工作空间
        self.db.query(Workspace).filter(
            Workspace.user_id == user_id,
            Workspace.is_default == True
        ).update({"is_default": False})

        # 设置新的默认工作空间
        workspace = self.get_workspace(workspace_id, user_id)
        workspace.is_default = True

        self.db.commit()
        self.db.refresh(workspace)

        return workspace

    def get_default_workspace(self, user_id: int) -> Optional[Workspace]:
        """
        获取用户的默认工作空间

        Args:
            user_id: 用户ID

        Returns:
            Optional[Workspace]: 默认工作空间，如果不存在则返回None
        """
        return self.db.query(Workspace).filter(
            Workspace.user_id == user_id,
            Workspace.is_default == True,
            Workspace.is_active == True
        ).first()

    def get_storage_usage(self, workspace_id: int, user_id: int) -> dict:
        """
        获取工作空间存储使用情况

        Args:
            workspace_id: 工作空间ID
            user_id: 用户ID

        Returns:
            dict: 存储使用情况统计
        """
        from sqlalchemy.exc import OperationalError

        workspace = self.get_workspace(workspace_id, user_id)

        # 计算已用存储
        total_used = 0
        try:
            from app.models.file_record import FileRecord
            total_used = self.db.query(
                func.sum(FileRecord.file_size)
            ).filter(
                FileRecord.workspace_id == workspace_id
            ).scalar() or 0
        except OperationalError:
            # file_records表不存在，返回0
            total_used = 0

        return {
            "workspace_id": workspace_id,
            "max_storage_bytes": workspace.max_storage_bytes,
            "used_storage_bytes": total_used,
            "available_storage_bytes": workspace.max_storage_bytes - total_used,
            "usage_percentage": round(
                (total_used / workspace.max_storage_bytes * 100), 2
            ) if workspace.max_storage_bytes > 0 else 0
        }

    def check_storage_available(
        self,
        workspace_id: int,
        user_id: int,
        required_bytes: int
    ) -> bool:
        """
        检查存储空间是否足够

        Args:
            workspace_id: 工作空间ID
            user_id: 用户ID
            required_bytes: 需要的存储空间（字节）

        Returns:
            bool: 是否有足够空间
        """
        usage = self.get_storage_usage(workspace_id, user_id)
        return usage["available_storage_bytes"] >= required_bytes
