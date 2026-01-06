"""技能管理相关API接口"""
from typing import Any, List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.skill_service import SkillService, SkillSessionService, SkillExecutionService, SkillRepositoryService
from pydantic import BaseModel, Field, validator


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = None
    description: Optional[str] = None
    version: str = Field(default="1.0.0", max_length=50)
    license: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: str = Field(default="local")
    source_url: Optional[str] = None
    content: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    author: Optional[str] = None
    documentation_url: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class SkillUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    license: Optional[str] = None
    tags: Optional[List[str]] = None
    content: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    documentation_url: Optional[str] = None
    requirements: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    version: str
    license: Optional[str]
    tags: List[str]
    source: str
    status: str
    is_system: bool
    icon: Optional[str]
    author: Optional[str]
    documentation_url: Optional[str]
    requirements: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int

    class Config:
        from_attributes = True

    @validator('created_at', 'updated_at', 'installed_at', 'last_used_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


class SkillListResponse(BaseModel):
    skills: List[SkillResponse]
    total: int
    skip: int
    limit: int


class SkillMatchRequest(BaseModel):
    task_description: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class SkillMatchResponse(BaseModel):
    matched_skills: List[SkillResponse]
    task_description: str


class SkillActivateRequest(BaseModel):
    conversation_id: int
    skill_ids: List[int]
    context: Optional[Dict[str, Any]] = None


class SkillExecuteRequest(BaseModel):
    task: str = Field(..., min_length=1)
    params: Optional[Dict[str, Any]] = None


class SkillExecuteResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., max_length=500)
    description: Optional[str] = None
    branch: str = Field(default="main", max_length=100)
    sync_interval_hours: int = Field(default=24, ge=1, le=168)


class RepositoryResponse(BaseModel):
    id: int
    name: str
    url: str
    description: Optional[str]
    branch: str
    is_enabled: bool
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str]

    class Config:
        from_attributes = True

    @validator('last_sync_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


router = APIRouter()


@router.get("/", response_model=SkillListResponse)
def list_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取技能列表"""
    skill_service = SkillService(db)
    tags_list = tags.split(',') if tags else None
    skills, total = skill_service.get_skills(skip=skip, limit=limit, status=status, tags=tags_list, search=search)
    return {
        "skills": skills,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    """获取单个技能详情"""
    skill_service = SkillService(db)
    skill = skill_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(skill_data: SkillCreate, db: Session = Depends(get_db)):
    """创建新技能"""
    skill_service = SkillService(db)
    existing = skill_service.get_skill_by_name(skill_data.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名称已存在")
    skill = skill_service.create_skill(skill_data.model_dump())
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(skill_id: int, skill_data: SkillUpdate, db: Session = Depends(get_db)):
    """更新技能"""
    skill_service = SkillService(db)
    skill = skill_service.update_skill(skill_id, skill_data.model_dump(exclude_unset=True))
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    """删除技能"""
    skill_service = SkillService(db)
    if not skill_service.delete_skill(skill_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return None


@router.post("/{skill_id}/enable", response_model=SkillResponse)
def enable_skill(skill_id: int, db: Session = Depends(get_db)):
    """启用技能"""
    skill_service = SkillService(db)
    skill = skill_service.enable_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.post("/{skill_id}/disable", response_model=SkillResponse)
def disable_skill(skill_id: int, db: Session = Depends(get_db)):
    """禁用技能"""
    skill_service = SkillService(db)
    skill = skill_service.disable_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.post("/match", response_model=SkillMatchResponse)
def match_skills(request: SkillMatchRequest, db: Session = Depends(get_db)):
    """根据任务描述匹配技能"""
    skill_service = SkillService(db)
    matched_skills = skill_service.match_skills(request.task_description, limit=request.limit)
    return {
        "matched_skills": matched_skills,
        "task_description": request.task_description
    }


@router.post("/activate", response_model=List[SkillResponse])
def activate_skills(request: SkillActivateRequest, db: Session = Depends(get_db)):
    """在会话中激活技能"""
    session_service = SkillSessionService(db)
    sessions = session_service.activate_skills(
        conversation_id=request.conversation_id,
        skill_ids=request.skill_ids,
        context=request.context
    )
    skill_service = SkillService(db)
    skills = [session_service.db.query(Skill).filter(Skill.id == session.skill_id).first() for session in sessions]
    return [s for s in skills if s is not None]


@router.post("/deactivate")
def deactivate_skills(
    conversation_id: int,
    skill_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """在会话中停用技能"""
    session_service = SkillSessionService(db)
    count = session_service.deactivate_skills(conversation_id, skill_ids)
    return {"deactivated_count": count}


@router.get("/context/{conversation_id}")
def get_active_skills(conversation_id: int, db: Session = Depends(get_db)):
    """获取会话中激活的技能"""
    session_service = SkillSessionService(db)
    sessions = session_service.get_active_skills(conversation_id)
    skill_service = SkillService(db)
    skills = []
    for session in sessions:
        skill = skill_service.get_skill(session.skill_id)
        if skill:
            skills.append({
                **SkillResponse.model_validate(skill).model_dump(),
                "session_id": session.id,
                "context": session.context
            })
    return {"active_skills": skills}


@router.post("/{skill_id}/execute", response_model=SkillExecuteResponse)
def execute_skill(
    skill_id: int,
    request: SkillExecuteRequest,
    session_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """执行技能"""
    execution_service = SkillExecutionService(db)
    result = execution_service.execute_skill(
        skill_id=skill_id,
        task=request.task,
        params=request.params,
        session_id=session_id,
        conversation_id=conversation_id
    )
    return SkillExecuteResponse(**result)


@router.post("/load-from-file")
def load_skill_from_file(file_path: str, db: Session = Depends(get_db)):
    """从文件加载技能"""
    skill_service = SkillService(db)
    skill = skill_service.load_skill_from_file(file_path)
    if not skill:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法加载技能文件")
    return {"skill": skill, "message": "技能加载成功"}


@router.post("/load-from-directory")
def load_skills_from_directory(directory: str, db: Session = Depends(get_db)):
    """从目录加载所有技能"""
    skill_service = SkillService(db)
    skills = skill_service.load_skills_from_directory(directory)
    return {
        "loaded_count": len(skills),
        "skills": skills,
        "message": f"成功从目录加载 {len(skills)} 个技能"
    }


@router.get("/repositories/", response_model=List[RepositoryResponse])
def list_repositories(db: Session = Depends(get_db)):
    """获取技能仓库列表"""
    repo_service = SkillRepositoryService(db)
    return repo_service.get_repositories()


@router.post("/repositories/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(repo_data: RepositoryCreate, db: Session = Depends(get_db)):
    """创建技能仓库"""
    repo_service = SkillRepositoryService(db)
    return repo_service.create_repository(repo_data.model_dump())


@router.post("/repositories/{repository_id}/sync")
def sync_repository(repository_id: int, db: Session = Depends(get_db)):
    """同步技能仓库"""
    repo_service = SkillRepositoryService(db)
    result = repo_service.sync_repository(repository_id)
    return result
