"""知识图谱服务模块"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, EntityRelationship, DocumentChunk, KnowledgeDocument, KnowledgeBase
)
from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
from app.services.knowledge.graph.graph_builder import KnowledgeGraphBuilder
from app.services.knowledge.knowledge_graph_cache import knowledge_graph_cache

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务，负责实体识别、关系提取和知识图谱查询"""

    def __init__(self):
        # 不在初始化时创建text_processor，因为需要db会话
        self._text_processor = None
        self.graph_builder = KnowledgeGraphBuilder()

    @property
    def text_processor(self):
        """获取文本处理器（兼容旧代码）
        
        返回一个默认的文本处理器实例，用于不依赖数据库会话的场景
        """
        if self._text_processor is None:
            self._text_processor = AdvancedTextProcessor(None, None)
        return self._text_processor

    def _get_text_processor(self, db: Session = None, knowledge_base_id: int = None, model_id: str = None):
        """获取文本处理器，如果没有db则使用默认处理器
        
        Args:
            db: 数据库会话
            knowledge_base_id: 知识库ID，用于加载知识库级提取策略配置
            model_id: 指定的模型ID（可选，可以是整数ID的字符串形式或模型字符串ID）
        """
        if db:
            text_processor = AdvancedTextProcessor(db, knowledge_base_id)
            # 如果指定了模型ID，设置到提取器中
            if model_id:
                # 尝试将model_id转换为模型字符串ID
                # model_id可能是整数ID的字符串形式（如"45"）或模型字符串ID（如"deepseek-r1:1.5b"）
                actual_model_id = model_id
                try:
                    # 尝试解析为整数
                    model_int_id = int(model_id)
                    # 如果是整数，需要从数据库获取模型字符串ID
                    from app.services.knowledge.extraction.llm_extractor import _get_model_string_id_from_db
                    actual_model_id = _get_model_string_id_from_db(model_int_id, db)
                    if actual_model_id:
                        logger.info(f"[_get_text_processor] 将模型整数ID {model_id} 转换为字符串ID: {actual_model_id}")
                    else:
                        logger.warning(f"[_get_text_processor] 无法将模型整数ID {model_id} 转换为字符串ID，使用原始值")
                        actual_model_id = model_id
                except ValueError:
                    # 不是整数，直接使用原始值
                    logger.info(f"[_get_text_processor] 使用模型字符串ID: {model_id}")
                    actual_model_id = model_id
                
                text_processor.llm_extractor.specified_model_id = actual_model_id
                logger.info(f"[_get_text_processor] 设置指定模型ID: {actual_model_id}")
            return text_processor
        return self.text_processor
    
    def extract_and_store_entities(self, db: Session, document: KnowledgeDocument,
                                   entities: List[Dict[str, Any]] = None,
                                   relationships: List[Dict[str, Any]] = None,
                                   knowledge_base_id: int = None,
                                   model_id: str = None) -> Dict[str, Any]:
        """从文档中提取实体并存储到数据库

        Args:
            db: 数据库会话
            document: 知识文档对象
            entities: 已提取的实体列表（可选，如果提供则不再重新提取）
            relationships: 已提取的关系列表（可选，如果提供则不再重新提取）
            knowledge_base_id: 知识库ID，用于加载知识库级提取策略配置
            model_id: 指定的模型ID（可选，如果提供则优先使用）
        """
        logger.info(f"[实体提取] 开始处理文档 {document.id}, knowledge_base_id={knowledge_base_id}, model_id={model_id}")

        try:
            if not document.content:
                logger.warning(f"[实体提取] 文档 {document.id} 没有内容，无法提取实体")
                return {"success": False, "error": "文档内容为空"}

            logger.info(f"[实体提取] 文档 {document.id} 内容长度: {len(document.content)}")

            # 如果没有提供实体和关系，则进行提取
            if entities is None or relationships is None:
                logger.info(f"[实体提取] 文档 {document.id} 未提供实体，开始提取...")
                # 使用带有db、knowledge_base_id和model_id的text_processor来获取正确的模型配置
                text_processor = self._get_text_processor(db, knowledge_base_id, model_id)
                logger.info(f"[实体提取] 文档 {document.id} 使用 TextProcessor, knowledge_base_id={knowledge_base_id}, model_id={model_id}")

                entities, relationships = text_processor.extract_entities_relationships_sync(document.content)
                logger.info(f"[实体提取] 文档 {document.id} 提取完成: {len(entities)} 个实体, {len(relationships)} 个关系")

                # 记录提取的实体详情
                if entities:
                    entity_types = {}
                    for e in entities:
                        t = e.get('type', 'UNKNOWN')
                        entity_types[t] = entity_types.get(t, 0) + 1
                    logger.info(f"[实体提取] 文档 {document.id} 实体类型分布: {entity_types}")
                    logger.info(f"[实体提取] 文档 {document.id} 前5个实体: {entities[:5]}")
                else:
                    logger.warning(f"[实体提取] 文档 {document.id} 没有提取到任何实体!")
            else:
                logger.info(f"[实体提取] 文档 {document.id} 使用已提供的实体: {len(entities)} 个实体, {len(relationships)} 个关系")

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
    
    def get_document_entities(self, db: Session, document_id: int, distinct: bool = True) -> List[Dict[str, Any]]:
        """获取文档的所有实体
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            distinct: 是否去重（默认True，按实体文本和类型去重）
        """
        entities = db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        ).all()
        
        if distinct:
            # 按实体文本和类型去重，保留置信度最高的
            entity_map = {}
            for entity in entities:
                key = (entity.entity_text, entity.entity_type)
                if key not in entity_map or entity.confidence > entity_map[key].confidence:
                    entity_map[key] = entity
            entities = list(entity_map.values())
        
        # 获取文档标题
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        document_name = document.title if document else '未知文档'
        
        return [
            {
                "id": entity.id,
                "text": entity.entity_text,
                "name": entity.entity_text,
                "type": entity.entity_type,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos,
                "confidence": entity.confidence,
                "document_id": entity.document_id,
                "document_name": document_name,
                "occurrences": 1,
                "status": "pending",
                "description": ""
            }
            for entity in entities
        ]

    def get_knowledge_base_entities(self, db: Session, knowledge_base_id: int, distinct: bool = True) -> List[Dict[str, Any]]:
        """获取知识库的所有实体
        
        Args:
            db: 数据库会话
            knowledge_base_id: 知识库ID
            distinct: 是否去重（默认True，按实体文本和类型去重）
        """
        # 获取知识库中的所有文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        if not documents:
            return []
        
        # 获取所有文档的实体
        all_entities = []
        document_ids = [doc.id for doc in documents]
        document_map = {doc.id: doc.title for doc in documents}
        
        entities = db.query(DocumentEntity).filter(
            DocumentEntity.document_id.in_(document_ids)
        ).all()
        
        if distinct:
            # 按实体文本和类型去重，保留置信度最高的
            entity_map = {}
            for entity in entities:
                key = (entity.entity_text, entity.entity_type)
                if key not in entity_map or entity.confidence > entity_map[key].confidence:
                    entity_map[key] = entity
            entities = list(entity_map.values())
        
        return [
            {
                "id": entity.id,
                "text": entity.entity_text,
                "name": entity.entity_text,
                "type": entity.entity_type,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos,
                "confidence": entity.confidence,
                "document_id": entity.document_id,
                "document_name": document_map.get(entity.document_id, '未知文档'),
                "occurrences": 1,
                "status": "pending",
                "description": ""
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
        edges = []
        
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
                edges.append({
                    "source": entity_map[rel.source_id],
                    "target": entity_map[rel.target_id],
                    "label": rel.relationship_type,
                    "relationship_id": rel.id,
                    "confidence": rel.confidence
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
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
        
        text_processor = self._get_text_processor()
        return text_processor.extract_keywords(document.content, top_n)
    
    def analyze_document_semantics(self, document: KnowledgeDocument) -> Dict[str, Any]:
        """分析文档语义特征"""
        if not document.content:
            return {"error": "文档内容为空"}
        
        text_processor = self._get_text_processor()
        
        # 提取关键词
        keywords = text_processor.extract_keywords(document.content, 20)
        
        # 分析文本特征
        text_length = len(document.content)
        word_count = len(document.content.split())
        
        # 计算实体密度（如果有实体）
        entities = text_processor.extract_entities_relationships(document.content)[0]
        entity_density = len(entities) / (text_length / 1000) if text_length > 0 else 0
        
        return {
            "text_length": text_length,
            "word_count": word_count,
            "entity_count": len(entities),
            "entity_density": round(entity_density, 2),
            "top_keywords": keywords[:10],
            "semantic_richness": min(1.0, len(entities) / 10)  # 语义丰富度评分
        }
    
    def build_document_graph(self, document_id: int, db: Session, knowledge_base_id: int = None) -> Dict[str, Any]:
        """构建单个文档的知识图谱 - 带缓存优化

        Args:
            document_id: 文档ID
            db: 数据库会话
            knowledge_base_id: 知识库ID，用于加载知识库级提取策略配置
        """
        logger.info(f"[构建图谱] 开始构建文档 {document_id} 的知识图谱, knowledge_base_id={knowledge_base_id}")

        try:
            # 检查文档是否存在
            document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
            if not document:
                logger.error(f"[构建图谱] 文档 {document_id} 不存在")
                return {"error": "文档不存在"}

            logger.info(f"[构建图谱] 文档 {document_id} 信息: 标题={document.title or '无'}, "
                       f"知识库ID={document.knowledge_base_id}, 内容长度={len(document.content or '')}")

            # 如果未传入 knowledge_base_id，从文档对象获取
            if knowledge_base_id is None and document.knowledge_base_id:
                knowledge_base_id = document.knowledge_base_id
                logger.info(f"[构建图谱] 从文档获取知识库ID: {knowledge_base_id}")

            # 检查缓存（使用文档内容的哈希作为缓存键的一部分）
            content_hash = None
            if document.content:
                import hashlib
                content_hash = hashlib.md5(document.content.encode()).hexdigest()[:16]

            cached_graph = knowledge_graph_cache.get(document_id, content_hash)
            if cached_graph:
                logger.info(f"[构建图谱] 文档 {document_id} 的知识图谱从缓存获取")
                return cached_graph

            # 1. 检查文档是否已进行实体提取，如果没有则先执行实体提取
            logger.info(f"[构建图谱] 文档 {document_id} 检查已有实体和关系...")
            entities = self.get_document_entities(db, document_id)
            relationships = self.get_document_relationships(db, document_id)
            logger.info(f"[构建图谱] 文档 {document_id} 已有实体: {len(entities)}, 关系: {len(relationships)}")

            if not entities:
                logger.info(f"[构建图谱] 文档 {document_id} 未进行实体提取，开始执行实体提取...")

                # 执行实体提取，传入 knowledge_base_id 以使用正确的提取策略
                logger.info(f"[构建图谱] 文档 {document_id} 调用 extract_and_store_entities, knowledge_base_id={knowledge_base_id}")
                extraction_result = self.extract_and_store_entities(
                    db,
                    document,
                    knowledge_base_id=knowledge_base_id
                )

                logger.info(f"[构建图谱] 文档 {document_id} 实体提取结果: success={extraction_result.get('success')}, "
                           f"entities_count={extraction_result.get('entities_count')}, "
                           f"error={extraction_result.get('error')}")

                if not extraction_result.get("success", False):
                    logger.error(f"[构建图谱] 文档 {document_id} 实体提取失败: {extraction_result.get('error', '未知错误')}")
                    return {"error": f"实体提取失败: {extraction_result.get('error', '未知错误')}"}

                # 重新获取实体和关系
                logger.info(f"[构建图谱] 文档 {document_id} 重新获取实体和关系...")
                entities = self.get_document_entities(db, document_id)
                relationships = self.get_document_relationships(db, document_id)
                logger.info(f"[构建图谱] 文档 {document_id} 重新获取后: 实体={len(entities)}, 关系={len(relationships)}")

                # 检查实体提取是否真的成功
                if not entities:
                    logger.error(f"[构建图谱] 文档 {document_id} 实体提取后仍然没有实体!")
                    return {"error": "实体提取后没有发现任何实体"}

                logger.info(f"[构建图谱] 文档 {document_id} 实体提取成功，提取到 {len(entities)} 个实体和 {len(relationships)} 个关系")
            elif not relationships:
                # 有实体但没有关系，需要重新提取关系
                logger.info(f"[构建图谱] 文档 {document_id} 有 {len(entities)} 个实体但没有关系，重新提取实体和关系...")

                # 清除旧的实体（因为关系需要基于新的实体ID）
                logger.info(f"[构建图谱] 文档 {document_id} 清除旧实体...")
                db.query(DocumentEntity).filter(DocumentEntity.document_id == document_id).delete()
                db.commit()

                # 重新执行实体提取（会同时提取关系）
                extraction_result = self.extract_and_store_entities(
                    db,
                    document,
                    knowledge_base_id=knowledge_base_id
                )

                if not extraction_result.get("success", False):
                    logger.error(f"[构建图谱] 文档 {document_id} 重新提取失败: {extraction_result.get('error', '未知错误')}")
                    return {"error": f"重新提取失败: {extraction_result.get('error', '未知错误')}"}

                # 重新获取实体和关系
                entities = self.get_document_entities(db, document_id)
                relationships = self.get_document_relationships(db, document_id)
                logger.info(f"[构建图谱] 文档 {document_id} 重新提取后: 实体={len(entities)}, 关系={len(relationships)}")
            else:
                logger.info(f"[构建图谱] 文档 {document_id} 已有 {len(entities)} 个实体和 {len(relationships)} 个关系，直接构建知识图谱")

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

            # 5. 缓存结果
            knowledge_graph_cache.set(document_id, graph, content_hash)

            logger.info(f"成功构建文档 {document_id} 的知识图谱，包含 {len(nodes)} 个节点和 {len(edges)} 条边")
            return graph
            
        except Exception as e:
            logger.error(f"构建文档 {document_id} 的知识图谱失败: {e}")
            return {"error": str(e)}
    
    def build_knowledge_base_graph(self, knowledge_base_id: int, db: Session) -> Dict[str, Any]:
        """构建整个知识库的知识图谱"""
        try:
            # 检查知识库是否存在
            knowledge_base = db.query(KnowledgeBase).filter(
                KnowledgeBase.id == knowledge_base_id
            ).first()

            if not knowledge_base:
                return {"error": "知识库不存在"}

            # 检查知识库是否有文档
            document_count = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).count()

            if document_count == 0:
                # 知识库存在但没有文档，返回空图谱而不是错误
                logger.info(f"知识库 {knowledge_base_id} 存在但没有文档，返回空图谱")
                return {
                    "nodes": [],
                    "edges": [],
                    "metadata": {
                        "knowledge_base_id": knowledge_base_id,
                        "knowledge_base_name": knowledge_base.name,
                        "document_count": 0,
                        "is_empty": True
                    }
                }

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
                "edges": graph.get("edges", []),
                "statistics": statistics
            }
            
        except Exception as e:
            logger.error(f"获取文档 {document_id} 的图谱数据失败: {e}")
            return {"error": str(e)}

    def get_knowledge_base_graph_data(self, db: Session, knowledge_base_id: int) -> Dict[str, Any]:
        """获取知识库的知识图谱数据"""
        try:
            # 首先尝试从缓存获取
            cached_graph = knowledge_graph_cache.get_kb_graph(knowledge_base_id)
            if cached_graph:
                logger.info(f"从缓存获取知识库 {knowledge_base_id} 的图谱数据")
                return cached_graph

            # 构建知识库图谱
            graph = self.build_knowledge_base_graph(knowledge_base_id, db)
            if "error" in graph:
                return graph

            # 获取统计信息
            statistics = self.get_graph_statistics(graph)

            result = {
                "nodes": graph.get("nodes", []),
                "edges": graph.get("edges", []),
                "statistics": statistics
            }

            # 缓存结果
            knowledge_graph_cache.set_kb_graph(knowledge_base_id, result)
            logger.info(f"知识库 {knowledge_base_id} 的图谱数据已缓存")

            return result

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

    def get_graph_data_by_layer(
        self, 
        db: Session, 
        layer: str = "document",
        knowledge_base_id: Optional[int] = None,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """根据层级获取知识图谱数据
        
        支持三级图谱数据查询：
        - document: 文档级实体和关系
        - kb: 知识库级实体和关系  
        - global: 全局级实体和关系
        
        Args:
            db: 数据库会话
            layer: 图层类型 (document, kb, global)
            knowledge_base_id: 知识库ID
            document_id: 文档ID
            
        Returns:
            图谱数据，包含nodes和edges
        """
        try:
            if layer == "document":
                # 文档级：查询单个文档的实体和关系
                if document_id:
                    return self.get_document_graph_data(db, document_id)
                elif knowledge_base_id:
                    # 如果只有知识库ID，返回该知识库下所有文档的汇总
                    return self._get_documents_graph_for_kb(db, knowledge_base_id)
                else:
                    return {"error": "文档级查询需要提供document_id或knowledge_base_id"}
                    
            elif layer == "kb":
                # 知识库级：查询知识库级的实体对齐和关系
                if knowledge_base_id:
                    return self.get_knowledge_base_graph_data(db, knowledge_base_id)
                else:
                    return {"error": "知识库级查询需要提供knowledge_base_id"}
                    
            elif layer == "global":
                # 全局级：查询跨知识库的全局实体和关系
                return self._get_global_graph_data(db)
                
            else:
                return {"error": f"不支持的图层类型: {layer}，支持的类型: document, kb, global"}
                
        except Exception as e:
            logger.error(f"获取{layer}级图谱数据失败: {e}")
            return {"error": str(e)}

    def _get_documents_graph_for_kb(self, db: Session, knowledge_base_id: int) -> Dict[str, Any]:
        """获取知识库下所有文档的图谱数据汇总"""
        try:
            # 获取知识库下的所有文档
            documents = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).all()
            
            if not documents:
                return {"nodes": [], "edges": [], "statistics": {"total_documents": 0}}
            
            # 汇总所有文档的实体和关系
            all_nodes = []
            all_edges = []
            entity_map = {}  # 用于去重
            
            for doc in documents:
                # 获取文档的实体
                entities = db.query(DocumentEntity).filter(
                    DocumentEntity.document_id == doc.id
                ).all()
                
                for entity in entities:
                    node_id = f"doc{doc.id}_entity{entity.id}"
                    if node_id not in entity_map:
                        entity_map[node_id] = {
                            "id": node_id,
                            "label": entity.entity_text,
                            "type": entity.entity_type,
                            "entity_id": entity.id,
                            "document_id": doc.id,
                            "document_name": doc.title,
                            "confidence": entity.confidence,
                            "group": entity.entity_type
                        }
                        all_nodes.append(entity_map[node_id])
                
                # 获取文档的关系
                relationships = db.query(EntityRelationship).filter(
                    EntityRelationship.document_id == doc.id
                ).all()
                
                for rel in relationships:
                    source_id = f"doc{doc.id}_entity{rel.source_id}"
                    target_id = f"doc{doc.id}_entity{rel.target_id}"
                    
                    if source_id in entity_map and target_id in entity_map:
                        all_edges.append({
                            "source": source_id,
                            "target": target_id,
                            "label": rel.relationship_type,
                            "relationship_id": rel.id,
                            "confidence": rel.confidence,
                            "document_id": doc.id
                        })
            
            # 统计信息
            entity_types = {}
            for node in all_nodes:
                entity_type = node.get("type", "未知")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            return {
                "nodes": all_nodes,
                "edges": all_edges,
                "statistics": {
                    "total_documents": len(documents),
                    "total_entities": len(all_nodes),
                    "total_relationships": len(all_edges),
                    "entity_types": entity_types
                }
            }
            
        except Exception as e:
            logger.error(f"获取知识库 {knowledge_base_id} 的文档图谱汇总失败: {e}")
            return {"error": str(e)}

    def _get_global_graph_data(self, db: Session) -> Dict[str, Any]:
        """获取全局级图谱数据（跨知识库）"""
        try:
            # 获取所有知识库
            from app.modules.knowledge.models.knowledge_document import KnowledgeBase
            
            knowledge_bases = db.query(KnowledgeBase).all()
            
            if not knowledge_bases:
                return {"nodes": [], "edges": [], "statistics": {"total_knowledge_bases": 0}}
            
            # 汇总所有知识库的实体和关系
            all_nodes = []
            all_edges = []
            entity_map = {}  # 用于去重
            
            for kb in knowledge_bases:
                # 获取知识库下的所有文档
                documents = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.knowledge_base_id == kb.id
                ).all()
                
                for doc in documents:
                    # 获取文档的实体
                    entities = db.query(DocumentEntity).filter(
                        DocumentEntity.document_id == doc.id
                    ).all()
                    
                    for entity in entities:
                        # 使用实体文本和类型作为唯一标识，实现跨文档去重
                        entity_key = f"{entity.entity_text}_{entity.entity_type}"
                        
                        if entity_key not in entity_map:
                            node_id = f"global_entity_{len(entity_map)}"
                            entity_map[entity_key] = node_id
                            all_nodes.append({
                                "id": node_id,
                                "label": entity.entity_text,
                                "type": entity.entity_type,
                                "entity_id": entity.id,
                                "document_id": doc.id,
                                "knowledge_base_id": kb.id,
                                "confidence": entity.confidence,
                                "group": entity.entity_type
                            })
            
            # 获取所有关系
            all_relationships = db.query(EntityRelationship).all()
            
            for rel in all_relationships:
                # 获取源实体和目标实体
                source_entity = db.query(DocumentEntity).filter(
                    DocumentEntity.id == rel.source_id
                ).first()
                target_entity = db.query(DocumentEntity).filter(
                    DocumentEntity.id == rel.target_id
                ).first()
                
                if source_entity and target_entity:
                    source_key = f"{source_entity.entity_text}_{source_entity.entity_type}"
                    target_key = f"{target_entity.entity_text}_{target_entity.entity_type}"
                    
                    if source_key in entity_map and target_key in entity_map:
                        all_edges.append({
                            "source": entity_map[source_key],
                            "target": entity_map[target_key],
                            "label": rel.relationship_type,
                            "relationship_id": rel.id,
                            "confidence": rel.confidence
                        })
            
            # 统计信息
            entity_types = {}
            for node in all_nodes:
                entity_type = node.get("type", "未知")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            return {
                "nodes": all_nodes,
                "edges": all_edges,
                "statistics": {
                    "total_knowledge_bases": len(knowledge_bases),
                    "total_entities": len(all_nodes),
                    "total_relationships": len(all_edges),
                    "entity_types": entity_types
                }
            }
            
        except Exception as e:
            logger.error(f"获取全局图谱数据失败: {e}")
            return {"error": str(e)}