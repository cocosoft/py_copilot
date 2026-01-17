"""智能体技能服务层"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.agent_skill_association import AgentSkillAssociation


class AgentSkillService:
    """智能体技能服务，负责智能体与技能的关联管理和技能调用"""
    
    @staticmethod
    def bind_skill_to_agent(
        db: Session,
        agent_id: int,
        skill_id: int,
        priority: int = 0,
        config: Dict[str, Any] = None
    ) -> AgentSkillAssociation:
        """绑定技能到智能体
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            skill_id: 技能ID
            priority: 技能调用优先级
            config: 技能调用配置
            
        Returns:
            创建或更新的智能体-技能关联对象
            
        Raises:
            ValueError: 当智能体或技能不存在时
        """
        # 检查智能体和技能是否存在
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        
        if not agent:
            raise ValueError(f"智能体不存在，ID: {agent_id}")
        
        if not skill:
            raise ValueError(f"技能不存在，ID: {skill_id}")
        
        # 检查是否已绑定
        existing = db.query(AgentSkillAssociation).filter(
            AgentSkillAssociation.agent_id == agent_id,
            AgentSkillAssociation.skill_id == skill_id
        ).first()
        
        if existing:
            # 更新现有绑定
            existing.priority = priority
            existing.config = config or {}
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        
        # 创建新绑定
        association = AgentSkillAssociation(
            agent_id=agent_id,
            skill_id=skill_id,
            priority=priority,
            enabled=True,  # 显式设置为True，确保默认值正确应用
            config=config or {}
        )
        
        db.add(association)
        db.commit()
        db.refresh(association)
        return association
    
    @staticmethod
    def unbind_skill_from_agent(db: Session, agent_id: int, skill_id: int) -> bool:
        """解除智能体与技能的绑定
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            skill_id: 技能ID
            
        Returns:
            是否成功解除绑定
        """
        association = db.query(AgentSkillAssociation).filter(
            AgentSkillAssociation.agent_id == agent_id,
            AgentSkillAssociation.skill_id == skill_id
        ).first()
        
        if not association:
            return False
        
        db.delete(association)
        db.commit()
        return True
    
    @staticmethod
    def get_agent_skills(db: Session, agent_id: int, enabled_only: bool = False) -> list[AgentSkillAssociation]:
        """获取智能体绑定的所有技能
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            enabled_only: 是否只返回启用的技能
            
        Returns:
            智能体-技能关联列表，按优先级排序
        """
        query = db.query(AgentSkillAssociation).filter(
            AgentSkillAssociation.agent_id == agent_id
        )
        
        if enabled_only:
            query = query.filter(AgentSkillAssociation.enabled == True)
        
        # 按优先级排序
        return query.order_by(AgentSkillAssociation.priority).all()
    
    @staticmethod
    def enable_skill_for_agent(db: Session, agent_id: int, skill_id: int) -> bool:
        """启用智能体的特定技能
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            skill_id: 技能ID
            
        Returns:
            是否成功启用
        """
        association = db.query(AgentSkillAssociation).filter(
            AgentSkillAssociation.agent_id == agent_id,
            AgentSkillAssociation.skill_id == skill_id
        ).first()
        
        if not association:
            return False
        
        association.enabled = True
        db.add(association)
        db.commit()
        return True
    
    @staticmethod
    def disable_skill_for_agent(db: Session, agent_id: int, skill_id: int) -> bool:
        """禁用智能体的特定技能
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            skill_id: 技能ID
            
        Returns:
            是否成功禁用
        """
        association = db.query(AgentSkillAssociation).filter(
            AgentSkillAssociation.agent_id == agent_id,
            AgentSkillAssociation.skill_id == skill_id
        ).first()
        
        if not association:
            return False
        
        association.enabled = False
        db.add(association)
        db.commit()
        return True
    
    @staticmethod
    def execute_skill_by_agent(
        db: Session,
        agent_id: int,
        skill_id: int,
        input_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """通过智能体执行技能
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            skill_id: 技能ID
            input_params: 技能输入参数
            
        Returns:
            技能执行结果
            
        Raises:
            ValueError: 当技能未绑定到智能体或已禁用时
        """
        # 检查技能是否已绑定到智能体且已启用
        association = db.query(AgentSkillAssociation).filter(
            AgentSkillAssociation.agent_id == agent_id,
            AgentSkillAssociation.skill_id == skill_id,
            AgentSkillAssociation.enabled == True
        ).first()
        
        if not association:
            raise ValueError("技能未绑定到智能体或已禁用")
        
        # 获取智能体信息
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"智能体不存在，ID: {agent_id}")
        
        # 获取技能信息
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise ValueError(f"技能不存在，ID: {skill_id}")
        
        # 合并技能输入参数和智能体配置
        skill_params = association.config.copy()
        if input_params:
            skill_params.update(input_params)
        
        # 构建完整的智能体上下文信息
        agent_context = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "agent_description": agent.description,
            "agent_prompt": agent.prompt,
            "agent_model": agent.model_id,
            "agent_model_version": agent.model_version,
            "agent_capabilities": agent.capabilities,
            "agent_skills": agent.skills,
            "agent_execution_config": agent.execution_config,
            "skill_config": association.config,
            "user_id": agent.user_id,
            "conversation_id": None,  # 可以从外部传入
            "session_id": None  # 可以从外部传入
        }
        
        # 调用技能执行引擎
        from app.services.skill_execution_engine import SkillExecutionEngine
        skill_engine = SkillExecutionEngine(db)
        result = skill_engine.execute_skill(
            skill_id=skill_id,
            user_id=agent.user_id,
            params=skill_params,
            context=agent_context
        )
        
        return result
