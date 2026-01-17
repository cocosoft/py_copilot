"""能力自动匹配服务"""
from typing import List, Dict, Any, Optional
from app.models.capability_db import CapabilityDB as Capability
from app.models.model_capability import ModelCapabilityAssociation, ModelCapability
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

class CapabilityMatcher:
    """能力自动匹配服务类"""
    
    def __init__(self):
        pass
    
    def match_capabilities(self, 
                          db: Session, 
                          query: str, 
                          source_type: str = "all",  # "all", "agent", "model"
                          top_n: int = 5) -> Dict[str, Any]:
        """
        自动匹配相关能力
        
        Args:
            db: 数据库会话
            query: 查询文本
            source_type: 来源类型
            top_n: 返回结果数量
            
        Returns:
            匹配结果
        """
        try:
            logger.info(f"开始能力匹配，查询: {query[:100]}...")
            logger.info(f"来源类型: {source_type}")
            
            # 1. 从查询中提取关键词
            keywords = self._extract_keywords(query)
            logger.info(f"提取的关键词: {keywords}")
            
            # 2. 基于关键词搜索相关能力
            relevant_capabilities = self._search_relevant_capabilities(db, keywords)
            logger.info(f"相关能力: {[cap.name for cap in relevant_capabilities]}")
            
            # 3. 计算能力与查询的匹配度
            capability_scores = self._calculate_match_scores(relevant_capabilities, query, keywords)
            logger.info(f"能力匹配度: {capability_scores}")
            
            # 4. 排序并返回前N个结果
            sorted_results = sorted(capability_scores.items(), key=lambda x: x[1], reverse=True)
            top_results = sorted_results[:top_n]
            logger.info(f"Top {top_n} 能力: {[cap[0] for cap in top_results]}")
            
            # 5. 获取匹配能力的详细信息
            detailed_results = []
            try:
                for capability_name, score in top_results:
                    logger.debug(f"处理能力: {capability_name}, 评分: {score}")
                    capability = db.query(Capability).filter(Capability.name == capability_name).first()
                    if capability:
                        logger.debug(f"找到能力: {capability.name}")
                        # 获取拥有该能力的模型和智能体数量
                        try:
                            model_count = db.query(ModelCapabilityAssociation).filter(
                                ModelCapabilityAssociation.capability_id == capability.id
                            ).count()
                            logger.debug(f"模型数量: {model_count}")
                        except Exception as e:
                            logger.error(f"获取模型数量失败: {str(e)}")
                            model_count = 0
                        
                        detailed_results.append({
                            "name": capability.name,
                            "display_name": capability.display_name,
                            "description": capability.description,
                            "type": capability.capability_type,
                            "match_score": score,
                            "model_count": model_count,
                            "is_active": capability.is_active
                        })
            except Exception as e:
                logger.error(f"处理详细结果失败: {str(e)}")
            
            return {
                "success": True,
                "query": query,
                "keywords": keywords,
                "results": detailed_results,
                "total_matched": len(relevant_capabilities),
                "message": "能力匹配成功"
            }
            
        except Exception as e:
            logger.error(f"能力匹配失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "能力匹配失败"
            }
    
    def get_capability_recommendations(self, 
                                      db: Session, 
                                      user_id: int, 
                                      recent_capabilities: List[str], 
                                      top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取能力推荐
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            recent_capabilities: 最近使用的能力列表
            top_n: 返回结果数量
            
        Returns:
            推荐能力列表
        """
        try:
            logger.info(f"开始获取能力推荐，用户ID: {user_id}")
            logger.info(f"最近使用的能力: {recent_capabilities}")
            
            # 1. 获取用户的使用历史（简化实现）
            user_history = recent_capabilities
            
            # 2. 查找相关能力
            related_capabilities = set()
            for cap_name in user_history:
                # 获取与当前能力相关的其他能力
                cap = db.query(Capability).filter(Capability.name == cap_name).first()
                if cap:
                    # 简化实现：基于能力类型获取相关能力
                    related = db.query(Capability).filter(
                        Capability.capability_type == cap.capability_type,
                        Capability.name != cap_name
                    ).limit(3).all()
                    
                    related_capabilities.update([rel_cap.name for rel_cap in related])
            
            # 3. 排除最近使用的能力
            recommendations = list(related_capabilities - set(user_history))
            
            # 4. 获取推荐能力的详细信息
            detailed_recommendations = []
            for cap_name in recommendations[:top_n]:
                cap = db.query(Capability).filter(Capability.name == cap_name).first()
                if cap:
                    detailed_recommendations.append({
                        "name": cap.name,
                        "display_name": cap.display_name,
                        "description": cap.description,
                        "type": cap.capability_type,
                        "is_active": cap.is_active
                    })
            
            logger.info(f"推荐能力: {[cap['name'] for cap in detailed_recommendations]}")
            return detailed_recommendations
            
        except Exception as e:
            logger.error(f"获取能力推荐失败: {str(e)}")
            return []
    
    def match_agent_to_capabilities(self, 
                                   db: Session, 
                                   agent_id: int, 
                                   capabilities: List[str]) -> Dict[str, Any]:
        """
        匹配智能体与能力
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            capabilities: 能力列表
            
        Returns:
            匹配结果
        """
        try:
            logger.info(f"开始匹配智能体与能力，智能体ID: {agent_id}")
            logger.info(f"能力列表: {capabilities}")
            
            # 简化实现：由于Agent没有capabilities字段，直接返回匹配结果
            from app.models.agent import Agent
            
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return {
                    "success": False,
                    "error": f"智能体不存在: {agent_id}",
                    "message": "智能体不存在"
                }
            
            # 计算匹配度
            match_count = len(capabilities)  # 简化实现
            match_score = min(10.0, match_count * 2.0)  # 简化实现
            
            return {
                "success": True,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "capabilities": capabilities,
                "match_count": match_count,
                "match_score": match_score,
                "message": "智能体与能力匹配成功"
            }
            
        except Exception as e:
            logger.error(f"匹配智能体与能力失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "智能体与能力匹配失败"
            }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        
        Args:
            query: 查询文本
            
        Returns:
            关键词列表
        """
        # 简化实现：基于中文关键词提取
        keywords = set()
        
        # 中文能力关键词
        chinese_keywords = [
            "搜索", "查询", "查找", "分析", "统计", "计算", 
            "写作", "生成", "创作", "翻译", "转换", "情感", 
            "情绪", "实体", "提取", "工作流", "流程", "自动化"
        ]
        
        # 英文能力关键词
        english_keywords = [
            "search", "query", "find", "analyze", "statistics", "calculate",
            "write", "generate", "create", "translate", "convert", "sentiment",
            "emotion", "entity", "extract", "workflow", "process", "automation"
        ]
        
        query_lower = query.lower()
        
        # 匹配中文关键词
        for keyword in chinese_keywords:
            if keyword in query_lower:
                keywords.add(keyword)
        
        # 匹配英文关键词
        for keyword in english_keywords:
            if keyword in query_lower:
                keywords.add(keyword)
        
        return list(keywords)
    
    def _search_relevant_capabilities(self, db: Session, keywords: List[str]) -> List[Capability]:
        """
        基于关键词搜索相关能力
        
        Args:
            db: 数据库会话
            keywords: 关键词列表
            
        Returns:
            相关能力列表
        """
        if not keywords:
            return []
        
        # 简化实现：基于关键词搜索
        query = db.query(Capability).filter(Capability.is_active == True)
        
        # 搜索名称、显示名称和描述中的关键词
        for keyword in keywords:
            query = query.filter(
                (Capability.name.contains(keyword)) | 
                (Capability.display_name.contains(keyword)) | 
                (Capability.description.contains(keyword))
            )
        
        return query.all()
    
    def _calculate_match_scores(self, 
                              capabilities: List[Capability], 
                              query: str, 
                              keywords: List[str]) -> Dict[str, float]:
        """
        计算能力与查询的匹配度
        
        Args:
            capabilities: 能力列表
            query: 查询文本
            keywords: 关键词列表
            
        Returns:
            能力匹配度字典
        """
        scores = {}
        
        for capability in capabilities:
            score = 0.0
            
            # 基于名称匹配
            if capability.name.lower() in query.lower():
                score += 5.0
            
            # 基于显示名称匹配
            if capability.display_name and capability.display_name.lower() in query.lower():
                score += 4.0
            
            # 基于描述匹配
            if capability.description:
                desc_lower = capability.description.lower()
                query_lower = query.lower()
                if any(keyword.lower() in desc_lower for keyword in keywords):
                    score += 3.0
            
            # 基于关键词匹配数量
            matched_keywords = 0
            for keyword in keywords:
                if (keyword in capability.name) or \
                   (capability.display_name and keyword in capability.display_name) or \
                   (capability.description and keyword in capability.description):
                    matched_keywords += 1
            
            # 关键词匹配权重
            if matched_keywords > 0:
                score += matched_keywords * 1.0
            
            scores[capability.name] = round(score, 2)
        
        return scores
