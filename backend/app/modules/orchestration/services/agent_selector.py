"""智能体选择器服务"""
from typing import List, Dict, Any, Optional
from app.models.agent import Agent
from app.models.supplier_db import ModelDB
from app.models.capability_db import CapabilityDB as Capability
from app.models.model_capability import ModelCapability
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import logging

logger = logging.getLogger(__name__)

class AgentSelector:
    """智能体选择器类"""
    
    def __init__(self):
        # 智能体评分权重配置
        self.scoring_weights = {
            "capability_match": 0.5,      # 能力匹配度权重
            "usage_frequency": 0.2,       # 使用频率权重
            "user_rating": 0.2,           # 用户评分权重
            "parameter_quality": 0.1      # 参数质量权重
        }
    
    def select_optimal_agent(
        self, 
        db: Session,
        task_description: str,
        required_capabilities: List[str],
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        选择最优智能体
        
        Args:
            db: 数据库会话
            task_description: 任务描述
            required_capabilities: 所需能力列表
            user_id: 用户ID
            
        Returns:
            {"type": "agent" | "model", "id": 实例ID, "name": 名称, "score": 评分}
        """
        try:
            logger.info(f"开始选择最优智能体，任务描述: {task_description[:100]}...")
            logger.info(f"所需能力: {required_capabilities}")
            
            # 1. 获取用户可用的智能体（公共智能体和用户自己的智能体）
            query = db.query(Agent).filter(
                (Agent.user_id == user_id) | (Agent.is_public == True)
            )
            
            all_agents = query.all()
            logger.info(f"找到 {len(all_agents)} 个可用智能体")
            
            # 2. 计算每个智能体的评分
            agent_scores = []
            for agent in all_agents:
                # 评估智能体的能力匹配度
                capability_score = self._evaluate_agent_capabilities(agent, required_capabilities)
                
                # 计算智能体的参数质量
                parameter_score = self._evaluate_agent_parameters(agent)
                
                # 获取智能体的使用频率和用户评分（默认值）
                usage_score = self._get_agent_usage_score(db, agent.id, user_id)
                rating_score = self._get_agent_rating_score(db, agent.id)
                
                # 综合评分
                total_score = (
                    capability_score * self.scoring_weights["capability_match"] +
                    usage_score * self.scoring_weights["usage_frequency"] +
                    rating_score * self.scoring_weights["user_rating"] +
                    parameter_score * self.scoring_weights["parameter_quality"]
                )
                
                agent_scores.append((agent, total_score))
                logger.debug(f"智能体评分: {agent.name} = {total_score:.2f} (能力匹配: {capability_score:.2f}, 使用频率: {usage_score:.2f}, 用户评分: {rating_score:.2f}, 参数质量: {parameter_score:.2f})")
            
            # 3. 选择评分最高的智能体
            if agent_scores:
                # 按评分排序
                agent_scores.sort(key=lambda x: x[1], reverse=True)
                
                # 只考虑评分大于0.3的智能体
                qualified_agents = [item for item in agent_scores if item[1] > 0.3]
                
                if qualified_agents:
                    best_agent, best_score = qualified_agents[0]
                    logger.info(f"选择智能体: {best_agent.name} (ID: {best_agent.id}, 评分: {best_score:.2f})")
                    
                    return {
                        "type": "agent",
                        "id": best_agent.id,
                        "name": best_agent.name,
                        "score": best_score
                    }
            
            # 4. 如果没有合适的智能体，选择合适的模型
            logger.info("没有找到合适的智能体，尝试选择模型")
            best_model = self._select_optimal_model(db, required_capabilities)
            
            if best_model:
                logger.info(f"选择最优模型: {best_model.model_name} (ID: {best_model.id})")
                return {
                    "type": "model",
                    "id": best_model.id,
                    "name": best_model.model_name,
                    "score": self._calculate_model_score(best_model)
                }
            
            # 5. 如果没有合适的模型，返回None
            logger.warning("没有找到合适的智能体或模型")
            return None
            
        except Exception as e:
            logger.error(f"选择最优智能体失败: {str(e)}")
            return None
    
    def _evaluate_agent_capabilities(self, agent: Agent, required_capabilities: List[str]) -> float:
        """
        评估智能体的能力匹配度
        
        Args:
            agent: 智能体实例
            required_capabilities: 所需能力列表
            
        Returns:
            能力匹配度评分（0-5）
        """
        if not required_capabilities:
            return 3.0  # 默认评分
        
        # 由于Agent模型没有直接的capabilities关系，我们从描述和prompt中提取关键词
        agent_text = f"{agent.name} {agent.description} {agent.prompt}"
        agent_text = agent_text.lower()
        
        matched_count = 0
        for capability in required_capabilities:
            if capability.lower() in agent_text:
                matched_count += 1
        
        # 计算匹配度
        match_score = (matched_count / len(required_capabilities)) * 5.0
        return match_score
    
    def _evaluate_agent_parameters(self, agent: Agent) -> float:
        """
        评估智能体的参数质量
        
        Args:
            agent: 智能体实例
            
        Returns:
            参数质量评分（0-5）
        """
        if not agent.parameters:
            return 1.0  # 没有参数的智能体评分较低
        
        # 评估参数的完整性和多样性
        parameter_count = len(agent.parameters)
        parameter_types = set(param.parameter_type for param in agent.parameters)
        
        # 计算参数质量评分
        count_score = min(parameter_count / 5, 1) * 2.5  # 最多5个参数，2.5分
        type_score = min(len(parameter_types) / 3, 1) * 2.5  # 最多3种参数类型，2.5分
        
        return count_score + type_score
    
    def _get_agent_usage_score(self, db: Session, agent_id: int, user_id: int) -> float:
        """
        获取智能体的使用频率评分
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            user_id: 用户ID
            
        Returns:
            使用频率评分（0-5）
        """
        # 从对话历史中统计智能体的使用频率
        from app.models.conversation import Conversation
        
        try:
            usage_count = db.query(Conversation).filter(
                Conversation.agent_id == agent_id,
                Conversation.user_id == user_id
            ).count()
            
            # 使用频率评分：0-5，使用次数越多评分越高
            usage_score = min(usage_count / 10, 1) * 5.0  # 最多10次使用，5分
            return usage_score
        except Exception as e:
            logger.error(f"获取智能体使用频率失败: {str(e)}")
            return 2.5  # 默认评分
    
    def _get_agent_rating_score(self, db: Session, agent_id: int) -> float:
        """
        获取智能体的用户评分
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            
        Returns:
            用户评分（0-5）
        """
        # 注意：目前没有智能体评分表，所以返回默认值
        return 3.0
    
    def _calculate_model_score(self, model: ModelDB) -> float:
        """
        计算模型的综合评分
        
        Args:
            model: 模型实例
            
        Returns:
            模型评分（0-5）
        """
        try:
            # 计算平均能力强度
            avg_strength = 0
            if hasattr(model, 'capability_associations') and model.capability_associations:
                avg_strength = sum(assoc.actual_strength for assoc in model.capability_associations) / len(model.capability_associations)
            else:
                avg_strength = 3  # 默认值
            
            # 考虑模型的响应速度、成本等因素
            response_score = model.response_speed if hasattr(model, 'response_speed') else 5
            cost_score = 10 - model.cost if hasattr(model, 'cost') else 5
            
            # 综合评分
            total_score = (avg_strength * 0.5) + (response_score * 0.3) + (cost_score * 0.2)
            return total_score
        except Exception as e:
            logger.error(f"计算模型评分失败: {str(e)}")
            return 3.0
    
    def _select_optimal_model(
        self, 
        db: Session,
        required_capabilities: List[str]
    ) -> Optional[ModelDB]:
        """
        选择最优模型
        
        Args:
            db: 数据库会话
            required_capabilities: 所需能力列表
            
        Returns:
            最优模型实例
        """
        try:
            # 1. 筛选具有所需能力的模型
            query = db.query(ModelDB)
            
            # 注意：这里简化实现，因为ModelDB和ModelCapability之间是多对多关系
            # 通过ModelCapabilityAssociation表连接
            
            if required_capabilities:
                # 确保模型具备所有所需能力
                from app.models.model_capability import ModelCapabilityAssociation
                
                for capability in required_capabilities:
                    query = query.filter(
                        ModelDB.id.in_(
                            db.query(ModelCapabilityAssociation.model_id)
                            .join(ModelCapability, ModelCapabilityAssociation.capability_id == ModelCapability.id)
                            .filter(ModelCapability.name == capability)
                        )
                    )
            
            # 2. 获取模型
            models = query.all()
            
            if not models:
                return None
            
            # 3. 计算模型的综合评分
            model_scores = []
            for model in models:
                # 计算平均能力强度（简化实现）
                avg_strength = 0
                try:
                    # 尝试获取模型的能力强度
                    if hasattr(model, 'capability_associations') and model.capability_associations:
                        avg_strength = sum(assoc.actual_strength for assoc in model.capability_associations) / len(model.capability_associations)
                    else:
                        avg_strength = 3  # 默认值
                except Exception:
                    avg_strength = 3  # 默认值
                
                # 考虑模型的响应速度、成本等因素
                response_score = model.response_speed if hasattr(model, 'response_speed') else 5
                cost_score = 10 - model.cost if hasattr(model, 'cost') else 5
                
                # 综合评分
                total_score = (avg_strength * 0.5) + (response_score * 0.3) + (cost_score * 0.2)
                model_scores.append((model, total_score))
            
            # 4. 选择评分最高的模型
            model_scores.sort(key=lambda x: x[1], reverse=True)
            
            return model_scores[0][0]
            
        except Exception as e:
            logger.error(f"选择最优模型失败: {str(e)}")
            return None
    
    def get_agent_recommendations(
        self, 
        db: Session,
        user_id: int,
        task_description: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取智能体推荐
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            task_description: 任务描述
            limit: 返回推荐的数量限制
            
        Returns:
            推荐智能体列表
        """
        try:
            logger.info(f"获取智能体推荐，用户ID: {user_id}, 任务描述: {task_description[:100]}...")
            
            # TODO: 实现基于用户历史的推荐逻辑
            
            # 2. 获取推荐的智能体（目前只返回公共智能体）
            query = db.query(Agent)
            
            # 如果用户不是管理员，只返回公共智能体或用户自己的智能体
            query = query.filter(
                Agent.is_public == True
            )
            
            # 注意：Agent类没有rating和usage_count字段，所以先按创建时间排序
            recommended_agents = query.order_by(
                desc(Agent.created_at)
            ).limit(limit).all()
            
            # 3. 格式化推荐结果
            recommendations = []
            for agent in recommended_agents:
                recommendations.append({
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "rating": 5.0,  # 默认评分
                    "usage_count": 0,  # 默认使用次数
                    "capabilities": []  # 目前Agent类没有capabilities关系
                })
            
            logger.info(f"获取到 {len(recommendations)} 个智能体推荐")
            return recommendations
            
        except Exception as e:
            logger.error(f"获取智能体推荐失败: {str(e)}")
            return []
