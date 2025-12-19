"""知识图谱服务模块"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, EntityRelationship, DocumentChunk, KnowledgeDocument
)
from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务，负责实体识别、关系提取和知识图谱查询"""
    
    def __init__(self):
        self.text_processor = AdvancedTextProcessor()
    
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