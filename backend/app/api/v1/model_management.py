"""模型管理API - 包含Webhook、配置、生命周期、配额管理"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.model_webhook import ModelWebhook, WebhookDelivery
from app.models.model_config import ModelConfig, ModelConfigVersion
from app.models.model_lifecycle import ModelLifecycle, LifecycleTransition, LifecycleApproval, LifecycleStatus
from app.models.model_quota import ModelQuota, QuotaUsage, QuotaPeriod

router = APIRouter(prefix="/model-management", tags=["model-management"])


# ========== Webhook管理 ==========

class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    model_id: Optional[int] = None
    supplier_id: Optional[int] = None
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: List[str]
    description: Optional[str]
    model_id: Optional[int]
    supplier_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    last_trigger_status: Optional[str]

    class Config:
        from_attributes = True


@router.get("/webhooks", response_model=List[WebhookResponse])
def get_webhooks(
    search: Optional[str] = Query(None),
    model_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """获取Webhook列表"""
    query = db.query(ModelWebhook)
    
    if search:
        query = query.filter(ModelWebhook.name.contains(search))
    if model_id:
        query = query.filter(ModelWebhook.model_id == model_id)
    if supplier_id:
        query = query.filter(ModelWebhook.supplier_id == supplier_id)
    if is_active is not None:
        query = query.filter(ModelWebhook.is_active == is_active)
    
    webhooks = query.order_by(ModelWebhook.created_at.desc()).all()
    return webhooks


@router.post("/webhooks", response_model=WebhookResponse)
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """创建Webhook"""
    db_webhook = ModelWebhook(**webhook.dict())
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """获取Webhook详情"""
    webhook = db.query(ModelWebhook).filter(ModelWebhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    return webhook


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
def update_webhook(webhook_id: int, webhook: WebhookUpdate, db: Session = Depends(get_db)):
    """更新Webhook"""
    db_webhook = db.query(ModelWebhook).filter(ModelWebhook.id == webhook_id).first()
    if not db_webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    for key, value in webhook.dict(exclude_unset=True).items():
        setattr(db_webhook, key, value)
    
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """删除Webhook"""
    db_webhook = db.query(ModelWebhook).filter(ModelWebhook.id == webhook_id).first()
    if not db_webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    db.delete(db_webhook)
    db.commit()
    return {"message": "Webhook删除成功"}


@router.post("/webhooks/{webhook_id}/test")
def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """测试Webhook"""
    webhook = db.query(ModelWebhook).filter(ModelWebhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 模拟发送测试请求
    webhook.last_triggered_at = datetime.utcnow()
    webhook.last_trigger_status = "success"
    db.commit()
    
    return {"message": "Webhook测试成功", "status": "success"}


# ========== 配置管理 ==========

class ConfigCreate(BaseModel):
    key: str
    name: str
    value: Optional[str] = None
    value_type: str = "string"
    description: Optional[str] = None
    environment: str = "production"
    is_encrypted: bool = False
    model_id: Optional[int] = None
    supplier_id: Optional[int] = None
    is_active: bool = True


class ConfigUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    is_encrypted: Optional[bool] = None
    is_active: Optional[bool] = None


class ConfigResponse(BaseModel):
    id: int
    key: str
    name: str
    value: Optional[str]
    value_type: str
    description: Optional[str]
    environment: str
    is_encrypted: bool
    model_id: Optional[int]
    supplier_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        from_attributes = True


@router.get("/configs", response_model=List[ConfigResponse])
def get_configs(
    search: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    model_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """获取配置列表"""
    query = db.query(ModelConfig)
    
    if search:
        query = query.filter(
            (ModelConfig.key.contains(search)) | 
            (ModelConfig.name.contains(search))
        )
    if environment:
        query = query.filter(ModelConfig.environment == environment)
    if model_id:
        query = query.filter(ModelConfig.model_id == model_id)
    if supplier_id:
        query = query.filter(ModelConfig.supplier_id == supplier_id)
    if is_active is not None:
        query = query.filter(ModelConfig.is_active == is_active)
    
    configs = query.order_by(ModelConfig.created_at.desc()).all()
    return configs


@router.post("/configs", response_model=ConfigResponse)
def create_config(config: ConfigCreate, db: Session = Depends(get_db)):
    """创建配置"""
    # 检查key是否已存在
    existing = db.query(ModelConfig).filter(ModelConfig.key == config.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置key已存在")
    
    db_config = ModelConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/configs/{config_id}", response_model=ConfigResponse)
def get_config(config_id: int, db: Session = Depends(get_db)):
    """获取配置详情"""
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.put("/configs/{config_id}", response_model=ConfigResponse)
def update_config(config_id: int, config: ConfigUpdate, db: Session = Depends(get_db)):
    """更新配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 保存旧版本
    if config.value is not None and config.value != db_config.value:
        version = ModelConfigVersion(
            config_id=config_id,
            value=db_config.value,
            value_type=db_config.value_type,
            changed_by=db_config.updated_by
        )
        db.add(version)
    
    for key, value in config.dict(exclude_unset=True).items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """删除配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.delete(db_config)
    db.commit()
    return {"message": "配置删除成功"}


@router.post("/configs/{config_id}/rollback/{version_id}")
def rollback_config(config_id: int, version_id: int, db: Session = Depends(get_db)):
    """回滚配置到指定版本"""
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    version = db.query(ModelConfigVersion).filter(
        ModelConfigVersion.id == version_id,
        ModelConfigVersion.config_id == config_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 保存当前版本
    current_version = ModelConfigVersion(
        config_id=config_id,
        value=config.value,
        value_type=config.value_type,
        changed_by=config.updated_by
    )
    db.add(current_version)
    
    # 回滚
    config.value = version.value
    config.value_type = version.value_type
    db.commit()
    
    return {"message": "配置回滚成功"}


# ========== 生命周期管理 ==========

class LifecycleCreate(BaseModel):
    model_id: int
    current_status: str = LifecycleStatus.DRAFT.value
    version: Optional[str] = None
    release_notes: Optional[str] = None
    migration_guide: Optional[str] = None


class LifecycleUpdate(BaseModel):
    current_status: Optional[str] = None
    version: Optional[str] = None
    release_notes: Optional[str] = None
    migration_guide: Optional[str] = None


class TransitionCreate(BaseModel):
    from_status: str
    to_status: str
    reason: Optional[str] = None


class ApprovalCreate(BaseModel):
    approver: str
    approval_status: str
    comments: Optional[str] = None


class LifecycleResponse(BaseModel):
    id: int
    model_id: int
    current_status: str
    previous_status: Optional[str]
    status_changed_at: datetime
    status_changed_by: Optional[str]
    version: Optional[str]
    release_notes: Optional[str]
    migration_guide: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    id: int
    lifecycle_id: int
    transition_id: int
    approver: str
    approval_status: str
    comments: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 注意：/lifecycles/approvals 必须在 /lifecycles/{lifecycle_id} 之前定义
@router.get("/lifecycles/approvals", response_model=List[ApprovalResponse])
def get_approvals(
    lifecycle_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取审批列表"""
    query = db.query(LifecycleApproval)

    if lifecycle_id:
        query = query.filter(LifecycleApproval.lifecycle_id == lifecycle_id)
    if status:
        query = query.filter(LifecycleApproval.approval_status == status)

    approvals = query.order_by(LifecycleApproval.created_at.desc()).all()
    return approvals


@router.get("/lifecycles", response_model=List[LifecycleResponse])
def get_lifecycles(
    model_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取生命周期列表"""
    query = db.query(ModelLifecycle)
    
    if model_id:
        query = query.filter(ModelLifecycle.model_id == model_id)
    if status:
        query = query.filter(ModelLifecycle.current_status == status)
    
    lifecycles = query.order_by(ModelLifecycle.created_at.desc()).all()
    return lifecycles


@router.post("/lifecycles", response_model=LifecycleResponse)
def create_lifecycle(lifecycle: LifecycleCreate, db: Session = Depends(get_db)):
    """创建生命周期"""
    # 检查模型是否已有生命周期
    existing = db.query(ModelLifecycle).filter(
        ModelLifecycle.model_id == lifecycle.model_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该模型已有生命周期记录")
    
    db_lifecycle = ModelLifecycle(**lifecycle.dict())
    db.add(db_lifecycle)
    db.commit()
    db.refresh(db_lifecycle)
    return db_lifecycle


@router.get("/lifecycles/{lifecycle_id}", response_model=LifecycleResponse)
def get_lifecycle(lifecycle_id: int, db: Session = Depends(get_db)):
    """获取生命周期详情"""
    lifecycle = db.query(ModelLifecycle).filter(ModelLifecycle.id == lifecycle_id).first()
    if not lifecycle:
        raise HTTPException(status_code=404, detail="生命周期记录不存在")
    return lifecycle


@router.put("/lifecycles/{lifecycle_id}", response_model=LifecycleResponse)
def update_lifecycle(lifecycle_id: int, lifecycle: LifecycleUpdate, db: Session = Depends(get_db)):
    """更新生命周期"""
    db_lifecycle = db.query(ModelLifecycle).filter(ModelLifecycle.id == lifecycle_id).first()
    if not db_lifecycle:
        raise HTTPException(status_code=404, detail="生命周期记录不存在")
    
    for key, value in lifecycle.dict(exclude_unset=True).items():
        setattr(db_lifecycle, key, value)
    
    db.commit()
    db.refresh(db_lifecycle)
    return db_lifecycle


@router.post("/lifecycles/{lifecycle_id}/transitions")
def create_transition(lifecycle_id: int, transition: TransitionCreate, db: Session = Depends(get_db)):
    """创建状态流转"""
    lifecycle = db.query(ModelLifecycle).filter(ModelLifecycle.id == lifecycle_id).first()
    if not lifecycle:
        raise HTTPException(status_code=404, detail="生命周期记录不存在")
    
    db_transition = LifecycleTransition(
        lifecycle_id=lifecycle_id,
        **transition.dict()
    )
    db.add(db_transition)
    
    # 更新生命周期状态
    lifecycle.previous_status = lifecycle.current_status
    lifecycle.current_status = transition.to_status
    lifecycle.status_changed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_transition)
    return db_transition


@router.post("/lifecycles/{lifecycle_id}/approvals")
def create_approval(lifecycle_id: int, approval: ApprovalCreate, db: Session = Depends(get_db)):
    """创建审批记录"""
    lifecycle = db.query(ModelLifecycle).filter(ModelLifecycle.id == lifecycle_id).first()
    if not lifecycle:
        raise HTTPException(status_code=404, detail="生命周期记录不存在")
    
    db_approval = LifecycleApproval(
        lifecycle_id=lifecycle_id,
        **approval.dict()
    )
    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)
    return db_approval


# ========== 配额管理 ==========

class QuotaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_id: Optional[int] = None
    supplier_id: Optional[int] = None
    user_id: Optional[str] = None
    api_key_id: Optional[str] = None
    max_requests: int = 1000
    max_tokens: int = 1000000
    max_cost: float = 100.0
    period: str = QuotaPeriod.DAILY.value
    warning_threshold: float = 0.8
    is_active: bool = True


class QuotaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_requests: Optional[int] = None
    max_tokens: Optional[int] = None
    max_cost: Optional[float] = None
    period: Optional[str] = None
    warning_threshold: Optional[float] = None
    is_active: Optional[bool] = None


class QuotaUsageCreate(BaseModel):
    requests_used: int = 0
    tokens_used: int = 0
    cost_incurred: float = 0.0
    details: Optional[dict] = None


class QuotaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    model_id: Optional[int]
    supplier_id: Optional[int]
    user_id: Optional[str]
    api_key_id: Optional[str]
    max_requests: int
    max_tokens: int
    max_cost: float
    current_requests: int
    current_tokens: int
    current_cost: float
    period: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    warning_threshold: float
    is_active: bool
    is_exceeded: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/quotas", response_model=List[QuotaResponse])
def get_quotas(
    search: Optional[str] = Query(None),
    model_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """获取配额列表"""
    query = db.query(ModelQuota)
    
    if search:
        query = query.filter(ModelQuota.name.contains(search))
    if model_id:
        query = query.filter(ModelQuota.model_id == model_id)
    if supplier_id:
        query = query.filter(ModelQuota.supplier_id == supplier_id)
    if user_id:
        query = query.filter(ModelQuota.user_id == user_id)
    if period:
        query = query.filter(ModelQuota.period == period)
    if is_active is not None:
        query = query.filter(ModelQuota.is_active == is_active)
    
    quotas = query.order_by(ModelQuota.created_at.desc()).all()
    return quotas


@router.post("/quotas", response_model=QuotaResponse)
def create_quota(quota: QuotaCreate, db: Session = Depends(get_db)):
    """创建配额"""
    db_quota = ModelQuota(**quota.dict())
    db.add(db_quota)
    db.commit()
    db.refresh(db_quota)
    return db_quota


@router.get("/quotas/{quota_id}", response_model=QuotaResponse)
def get_quota(quota_id: int, db: Session = Depends(get_db)):
    """获取配额详情"""
    quota = db.query(ModelQuota).filter(ModelQuota.id == quota_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")
    return quota


@router.put("/quotas/{quota_id}", response_model=QuotaResponse)
def update_quota(quota_id: int, quota: QuotaUpdate, db: Session = Depends(get_db)):
    """更新配额"""
    db_quota = db.query(ModelQuota).filter(ModelQuota.id == quota_id).first()
    if not db_quota:
        raise HTTPException(status_code=404, detail="配额不存在")
    
    for key, value in quota.dict(exclude_unset=True).items():
        setattr(db_quota, key, value)
    
    db.commit()
    db.refresh(db_quota)
    return db_quota


@router.delete("/quotas/{quota_id}")
def delete_quota(quota_id: int, db: Session = Depends(get_db)):
    """删除配额"""
    db_quota = db.query(ModelQuota).filter(ModelQuota.id == quota_id).first()
    if not db_quota:
        raise HTTPException(status_code=404, detail="配额不存在")
    
    db.delete(db_quota)
    db.commit()
    return {"message": "配额删除成功"}


@router.post("/quotas/{quota_id}/usage")
def record_usage(quota_id: int, usage: QuotaUsageCreate, db: Session = Depends(get_db)):
    """记录配额使用"""
    quota = db.query(ModelQuota).filter(ModelQuota.id == quota_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")
    
    # 创建使用记录
    db_usage = QuotaUsage(quota_id=quota_id, **usage.dict())
    db.add(db_usage)
    
    # 更新配额使用量
    quota.current_requests += usage.requests_used
    quota.current_tokens += usage.tokens_used
    quota.current_cost += usage.cost_incurred
    
    # 检查是否超出配额
    if (quota.current_requests >= quota.max_requests or
        quota.current_tokens >= quota.max_tokens or
        quota.current_cost >= quota.max_cost):
        quota.is_exceeded = True
    
    db.commit()
    db.refresh(db_usage)
    return db_usage


@router.post("/quotas/{quota_id}/reset")
def reset_quota(quota_id: int, db: Session = Depends(get_db)):
    """重置配额使用量"""
    quota = db.query(ModelQuota).filter(ModelQuota.id == quota_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")
    
    quota.current_requests = 0
    quota.current_tokens = 0
    quota.current_cost = 0.0
    quota.is_exceeded = False
    quota.period_start = datetime.utcnow()
    
    db.commit()
    return {"message": "配额重置成功"}
