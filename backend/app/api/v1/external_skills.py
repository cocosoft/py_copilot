"""外部技能仓库同步 API"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.skill import SkillRepository, RemoteSkill
from app.schemas.skill import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryListResponse,
    RemoteSkillResponse,
    RemoteSkillListResponse,
    RepositorySyncResponse
)
from app.services.external_skill_sync import ExternalSkillSyncService

router = APIRouter()


@router.post("/repositories", response_model=RepositoryResponse, tags=["external-skills"])
def create_repository(
    repo_data: RepositoryCreate,
    db: Session = Depends(get_db)
):
    """创建技能仓库配置"""
    existing = db.query(SkillRepository).filter(
        SkillRepository.url == repo_data.url
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="该仓库已存在"
        )

    repository = SkillRepository(
        name=repo_data.name,
        url=repo_data.url,
        description=repo_data.description,
        branch=repo_data.branch or "main",
        is_enabled=repo_data.is_enabled,
        sync_interval_hours=repo_data.sync_interval_hours or 24,
        credentials=repo_data.credentials
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    return repository


@router.get("/repositories", response_model=RepositoryListResponse, tags=["external-skills"])
def list_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    is_enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取技能仓库列表"""
    query = db.query(SkillRepository)

    if is_enabled is not None:
        query = query.filter(SkillRepository.is_enabled == is_enabled)

    total = query.count()
    repositories = query.offset(skip).limit(limit).all()

    return {
        "repositories": repositories,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/repositories/{repository_id}", response_model=RepositoryResponse, tags=["external-skills"])
def get_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """获取单个仓库详情"""
    repository = db.query(SkillRepository).filter(
        SkillRepository.id == repository_id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="仓库不存在"
        )

    return repository


@router.delete("/repositories/{repository_id}", tags=["external-skills"])
def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """删除技能仓库配置"""
    repository = db.query(SkillRepository).filter(
        SkillRepository.id == repository_id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="仓库不存在"
        )

    db.query(RemoteSkill).filter(
        RemoteSkill.repository_id == repository_id
    ).delete()

    db.delete(repository)
    db.commit()

    return {"message": "仓库删除成功"}


@router.post("/repositories/{repository_id}/sync", response_model=RepositorySyncResponse, tags=["external-skills"])
def sync_repository(
    repository_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """同步技能仓库（后台任务）"""
    repository = db.query(SkillRepository).filter(
        SkillRepository.id == repository_id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="仓库不存在"
        )

    try:
        sync_service = ExternalSkillSyncService(db)
        result = sync_service.sync_repository(repository_id)

        return {
            "repository_id": repository_id,
            "status": "success",
            "message": "仓库同步成功",
            "synced_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"同步失败: {str(e)}"
        )


@router.get("/repositories/{repository_id}/skills", response_model=RemoteSkillListResponse, tags=["external-skills"])
def list_remote_skills(
    repository_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    is_installed: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取远程技能列表"""
    repository = db.query(SkillRepository).filter(
        SkillRepository.id == repository_id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="仓库不存在"
        )

    query = db.query(RemoteSkill).filter(
        RemoteSkill.repository_id == repository_id
    )

    if is_installed is not None:
        query = query.filter(RemoteSkill.is_installed == is_installed)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                RemoteSkill.name.ilike(search_term),
                RemoteSkill.display_name.ilike(search_term),
                RemoteSkill.description.ilike(search_term)
            )
        )

    total = query.count()
    skills = query.offset(skip).limit(limit).all()

    return {
        "skills": skills,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/remote-skills/{remote_skill_id}/content", tags=["external-skills"])
def get_remote_skill_content(
    remote_skill_id: int,
    db: Session = Depends(get_db)
):
    """获取远程技能内容"""
    sync_service = ExternalSkillSyncService(db)
    content = sync_service.get_remote_skill_content(remote_skill_id)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="技能不存在或无法读取"
        )

    return {"content": content}


@router.post("/remote-skills/{remote_skill_id}/install", tags=["external-skills"])
def install_remote_skill(
    remote_skill_id: int,
    db: Session = Depends(get_db)
):
    """安装远程技能"""
    repository = db.query(RemoteSkill).filter(
        RemoteSkill.id == remote_skill_id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="远程技能不存在"
        )

    try:
        sync_service = ExternalSkillSyncService(db)
        skills_dir = Path(__file__).parent.parent.parent / "skills"

        if not skills_dir.exists():
            skills_dir.mkdir(parents=True)

        skill = sync_service.install_remote_skill(remote_skill_id, skills_dir)

        return {
            "status": "success",
            "skill_id": skill.id,
            "skill_name": skill.name,
            "message": "技能安装成功"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"安装失败: {str(e)}"
        )


@router.post("/remote-skills/{remote_skill_id}/uninstall", tags=["external-skills"])
def uninstall_remote_skill(
    remote_skill_id: int,
    db: Session = Depends(get_db)
):
    """卸载已安装的远程技能"""
    remote_skill = db.query(RemoteSkill).filter(
        RemoteSkill.id == remote_skill_id
    ).first()

    if not remote_skill:
        raise HTTPException(
            status_code=404,
            detail="远程技能不存在"
        )

    try:
        sync_service = ExternalSkillSyncService(db)
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        sync_service.uninstall_remote_skill(remote_skill_id, skills_dir)

        return {
            "status": "success",
            "skill_name": remote_skill.name,
            "message": "技能卸载成功"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"卸载失败: {str(e)}"
        )


@router.get("/search", response_model=RemoteSkillListResponse, tags=["external-skills"])
def search_all_remote_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    tags: Optional[str] = None,
    search: Optional[str] = None,
    is_installed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """搜索所有仓库中的远程技能"""
    query = db.query(RemoteSkill)

    if is_installed is not None:
        query = query.filter(RemoteSkill.is_installed == is_installed)

    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        for tag in tag_list:
            query = query.filter(RemoteSkill.tags.contains([tag]))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                RemoteSkill.name.ilike(search_term),
                RemoteSkill.display_name.ilike(search_term),
                RemoteSkill.description.ilike(search_term)
            )
        )

    total = query.count()
    skills = query.offset(skip).limit(limit).all()

    return {
        "skills": skills,
        "total": total,
        "skip": skip,
        "limit": limit
    }
