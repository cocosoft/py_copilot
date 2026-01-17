"""技能自动组合服务"""
from typing import List, Dict, Any, Optional
from app.models.capability_db import CapabilityDB as Capability
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class SkillComposer:
    """技能自动组合服务类"""
    
    def __init__(self):
        pass
    
    def compose_skills(self, 
                      db: Session, 
                      task_description: str, 
                      available_capabilities: List[str]) -> Dict[str, Any]:
        """
        根据任务描述自动组合所需技能
        
        Args:
            db: 数据库会话
            task_description: 任务描述
            available_capabilities: 可用能力列表
            
        Returns:
            技能组合结果
        """
        try:
            logger.info(f"开始技能组合，任务描述: {task_description[:100]}...")
            logger.info(f"可用能力: {available_capabilities}")
            
            # 1. 从任务描述中提取需要的能力
            required_capabilities = self._extract_required_capabilities(task_description)
            logger.info(f"从任务中提取的能力: {required_capabilities}")
            
            # 2. 过滤出系统中实际存在的能力
            valid_capabilities = self._filter_valid_capabilities(db, required_capabilities)
            logger.info(f"验证后的有效能力: {valid_capabilities}")
            
            # 3. 计算能力的依赖关系
            capability_dependencies = self._calculate_capability_dependencies(db, valid_capabilities)
            logger.info(f"能力依赖关系: {capability_dependencies}")
            
            # 4. 生成最佳能力组合序列
            optimal_sequence = self._generate_optimal_sequence(valid_capabilities, capability_dependencies)
            logger.info(f"最佳能力组合序列: {optimal_sequence}")
            
            # 5. 评估组合的适用性
            suitability_score = self._evaluate_suitability(
                task_description, 
                optimal_sequence, 
                available_capabilities
            )
            logger.info(f"组合适用性评分: {suitability_score}")
            
            return {
                "success": True,
                "required_capabilities": valid_capabilities,
                "capability_dependencies": capability_dependencies,
                "optimal_sequence": optimal_sequence,
                "suitability_score": suitability_score,
                "message": "技能组合成功"
            }
            
        except Exception as e:
            logger.error(f"技能组合失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "技能组合失败"
            }
    
    def _extract_required_capabilities(self, task_description: str) -> List[str]:
        """
        从任务描述中提取需要的能力
        
        Args:
            task_description: 任务描述
            
        Returns:
            需要的能力列表
        """
        # 简化实现：基于关键词匹配提取能力
        capability_mapping = {
            "搜索": "knowledge_search",
            "查询": "knowledge_search",
            "查找": "knowledge_search",
            "分析": "data_analysis",
            "统计": "data_analysis",
            "计算": "data_analysis",
            "写作": "content_generation",
            "生成": "content_generation",
            "创作": "content_generation",
            "翻译": "translation",
            "转换": "translation",
            "情感": "sentiment_analysis",
            "情绪": "sentiment_analysis",
            "实体": "entity_extraction",
            "提取": "entity_extraction",
            "工作流": "workflow_generation",
            "流程": "workflow_generation",
            "自动化": "workflow_generation"
        }
        
        required_capabilities = set()
        task_lower = task_description.lower()
        
        for keyword, capability in capability_mapping.items():
            if keyword in task_lower:
                required_capabilities.add(capability)
        
        # 如果没有提取到任何能力，默认添加knowledge_search
        if not required_capabilities:
            required_capabilities.add("knowledge_search")
        
        return list(required_capabilities)
    
    def _filter_valid_capabilities(self, db: Session, capabilities: List[str]) -> List[str]:
        """
        过滤出系统中实际存在的能力
        
        Args:
            db: 数据库会话
            capabilities: 能力列表
            
        Returns:
            有效能力列表
        """
        if not capabilities:
            return []
        
        # 查询数据库中存在的能力
        valid_capabilities = db.query(Capability.name).filter(
            Capability.name.in_(capabilities),
            Capability.is_active == True
        ).all()
        
        # db.query(Capability.name)返回的是元组列表 [(name1,), (name2,), ...]
        return [cap[0] for cap in valid_capabilities]
    
    def _calculate_capability_dependencies(self, db: Session, capabilities: List[str]) -> Dict[str, List[str]]:
        """
        计算能力的依赖关系
        
        Args:
            db: 数据库会话
            capabilities: 能力列表
            
        Returns:
            依赖关系字典 {"能力": [依赖的能力]}
        """
        # 简化实现：预设的依赖关系
        dependencies = {
            "data_analysis": ["knowledge_search"],
            "content_generation": ["knowledge_search", "data_analysis"],
            "workflow_generation": ["knowledge_search", "data_analysis"]
        }
        
        capability_dependencies = {}
        for capability in capabilities:
            capability_dependencies[capability] = dependencies.get(capability, [])
        
        return capability_dependencies
    
    def _generate_optimal_sequence(self, 
                                 capabilities: List[str], 
                                 dependencies: Dict[str, List[str]]) -> List[str]:
        """
        生成最佳能力组合序列
        
        Args:
            capabilities: 能力列表
            dependencies: 依赖关系字典
            
        Returns:
            最佳能力组合序列
        """
        # 简化实现：基于依赖关系排序
        sequence = []
        processed = set()
        
        def process_capability(capability):
            if capability in processed:
                return
            
            # 先处理依赖的能力
            for dep in dependencies.get(capability, []):
                if dep in capabilities and dep not in processed:
                    process_capability(dep)
            
            sequence.append(capability)
            processed.add(capability)
        
        # 处理所有能力
        for capability in capabilities:
            process_capability(capability)
        
        return sequence
    
    def _evaluate_suitability(self, 
                             task_description: str, 
                             sequence: List[str], 
                             available_capabilities: List[str]) -> float:
        """
        评估组合的适用性
        
        Args:
            task_description: 任务描述
            sequence: 能力组合序列
            available_capabilities: 可用能力列表
            
        Returns:
            适用性评分 (0-10)
        """
        if not sequence:
            return 0.0
        
        # 计算覆盖率
        coverage = len([cap for cap in sequence if cap in available_capabilities]) / len(sequence)
        
        # 基于任务长度调整评分
        task_length_score = min(1.0, len(task_description) / 100)
        
        # 组合评分
        score = (coverage * 0.7) + (task_length_score * 0.3)
        
        return round(score * 10, 2)
    
    def suggest_additional_capabilities(self, 
                                      db: Session, 
                                      task_description: str, 
                                      existing_capabilities: List[str]) -> List[str]:
        """
        建议额外的能力
        
        Args:
            db: 数据库会话
            task_description: 任务描述
            existing_capabilities: 现有能力列表
            
        Returns:
            建议的额外能力列表
        """
        # 简化实现：基于任务描述和现有能力的差异建议
        potential_capabilities = self._extract_required_capabilities(task_description)
        
        # 过滤出系统中存在但尚未使用的能力
        all_capabilities = [cap.name for cap in db.query(Capability.name).filter(Capability.is_active == True).all()]
        
        suggested = [cap for cap in potential_capabilities 
                    if cap in all_capabilities and cap not in existing_capabilities]
        
        return suggested
