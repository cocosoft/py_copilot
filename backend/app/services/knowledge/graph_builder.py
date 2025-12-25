"""知识图谱构建器模块"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, EntityRelationship, KnowledgeDocument
)

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """知识图谱构建器 - 负责将实体关系转换为图谱结构"""
    
    def __init__(self):
        self.graph = nx.Graph()
    
    def build_graph_from_document(self, document_id: int, db: Session) -> Dict[str, Any]:
        """从单个文档构建知识图谱"""
        try:
            # 1. 获取文档的所有实体和关系
            entities = self._get_document_entities(document_id, db)
            relationships = self._get_document_relationships(document_id, db)
            
            # 2. 构建图结构
            graph = self._construct_graph(entities, relationships)
            
            # 3. 应用图谱化算法
            graph = self._apply_graph_operations(graph)
            
            logger.info(f"成功构建文档 {document_id} 的知识图谱，包含 {len(entities)} 个实体和 {len(relationships)} 个关系")
            return graph
            
        except Exception as e:
            logger.error(f"构建文档 {document_id} 的知识图谱失败: {e}")
            return {"error": str(e)}
    
    def build_cross_document_graph(self, knowledge_base_id: int, db: Session) -> Dict[str, Any]:
        """构建跨文档的知识图谱"""
        try:
            # 1. 获取知识库所有文档的实体关系
            all_entities, all_relationships = self._get_knowledge_base_data(knowledge_base_id, db)
            
            # 2. 实体消歧和链接
            linked_entities = self._entity_linking(all_entities)
            
            # 3. 构建全局图谱
            global_graph = self._construct_global_graph(linked_entities, all_relationships)
            
            # 4. 应用图谱优化算法
            global_graph = self._apply_graph_operations(global_graph)
            
            logger.info(f"成功构建知识库 {knowledge_base_id} 的全局知识图谱，包含 {len(linked_entities)} 个链接实体和 {len(all_relationships)} 个关系")
            return global_graph
            
        except Exception as e:
            logger.error(f"构建知识库 {knowledge_base_id} 的全局知识图谱失败: {e}")
            return {"error": str(e)}
    
    def _get_document_entities(self, document_id: int, db: Session) -> List[DocumentEntity]:
        """获取文档的所有实体"""
        return db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        ).all()
    
    def _get_document_relationships(self, document_id: int, db: Session) -> List[EntityRelationship]:
        """获取文档的所有关系"""
        return db.query(EntityRelationship).filter(
            EntityRelationship.document_id == document_id
        ).all()
    
    def _get_knowledge_base_data(self, knowledge_base_id: int, db: Session) -> Tuple[List[DocumentEntity], List[EntityRelationship]]:
        """获取知识库所有文档的实体和关系"""
        # 获取所有实体
        entities = db.query(DocumentEntity).join(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 获取所有关系
        relationships = db.query(EntityRelationship).join(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        return entities, relationships
    
    def _construct_graph(self, entities: List[DocumentEntity], relationships: List[EntityRelationship]) -> Dict[str, Any]:
        """将实体关系转换为图结构"""
        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "node_count": len(entities),
                "edge_count": len(relationships),
                "graph_type": "document_graph"
            }
        }
        
        # 添加实体节点
        entity_map = {}
        for entity in entities:
            node_id = f"entity_{entity.id}"
            entity_map[entity.id] = node_id
            
            graph["nodes"].append({
                "id": node_id,
                "label": entity.entity_text,
                "type": entity.entity_type,
                "entity_id": entity.id,
                "document_id": entity.document_id,
                "confidence": entity.confidence,
                "group": entity.entity_type,
                "properties": {
                    "start_pos": entity.start_pos,
                    "end_pos": entity.end_pos
                }
            })
        
        # 添加关系边
        for rel in relationships:
            if rel.source_id in entity_map and rel.target_id in entity_map:
                graph["edges"].append({
                    "source": entity_map[rel.source_id],
                    "target": entity_map[rel.target_id],
                    "label": rel.relationship_type,
                    "relationship_id": rel.id,
                    "confidence": rel.confidence,
                    "properties": {
                        "document_id": rel.document_id
                    }
                })
        
        return graph
    
    def _construct_global_graph(self, linked_entities: List[Dict], relationships: List[EntityRelationship]) -> Dict[str, Any]:
        """构建全局图谱结构"""
        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "node_count": len(linked_entities),
                "edge_count": len(relationships),
                "graph_type": "global_graph"
            }
        }
        
        # 添加链接后的实体节点
        entity_map = {}
        for entity_group in linked_entities:
            node_id = f"cluster_{entity_group['cluster_id']}"
            entity_map[entity_group['cluster_id']] = node_id
            
            graph["nodes"].append({
                "id": node_id,
                "label": entity_group['representative_text'],
                "type": entity_group['entity_type'],
                "cluster_id": entity_group['cluster_id'],
                "entity_count": len(entity_group['entities']),
                "confidence": entity_group['confidence'],
                "group": entity_group['entity_type'],
                "properties": {
                    "entity_ids": [e.id for e in entity_group['entities']],
                    "document_ids": list(set([e.document_id for e in entity_group['entities']]))
                }
            })
        
        # 添加关系边（基于链接后的实体）
        for rel in relationships:
            source_cluster = self._find_entity_cluster(linked_entities, rel.source_id)
            target_cluster = self._find_entity_cluster(linked_entities, rel.target_id)
            
            if source_cluster and target_cluster:
                edge_id = f"edge_{rel.id}"
                graph["edges"].append({
                    "id": edge_id,
                    "source": entity_map[source_cluster],
                    "target": entity_map[target_cluster],
                    "label": rel.relationship_type,
                    "relationship_id": rel.id,
                    "confidence": rel.confidence,
                    "properties": {
                        "document_id": rel.document_id
                    }
                })
        
        return graph
    
    def _entity_linking(self, entities: List[DocumentEntity]) -> List[Dict]:
        """实体消歧和跨文档链接"""
        if not entities:
            return []
        
        # 按实体类型分组
        entities_by_type = {}
        for entity in entities:
            if entity.entity_type not in entities_by_type:
                entities_by_type[entity.entity_type] = []
            entities_by_type[entity.entity_type].append(entity)
        
        linked_entities = []
        cluster_id = 0
        
        # 对每种实体类型进行聚类
        for entity_type, type_entities in entities_by_type.items():
            if len(type_entities) <= 1:
                # 只有一个实体，直接作为集群
                linked_entities.append({
                    "cluster_id": cluster_id,
                    "entity_type": entity_type,
                    "representative_text": type_entities[0].entity_text,
                    "entities": type_entities,
                    "confidence": type_entities[0].confidence
                })
                cluster_id += 1
                continue
            
            # 使用文本相似度进行聚类
            clusters = self._cluster_similar_entities(type_entities)
            
            for cluster in clusters:
                if cluster:
                    # 选择最长的实体文本作为代表
                    representative = max(cluster, key=lambda e: len(e.entity_text))
                    linked_entities.append({
                        "cluster_id": cluster_id,
                        "entity_type": entity_type,
                        "representative_text": representative.entity_text,
                        "entities": cluster,
                        "confidence": np.mean([e.confidence for e in cluster])
                    })
                    cluster_id += 1
        
        return linked_entities
    
    def _cluster_similar_entities(self, entities: List[DocumentEntity], similarity_threshold: float = 0.7) -> List[List[DocumentEntity]]:
        """基于文本相似度对实体进行聚类"""
        if len(entities) <= 1:
            return [entities]
        
        # 提取实体文本
        texts = [entity.entity_text for entity in entities]
        
        # 使用TF-IDF计算相似度
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 使用简单的聚类算法
            clusters = []
            used_indices = set()
            
            for i in range(len(entities)):
                if i in used_indices:
                    continue
                
                cluster = [entities[i]]
                used_indices.add(i)
                
                for j in range(i + 1, len(entities)):
                    if j in used_indices:
                        continue
                    
                    if similarity_matrix[i][j] >= similarity_threshold:
                        cluster.append(entities[j])
                        used_indices.add(j)
                
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.warning(f"实体聚类失败，使用简单分组: {e}")
            # 如果聚类失败，每个实体单独成组
            return [[entity] for entity in entities]
    
    def _find_entity_cluster(self, linked_entities: List[Dict], entity_id: int) -> Optional[int]:
        """查找实体所属的集群"""
        for entity_group in linked_entities:
            for entity in entity_group['entities']:
                if entity.id == entity_id:
                    return entity_group['cluster_id']
        return None
    
    def _apply_graph_operations(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """应用图谱优化算法"""
        # 社区发现
        graph = self._detect_communities(graph)
        
        # 中心性分析
        graph = self._calculate_centrality(graph)
        
        # 路径分析
        graph = self._find_shortest_paths(graph)
        
        return graph
    
    def _detect_communities(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """社区发现算法"""
        # 将图转换为networkx格式
        nx_graph = nx.Graph()
        
        # 添加节点
        for node in graph["nodes"]:
            nx_graph.add_node(node["id"], **node)
        
        # 添加边
        for edge in graph["edges"]:
            nx_graph.add_edge(edge["source"], edge["target"], **edge)
        
        # 使用Louvain算法进行社区发现
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(nx_graph)
            
            # 更新节点的社区信息
            for node in graph["nodes"]:
                node["community"] = partition.get(node["id"], 0)
            
            graph["metadata"]["communities"] = len(set(partition.values()))
            
        except ImportError:
            logger.warning("未安装python-louvain库，跳过社区发现")
            for node in graph["nodes"]:
                node["community"] = 0
            graph["metadata"]["communities"] = 1
        
        return graph
    
    def _calculate_centrality(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """计算节点中心性"""
        # 将图转换为networkx格式
        nx_graph = nx.Graph()
        
        # 添加节点
        for node in graph["nodes"]:
            nx_graph.add_node(node["id"], **node)
        
        # 添加边
        for edge in graph["edges"]:
            nx_graph.add_edge(edge["source"], edge["target"], **edge)
        
        # 计算度中心性
        degree_centrality = nx.degree_centrality(nx_graph)
        
        # 计算接近中心性
        try:
            closeness_centrality = nx.closeness_centrality(nx_graph)
        except:
            closeness_centrality = {}
        
        # 计算介数中心性
        try:
            betweenness_centrality = nx.betweenness_centrality(nx_graph)
        except:
            betweenness_centrality = {}
        
        # 更新节点中心性信息
        for node in graph["nodes"]:
            node_id = node["id"]
            node["centrality"] = {
                "degree": degree_centrality.get(node_id, 0),
                "closeness": closeness_centrality.get(node_id, 0),
                "betweenness": betweenness_centrality.get(node_id, 0)
            }
        
        return graph
    
    def _find_shortest_paths(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """查找最短路径"""
        # 将图转换为networkx格式
        nx_graph = nx.Graph()
        
        # 添加节点
        for node in graph["nodes"]:
            nx_graph.add_node(node["id"], **node)
        
        # 添加边
        for edge in graph["edges"]:
            nx_graph.add_edge(edge["source"], edge["target"], **edge)
        
        # 计算图的直径和平均最短路径长度
        try:
            if nx.is_connected(nx_graph):
                graph["metadata"]["diameter"] = nx.diameter(nx_graph)
                graph["metadata"]["avg_shortest_path_length"] = nx.average_shortest_path_length(nx_graph)
            else:
                graph["metadata"]["diameter"] = 0
                graph["metadata"]["avg_shortest_path_length"] = 0
        except:
            graph["metadata"]["diameter"] = 0
            graph["metadata"]["avg_shortest_path_length"] = 0
        
        return graph