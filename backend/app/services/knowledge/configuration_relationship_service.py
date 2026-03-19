"""
配置关系服务

建立配置与大模型自动识别的协同机制

@task DB-001
@phase 实体识别配置优化
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session


class ModelAutoConfigService:
    """
    模型自动配置服务
    """
    
    def __init__(self, db: Session):
        """
        初始化模型自动配置服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def analyze_model_output(self, model_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析模型输出
        
        Args:
            model_output: 模型输出
            
        Returns:
            分析结果
        """
        # 分析实体识别结果
        entity_analysis = self._analyze_entities(model_output.get('entities', []))
        
        # 分析关系提取结果
        relationship_analysis = self._analyze_relationships(model_output.get('relationships', []))
        
        return {
            'entity_analysis': entity_analysis,
            'relationship_analysis': relationship_analysis,
            'confidence_distribution': self._analyze_confidence_distribution(model_output)
        }
    
    def _analyze_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析实体识别结果
        """
        entity_types = {}
        confidence_scores = []
        
        for entity in entities:
            entity_type = entity.get('type')
            confidence = entity.get('confidence', 0)
            
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            entity_types[entity_type] += 1
            
            confidence_scores.append(confidence)
        
        # 计算平均置信度
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'entity_types': entity_types,
            'total_entities': len(entities),
            'average_confidence': avg_confidence
        }
    
    def _analyze_relationships(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析关系提取结果
        """
        relationship_types = {}
        confidence_scores = []
        
        for rel in relationships:
            rel_type = rel.get('type')
            confidence = rel.get('confidence', 0)
            
            if rel_type not in relationship_types:
                relationship_types[rel_type] = 0
            relationship_types[rel_type] += 1
            
            confidence_scores.append(confidence)
        
        # 计算平均置信度
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'relationship_types': relationship_types,
            'total_relationships': len(relationships),
            'average_confidence': avg_confidence
        }
    
    def _analyze_confidence_distribution(self, model_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析置信度分布
        """
        entities = model_output.get('entities', [])
        relationships = model_output.get('relationships', [])
        
        all_confidences = [e.get('confidence', 0) for e in entities] + \
                         [r.get('confidence', 0) for r in relationships]
        
        if not all_confidences:
            return {
                'high_confidence': 0,  # > 0.8
                'medium_confidence': 0,  # 0.5-0.8
                'low_confidence': 0  # < 0.5
            }
        
        high = sum(1 for c in all_confidences if c > 0.8)
        medium = sum(1 for c in all_confidences if 0.5 <= c <= 0.8)
        low = sum(1 for c in all_confidences if c < 0.5)
        
        return {
            'high_confidence': high,
            'medium_confidence': medium,
            'low_confidence': low,
            'total': len(all_confidences)
        }
    
    def generate_config_suggestions(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于分析结果生成配置建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            配置建议
        """
        entity_analysis = analysis.get('entity_analysis', {})
        relationship_analysis = analysis.get('relationship_analysis', {})
        confidence_distribution = analysis.get('confidence_distribution', {})
        
        # 生成实体识别配置建议
        entity_config = self._generate_entity_config_suggestions(entity_analysis, confidence_distribution)
        
        # 生成关系提取配置建议
        relationship_config = self._generate_relationship_config_suggestions(relationship_analysis, confidence_distribution)
        
        return {
            'entity_recognition': entity_config,
            'relationship_extraction': relationship_config
        }
    
    def _generate_entity_config_suggestions(self, entity_analysis: Dict[str, Any], 
                                          confidence_distribution: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成实体识别配置建议
        """
        avg_confidence = entity_analysis.get('average_confidence', 0)
        high_confidence = confidence_distribution.get('high_confidence', 0)
        total = confidence_distribution.get('total', 1)
        
        # 基于置信度调整阈值
        if avg_confidence > 0.8:
            confidence_threshold = 0.7
        elif avg_confidence > 0.6:
            confidence_threshold = 0.6
        else:
            confidence_threshold = 0.5
        
        # 推荐启用的实体类型
        recommended_entities = list(entity_analysis.get('entity_types', {}).keys())
        
        return {
            'confidence_threshold': confidence_threshold,
            'recommended_entities': recommended_entities,
            'high_confidence_ratio': high_confidence / total if total > 0 else 0
        }
    
    def _generate_relationship_config_suggestions(self, relationship_analysis: Dict[str, Any], 
                                                confidence_distribution: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成关系提取配置建议
        """
        avg_confidence = relationship_analysis.get('average_confidence', 0)
        
        # 基于置信度调整阈值
        if avg_confidence > 0.7:
            min_confidence = 0.6
        elif avg_confidence > 0.5:
            min_confidence = 0.4
        else:
            min_confidence = 0.3
        
        # 推荐启用的关系类型
        recommended_relationships = list(relationship_analysis.get('relationship_types', {}).keys())
        
        return {
            'min_confidence': min_confidence,
            'recommended_relationships': recommended_relationships
        }


class ConfigurationSyncService:
    """
    配置同步服务
    """
    
    def __init__(self, db: Session):
        """
        初始化配置同步服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def sync_configuration(self, knowledge_base_id: int, model_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步配置与模型输出
        
        Args:
            knowledge_base_id: 知识库ID
            model_output: 模型输出
            
        Returns:
            同步结果
        """
        # 分析模型输出
        model_config_service = ModelAutoConfigService(self.db)
        analysis = model_config_service.analyze_model_output(model_output)
        
        # 生成配置建议
        suggestions = model_config_service.generate_config_suggestions(analysis)
        
        # 加载现有配置
        from .configuration_ui_optimizer import ConfigurationManager
        config_manager = ConfigurationManager(self.db)
        existing_config = config_manager.load_configuration(knowledge_base_id)
        
        # 合并配置
        merged_config = self._merge_configurations(existing_config, suggestions)
        
        # 保存更新后的配置
        save_result = config_manager.save_configuration(knowledge_base_id, merged_config)
        
        return {
            'analysis': analysis,
            'suggestions': suggestions,
            'merged_config': merged_config,
            'save_result': save_result
        }
    
    def _merge_configurations(self, existing: Dict[str, Any], suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并现有配置和建议配置
        """
        merged = existing.copy()
        
        # 合并实体识别配置
        if 'entity_recognition' in suggestions:
            entity_suggestions = suggestions['entity_recognition']
            if 'entity_recognition' not in merged:
                merged['entity_recognition'] = {}
            
            # 只更新置信度阈值，保留用户选择的实体类型
            if 'confidence_threshold' in entity_suggestions:
                merged['entity_recognition']['confidence_threshold'] = entity_suggestions['confidence_threshold']
        
        # 合并关系提取配置
        if 'relationship_extraction' in suggestions:
            relationship_suggestions = suggestions['relationship_extraction']
            if 'relationship_extraction' not in merged:
                merged['relationship_extraction'] = {}
            
            # 只更新最小置信度，保留用户选择的关系类型
            if 'min_confidence' in relationship_suggestions:
                merged['relationship_extraction']['min_confidence'] = relationship_suggestions['min_confidence']
        
        return merged


class ConfigurationFeedbackService:
    """
    配置反馈服务
    """
    
    def __init__(self, db: Session):
        """
        初始化配置反馈服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def collect_feedback(self, knowledge_base_id: int, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        收集配置反馈
        
        Args:
            knowledge_base_id: 知识库ID
            feedback: 反馈信息
            
        Returns:
            收集结果
        """
        # 实现反馈收集逻辑
        return {
            'success': True,
            'message': 'Feedback collected successfully',
            'feedback_id': 1
        }
    
    def analyze_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析反馈数据
        
        Args:
            feedback: 反馈列表
            
        Returns:
            分析结果
        """
        # 实现反馈分析逻辑
        return {
            'total_feedback': len(feedback),
            'positive_feedback': 0,
            'negative_feedback': 0,
            'common_issues': []
        }
    
    def generate_feedback_based_suggestions(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于反馈生成配置建议
        
        Args:
            analysis: 反馈分析结果
            
        Returns:
            配置建议
        """
        # 实现基于反馈的建议生成逻辑
        return {
            'suggestions': []
        }


class ConfigurationRelationshipService:
    """
    配置关系服务
    """
    
    def __init__(self, db: Session):
        """
        初始化配置关系服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.model_auto_config_service = ModelAutoConfigService(db)
        self.configuration_sync_service = ConfigurationSyncService(db)
        self.configuration_feedback_service = ConfigurationFeedbackService(db)
    
    def establish_configuration_relationship(self, knowledge_base_id: int, model_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        建立配置与模型输出的关系
        
        Args:
            knowledge_base_id: 知识库ID
            model_output: 模型输出
            
        Returns:
            建立结果
        """
        # 1. 分析模型输出
        analysis = self.model_auto_config_service.analyze_model_output(model_output)
        
        # 2. 生成配置建议
        suggestions = self.model_auto_config_service.generate_config_suggestions(analysis)
        
        # 3. 同步配置
        sync_result = self.configuration_sync_service.sync_configuration(knowledge_base_id, model_output)
        
        # 4. 生成协同机制报告
        report = self._generate_collaboration_report(analysis, suggestions, sync_result)
        
        return {
            'analysis': analysis,
            'suggestions': suggestions,
            'sync_result': sync_result,
            'report': report
        }
    
    def get_configuration_health(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        获取配置健康状态
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            健康状态
        """
        # 加载配置
        from .configuration_ui_optimizer import ConfigurationManager
        config_manager = ConfigurationManager(self.db)
        configuration = config_manager.load_configuration(knowledge_base_id)
        
        # 分析配置健康度
        health_score = self._calculate_configuration_health(configuration)
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 0.7 else 'needs_attention' if health_score > 0.4 else 'critical',
            'recommendations': self._generate_health_recommendations(health_score, configuration)
        }
    
    def _generate_collaboration_report(self, analysis: Dict[str, Any], 
                                    suggestions: Dict[str, Any], 
                                    sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成协同机制报告
        """
        return {
            'model_performance': {
                'entity_recognition': analysis.get('entity_analysis', {}),
                'relationship_extraction': analysis.get('relationship_analysis', {})
            },
            'configuration_adjustments': {
                'entity_recognition': suggestions.get('entity_recognition', {}),
                'relationship_extraction': suggestions.get('relationship_extraction', {})
            },
            'sync_status': sync_result.get('save_result', {})
        }
    
    def _calculate_configuration_health(self, configuration: Dict[str, Any]) -> float:
        """
        计算配置健康度
        """
        # 实现配置健康度计算逻辑
        return 0.8  # 示例值
    
    def _generate_health_recommendations(self, health_score: float, 
                                       configuration: Dict[str, Any]) -> List[str]:
        """
        生成健康建议
        """
        # 实现健康建议生成逻辑
        return []
    
    def optimize_configuration(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        优化配置
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            优化结果
        """
        # 1. 加载现有配置
        from .configuration_ui_optimizer import ConfigurationManager
        config_manager = ConfigurationManager(self.db)
        existing_config = config_manager.load_configuration(knowledge_base_id)
        
        # 2. 分析配置
        analysis = self._analyze_configuration(existing_config)
        
        # 3. 生成优化建议
        suggestions = self._generate_optimization_suggestions(analysis)
        
        # 4. 应用优化
        optimized_config = self._apply_optimization(existing_config, suggestions)
        
        # 5. 保存优化后的配置
        save_result = config_manager.save_configuration(knowledge_base_id, optimized_config)
        
        return {
            'analysis': analysis,
            'suggestions': suggestions,
            'optimized_config': optimized_config,
            'save_result': save_result
        }
    
    def _analyze_configuration(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析配置
        """
        # 实现配置分析逻辑
        return {
            'entity_recognition': configuration.get('entity_recognition', {}),
            'relationship_extraction': configuration.get('relationship_extraction', {})
        }
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成优化建议
        """
        # 实现优化建议生成逻辑
        return {
            'entity_recognition': {},
            'relationship_extraction': {}
        }
    
    def _apply_optimization(self, configuration: Dict[str, Any], 
                          suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用优化
        """
        # 实现优化应用逻辑
        return configuration