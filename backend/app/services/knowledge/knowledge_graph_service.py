"""知识图谱服务模块"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, EntityRelationship, DocumentChunk, KnowledgeDocument
)
from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
from app.services.knowledge.graph_builder import KnowledgeGraphBuilder

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务，负责实体识别、关系提取和知识图谱查询"""
    
    def __init__(self):
        self.text_processor = AdvancedTextProcessor()
        self.graph_builder = KnowledgeGraphBuilder()
    
    def extract_and_store_entities(self, db: Session, document: KnowledgeDocument) -> Dict[str, Any]:
        """从文档中提取实体并存储到数据库"""
        try:
            if not document.content:
                logger.warning(f"文档 {document.id} 没有内容，无法提取实体")
                return {"success": False, "error": "文档内容为空"}
            
            # 提取实体和关系
            entities, relationships = self.text_processor.extract_entities_relationships(document.content)
            
            # 存储实体到数据库
            stored_entities = []
            for entity_info in entities:
                entity = DocumentEntity(
                    document_id=document.id,
                    entity_text=entity_info['text'],
                    entity_type=entity_info['type'],
                    start_pos=entity_info['start_pos'],
                    end_pos=entity_info['end_pos'],
                    confidence=entity_info.get('confidence', 0.7)
                )
                db.add(entity)
                stored_entities.append(entity)
            
            db.flush()  # 刷新以获取实体ID
            
            # 存储关系到数据库
            stored_relationships = []
            for rel_info in relationships:
                # 查找对应的实体
                source_entity = self._find_entity_by_text(stored_entities, rel_info['subject'])
                target_entity = self._find_entity_by_text(stored_entities, rel_info['object'])
                
                if source_entity and target_entity:
                    relationship = EntityRelationship(
                        document_id=document.id,
                        source_id=source_entity.id,
                        target_id=target_entity.id,
                        relationship_type=rel_info['relation'],
                        confidence=rel_info.get('confidence', 0.7)
                    )
                    db.add(relationship)
                    stored_relationships.append(relationship)
            
            db.commit()
            
            logger.info(f"成功提取并存储 {len(stored_entities)} 个实体和 {len(stored_relationships)} 个关系")
            return {
                "success": True,
                "entities_count": len(stored_entities),
                "relationships_count": len(stored_relationships)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"提取实体失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _find_entity_by_text(self, entities: List[DocumentEntity], text: str) -> Optional[DocumentEntity]:
        """根据实体文本查找实体"""
        for entity in entities:
            if entity.entity_text == text:
                return entity
        return None
    
    def get_document_entities(self, db: Session, document_id: int) -> List[Dict[str, Any]]:
        """获取文档的所有实体"""
        entities = db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        ).all()
        
        return [
            {
                "id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos,
                "confidence": entity.confidence
            }
            for entity in entities
        ]
    
    def get_document_relationships(self, db: Session, document_id: int) -> List[Dict[str, Any]]:
        """获取文档的所有关系"""
        relationships = db.query(EntityRelationship).filter(
            EntityRelationship.document_id == document_id
        ).all()
        
        result = []
        for rel in relationships:
            # 获取源实体和目标实体的详细信息
            source_entity = db.query(DocumentEntity).filter(DocumentEntity.id == rel.source_id).first()
            target_entity = db.query(DocumentEntity).filter(DocumentEntity.id == rel.target_id).first()
            
            if source_entity and target_entity:
                result.append({
                    "id": rel.id,
                    "source": {
                        "id": source_entity.id,
                        "text": source_entity.entity_text,
                        "type": source_entity.entity_type
                    },
                    "target": {
                        "id": target_entity.id,
                        "text": target_entity.entity_text,
                        "type": target_entity.entity_type
                    },
                    "relationship_type": rel.relationship_type,
                    "confidence": rel.confidence
                })
        
        return result
    
    def search_entities(self, db: Session, entity_text: str, entity_type: Optional[str] = None, 
                       knowledge_base_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """搜索实体"""
        query = db.query(DocumentEntity).join(KnowledgeDocument).filter(
            DocumentEntity.entity_text.ilike(f"%{entity_text}%")
        )
        
        if entity_type:
            query = query.filter(DocumentEntity.entity_type == entity_type)
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        entities = query.all()
        
        return [
            {
                "id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "document_id": entity.document_id,
                "document_title": entity.document.title if entity.document else "未知",
                "confidence": entity.confidence
            }
            for entity in entities
        ]
    
    def get_entity_relationships(self, db: Session, entity_id: int) -> Dict[str, Any]:
        """获取实体的所有关系"""
        entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
        if not entity:
            return {"error": "实体不存在"}
        
        # 作为源实体的关系
        source_relationships = db.query(EntityRelationship).filter(
            EntityRelationship.source_id == entity_id
        ).all()
        
        # 作为目标实体的关系
        target_relationships = db.query(EntityRelationship).filter(
            EntityRelationship.target_id == entity_id
        ).all()
        
        result = {
            "entity": {
                "id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "document_id": entity.document_id
            },
            "outgoing_relationships": [],
            "incoming_relationships": []
        }
        
        # 处理出关系
        for rel in source_relationships:
            target_entity = db.query(DocumentEntity).filter(DocumentEntity.id == rel.target_id).first()
            if target_entity:
                result["outgoing_relationships"].append({
                    "id": rel.id,
                    "target_entity": {
                        "id": target_entity.id,
                        "text": target_entity.entity_text,
                        "type": target_entity.entity_type
                    },
                    "relationship_type": rel.relationship_type,
                    "confidence": rel.confidence
                })
        
        # 处理入关系
        for rel in target_relationships:
            source_entity = db.query(DocumentEntity).filter(DocumentEntity.id == rel.source_id).first()
            if source_entity:
                result["incoming_relationships"].append({
                    "id": rel.id,
                    "source_entity": {
                        "id": source_entity.id,
                        "text": source_entity.entity_text,
                        "type": source_entity.entity_type
                    },
                    "relationship_type": rel.relationship_type,
                    "confidence": rel.confidence
                })
        
        return result
    
    def get_knowledge_graph_data(self, db: Session, knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
        """获取知识图谱数据（用于可视化）"""
        # 构建查询
        query = db.query(DocumentEntity)
        if knowledge_base_id:
            query = query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        entities = query.all()
        
        # 获取所有关系
        relationships_query = db.query(EntityRelationship)
        if knowledge_base_id:
            relationships_query = relationships_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        relationships = relationships_query.all()
        
        # 构建图谱数据
        nodes = []
        links = []
        
        # 添加实体节点
        entity_map = {}
        for entity in entities:
            node_id = f"entity_{entity.id}"
            entity_map[entity.id] = node_id
            
            nodes.append({
                "id": node_id,
                "label": entity.entity_text,
                "type": entity.entity_type,
                "entity_id": entity.id,
                "document_id": entity.document_id,
                "confidence": entity.confidence,
                "group": entity.entity_type  # 按类型分组
            })
        
        # 添加关系边
        for rel in relationships:
            if rel.source_id in entity_map and rel.target_id in entity_map:
                links.append({
                    "source": entity_map[rel.source_id],
                    "target": entity_map[rel.target_id],
                    "label": rel.relationship_type,
                    "relationship_id": rel.id,
                    "confidence": rel.confidence
                })
        
        return {
            "nodes": nodes,
            "links": links,
            "statistics": {
                "total_entities": len(entities),
                "total_relationships": len(relationships),
                "entity_types": {},
                "relationship_types": {}
            }
        }
    
    def extract_keywords_from_document(self, document: KnowledgeDocument, top_n: int = 10) -> List[Dict[str, Any]]:
        """从文档中提取关键词"""
        if not document.content:
            return []
        
        return self.text_processor.extract_keywords(document.content, top_n)
    
    def analyze_document_semantics(self, document: KnowledgeDocument) -> Dict[str, Any]:
        """分析文档语义特征"""
        if not document.content:
            return {"error": "文档内容为空"}
        
        # 提取关键词
        keywords = self.text_processor.extract_keywords(document.content, 20)
        
        # 分析文本特征
        text_length = len(document.content)
        word_count = len(document.content.split())
        
        # 计算实体密度（如果有实体）
        entities = self.text_processor.extract_entities_relationships(document.content)[0]
        entity_density = len(entities) / (text_length / 1000) if text_length > 0 else 0
        
        return {
            "text_length": text_length,
            "word_count": word_count,
            "entity_count": len(entities),
            "entity_density": round(entity_density, 2),
            "top_keywords": keywords[:10],
            "semantic_richness": min(1.0, len(entities) / 10)  # 语义丰富度评分
        }
    
    def build_document_graph(self, document_id: int, db: Session) -> Dict[str, Any]:
        """构建单个文档的知识图谱"""
        try:
            # 检查文档是否存在
            document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
            if not document:
                return {"error": "文档不存在"}
            
            # 1. 检查文档是否已进行实体提取，如果没有则先执行实体提取
            entities = self.get_document_entities(db, document_id)
            relationships = self.get_document_relationships(db, document_id)
            
            if not entities and not relationships:
                logger.info(f"文档 {document_id} 未进行实体提取，开始执行实体提取...")
                
                # 执行实体提取
                extraction_result = self.extract_and_store_entities(db, document)
                if not extraction_result.get("success", False):
                    logger.warning(f"文档 {document_id} 实体提取失败: {extraction_result.get('error', '未知错误')}")
                    return {"error": f"实体提取失败: {extraction_result.get('error', '未知错误')}"}
                
                # 重新获取实体和关系
                entities = self.get_document_entities(db, document_id)
                relationships = self.get_document_relationships(db, document_id)
                
                # 检查实体提取是否真的成功
                if not entities:
                    logger.warning(f"文档 {document_id} 实体提取后仍然没有实体")
                    return {"error": "实体提取后没有发现任何实体"}
                
                logger.info(f"文档 {document_id} 实体提取成功，提取到 {len(entities)} 个实体和 {len(relationships)} 个关系")
            else:
                logger.info(f"文档 {document_id} 已有 {len(entities)} 个实体和 {len(relationships)} 个关系，直接构建知识图谱")
            
            # 2. 使用图谱构建器构建图谱
            graph = self.graph_builder.build_graph_from_document(document_id, db)
            
            # 3. 检查图谱构建结果是否有效
            if "error" in graph:
                logger.error(f"图谱构建失败: {graph['error']}")
                return graph
            
            # 4. 添加统计信息
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            
            if not nodes:
                logger.warning(f"文档 {document_id} 构建的知识图谱没有节点")
                return {"error": "知识图谱构建成功但没有发现任何节点"}
            
            # 计算社区数量
            communities_count = len(set(node.get("community", 0) for node in nodes))
            
            graph.update({
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "communities_count": communities_count,
                "statistics": self.get_graph_statistics(graph)
            })
            
            logger.info(f"成功构建文档 {document_id} 的知识图谱，包含 {len(nodes)} 个节点和 {len(edges)} 条边")
            return graph
            
        except Exception as e:
            logger.error(f"构建文档 {document_id} 的知识图谱失败: {e}")
            return {"error": str(e)}
    
    def build_knowledge_base_graph(self, knowledge_base_id: int, db: Session) -> Dict[str, Any]:
        """构建整个知识库的知识图谱"""
        try:
            # 检查知识库是否存在
            knowledge_base = db.query(KnowledgeDocument.knowledge_base_id).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).first()
            
            if not knowledge_base:
                return {"error": "知识库不存在或没有文档"}
            
            # 使用图谱构建器构建全局图谱
            graph = self.graph_builder.build_cross_document_graph(knowledge_base_id, db)
            
            # 记录图谱构建日志
            if "error" not in graph:
                logger.info(f"成功构建知识库 {knowledge_base_id} 的全局知识图谱")
            
            return graph
            
        except Exception as e:
            logger.error(f"构建知识库 {knowledge_base_id} 的全局知识图谱失败: {e}")
            return {"error": str(e)}
    
    def get_graph_statistics(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """获取图谱统计信息"""
        if "error" in graph:
            return {"error": graph["error"]}
        
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        metadata = graph.get("metadata", {})
        
        # 按实体类型统计
        entity_types = {}
        for node in nodes:
            entity_type = node.get("type", "未知")
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            entity_types[entity_type] += 1
        
        # 按关系类型统计
        relationship_types = {}
        for edge in edges:
            rel_type = edge.get("label", "未知")
            if rel_type not in relationship_types:
                relationship_types[rel_type] = 0
            relationship_types[rel_type] += 1
        
        # 计算中心性统计
        centrality_stats = self._calculate_centrality_statistics(nodes)
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entity_types": entity_types,
            "relationship_types": relationship_types,
            "centrality_statistics": centrality_stats,
            "graph_metadata": metadata
        }
    
    def _calculate_centrality_statistics(self, nodes: List[Dict]) -> Dict[str, Any]:
        """计算中心性统计信息"""
        if not nodes:
            return {}
        
        degrees = []
        closeness = []
        betweenness = []
        
        for node in nodes:
            centrality = node.get("centrality", {})
            degrees.append(centrality.get("degree", 0))
            closeness.append(centrality.get("closeness", 0))
            betweenness.append(centrality.get("betweenness", 0))
        
        return {
            "degree": {
                "max": max(degrees) if degrees else 0,
                "min": min(degrees) if degrees else 0,
                "avg": sum(degrees) / len(degrees) if degrees else 0
            },
            "closeness": {
                "max": max(closeness) if closeness else 0,
                "min": min(closeness) if closeness else 0,
                "avg": sum(closeness) / len(closeness) if closeness else 0
            },
            "betweenness": {
                "max": max(betweenness) if betweenness else 0,
                "min": min(betweenness) if betweenness else 0,
                "avg": sum(betweenness) / len(betweenness) if betweenness else 0
            }
        }
    
    def find_entity_paths(self, graph: Dict[str, Any], source_entity_id: str, target_entity_id: str, max_depth: int = 3) -> List[List[str]]:
        """查找两个实体之间的路径"""
        if "error" in graph:
            return []
        
        # 将图转换为networkx格式
        import networkx as nx
        nx_graph = nx.Graph()
        
        # 添加节点
        for node in graph["nodes"]:
            nx_graph.add_node(node["id"], **node)
        
        # 添加边
        for edge in graph["edges"]:
            nx_graph.add_edge(edge["source"], edge["target"], **edge)
        
        # 查找所有简单路径
        try:
            paths = list(nx.all_simple_paths(nx_graph, source_entity_id, target_entity_id, cutoff=max_depth))
            return paths
        except:
            return []
    
    def get_entity_neighbors(self, graph: Dict[str, Any], entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """获取实体的邻居节点"""
        if "error" in graph:
            return {"error": graph["error"]}
        
        # 将图转换为networkx格式
        import networkx as nx
        nx_graph = nx.Graph()
        
        # 添加节点
        for node in graph["nodes"]:
            nx_graph.add_node(node["id"], **node)
        
        # 添加边
        for edge in graph["edges"]:
            nx_graph.add_edge(edge["source"], edge["target"], **edge)
        
        # 查找邻居节点
        try:
            neighbors = {}
            for i in range(1, depth + 1):
                neighbors[f"depth_{i}"] = []
                
                # 获取第i层邻居
                if i == 1:
                    # 直接邻居
                    for neighbor_id in nx_graph.neighbors(entity_id):
                        neighbor_node = next((n for n in graph["nodes"] if n["id"] == neighbor_id), None)
                        if neighbor_node:
                            neighbors[f"depth_{i}"].append(neighbor_node)
                else:
                    # 多层邻居
                    for node_id in nx_graph.nodes():
                        try:
                            if nx.shortest_path_length(nx_graph, entity_id, node_id) == i:
                                neighbor_node = next((n for n in graph["nodes"] if n["id"] == node_id), None)
                                if neighbor_node:
                                    neighbors[f"depth_{i}"].append(neighbor_node)
                        except:
                            continue
            
            return neighbors
            
        except Exception as e:
            logger.error(f"获取实体 {entity_id} 的邻居失败: {e}")
            return {"error": str(e)}

    def get_document_graph_data(self, db: Session, document_id: int) -> Dict[str, Any]:
        """获取文档的知识图谱数据"""
        try:
            # 检查文档是否存在
            document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
            if not document:
                return {"error": "文档不存在"}
            
            # 构建图谱
            graph = self.build_document_graph(document_id, db)
            if "error" in graph:
                return graph
            
            # 获取统计信息
            statistics = self.get_graph_statistics(graph)
            
            return {
                "nodes": graph.get("nodes", []),
                "links": graph.get("edges", []),
                "statistics": statistics
            }
            
        except Exception as e:
            logger.error(f"获取文档 {document_id} 的图谱数据失败: {e}")
            return {"error": str(e)}

    def get_knowledge_base_graph_data(self, db: Session, knowledge_base_id: int) -> Dict[str, Any]:
        """获取知识库的知识图谱数据"""
        try:
            # 构建知识库图谱
            graph = self.build_knowledge_base_graph(knowledge_base_id, db)
            if "error" in graph:
                return graph
            
            # 获取统计信息
            statistics = self.get_graph_statistics(graph)
            
            return {
                "nodes": graph.get("nodes", []),
                "links": graph.get("edges", []),
                "statistics": statistics
            }
            
        except Exception as e:
            logger.error(f"获取知识库 {knowledge_base_id} 的图谱数据失败: {e}")
            return {"error": str(e)}

    def analyze_graph(self, graph_id: str, db: Session) -> Dict[str, Any]:
        """分析知识图谱"""
        try:
            # 根据graph_id获取图谱数据
            # 这里简化处理，实际应该根据graph_id从数据库或缓存中获取图谱
            if graph_id.startswith("doc_"):
                document_id = int(graph_id.replace("doc_", ""))
                graph_data = self.get_document_graph_data(db, document_id)
            elif graph_id.startswith("kb_"):
                knowledge_base_id = int(graph_id.replace("kb_", ""))
                graph_data = self.get_knowledge_base_graph_data(db, knowledge_base_id)
            else:
                return {"error": "无效的图谱ID"}
            
            if "error" in graph_data:
                return graph_data
            
            # 进行图谱分析
            analysis = self._perform_graph_analysis(graph_data)
            
            return {
                "graph_id": graph_id,
                "analysis": analysis,
                "communities": graph_data.get("communities", []),
                "central_nodes": graph_data.get("central_nodes", [])
            }
            
        except Exception as e:
            logger.error(f"分析图谱 {graph_id} 失败: {e}")
            return {"error": str(e)}

    def _perform_graph_analysis(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行图谱分析"""
        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])
        statistics = graph_data.get("statistics", {})
        
        # 计算网络密度
        n_nodes = len(nodes)
        n_edges = len(links)
        max_possible_edges = n_nodes * (n_nodes - 1) / 2
        density = n_edges / max_possible_edges if max_possible_edges > 0 else 0
        
        # 计算平均度
        avg_degree = (2 * n_edges) / n_nodes if n_nodes > 0 else 0
        
        # 计算连通分量
        import networkx as nx
        nx_graph = nx.Graph()
        
        for node in nodes:
            nx_graph.add_node(node["id"], **node)
        
        for link in links:
            nx_graph.add_edge(link["source"], link["target"], **link)
        
        connected_components = list(nx.connected_components(nx_graph))
        
        return {
            "network_density": round(density, 3),
            "average_degree": round(avg_degree, 2),
            "connected_components": len(connected_components),
            "largest_component_size": max(len(comp) for comp in connected_components) if connected_components else 0,
            **statistics
        }

    def find_similar_nodes(self, graph_id: str, node_id: str, max_results: int, db: Session) -> Dict[str, Any]:
        """查找相似节点"""
        try:
            # 获取图谱数据
            if graph_id.startswith("doc_"):
                document_id = int(graph_id.replace("doc_", ""))
                graph_data = self.get_document_graph_data(db, document_id)
            elif graph_id.startswith("kb_"):
                knowledge_base_id = int(graph_id.replace("kb_", ""))
                graph_data = self.get_knowledge_base_graph_data(db, knowledge_base_id)
            else:
                return {"error": "无效的图谱ID"}
            
            if "error" in graph_data:
                return graph_data
            
            # 查找目标节点
            target_node = next((node for node in graph_data["nodes"] if node["id"] == node_id), None)
            if not target_node:
                return {"error": "节点不存在"}
            
            # 基于节点属性和邻居关系计算相似度
            similar_nodes = self._calculate_similar_nodes(graph_data, target_node, max_results)
            
            return similar_nodes
            
        except Exception as e:
            logger.error(f"查找相似节点失败: {e}")
            return {"error": str(e)}

    def _calculate_similar_nodes(self, graph_data: Dict[str, Any], target_node: Dict, max_results: int) -> List[Dict]:
        """计算相似节点"""
        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])
        
        # 构建邻接表
        adjacency = {}
        for link in links:
            source, target = link["source"], link["target"]
            if source not in adjacency:
                adjacency[source] = []
            adjacency[source].append(target)
            
            if target not in adjacency:
                adjacency[target] = []
            adjacency[target].append(source)
        
        # 计算相似度得分
        similar_nodes = []
        for node in nodes:
            if node["id"] == target_node["id"]:
                continue
            
            # 基于类型相似度
            type_similarity = 1.0 if node.get("type") == target_node.get("type") else 0.0
            
            # 基于邻居相似度
            target_neighbors = set(adjacency.get(target_node["id"], []))
            node_neighbors = set(adjacency.get(node["id"], []))
            
            neighbor_intersection = len(target_neighbors.intersection(node_neighbors))
            neighbor_union = len(target_neighbors.union(node_neighbors))
            neighbor_similarity = neighbor_intersection / neighbor_union if neighbor_union > 0 else 0
            
            # 综合相似度
            total_similarity = 0.6 * type_similarity + 0.4 * neighbor_similarity
            
            similar_nodes.append({
                "node": node,
                "similarity_score": round(total_similarity, 3),
                "type_similarity": type_similarity,
                "neighbor_similarity": neighbor_similarity
            })
        
        # 按相似度排序并返回前max_results个
        similar_nodes.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_nodes[:max_results]

    def find_path_between_nodes(self, graph_id: str, source_node: str, target_node: str, max_path_length: int, db: Session) -> Dict[str, Any]:
        """查找两个节点之间的路径"""
        try:
            # 获取图谱数据
            if graph_id.startswith("doc_"):
                document_id = int(graph_id.replace("doc_", ""))
                graph_data = self.get_document_graph_data(db, document_id)
            elif graph_id.startswith("kb_"):
                knowledge_base_id = int(graph_id.replace("kb_", ""))
                graph_data = self.get_knowledge_base_graph_data(db, knowledge_base_id)
            else:
                return {"error": "无效的图谱ID"}
            
            if "error" in graph_data:
                return graph_data
            
            # 查找路径
            paths = self.find_entity_paths(graph_data, source_node, target_node, max_path_length)
            
            # 格式化路径结果
            formatted_paths = []
            for path in paths:
                formatted_path = []
                for node_id in path:
                    node = next((n for n in graph_data["nodes"] if n["id"] == node_id), None)
                    if node:
                        formatted_path.append(node)
                
                if len(formatted_path) >= 2:  # 至少需要两个节点才能形成路径
                    formatted_paths.append({
                        "path": formatted_path,
                        "length": len(formatted_path) - 1,
                        "nodes": [n["text"] for n in formatted_path]
                    })
            
            return {
                "source_node": source_node,
                "target_node": target_node,
                "paths": formatted_paths,
                "total_paths": len(formatted_paths)
            }
            
        except Exception as e:
            logger.error(f"查找路径失败: {e}")
            return {"error": str(e)}