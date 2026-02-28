"""将Agent的skills JSON字段迁移到关联表"""

import sys
import os
import json

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.agent_skill_association import AgentSkillAssociation


def migrate_agent_skills():
    """迁移智能体的技能字段到关联表"""
    db = SessionLocal()
    
    try:
        # 获取所有有skills字段的智能体
        agents = db.query(Agent).filter(
            Agent.skills.isnot(None)
        ).all()
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for agent in agents:
            if not agent.skills:
                continue
            
            skill_ids = agent.skills
            if isinstance(skill_ids, str):
                try:
                    skill_ids = json.loads(skill_ids)
                except json.JSONDecodeError:
                    print(f"  智能体 {agent.name}(ID:{agent.id}): skills字段格式错误，跳过")
                    error_count += 1
                    continue
            
            if not isinstance(skill_ids, list):
                print(f"  智能体 {agent.name}(ID:{agent.id}): skills字段不是列表，跳过")
                error_count += 1
                continue
            
            agent_migrated = 0
            for idx, skill_id in enumerate(skill_ids):
                # 验证技能存在
                skill = db.query(Skill).filter(Skill.id == skill_id).first()
                if not skill:
                    print(f"    跳过不存在的技能ID: {skill_id}")
                    skipped_count += 1
                    continue
                
                # 检查是否已关联
                existing = db.query(AgentSkillAssociation).filter(
                    AgentSkillAssociation.agent_id == agent.id,
                    AgentSkillAssociation.skill_id == skill_id
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # 创建关联
                assoc = AgentSkillAssociation(
                    agent_id=agent.id,
                    skill_id=skill_id,
                    priority=idx,
                    enabled=True,
                    config={}
                )
                db.add(assoc)
                migrated_count += 1
                agent_migrated += 1
            
            if agent_migrated > 0:
                print(f"  智能体 {agent.name}(ID:{agent.id}): 迁移 {agent_migrated} 个技能")
        
        db.commit()
        print(f"\n✅ 迁移完成")
        print(f"   成功创建: {migrated_count} 个关联")
        print(f"   跳过已存在/不存在: {skipped_count} 个")
        print(f"   错误: {error_count} 个")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始迁移智能体技能到关联表...")
    migrate_agent_skills()
