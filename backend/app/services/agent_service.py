"""智能体服务层"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.agent import Agent
from app.models.agent_category import AgentCategory
from app.models.supplier_db import ModelDB
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services.parameter_management.agent_parameter_manager import AgentParameterManager


def create_agent(db: Session, agent: AgentCreate, user_id: int, model_id: int = None) -> Agent:
    """创建智能体，支持关联模型并自动继承模型能力和参数"""
    from app.services.audit_log_service import AuditLogService
    from app.core.dependencies import get_request
    
    # 创建智能体基本信息
    agent_dict = agent.dict()
    if model_id:
        agent_dict['model_id'] = model_id
    
    db_agent = Agent(**agent_dict, user_id=user_id)
    db.add(db_agent)
    db.flush()  # 刷新以获取agent_id
    
    # 自动继承模型能力和参数
    if model_id:
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if model:
            # 继承模型能力
            # 注意：这里需要根据实际的模型能力获取方式进行调整
            # 假设模型能力存储在model.capabilities字段中
            if hasattr(model, 'capabilities') and model.capabilities:
                db_agent.capabilities = model.capabilities
            
            # 继承模型参数
            # 注意：这里需要根据实际的模型参数获取方式进行调整
            # 假设模型参数存储在model.parameters字段中
            if hasattr(model, 'parameters') and model.parameters:
                for param in model.parameters:
                    AgentParameterManager.create_parameter(
                        db=db,
                        agent_id=db_agent.id,
                        parameter_name=param.get("parameter_name"),
                        parameter_value=param.get("parameter_value"),
                        parameter_type=param.get("parameter_type"),
                        description=param.get("description"),
                        parameter_group=param.get("parameter_group"),
                        source="model",
                        inherited=True,
                        inherited_from=f"model_{model_id}"
                    )
    
    db.commit()
    db.refresh(db_agent)
    
    # 记录审计日志
    try:
        request = get_request()
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="create",
            resource_type="agent",
            resource_id=db_agent.id,
            new_values={
                "name": db_agent.name,
                "description": db_agent.description,
                "avatar": db_agent.avatar,
                "prompt": db_agent.prompt,
                "category_id": db_agent.category_id,
                "default_model": db_agent.default_model
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"记录审计日志失败: {e}")
    
    return db_agent


def get_agent(db: Session, agent_id: int) -> Optional[Agent]:
    """根据ID获取智能体"""
    return db.query(Agent).filter(Agent.id == agent_id, Agent.is_deleted == False).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None, category_id: Optional[int] = None) -> tuple[List[Agent], int]:
    """获取智能体列表"""
    query = db.query(Agent).options(joinedload(Agent.category)).filter(Agent.is_deleted == False)
    if user_id is not None:
        query = query.filter(Agent.user_id == user_id)
    if category_id is not None:
        query = query.filter(Agent.category_id == category_id)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total


def update_agent(db: Session, agent_id: int, agent_update: AgentUpdate, user_id: int) -> Optional[Agent]:
    """更新智能体"""
    from app.services.audit_log_service import AuditLogService
    from app.core.dependencies import get_request
    
    db_agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id, Agent.is_deleted == False).first()
    if not db_agent:
        return None
    
    # 保存旧值用于审计日志
    old_values = {
        "name": db_agent.name,
        "description": db_agent.description,
        "avatar": db_agent.avatar,
        "prompt": db_agent.prompt,
        "category_id": db_agent.category_id,
        "default_model": db_agent.default_model
    }
    
    # 获取更新数据，只包含实际设置的字段（排除未设置的字段）
    update_data = agent_update.dict(exclude_unset=True)
    
    # 只更新实际提供的字段，避免将必填字段设置为None
    for key, value in update_data.items():
        setattr(db_agent, key, value)
    
    db.commit()
    db.refresh(db_agent)
    
    # 记录审计日志
    try:
        request = get_request()
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        new_values = {}
        for key in old_values.keys():
            if key in update_data:
                new_values[key] = getattr(db_agent, key)
        
        AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="update",
            resource_type="agent",
            resource_id=agent_id,
            old_values=old_values,
            new_values=new_values if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"记录审计日志失败: {e}")
    
    return db_agent


def delete_agent(db: Session, agent_id: int, user_id: int) -> bool:
    """软删除智能体"""
    from datetime import datetime
    from app.services.audit_log_service import AuditLogService
    from app.core.dependencies import get_request
    
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id, Agent.is_deleted == False).first()
    if not agent:
        return False
    
    # 保存旧值用于审计日志
    old_values = {
        "name": agent.name,
        "description": agent.description,
        "avatar": agent.avatar,
        "prompt": agent.prompt,
        "category_id": agent.category_id,
        "default_model": agent.default_model
    }
    
    agent.is_deleted = True
    agent.deleted_at = datetime.now()
    agent.deleted_by = user_id
    
    db.commit()
    
    # 记录审计日志
    try:
        request = get_request()
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="delete",
            resource_type="agent",
            resource_id=agent_id,
            old_values=old_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"记录审计日志失败: {e}")
    
    return True


def get_public_agents(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Agent], int]:
    """获取公开智能体列表"""
    query = db.query(Agent).filter(Agent.is_public == True, Agent.is_deleted == False)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total


def get_recommended_agents(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Agent], int]:
    """获取推荐智能体列表"""
    query = db.query(Agent).filter(Agent.is_recommended == True, Agent.is_deleted == False)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total


def search_agents(
    db: Session, 
    keyword: str, 
    user_id: Optional[int] = None,
    category_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
) -> tuple[List[Agent], int]:
    """
    搜索智能体
    
    Args:
        db: 数据库会话
        keyword: 搜索关键词
        user_id: 用户ID（可选）
        category_id: 分类ID（可选）
        skip: 跳过数量
        limit: 限制数量
    
    Returns:
        智能体列表和总数
    """
    query = db.query(Agent).options(joinedload(Agent.category))
    
    if user_id is not None:
        query = query.filter(Agent.user_id == user_id)
    
    if category_id is not None:
        query = query.filter(Agent.category_id == category_id)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            (Agent.name.like(keyword_pattern)) | 
            (Agent.description.like(keyword_pattern))
        )
    
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    
    return agents, total


def test_agent(
    db: Session, 
    agent_id: int, 
    user_id: int,
    test_message: str = "你好，请介绍一下你自己"
) -> dict:
    """
    测试智能体
    
    Args:
        db: 数据库会话
        agent_id: 智能体ID
        user_id: 用户ID
        test_message: 测试消息
    
    Returns:
        测试结果
    """
    from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
    
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).first()
    if not agent:
        raise ValueError("智能体不存在")
    
    try:
        messages = [
            {"role": "system", "content": agent.prompt},
            {"role": "user", "content": test_message}
        ]
        
        response = enhanced_llm_service.chat_completion(
            db=db,
            messages=messages,
            model_name=agent.default_model or "gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7
        )
        
        return {
            "success": True,
            "response": response.get("content", ""),
            "model_used": response.get("model", ""),
            "tokens_used": response.get("usage", {}).get("total_tokens", 0)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def copy_agent(
    db: Session, 
    agent_id: int, 
    user_id: int,
    new_name: Optional[str] = None
) -> Agent:
    """
    复制智能体
    
    Args:
        db: 数据库会话
        agent_id: 智能体ID
        user_id: 用户ID
        new_name: 新智能体名称（可选）
    
    Returns:
        复制后的智能体
    
    Raises:
        ValueError: 智能体不存在时抛出
    """
    source_agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id, Agent.is_deleted == False).first()
    if not source_agent:
        raise ValueError("智能体不存在")
    
    new_agent = Agent(
        name=new_name or f"{source_agent.name} (副本)",
        description=source_agent.description,
        avatar=source_agent.avatar,
        prompt=source_agent.prompt,
        knowledge_base=source_agent.knowledge_base,
        category_id=source_agent.category_id,
        default_model=source_agent.default_model,
        skills=source_agent.skills,
        is_public=False,
        is_recommended=False,
        is_favorite=False,
        user_id=user_id
    )
    
    db.add(new_agent)
    db.flush()
    
    db.commit()
    db.refresh(new_agent)
    
    return new_agent


def restore_agent(db: Session, agent_id: int, user_id: int) -> bool:
    """
    恢复已删除的智能体
    
    Args:
        db: 数据库会话
        agent_id: 智能体ID
        user_id: 用户ID
    
    Returns:
        是否恢复成功
    """
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id, Agent.is_deleted == True).first()
    if not agent:
        return False
    
    agent.is_deleted = False
    agent.deleted_at = None
    agent.deleted_by = None
    
    db.commit()
    return True


def get_deleted_agents(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> tuple[List[Agent], int]:
    """
    获取已删除的智能体列表
    
    Args:
        db: 数据库会话
        skip: 跳过数量
        limit: 限制数量
        user_id: 用户ID（可选）
    
    Returns:
        已删除智能体列表和总数
    """
    query = db.query(Agent).options(joinedload(Agent.category)).filter(Agent.is_deleted == True)
    
    if user_id is not None:
        query = query.filter(Agent.user_id == user_id)
    
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    
    return agents, total


def export_agent(db: Session, agent_id: int, user_id: int) -> dict:
    """
    导出智能体配置
    
    Args:
        db: 数据库会话
        agent_id: 智能体ID
        user_id: 用户ID
    
    Returns:
        智能体配置字典
    
    Raises:
        ValueError: 智能体不存在时抛出
    """
    from app.services.parameter_management.agent_parameter_manager import AgentParameterManager
    
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id, Agent.is_deleted == False).first()
    if not agent:
        raise ValueError("智能体不存在")
    
    export_data = {
        "version": "1.0",
        "name": agent.name,
        "description": agent.description,
        "avatar": agent.avatar,
        "prompt": agent.prompt,
        "knowledge_base": agent.knowledge_base,
        "category": {
            "id": agent.category_id,
            "name": agent.category.name if agent.category else None
        } if agent.category else None,
        "default_model": agent.default_model,
        "skills": agent.skills,
        "is_public": False,
        "is_recommended": False,
        "is_favorite": False,
        "parameters": []
    }
    
    # 导出参数
    parameters = AgentParameterManager.get_agent_parameters(db, agent_id)
    export_data["parameters"] = [
        {
            "parameter_name": param.parameter_name,
            "parameter_value": param.parameter_value,
            "parameter_type": param.parameter_type,
            "description": param.description,
            "parameter_group": param.parameter_group,
            "source": param.source,
            "inherited": param.inherited,
            "inherited_from": param.inherited_from
        }
        for param in parameters
    ]
    
    return export_data


def import_agent(db: Session, import_data: dict, user_id: int) -> Agent:
    """
    导入智能体配置
    
    Args:
        db: 数据库会话
        import_data: 导入数据
        user_id: 用户ID
    
    Returns:
        导入的智能体
    
    Raises:
        ValueError: 数据格式错误时抛出
    """
    from app.services.parameter_management.agent_parameter_manager import AgentParameterManager
    
    if not import_data.get("name"):
        raise ValueError("智能体名称不能为空")
    
    new_agent = Agent(
        name=import_data.get("name"),
        description=import_data.get("description"),
        avatar=import_data.get("avatar", "🤖"),
        prompt=import_data.get("prompt", ""),
        knowledge_base=import_data.get("knowledge_base"),
        category_id=import_data.get("category", {}).get("id") if import_data.get("category") else None,
        default_model=import_data.get("default_model"),
        skills=import_data.get("skills", []),
        is_public=False,
        is_recommended=False,
        is_favorite=False,
        user_id=user_id
    )
    
    db.add(new_agent)
    db.flush()
    
    # 导入参数
    parameters = import_data.get("parameters", [])
    for param in parameters:
        try:
            AgentParameterManager.create_parameter(
                db=db,
                agent_id=new_agent.id,
                parameter_name=param.get("parameter_name"),
                parameter_value=param.get("parameter_value"),
                parameter_type=param.get("parameter_type"),
                description=param.get("description"),
                parameter_group=param.get("parameter_group"),
                source=param.get("source", "imported"),
                inherited=param.get("inherited", False),
                inherited_from=param.get("inherited_from")
            )
        except Exception as e:
            print(f"导入参数失败: {e}")
    
    db.commit()
    db.refresh(new_agent)
    
    return new_agent