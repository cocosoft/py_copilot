"""
工作空间API路由

提供工作空间的RESTful API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.services.workspace_service import WorkspaceService
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    StorageUsageResponse
)

router = APIRouter(tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建工作空间

    Args:
        workspace_data: 工作空间创建数据
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceResponse: 创建的工作空间信息
    """
    service = WorkspaceService(db)
    workspace = service.create_workspace(
        user_id=current_user.id,
        name=workspace_data.name,
        description=workspace_data.description,
        max_storage_bytes=workspace_data.max_storage_bytes
    )
    return workspace


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的工作空间列表

    Args:
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceListResponse: 工作空间列表
    """
    service = WorkspaceService(db)
    workspaces = service.get_user_workspaces(current_user.id)

    return WorkspaceListResponse(
        workspaces=workspaces,
        total=len(workspaces)
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作空间详情

    Args:
        workspace_id: 工作空间ID
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceResponse: 工作空间详情
    """
    service = WorkspaceService(db)
    workspace = service.get_workspace(workspace_id, current_user.id)
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新工作空间信息

    Args:
        workspace_id: 工作空间ID
        workspace_data: 更新数据
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceResponse: 更新后的工作空间信息
    """
    service = WorkspaceService(db)
    workspace = service.update_workspace(
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=workspace_data.name,
        description=workspace_data.description,
        max_storage_bytes=workspace_data.max_storage_bytes
    )
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除工作空间（软删除）

    Args:
        workspace_id: 工作空间ID
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        None
    """
    service = WorkspaceService(db)
    service.delete_workspace(workspace_id, current_user.id)
    return None


@router.post("/{workspace_id}/set-default", response_model=WorkspaceResponse)
async def set_default_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    设置默认工作空间

    Args:
        workspace_id: 工作空间ID
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceResponse: 新的默认工作空间
    """
    service = WorkspaceService(db)
    workspace = service.set_default_workspace(workspace_id, current_user.id)

    # 更新用户当前工作空间
    current_user.current_workspace_id = workspace_id
    db.commit()

    return workspace


@router.get("/{workspace_id}/storage", response_model=StorageUsageResponse)
async def get_storage_usage(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作空间存储使用情况

    Args:
        workspace_id: 工作空间ID
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        StorageUsageResponse: 存储使用情况
    """
    service = WorkspaceService(db)
    usage = service.get_storage_usage(workspace_id, current_user.id)
    return StorageUsageResponse(**usage)


@router.get("/current/default", response_model=WorkspaceResponse)
async def get_current_workspace(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前工作空间

    如果用户已设置当前工作空间则返回，否则返回默认工作空间

    Args:
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceResponse: 当前工作空间信息
    """
    print(f"[DEBUG] get_current_workspace called: user={current_user.username} (id={current_user.id}), current_workspace_id={current_user.current_workspace_id}")
    service = WorkspaceService(db)

    # 首先尝试获取用户设置的当前工作空间
    if current_user.current_workspace_id:
        try:
            workspace = service.get_workspace(
                current_user.current_workspace_id,
                current_user.id
            )
            print(f"[DEBUG] returning current workspace: {workspace.name} (id={workspace.id})")
            return workspace
        except HTTPException as e:
            print(f"[DEBUG] failed to get current workspace: {e.detail}")
            pass

    # 否则获取默认工作空间
    workspace = service.get_default_workspace(current_user.id)
    print(f"[DEBUG] returning default workspace: {workspace.name if workspace else 'None'} (id={workspace.id if workspace else 'None'})")

    if not workspace:
        # 如果没有默认工作空间，创建一个
        workspace = service.create_workspace(
            user_id=current_user.id,
            name="默认工作空间",
            description="系统自动创建的默认工作空间"
        )

    # 更新用户当前工作空间
    current_user.current_workspace_id = workspace.id
    db.commit()

    return workspace


@router.post("/switch/{workspace_id}", response_model=WorkspaceResponse)
async def switch_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    切换当前工作空间

    Args:
        workspace_id: 要切换到的目标工作空间ID
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        WorkspaceResponse: 切换后的工作空间信息
    """
    print(f"[DEBUG] switch_workspace called: workspace_id={workspace_id}, current_user={current_user.username} (id={current_user.id})")
    service = WorkspaceService(db)

    # 验证工作空间存在且属于当前用户
    workspace = service.get_workspace(workspace_id, current_user.id)
    print(f"[DEBUG] workspace found: {workspace.name} (id={workspace.id})")

    # 更新用户当前工作空间
    old_workspace_id = current_user.current_workspace_id
    current_user.current_workspace_id = workspace_id
    db.commit()
    print(f"[DEBUG] updated current_workspace_id: {old_workspace_id} -> {workspace_id}")

    return workspace
