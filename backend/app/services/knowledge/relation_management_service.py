"""
关系管理增强服务

实现关系权重计算、关系自动发现、关系可视化数据生成

任务编号: Phase3-Week11
阶段: 第三阶段 - 功能不完善问题优化
"""

import logging
import re
import math
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """关系类型"""
    HIERARCHICAL = "hierarchical"
    ASSOCIATIVE = "associative"
    CAUSAL = "causal"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    ATTRIBUTE = "attribute"
    COMPARATIVE = "comparative"


class WeightFactor(Enum):
    """权重因子"""
    FREQUENCY = "frequency"
    CONFIDENCE = "confidence"
    RECENCY = "recency"
    SOURCE_QUALITY = "source_quality"
    CONTEXT_RELEVANCE = "context_relevance"


@dataclass
class EntityNode:
    """实体节点"""
    id: str
    name: str
    entity_type: str
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "weight": self.weight,
            "attributes": self.attributes
        }


@dataclass
class RelationEdge:
    """关系边"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    confidence: float = 0.7
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "weight": self.weight,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata
        }


@dataclass
class WeightConfig:
    """权重配置"""
    frequency_weight: float = 0.25
    confidence_weight: float = 0.30
    recency_weight: float = 0.15
    source_quality_weight: float = 0.15
    context_relevance_weight: float = 0.15
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frequency_weight": self.frequency_weight,
            "confidence_weight": self.confidence_weight,
            "recency_weight": self.recency_weight,
            "source_quality_weight": self.source_quality_weight,
            "context_relevance_weight": self.context_relevance_weight
        }


class RelationWeightCalculator:
    """关系权重计算器"""
    
    def __init__(self, config: Optional[WeightConfig] = None):
        self.config = config or WeightConfig()
    
    def calculate_weight(self, relation: RelationEdge, 
                        context: Optional[Dict[str, Any]] = None) -> float:
        """计算关系权重"""
        scores = {}
        
        scores[WeightFactor.FREQUENCY.value] = self._calculate_frequency_score(relation)
        scores[WeightFactor.CONFIDENCE.value] = relation.confidence
        scores[WeightFactor.RECENCY.value] = self._calculate_recency_score(relation)
        scores[WeightFactor.SOURCE_QUALITY.value] = self._calculate_source_quality_score(relation)
        scores[WeightFactor.CONTEXT_RELEVANCE.value] = self._calculate_context_relevance(relation, context)
        
        total_weight = (
            scores[WeightFactor.FREQUENCY.value] * self.config.frequency_weight +
            scores[WeightFactor.CONFIDENCE.value] * self.config.confidence_weight +
            scores[WeightFactor.RECENCY.value] * self.config.recency_weight +
            scores[WeightFactor.SOURCE_QUALITY.value] * self.config.source_quality_weight +
            scores[WeightFactor.CONTEXT_RELEVANCE.value] * self.config.context_relevance_weight
        )
        
        return min(1.0, max(0.0, total_weight))
    
    def _calculate_frequency_score(self, relation: RelationEdge) -> float:
        """计算频率分数"""
        evidence_count = len(relation.evidence)
        if evidence_count == 0:
            return 0.3
        elif evidence_count == 1:
            return 0.5
        elif evidence_count <= 3:
            return 0.7
        elif evidence_count <= 5:
            return 0.85
        else:
            return 1.0
    
    def _calculate_recency_score(self, relation: RelationEdge) -> float:
        """计算时效性分数"""
        created_at = relation.metadata.get("created_at")
        if not created_at:
            return 0.5
        
        try:
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_date = created_at
            
            now = datetime.now(created_date.tzinfo) if created_date.tzinfo else datetime.now()
            days_diff = (now - created_date).days
            
            if days_diff <= 7:
                return 1.0
            elif days_diff <= 30:
                return 0.8
            elif days_diff <= 90:
                return 0.6
            elif days_diff <= 365:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5
    
    def _calculate_source_quality_score(self, relation: RelationEdge) -> float:
        """计算来源质量分数"""
        source_type = relation.metadata.get("source_type", "").lower()
        
        quality_scores = {
            "wikipedia": 0.9,
            "arxiv": 0.95,
            "github": 0.85,
            "stackoverflow": 0.8,
            "documentation": 0.85,
            "research_paper": 0.95,
            "news": 0.6,
            "blog": 0.5,
            "social_media": 0.3
        }
        
        return quality_scores.get(source_type, 0.5)
    
    def _calculate_context_relevance(self, relation: RelationEdge, 
                                    context: Optional[Dict[str, Any]]) -> float:
        """计算上下文相关性"""
        if not context:
            return 0.5
        
        query_entities = context.get("query_entities", [])
        query_relations = context.get("query_relations", [])
        
        relevance_score = 0.5
        
        if relation.source_id in query_entities or relation.target_id in query_entities:
            relevance_score += 0.3
        
        if relation.relation_type in query_relations:
            relevance_score += 0.2
        
        return min(1.0, relevance_score)
    
    def batch_calculate_weights(self, relations: List[RelationEdge],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """批量计算权重"""
        weights = {}
        for relation in relations:
            weights[relation.id] = self.calculate_weight(relation, context)
        return weights


class RelationDiscovery:
    """关系自动发现"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """初始化关系模式"""
        return {
            "hierarchical": [
                r"(.+?)是(.+?)的一种",
                r"(.+?)属于(.+?)",
                r"(.+?)包含(.+?)",
                r"(.+?)包括(.+?)",
                r"(.+?)分为(.+?)"
            ],
            "causal": [
                r"(.+?)导致(.+?)",
                r"(.+?)引起(.+?)",
                r"(.+?)造成(.+?)",
                r"因为(.+?)所以(.+?)",
                r"(.+?)使得(.+?)"
            ],
            "associative": [
                r"(.+?)与(.+?)相关",
                r"(.+?)和(.+?)有关",
                r"(.+?)关联(.+?)",
                r"(.+?)联系(.+?)"
            ],
            "temporal": [
                r"(.+?)之后(.+?)",
                r"(.+?)之前(.+?)",
                r"(.+?)同时(.+?)",
                r"(.+?)接着(.+?)"
            ],
            "spatial": [
                r"(.+?)位于(.+?)",
                r"(.+?)在(.+?)中",
                r"(.+?)附近(.+?)",
                r"(.+?)周围(.+?)"
            ],
            "attribute": [
                r"(.+?)具有(.+?)",
                r"(.+?)拥有(.+?)",
                r"(.+?)的(.+?)是",
                r"(.+?)特点(.+?)"
            ],
            "comparative": [
                r"(.+?)比(.+?)更",
                r"(.+?)与(.+?)相比",
                r"(.+?)类似于(.+?)",
                r"(.+?)不同于(.+?)"
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, str]:
        """初始化实体模式"""
        return {
            "PERSON": r"[\u4e00-\u9fff]{2,4}",
            "ORG": r"[\u4e00-\u9fff]{2,8}(?:公司|集团|机构|大学|学院|研究所)",
            "LOC": r"[\u4e00-\u9fff]{2,6}(?:省|市|县|区|镇|村)",
            "TECH": r"[A-Z]{2,}|[\u4e00-\u9fff]{2,6}(?:技术|系统|框架|算法|模型)",
            "PRODUCT": r"[\u4e00-\u9fff]{2,8}(?:版|系统|平台|应用)"
        }
    
    def discover_relations(self, text: str, 
                          existing_entities: Optional[List[EntityNode]] = None) -> List[RelationEdge]:
        """从文本中发现关系"""
        discovered = []
        
        for relation_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    source = match.group(1).strip()
                    target = match.group(2).strip()
                    
                    if len(source) < 2 or len(target) < 2:
                        continue
                    
                    relation = RelationEdge(
                        id=f"discovered_{len(discovered)}",
                        source_id=source,
                        target_id=target,
                        relation_type=relation_type,
                        weight=0.5,
                        confidence=0.6,
                        evidence=[match.group(0)],
                        metadata={"discovery_method": "pattern_matching"}
                    )
                    discovered.append(relation)
        
        if existing_entities:
            discovered = self._filter_by_entities(discovered, existing_entities)
        
        return discovered
    
    def _filter_by_entities(self, relations: List[RelationEdge], 
                           entities: List[EntityNode]) -> List[RelationEdge]:
        """根据已知实体过滤关系"""
        entity_names = {e.name for e in entities}
        
        filtered = []
        for rel in relations:
            if rel.source_id in entity_names or rel.target_id in entity_names:
                filtered.append(rel)
        
        return filtered
    
    def discover_entities(self, text: str) -> List[EntityNode]:
        """从文本中发现实体"""
        entities = []
        seen = set()
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_name = match.group(0)
                
                if entity_name in seen:
                    continue
                
                seen.add(entity_name)
                
                entity = EntityNode(
                    id=f"entity_{len(entities)}",
                    name=entity_name,
                    entity_type=entity_type,
                    weight=1.0,
                    attributes={"position": match.span()}
                )
                entities.append(entity)
        
        return entities


class RelationVisualizer:
    """关系可视化数据生成器"""
    
    def __init__(self):
        self.node_colors = {
            "PERSON": "#FF6B6B",
            "ORG": "#4ECDC4",
            "LOC": "#45B7D1",
            "TECH": "#96CEB4",
            "PRODUCT": "#FECA57",
            "EVENT": "#FF9FF3",
            "CONCEPT": "#54A0FF",
            "default": "#95A5A6"
        }
        
        self.edge_colors = {
            "hierarchical": "#3498DB",
            "causal": "#E74C3C",
            "associative": "#2ECC71",
            "temporal": "#9B59B6",
            "spatial": "#F39C12",
            "attribute": "#1ABC9C",
            "comparative": "#E67E22",
            "default": "#BDC3C7"
        }
    
    def generate_graph_data(self, entities: List[EntityNode], 
                           relations: List[RelationEdge],
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成图可视化数据"""
        options = options or {}
        
        nodes = []
        for entity in entities:
            node = {
                "id": entity.id,
                "label": entity.name,
                "size": self._calculate_node_size(entity),
                "color": self.node_colors.get(entity.entity_type, self.node_colors["default"]),
                "group": entity.entity_type,
                "title": f"{entity.name} ({entity.entity_type})",
                "attributes": entity.attributes
            }
            nodes.append(node)
        
        edges = []
        for relation in relations:
            edge = {
                "id": relation.id,
                "source": relation.source_id,
                "target": relation.target_id,
                "label": relation.relation_type,
                "weight": relation.weight,
                "width": self._calculate_edge_width(relation),
                "color": self.edge_colors.get(relation.relation_type, self.edge_colors["default"]),
                "arrows": "to",
                "title": f"{relation.relation_type} (权重: {relation.weight:.2f})",
                "smooth": {"type": "curvedCW", "roundness": 0.2}
            }
            edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "options": self._generate_vis_options(options)
        }
    
    def _calculate_node_size(self, entity: EntityNode) -> int:
        """计算节点大小"""
        base_size = 20
        weight_factor = entity.weight * 15
        return int(base_size + weight_factor)
    
    def _calculate_edge_width(self, relation: RelationEdge) -> float:
        """计算边宽度"""
        base_width = 1.0
        weight_factor = relation.weight * 3
        return round(base_width + weight_factor, 1)
    
    def _generate_vis_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """生成可视化选项"""
        return {
            "nodes": {
                "shape": "dot",
                "font": {
                    "size": 14,
                    "face": "Arial"
                },
                "borderWidth": 2,
                "shadow": True
            },
            "edges": {
                "width": 2,
                "color": {"inherit": "from"},
                "smooth": {
                    "type": "continuous"
                },
                "arrows": {
                    "to": {"enabled": True, "scaleFactor": 0.5}
                }
            },
            "physics": {
                "enabled": True,
                "barnesHut": {
                    "gravitationalConstant": -3000,
                    "centralGravity": 0.3,
                    "springLength": 100
                },
                "stabilization": {
                    "iterations": 200
                }
            },
            "interaction": {
                "hover": True,
                "tooltipDelay": 200,
                "zoomView": True
            },
            **options
        }
    
    def generate_tree_data(self, entities: List[EntityNode],
                          relations: List[RelationEdge],
                          root_id: Optional[str] = None) -> Dict[str, Any]:
        """生成树形可视化数据"""
        children_map = defaultdict(list)
        parent_map = {}
        
        for rel in relations:
            if rel.relation_type in ["hierarchical", "attribute"]:
                children_map[rel.source_id].append(rel.target_id)
                parent_map[rel.target_id] = rel.source_id
        
        if not root_id:
            all_children = set()
            for children in children_map.values():
                all_children.update(children)
            
            potential_roots = [e.id for e in entities if e.id not in all_children]
            root_id = potential_roots[0] if potential_roots else entities[0].id if entities else None
        
        if not root_id:
            return {"name": "empty", "children": []}
        
        entity_map = {e.id: e for e in entities}
        
        def build_tree(node_id: str, visited: Set[str] = None) -> Dict[str, Any]:
            if visited is None:
                visited = set()
            
            if node_id in visited:
                return None
            
            visited.add(node_id)
            
            entity = entity_map.get(node_id)
            if not entity:
                return None
            
            node = {
                "name": entity.name,
                "type": entity.entity_type,
                "children": []
            }
            
            for child_id in children_map.get(node_id, []):
                child_tree = build_tree(child_id, visited.copy())
                if child_tree:
                    node["children"].append(child_tree)
            
            return node
        
        return build_tree(root_id)
    
    def generate_matrix_data(self, entities: List[EntityNode],
                            relations: List[RelationEdge]) -> Dict[str, Any]:
        """生成矩阵可视化数据"""
        entity_ids = [e.id for e in entities]
        entity_names = [e.name for e in entities]
        
        matrix = [[0.0] * len(entities) for _ in range(len(entities))]
        
        relation_map = defaultdict(list)
        for rel in relations:
            relation_map[(rel.source_id, rel.target_id)].append(rel)
        
        for i, source_id in enumerate(entity_ids):
            for j, target_id in enumerate(entity_ids):
                rels = relation_map.get((source_id, target_id), [])
                if rels:
                    max_weight = max(r.weight for r in rels)
                    matrix[i][j] = max_weight
        
        return {
            "labels": entity_names,
            "matrix": matrix,
            "entities": [e.to_dict() for e in entities]
        }


class RelationManagementService:
    """关系管理增强服务"""
    
    def __init__(self, weight_config: Optional[WeightConfig] = None):
        self.weight_calculator = RelationWeightCalculator(weight_config)
        self.discovery = RelationDiscovery()
        self.visualizer = RelationVisualizer()
    
    def analyze_relations(self, entities: List[EntityNode], 
                         relations: List[RelationEdge],
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析关系"""
        weights = self.weight_calculator.batch_calculate_weights(relations, context)
        
        for relation in relations:
            if relation.id in weights:
                relation.weight = weights[relation.id]
        
        stats = self._calculate_statistics(entities, relations)
        
        return {
            "weights": weights,
            "statistics": stats,
            "top_relations": self._get_top_relations(relations, 10)
        }
    
    def _calculate_statistics(self, entities: List[EntityNode], 
                             relations: List[RelationEdge]) -> Dict[str, Any]:
        """计算统计信息"""
        entity_degree = defaultdict(int)
        for rel in relations:
            entity_degree[rel.source_id] += 1
            entity_degree[rel.target_id] += 1
        
        avg_degree = sum(entity_degree.values()) / len(entities) if entities else 0
        
        relation_types = defaultdict(int)
        for rel in relations:
            relation_types[rel.relation_type] += 1
        
        avg_weight = sum(r.weight for r in relations) / len(relations) if relations else 0
        
        return {
            "entity_count": len(entities),
            "relation_count": len(relations),
            "average_degree": round(avg_degree, 2),
            "average_weight": round(avg_weight, 3),
            "relation_types": dict(relation_types),
            "max_degree": max(entity_degree.values()) if entity_degree else 0,
            "min_degree": min(entity_degree.values()) if entity_degree else 0
        }
    
    def _get_top_relations(self, relations: List[RelationEdge], 
                          top_n: int) -> List[Dict[str, Any]]:
        """获取权重最高的关系"""
        sorted_relations = sorted(relations, key=lambda r: r.weight, reverse=True)
        return [r.to_dict() for r in sorted_relations[:top_n]]
    
    def discover_from_text(self, text: str,
                          existing_entities: Optional[List[EntityNode]] = None) -> Dict[str, Any]:
        """从文本发现实体和关系"""
        entities = self.discovery.discover_entities(text)
        relations = self.discovery.discover_relations(text, existing_entities or entities)
        
        return {
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations],
            "entity_count": len(entities),
            "relation_count": len(relations)
        }
    
    def generate_visualization(self, entities: List[EntityNode],
                              relations: List[RelationEdge],
                              viz_type: str = "graph",
                              options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成可视化数据"""
        if viz_type == "graph":
            return self.visualizer.generate_graph_data(entities, relations, options)
        elif viz_type == "tree":
            root_id = options.get("root_id") if options else None
            return self.visualizer.generate_tree_data(entities, relations, root_id)
        elif viz_type == "matrix":
            return self.visualizer.generate_matrix_data(entities, relations)
        else:
            return self.visualizer.generate_graph_data(entities, relations, options)


_relation_management_service: Optional[RelationManagementService] = None


def get_relation_management_service() -> RelationManagementService:
    """获取关系管理服务实例"""
    global _relation_management_service
    if _relation_management_service is None:
        _relation_management_service = RelationManagementService()
    return _relation_management_service
