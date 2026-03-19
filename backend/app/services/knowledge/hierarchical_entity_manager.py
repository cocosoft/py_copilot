"""
层级实体管理器

管理全局级、知识库级、文档级的实体层级关系
实现实体对齐、关系聚合和跨层级查询功能

@task DB-001
@phase 基础架构重构
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    GlobalEntity, KBEntity, DocumentEntity,
    GlobalRelationship, KBRelationship, EntityRelationship
)
from app.modules.knowledge.models.knowledge_document import KnowledgeBase, KnowledgeDocument


class EntityAlignmentService:
    """
    实体对齐服务
    负责不同层级实体之间的映射和对齐
    """
    
    def align_to_kb(self, document_entities: List[DocumentEntity]) -> List[KBEntity]:
        """
        将文档级实体对齐到知识库级实体
        
        Args:
            document_entities: 文档级实体列表
            
        Returns:
            知识库级实体列表
        """
        kb_entities = []
        
        for doc_entity in document_entities:
            # 查找或创建KB级实体
            kb_entity = self._find_or_create_kb_entity(doc_entity)
            doc_entity.kb_entity_id = kb_entity.id
            kb_entities.append(kb_entity)
        
        return kb_entities
    
    def link_to_global(self, kb_entities: List[KBEntity]) -> List[GlobalEntity]:
        """
        将知识库级实体链接到全局级实体
        
        Args:
            kb_entities: 知识库级实体列表
            
        Returns:
            全局级实体列表
        """
        global_entities = []
        
        for kb_entity in kb_entities:
            # 查找或创建全局级实体
            global_entity = self._find_or_create_global_entity(kb_entity)
            kb_entity.global_entity_id = global_entity.id
            global_entities.append(global_entity)
        
        return global_entities
    
    def _find_or_create_kb_entity(self, doc_entity: DocumentEntity) -> KBEntity:
        """
        查找或创建KB级实体
        """
        # 这里应该实现具体的查找逻辑
        # 基于实体文本、类型等进行匹配
        pass
    
    def _find_or_create_global_entity(self, kb_entity: KBEntity) -> GlobalEntity:
        """
        查找或创建全局级实体
        """
        # 这里应该实现具体的查找逻辑
        # 基于规范名称、类型等进行匹配
        pass


class RelationshipAggregator:
    """
    关系聚合服务
    负责聚合不同层级的关系
    """
    
    def aggregate_document_relationships(self, document_entities: List[DocumentEntity]) -> List[KBRelationship]:
        """
        聚合文档级关系到知识库级关系
        
        Args:
            document_entities: 文档级实体列表
            
        Returns:
            知识库级关系列表
        """
        kb_relationships = []
        
        # 收集文档级关系
        doc_relationships = []
        for doc_entity in document_entities:
            doc_relationships.extend(doc_entity.source_relationships)
            doc_relationships.extend(doc_entity.target_relationships)
        
        # 聚合到KB级关系
        for doc_rel in doc_relationships:
            if doc_rel.source_entity.kb_entity_id and doc_rel.target_entity.kb_entity_id:
                kb_rel = self._find_or_create_kb_relationship(doc_rel)
                kb_relationships.append(kb_rel)
        
        return kb_relationships
    
    def aggregate_kb_relationships(self, kb_relationships: List[KBRelationship]) -> List[GlobalRelationship]:
        """
        聚合知识库级关系到全局级关系
        
        Args:
            kb_relationships: 知识库级关系列表
            
        Returns:
            全局级关系列表
        """
        global_relationships = []
        
        for kb_rel in kb_relationships:
            if (kb_rel.source_entity.global_entity_id and 
                kb_rel.target_entity.global_entity_id):
                global_rel = self._find_or_create_global_relationship(kb_rel)
                global_relationships.append(global_rel)
        
        return global_relationships
    
    def _find_or_create_kb_relationship(self, doc_rel: EntityRelationship) -> KBRelationship:
        """
        查找或创建KB级关系
        """
        # 这里应该实现具体的查找逻辑
        pass
    
    def _find_or_create_global_relationship(self, kb_rel: KBRelationship) -> GlobalRelationship:
        """
        查找或创建全局级关系
        """
        # 这里应该实现具体的查找逻辑
        pass


class HierarchicalEntityManager:
    """
    层级实体管理器
    负责管理全局级、知识库级、文档级的实体层级关系
    """
    
    def __init__(self, db: Session):
        """
        初始化层级实体管理器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.entity_alignment_service = EntityAlignmentService()
        self.relationship_aggregator = RelationshipAggregator()
    
    def build_hierarchy(self, document_entities: List[DocumentEntity]) -> Dict[str, Any]:
        """
        构建层级实体关系
        
        Args:
            document_entities: 文档级实体列表
            
        Returns:
            包含各层级实体和关系的字典
        """
        # 1. 文档级 -> 知识库级实体对齐
        kb_entities = self.entity_alignment_service.align_to_kb(document_entities)
        
        # 2. 知识库级 -> 全局级实体链接
        global_entities = self.entity_alignment_service.link_to_global(kb_entities)
        
        # 3. 关系聚合
        kb_relationships = self.relationship_aggregator.aggregate_document_relationships(document_entities)
        global_relationships = self.relationship_aggregator.aggregate_kb_relationships(kb_relationships)
        
        return {
            'document_level': document_entities,
            'kb_level': kb_entities,
            'global_level': global_entities,
            'kb_relationships': kb_relationships,
            'global_relationships': global_relationships
        }
    
    def query_entity_hierarchy(self, entity_id: str, level: str) -> Dict[str, Any]:
        """
        查询实体层级关系
        
        Args:
            entity_id: 实体ID
            level: 实体级别 (document/kb/global)
            
        Returns:
            包含实体层级关系的字典
        """
        if level == 'document':
            # 向上导航到KB级和全局级
            doc_entity = self.db.query(DocumentEntity).filter(
                DocumentEntity.id == entity_id
            ).first()
            
            if not doc_entity:
                return {"error": "Document entity not found"}
            
            kb_entity = doc_entity.kb_entity if doc_entity.kb_entity_id else None
            global_entity = kb_entity.global_entity if kb_entity and kb_entity.global_entity_id else None
            
            return {
                'document_entity': doc_entity,
                'kb_entity': kb_entity,
                'global_entity': global_entity
            }
        
        elif level == 'kb':
            # 双向导航
            kb_entity = self.db.query(KBEntity).filter(
                KBEntity.id == entity_id
            ).first()
            
            if not kb_entity:
                return {"error": "KB entity not found"}
            
            # 向下钻取到文档级
            doc_entities = self.db.query(DocumentEntity).filter(
                DocumentEntity.kb_entity_id == entity_id
            ).all()
            
            # 向上导航到全局级
            global_entity = kb_entity.global_entity if kb_entity.global_entity_id else None
            
            return {
                'kb_entity': kb_entity,
                'document_entities': doc_entities,
                'global_entity': global_entity
            }
        
        elif level == 'global':
            # 向下钻取到KB级和文档级
            global_entity = self.db.query(GlobalEntity).filter(
                GlobalEntity.id == entity_id
            ).first()
            
            if not global_entity:
                return {"error": "Global entity not found"}
            
            # 向下钻取到KB级
            kb_entities = self.db.query(KBEntity).filter(
                KBEntity.global_entity_id == entity_id
            ).all()
            
            # 向下钻取到文档级
            doc_entities = []
            for kb_entity in kb_entities:
                docs = self.db.query(DocumentEntity).filter(
                    DocumentEntity.kb_entity_id == kb_entity.id
                ).all()
                doc_entities.extend(docs)
            
            return {
                'global_entity': global_entity,
                'kb_entities': kb_entities,
                'document_entities': doc_entities
            }
        
        else:
            return {"error": "Invalid level"}
    
    def get_entity_statistics(self, entity_id: str, level: str) -> Dict[str, Any]:
        """
        获取实体统计信息
        
        Args:
            entity_id: 实体ID
            level: 实体级别
            
        Returns:
            实体统计信息
        """
        if level == 'global':
            entity = self.db.query(GlobalEntity).filter(
                GlobalEntity.id == entity_id
            ).first()
            
            if not entity:
                return {"error": "Global entity not found"}
            
            return {
                'entity_type': entity.entity_type,
                'kb_count': entity.kb_count,
                'document_count': entity.document_count,
                'aliases_count': len(entity.all_aliases) if entity.all_aliases else 0
            }
        
        elif level == 'kb':
            entity = self.db.query(KBEntity).filter(
                KBEntity.id == entity_id
            ).first()
            
            if not entity:
                return {"error": "KB entity not found"}
            
            return {
                'entity_type': entity.entity_type,
                'document_count': entity.document_count,
                'occurrence_count': entity.occurrence_count,
                'aliases_count': len(entity.aliases) if entity.aliases else 0
            }
        
        elif level == 'document':
            entity = self.db.query(DocumentEntity).filter(
                DocumentEntity.id == entity_id
            ).first()
            
            if not entity:
                return {"error": "Document entity not found"}
            
            # 统计关系数量
            source_rel_count = len(entity.source_relationships)
            target_rel_count = len(entity.target_relationships)
            
            return {
                'entity_type': entity.entity_type,
                'confidence': entity.confidence,
                'status': entity.status,
                'relationship_count': source_rel_count + target_rel_count
            }
        
        else:
            return {"error": "Invalid level"}