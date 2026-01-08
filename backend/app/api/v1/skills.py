"""技能管理相关API接口"""
from typing import Any, List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.dependencies import (
    get_db,
    get_skill_service,
    get_session_service,
    get_execution_service,
    get_repository_service,
    get_skill_execution_engine
)
from app.services.skill_execution_engine import SkillExecutionEngine
from app.api.deps import get_current_active_user, get_current_active_superuser
from app.models.skill import Skill
from app.models.user import User
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


class SkillArtifactResponse(BaseModel):
    id: int
    name: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


class SkillExecutionResponse(BaseModel):
    execution_id: int
    skill_id: int
    status: str
    input_params: Dict[str, Any]
    output_result: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[SkillArtifactResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


class SkillExecuteResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int
    execution_id: Optional[int] = None
    artifacts: List[SkillArtifactResponse] = Field(default_factory=list)


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


# 技能版本相关模型
class SkillVersionCreate(BaseModel):
    version: str = Field(..., max_length=50)
    content: Optional[str] = None
    description: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    requirements: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    change_log: Optional[str] = None


class SkillVersionResponse(BaseModel):
    id: int
    skill_id: int
    version: str
    description: Optional[str]
    tags: List[str]
    is_current: bool
    change_log: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


class SkillVersionCompareRequest(BaseModel):
    version_id_1: int
    version_id_2: int


class SkillVersionCompareResponse(BaseModel):
    version1: str
    version2: str
    diffs: Dict[str, Any]


router = APIRouter()


@router.get("", response_model=SkillListResponse)
def list_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    skill_service: SkillService = Depends(get_skill_service)
):
    """获取技能列表"""
    tags_list = tags.split(',') if tags else None
    skills, total = skill_service.get_skills(skip=skip, limit=limit, status=status, tags=tags_list, search=search)
    return {
        "skills": skills,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(skill_id: int, current_user: User = Depends(get_current_active_user), skill_service: SkillService = Depends(get_skill_service)):
    """获取单个技能详情"""
    skill = skill_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(skill_data: SkillCreate, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """创建新技能"""
    existing = skill_service.get_skill_by_name(skill_data.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名称已存在")
    skill = skill_service.create_skill(skill_data.model_dump())
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(skill_id: int, skill_data: SkillUpdate, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """更新技能"""
    skill = skill_service.update_skill(skill_id, skill_data.model_dump(exclude_unset=True))
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """删除技能"""
    if not skill_service.delete_skill(skill_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return None


@router.post("/{skill_id}/enable", response_model=SkillResponse)
def enable_skill(skill_id: int, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """启用技能"""
    skill = skill_service.enable_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.post("/{skill_id}/disable", response_model=SkillResponse)
def disable_skill(skill_id: int, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """禁用技能"""
    skill = skill_service.disable_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


@router.post("/match", response_model=SkillMatchResponse)
def match_skills(request: SkillMatchRequest, current_user: User = Depends(get_current_active_user), skill_service: SkillService = Depends(get_skill_service)):
    """根据任务描述匹配技能"""
    matched_skills = skill_service.match_skills(request.task_description, limit=request.limit)
    return {
        "matched_skills": matched_skills,
        "task_description": request.task_description
    }


@router.post("/activate", response_model=List[SkillResponse])
def activate_skills(request: SkillActivateRequest, current_user: User = Depends(get_current_active_user), session_service: SkillSessionService = Depends(get_session_service), skill_service: SkillService = Depends(get_skill_service)):
    """在会话中激活技能"""
    sessions = session_service.activate_skills(
        conversation_id=request.conversation_id,
        skill_ids=request.skill_ids,
        context=request.context
    )
    skills = [session_service.db.query(Skill).filter(Skill.id == session.skill_id).first() for session in sessions]
    return [s for s in skills if s is not None]


@router.post("/deactivate")
def deactivate_skills(
    conversation_id: int,
    skill_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_current_active_user),
    session_service: SkillSessionService = Depends(get_session_service)
):
    """在会话中停用技能"""
    count = session_service.deactivate_skills(conversation_id, skill_ids)
    return {"deactivated_count": count}


@router.get("/context/{conversation_id}")
def get_active_skills(conversation_id: int, current_user: User = Depends(get_current_active_user), session_service: SkillSessionService = Depends(get_session_service), skill_service: SkillService = Depends(get_skill_service)):
    """获取会话中激活的技能"""
    sessions = session_service.get_active_skills(conversation_id)
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
    current_user: User = Depends(get_current_active_user),
    skill_execution_engine: SkillExecutionEngine = Depends(get_skill_execution_engine)
):
    """执行技能"""
    result = skill_execution_engine.execute(
        skill_id=skill_id,
        task=request.task,
        params=request.params,
        session_id=session_id,
        conversation_id=conversation_id
    )
    return SkillExecuteResponse(**result)


@router.post("/load-from-file")
def load_skill_from_file(file_path: str, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """从文件加载技能"""
    skill = skill_service.load_skill_from_file(file_path)
    if not skill:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法加载技能文件")
    return {"skill": skill, "message": "技能加载成功"}


@router.post("/load-from-directory")
def load_skills_from_directory(directory: str, current_user: User = Depends(get_current_active_superuser), skill_service: SkillService = Depends(get_skill_service)):
    """从目录加载所有技能"""
    skills = skill_service.load_skills_from_directory(directory)
    return {
        "loaded_count": len(skills),
        "skills": skills,
        "message": f"成功从目录加载 {len(skills)} 个技能"
    }


@router.get("/repositories/", response_model=List[RepositoryResponse])
def list_repositories(current_user: User = Depends(get_current_active_superuser), repo_service: SkillRepositoryService = Depends(get_repository_service)):
    """获取技能仓库列表"""
    return repo_service.get_repositories()


@router.post("/repositories/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(repo_data: RepositoryCreate, current_user: User = Depends(get_current_active_superuser), repo_service: SkillRepositoryService = Depends(get_repository_service)):
    """创建技能仓库"""
    return repo_service.create_repository(repo_data.model_dump())


@router.post("/repositories/{repository_id}/sync")
def sync_repository(repository_id: int, current_user: User = Depends(get_current_active_superuser), repo_service: SkillRepositoryService = Depends(get_repository_service)):
    """同步技能仓库"""
    result = repo_service.sync_repository(repository_id)
    return result


# 技能版本管理相关API
@router.get("/{skill_id}/versions", response_model=List[SkillVersionResponse])
def get_skill_versions(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    skill_service: SkillService = Depends(get_skill_service)
):
    """获取技能版本列表"""
    versions = skill_service.get_skill_versions(skill_id)
    return versions


@router.get("/versions/{version_id}", response_model=SkillVersionResponse)
def get_version(
    version_id: int,
    current_user: User = Depends(get_current_active_user),
    skill_service: SkillService = Depends(get_skill_service)
):
    """获取单个版本详情"""
    version = skill_service.get_skill_version(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
    return version


@router.post("/{skill_id}/versions", response_model=SkillVersionResponse, status_code=status.HTTP_201_CREATED)
def create_version(
    skill_id: int,
    version_data: SkillVersionCreate,
    current_user: User = Depends(get_current_active_superuser),
    skill_service: SkillService = Depends(get_skill_service)
):
    """创建新的技能版本"""
    version = skill_service.create_skill_version(
        skill_id=skill_id,
        version_data={**version_data.model_dump(), "author_id": current_user.id}
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return version


@router.post("/{skill_id}/versions/{version_id}/rollback", response_model=SkillResponse)
def rollback_version(
    skill_id: int,
    version_id: int,
    current_user: User = Depends(get_current_active_superuser),
    skill_service: SkillService = Depends(get_skill_service)
):
    """回滚到指定版本"""
    skill = skill_service.rollback_skill_version(skill_id, version_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能或版本不存在")
    return skill


@router.post("/versions/compare", response_model=SkillVersionCompareResponse)
def compare_versions(
    compare_request: SkillVersionCompareRequest,
    current_user: User = Depends(get_current_active_user),
    skill_service: SkillService = Depends(get_skill_service)
):
    """比较两个版本的差异"""
    diffs = skill_service.compare_skill_versions(compare_request.version_id_1, compare_request.version_id_2)
    if not diffs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
    return diffs


@router.get("/executions/{execution_id}/artifacts", response_model=List[SkillArtifactResponse])
def get_execution_artifacts(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取技能执行产生的artifacts列表"""
    from app.models.skill import SkillExecutionLog, SkillArtifact
    
    execution = db.query(SkillExecutionLog).filter(SkillExecutionLog.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能执行记录不存在")
    
    artifacts = db.query(SkillArtifact).filter(SkillArtifact.skill_execution_id == execution_id).all()
    return artifacts


@router.get("/artifacts/{artifact_id}")
def get_artifact_content(
    artifact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个artifact的内容"""
    from app.models.skill import SkillArtifact
    
    artifact = db.query(SkillArtifact).filter(SkillArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact不存在")
    
    return {
        "id": artifact.id,
        "name": artifact.name,
        "type": artifact.type,
        "content": artifact.content,
        "created_at": artifact.created_at
    }


# 技能依赖管理相关模型
class SkillDependencyCreate(BaseModel):
    dependency_skill_id: int = Field(..., ge=1)
    version_requirement: Optional[str] = Field(None, max_length=50)


class SkillDependencyResponse(BaseModel):
    id: int
    skill_id: int
    dependency_skill_id: int
    version_requirement: Optional[str]
    dependency_skill_name: str
    dependency_skill_version: str
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


class SkillDependencyCheckResponse(BaseModel):
    skill_id: int
    skill_name: str
    dependency_skill_id: int
    dependency_skill_name: str
    version_requirement: Optional[str]
    current_version: str
    is_compatible: bool
    missing_dependencies: List[str] = Field(default_factory=list)
    incompatible_dependencies: List[Dict[str, Any]] = Field(default_factory=list)


# 技能依赖管理相关API
@router.get("/{skill_id}/dependencies", response_model=List[SkillDependencyResponse])
def get_skill_dependencies(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取技能的依赖列表"""
    from app.models.skill import SkillDependency, Skill
    
    dependencies = db.query(SkillDependency).filter(SkillDependency.skill_id == skill_id).all()
    
    result = []
    for dep in dependencies:
        dependency_skill = db.query(Skill).filter(Skill.id == dep.dependency_skill_id).first()
        if dependency_skill:
            result.append({
                "id": dep.id,
                "skill_id": dep.skill_id,
                "dependency_skill_id": dep.dependency_skill_id,
                "version_requirement": dep.version_requirement,
                "dependency_skill_name": dependency_skill.name,
                "dependency_skill_version": dependency_skill.version,
                "created_at": dep.created_at
            })
    
    return result


@router.post("/{skill_id}/dependencies", response_model=SkillDependencyResponse, status_code=status.HTTP_201_CREATED)
def add_skill_dependency(
    skill_id: int,
    dependency_data: SkillDependencyCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """为技能添加依赖"""
    from app.models.skill import SkillDependency, Skill
    
    # 检查技能是否存在
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    # 检查依赖技能是否存在
    dependency_skill = db.query(Skill).filter(Skill.id == dependency_data.dependency_skill_id).first()
    if not dependency_skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="依赖技能不存在")
    
    # 检查是否已存在相同依赖
    existing = db.query(SkillDependency).filter(
        SkillDependency.skill_id == skill_id,
        SkillDependency.dependency_skill_id == dependency_data.dependency_skill_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该依赖已存在")
    
    # 创建依赖关系
    dependency = SkillDependency(
        skill_id=skill_id,
        dependency_skill_id=dependency_data.dependency_skill_id,
        version_requirement=dependency_data.version_requirement,
        created_at=datetime.now()
    )
    
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    
    return {
        "id": dependency.id,
        "skill_id": dependency.skill_id,
        "dependency_skill_id": dependency.dependency_skill_id,
        "version_requirement": dependency.version_requirement,
        "dependency_skill_name": dependency_skill.name,
        "dependency_skill_version": dependency_skill.version,
        "created_at": dependency.created_at
    }


@router.delete("/{skill_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill_dependency(
    skill_id: int,
    dependency_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """移除技能的依赖"""
    from app.models.skill import SkillDependency
    
    dependency = db.query(SkillDependency).filter(
        SkillDependency.id == dependency_id,
        SkillDependency.skill_id == skill_id
    ).first()
    
    if not dependency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="依赖关系不存在")
    
    db.delete(dependency)
    db.commit()
    
    return None


@router.get("/{skill_id}/dependencies/check", response_model=SkillDependencyCheckResponse)
def check_skill_dependencies(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检查技能的依赖兼容性"""
    from app.models.skill import SkillDependency, Skill
    from app.services.skill_execution_engine import SkillExecutionEngine
    
    # 获取技能
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    # 获取所有依赖
    dependencies = db.query(SkillDependency).filter(SkillDependency.skill_id == skill_id).all()
    
    # 创建执行引擎实例用于版本检查
    execution_engine = SkillExecutionEngine(db)
    
    missing_dependencies = []
    incompatible_dependencies = []
    
    for dep in dependencies:
        dependency_skill = db.query(Skill).filter(Skill.id == dep.dependency_skill_id).first()
        
        if not dependency_skill:
            missing_dependencies.append(f"技能ID: {dep.dependency_skill_id}")
            continue
        
        # 检查版本兼容性
        if dep.version_requirement:
            is_compatible = execution_engine._check_version_compatibility(
                dependency_skill.version, 
                dep.version_requirement
            )
            
            if not is_compatible:
                incompatible_dependencies.append({
                    "dependency_skill_id": dep.dependency_skill_id,
                    "dependency_skill_name": dependency_skill.name,
                    "version_requirement": dep.version_requirement,
                    "current_version": dependency_skill.version
                })
    
    return {
        "skill_id": skill_id,
        "skill_name": skill.name,
        "dependency_skill_id": dependencies[0].dependency_skill_id if dependencies else 0,
        "dependency_skill_name": dependencies[0].dependency_skill.name if dependencies else "",
        "version_requirement": dependencies[0].version_requirement if dependencies else None,
        "current_version": dependencies[0].dependency_skill.version if dependencies else "",
        "is_compatible": len(missing_dependencies) == 0 and len(incompatible_dependencies) == 0,
        "missing_dependencies": missing_dependencies,
        "incompatible_dependencies": incompatible_dependencies
    }


@router.get("/{skill_id}/dependencies/resolve", response_model=Dict[str, Any])
def resolve_skill_dependencies(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """解析技能的所有依赖关系（包括间接依赖）"""
    from app.models.skill import SkillDependency, Skill
    
    def resolve_dependencies(skill_id: int, visited: set = None) -> Dict[str, Any]:
        if visited is None:
            visited = set()
        
        if skill_id in visited:
            return {"skill_id": skill_id, "circular": True}
        
        visited.add(skill_id)
        
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return {"skill_id": skill_id, "error": "技能不存在"}
        
        dependencies = db.query(SkillDependency).filter(SkillDependency.skill_id == skill_id).all()
        
        result = {
            "skill_id": skill_id,
            "skill_name": skill.name,
            "version": skill.version,
            "direct_dependencies": [],
            "transitive_dependencies": []
        }
        
        for dep in dependencies:
            dependency_skill = db.query(Skill).filter(Skill.id == dep.dependency_skill_id).first()
            if dependency_skill:
                direct_dep = {
                    "skill_id": dep.dependency_skill_id,
                    "skill_name": dependency_skill.name,
                    "version_requirement": dep.version_requirement,
                    "current_version": dependency_skill.version
                }
                result["direct_dependencies"].append(direct_dep)
                
                # 递归解析间接依赖
                transitive = resolve_dependencies(dep.dependency_skill_id, visited.copy())
                result["transitive_dependencies"].append(transitive)
        
        return result
    
    return resolve_dependencies(skill_id)


# 技能执行流程相关模型
class ExecutionFlowStep(BaseModel):
    order: int = Field(..., ge=1)
    type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ExecutionFlowUpdate(BaseModel):
    flow: List[ExecutionFlowStep] = Field(default_factory=list)


# 技能执行流程相关API
@router.get("/{skill_id}/execution-flow", response_model=Dict[str, Any])
def get_skill_execution_flow(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取技能的执行流程"""
    from app.models.skill import Skill
    
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    return {
        "skill_id": skill_id,
        "skill_name": skill.name,
        "execution_flow": skill.execution_flow or []
    }


@router.put("/{skill_id}/execution-flow", response_model=Dict[str, Any])
def update_skill_execution_flow(
    skill_id: int,
    flow_data: ExecutionFlowUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """更新技能的执行流程"""
    from app.models.skill import Skill
    
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    # 验证执行流程数据
    for step in flow_data.flow:
        if not step.order or step.order < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="执行步骤顺序必须大于0")
        if not step.type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="执行步骤类型不能为空")
        if not step.name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="执行步骤名称不能为空")
    
    # 更新执行流程
    skill.execution_flow = flow_data.flow
    db.commit()
    
    return {
        "skill_id": skill_id,
        "skill_name": skill.name,
        "execution_flow": skill.execution_flow,
        "message": "执行流程更新成功"
    }


# 技能Artifacts相关模型
class SkillArtifactResponse(BaseModel):
    id: int
    skill_id: int
    execution_log_id: int
    name: str
    type: str
    content: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', pre=True, always=True)
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, AttributeError):
            return None


# 技能Artifacts相关API
@router.get("/{skill_id}/artifacts/{execution_log_id}", response_model=Dict[str, Any])
def get_skill_artifacts(
    skill_id: int,
    execution_log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取技能执行生成的artifacts"""
    from app.models.skill import Skill, SkillExecutionLog, SkillArtifact
    
    # 检查技能是否存在
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    # 检查执行日志是否存在
    execution_log = db.query(SkillExecutionLog).filter(
        SkillExecutionLog.id == execution_log_id,
        SkillExecutionLog.skill_id == skill_id
    ).first()
    
    if not execution_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行日志不存在")
    
    # 获取artifacts
    artifacts = db.query(SkillArtifact).filter(
        SkillArtifact.skill_id == skill_id,
        SkillArtifact.execution_log_id == execution_log_id
    ).all()
    
    return {
        "skill_id": skill_id,
        "execution_log_id": execution_log_id,
        "artifacts": [
            {
                "id": artifact.id,
                "skill_id": artifact.skill_id,
                "execution_log_id": artifact.execution_log_id,
                "name": artifact.name,
                "type": artifact.type,
                "content": artifact.content,
                "file_path": artifact.file_path,
                "metadata": artifact.metadata or {},
                "created_at": artifact.created_at
            }
            for artifact in artifacts
        ]
    }


@router.get("/{skill_id}/artifacts/{execution_log_id}/{artifact_id}/download")
def download_skill_artifact(
    skill_id: int,
    execution_log_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """下载技能artifact文件"""
    from app.models.skill import Skill, SkillExecutionLog, SkillArtifact
    
    # 检查技能是否存在
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    # 检查执行日志是否存在
    execution_log = db.query(SkillExecutionLog).filter(
        SkillExecutionLog.id == execution_log_id,
        SkillExecutionLog.skill_id == skill_id
    ).first()
    
    if not execution_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行日志不存在")
    
    # 检查artifact是否存在
    artifact = db.query(SkillArtifact).filter(
        SkillArtifact.id == artifact_id,
        SkillArtifact.skill_id == skill_id,
        SkillArtifact.execution_log_id == execution_log_id
    ).first()
    
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact不存在")
    
    if not artifact.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该Artifact没有文件路径")
    
    # 这里应该返回文件下载响应，暂时返回文件路径信息
    return {
        "artifact_id": artifact_id,
        "file_path": artifact.file_path,
        "name": artifact.name,
        "type": artifact.type
    }


@router.get("/{skill_id}/artifacts/{execution_log_id}/{artifact_id}/preview", response_model=Dict[str, Any])
def preview_skill_artifact(
    skill_id: int,
    execution_log_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """预览技能artifact内容"""
    from app.models.skill import Skill, SkillExecutionLog, SkillArtifact
    
    # 检查技能是否存在
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    
    # 检查执行日志是否存在
    execution_log = db.query(SkillExecutionLog).filter(
        SkillExecutionLog.id == execution_log_id,
        SkillExecutionLog.skill_id == skill_id
    ).first()
    
    if not execution_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行日志不存在")
    
    # 检查artifact是否存在
    artifact = db.query(SkillArtifact).filter(
        SkillArtifact.id == artifact_id,
        SkillArtifact.skill_id == skill_id,
        SkillArtifact.execution_log_id == execution_log_id
    ).first()
    
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact不存在")
    
    return {
        "id": artifact.id,
        "skill_id": artifact.skill_id,
        "execution_log_id": artifact.execution_log_id,
        "name": artifact.name,
        "type": artifact.type,
        "content": artifact.content,
        "file_path": artifact.file_path,
        "metadata": artifact.metadata or {},
        "created_at": artifact.created_at
    }
