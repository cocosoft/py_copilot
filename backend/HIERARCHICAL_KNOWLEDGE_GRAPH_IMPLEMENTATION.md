# 分层知识图谱实施方案

## 1. 项目概述

### 1.1 目标
基于现有知识图谱系统，构建三层知识图谱体系：
- **文档级图谱 (Document)**: 单一文档的微观知识结构（已存在）
- **知识库级图谱 (Knowledge Base)**: 单一知识库内的知识整合（新增）
- **全局级图谱 (Global)**: 跨所有知识库的全局视角（新增）

### 1.2 实施范围
- 数据库模型扩展
- 核心算法实现
- 分层构建流程
- API接口开发
- 前端可视化适配

---

## 2. 数据库表结构实现

### 2.1 新增表结构

#### 2.1.1 知识库级实体表 (kb_entities)

```python
# app/modules/knowledge/models/knowledge_document.py 中添加

class KBEntity(Base):
    """
    知识库级实体 - 跨文档整合
    
    用于聚合同一知识库内不同文档中的相同实体
    """
    __tablename__ = "kb_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    # 实体信息
    canonical_name = Column(String(200), nullable=False)  # 规范名称
    entity_type = Column(String(50), nullable=False, index=True)  # 实体类型
    aliases = Column(JSON, default=list)  # 别名列表 ["别名1", "别名2"]
    
    # 统计信息
    document_count = Column(Integer, default=0)  # 出现文档数
    occurrence_count = Column(Integer, default=0)  # 总出现次数
    
    # 层级关联
    global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=True, index=True)
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="kb_entities")
    global_entity = relationship("GlobalEntity", back_populates="kb_entities")
    document_entities = relationship("DocumentEntity", back_populates="kb_entity")
    
    def __repr__(self):
        return f"<KBEntity(id={self.id}, name='{self.canonical_name}', type='{self.entity_type}')>"
```

#### 2.1.2 全局级实体表 (global_entities)

```python
# app/modules/knowledge/models/knowledge_document.py 中添加

class GlobalEntity(Base):
    """
    全局级实体 - 跨知识库统一
    
    用于聚合不同知识库中的相同实体，提供全局视角
    """
    __tablename__ = "global_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 实体信息
    global_name = Column(String(200), nullable=False)  # 全局规范名称
    entity_type = Column(String(50), nullable=False, index=True)  # 实体类型
    all_aliases = Column(JSON, default=list)  # 所有别名（跨知识库）
    
    # 统计信息
    kb_count = Column(Integer, default=0)  # 出现知识库数
    document_count = Column(Integer, default=0)  # 出现文档数
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    kb_entities = relationship("KBEntity", back_populates="global_entity")
    
    def __repr__(self):
        return f"<GlobalEntity(id={self.id}, name='{self.global_name}', type='{self.entity_type}')>"
```

#### 2.1.3 知识库级关系表 (kb_relationships)

```python
# app/modules/knowledge/models/knowledge_document.py 中添加

class KBRelationship(Base):
    """
    知识库级关系 - 跨文档聚合
    
    聚合同一知识库内不同文档中的相同关系
    """
    __tablename__ = "kb_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    # 关联的KB级实体
    source_kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=False, index=True)
    target_kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=False, index=True)
    
    # 关系信息
    relationship_type = Column(String(100), nullable=False)  # 关系类型
    aggregated_count = Column(Integer, default=0)  # 聚合的关系数量
    
    # 来源文档关系ID列表
    source_relationships = Column(JSON, default=list)  # [doc_rel_id1, doc_rel_id2, ...]
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase")
    source_entity = relationship("KBEntity", foreign_keys=[source_kb_entity_id])
    target_entity = relationship("KBEntity", foreign_keys=[target_kb_entity_id])
    
    def __repr__(self):
        return f"<KBRelationship(id={self.id}, type='{self.relationship_type}')>"
```

#### 2.1.4 全局级关系表 (global_relationships)

```python
# app/modules/knowledge/models/knowledge_document.py 中添加

class GlobalRelationship(Base):
    """
    全局级关系 - 跨知识库发现
    
    发现不同知识库中实体间的关联关系
    """
    __tablename__ = "global_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的全局实体
    source_global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=False, index=True)
    target_global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=False, index=True)
    
    # 关系信息
    relationship_type = Column(String(100), nullable=False)  # 关系类型
    aggregated_count = Column(Integer, default=0)  # 聚合的关系数量
    
    # 来源知识库ID列表
    source_kbs = Column(JSON, default=list)  # [kb_id1, kb_id2, ...]
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # 关系
    source_entity = relationship("GlobalEntity", foreign_keys=[source_global_entity_id])
    target_entity = relationship("GlobalEntity", foreign_keys=[target_global_entity_id])
    
    def __repr__(self):
        return f"<GlobalRelationship(id={self.id}, type='{self.relationship_type}')>"
```

### 2.2 修改现有表

#### 2.2.1 修改 DocumentEntity 表

```python
# 在 DocumentEntity 类中添加层级关联字段

class DocumentEntity(Base):
    """文档实体模型"""
    __tablename__ = "document_entities"
    
    # ... 现有字段 ...
    
    # 新增：层级关联字段
    kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=True, index=True)
    global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=True, index=True)
    
    # 新增：关系
    kb_entity = relationship("KBEntity", back_populates="document_entities")
    global_entity = relationship("GlobalEntity")
    
    # ... 现有代码 ...
```

#### 2.2.2 修改 KnowledgeBase 表

```python
# 在 KnowledgeBase 类中添加关系

class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    # ... 现有字段 ...
    
    # 新增：关系
    kb_entities = relationship("KBEntity", back_populates="knowledge_base", cascade="all, delete-orphan")
    kb_relationships = relationship("KBRelationship", cascade="all, delete-orphan")
    
    # ... 现有代码 ...
```

### 2.3 数据库迁移脚本

```python
# alembic/versions/xxx_add_hierarchical_knowledge_graph.py

"""添加分层知识图谱支持

Revision ID: xxx
Revises: 006_add_file_hash_to_knowledge_documents
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'xxx'
down_revision = '006_add_file_hash_to_knowledge_documents'
branch_labels = None
depends_on = None


def upgrade():
    # 创建全局实体表
    op.create_table(
        'global_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('global_name', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('all_aliases', sa.JSON(), nullable=True),
        sa.Column('kb_count', sa.Integer(), default=0),
        sa.Column('document_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_global_entities_type', 'global_entities', ['entity_type'])
    
    # 创建知识库级实体表
    op.create_table(
        'kb_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False),
        sa.Column('canonical_name', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('document_count', sa.Integer(), default=0),
        sa.Column('occurrence_count', sa.Integer(), default=0),
        sa.Column('global_entity_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id']),
        sa.ForeignKeyConstraint(['global_entity_id'], ['global_entities.id'])
    )
    op.create_index('idx_kb_entities_kb', 'kb_entities', ['knowledge_base_id'])
    op.create_index('idx_kb_entities_type', 'kb_entities', ['entity_type'])
    op.create_index('idx_kb_entities_global', 'kb_entities', ['global_entity_id'])
    
    # 创建知识库级关系表
    op.create_table(
        'kb_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False),
        sa.Column('source_kb_entity_id', sa.Integer(), nullable=False),
        sa.Column('target_kb_entity_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('aggregated_count', sa.Integer(), default=0),
        sa.Column('source_relationships', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id']),
        sa.ForeignKeyConstraint(['source_kb_entity_id'], ['kb_entities.id']),
        sa.ForeignKeyConstraint(['target_kb_entity_id'], ['kb_entities.id'])
    )
    op.create_index('idx_kb_relations_kb', 'kb_relationships', ['knowledge_base_id'])
    op.create_index('idx_kb_relations_source', 'kb_relationships', ['source_kb_entity_id'])
    op.create_index('idx_kb_relations_target', 'kb_relationships', ['target_kb_entity_id'])
    
    # 创建全局级关系表
    op.create_table(
        'global_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_global_entity_id', sa.Integer(), nullable=False),
        sa.Column('target_global_entity_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('aggregated_count', sa.Integer(), default=0),
        sa.Column('source_kbs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_global_entity_id'], ['global_entities.id']),
        sa.ForeignKeyConstraint(['target_global_entity_id'], ['global_entities.id'])
    )
    op.create_index('idx_global_relations_source', 'global_relationships', ['source_global_entity_id'])
    op.create_index('idx_global_relations_target', 'global_relationships', ['target_global_entity_id'])
    
    # 修改 document_entities 表，添加层级关联
    op.add_column('document_entities', sa.Column('kb_entity_id', sa.Integer(), nullable=True))
    op.add_column('document_entities', sa.Column('global_entity_id', sa.Integer(), nullable=True))
    op.create_index('idx_doc_entities_kb', 'document_entities', ['kb_entity_id'])
    op.create_index('idx_doc_entities_global', 'document_entities', ['global_entity_id'])
    op.create_foreign_key('fk_doc_entities_kb', 'document_entities', 'kb_entities', ['kb_entity_id'], ['id'])
    op.create_foreign_key('fk_doc_entities_global', 'document_entities', 'global_entities', ['global_entity_id'], ['id'])


def downgrade():
    # 删除外键
    op.drop_constraint('fk_doc_entities_kb', 'document_entities', type_='foreignkey')
    op.drop_constraint('fk_doc_entities_global', 'document_entities', type_='foreignkey')
    
    # 删除列
    op.drop_column('document_entities', 'kb_entity_id')
    op.drop_column('document_entities', 'global_entity_id')
    
    # 删除表
    op.drop_table('global_relationships')
    op.drop_table('kb_relationships')
    op.drop_table('kb_entities')
    op.drop_table('global_entities')
```

---

## 3. 核心算法实现

### 3.1 实体对齐服务

```python
# app/services/knowledge/entity_alignment_service.py

import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
import logging

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, KBEntity, KnowledgeDocument
)

logger = logging.getLogger(__name__)


class EntityAlignmentService:
    """
    实体对齐服务
    
    用于将文档级实体对齐到知识库级实体
    核心功能：实体聚类、相似度计算、别名发现
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.text_similarity_threshold = 0.75
        self.semantic_similarity_threshold = 0.70
    
    def align_entities_for_kb(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        对指定知识库的所有文档实体进行对齐
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            {
                "success": bool,
                "kb_entities_created": int,
                "entities_aligned": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取知识库内所有文档实体
            entities = self.db.query(DocumentEntity).join(
                KnowledgeDocument
            ).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).all()
            
            if not entities:
                return {
                    "success": True,
                    "kb_entities_created": 0,
                    "entities_aligned": 0,
                    "message": "知识库中没有文档实体"
                }
            
            # 2. 按实体类型分组
            entity_groups = self._group_by_type(entities)
            
            total_kb_entities = 0
            total_aligned = 0
            
            # 3. 对每个类型组进行对齐
            for entity_type, type_entities in entity_groups.items():
                kb_entities, aligned_count = self._align_entity_group(
                    knowledge_base_id, entity_type, type_entities
                )
                total_kb_entities += len(kb_entities)
                total_aligned += aligned_count
            
            return {
                "success": True,
                "kb_entities_created": total_kb_entities,
                "entities_aligned": total_aligned
            }
            
        except Exception as e:
            logger.error(f"实体对齐失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _group_by_type(self, entities: List[DocumentEntity]) -> Dict[str, List[DocumentEntity]]:
        """按实体类型分组"""
        groups = defaultdict(list)
        for entity in entities:
            groups[entity.entity_type].append(entity)
        return dict(groups)
    
    def _align_entity_group(
        self, 
        knowledge_base_id: int, 
        entity_type: str, 
        entities: List[DocumentEntity]
    ) -> Tuple[List[KBEntity], int]:
        """
        对齐同一类型的实体组
        
        Args:
            knowledge_base_id: 知识库ID
            entity_type: 实体类型
            entities: 实体列表
            
        Returns:
            (KBEntity列表, 对齐的实体数量)
        """
        if len(entities) == 0:
            return [], 0
        
        # 1. 计算相似度矩阵
        similarity_matrix = self._compute_similarity_matrix(entities)
        
        # 2. 层次聚类
        clusters = self._hierarchical_clustering(entities, similarity_matrix)
        
        # 3. 为每个聚类创建KB实体
        kb_entities = []
        aligned_count = 0
        
        for cluster in clusters:
            kb_entity = self._create_kb_entity(knowledge_base_id, entity_type, cluster)
            kb_entities.append(kb_entity)
            aligned_count += len(cluster)
        
        return kb_entities, aligned_count
    
    def _compute_similarity_matrix(
        self, 
        entities: List[DocumentEntity]
    ) -> np.ndarray:
        """
        计算实体间的相似度矩阵
        
        使用多维度相似度：
        - 文本相似度 (40%): Jaro-Winkler
        - 语义相似度 (40%): 基于词向量的余弦相似度
        - 上下文相似度 (20%): 文档相关性
        """
        n = len(entities)
        similarity = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                # 文本相似度
                text_sim = self._text_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )
                
                # 语义相似度（简化实现，可使用词向量）
                semantic_sim = self._semantic_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )
                
                # 上下文相似度
                context_sim = self._context_similarity(
                    entities[i].document_id,
                    entities[j].document_id
                )
                
                # 加权组合
                similarity[i][j] = similarity[j][i] = (
                    0.4 * text_sim +
                    0.4 * semantic_sim +
                    0.2 * context_sim
                )
        
        return similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度
        
        使用 SequenceMatcher 计算 Jaro-Winkler 风格的相似度
        """
        if not text1 or not text2:
            return 0.0
        
        # 标准化文本
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        # 完全匹配
        if t1 == t2:
            return 1.0
        
        # 包含关系
        if t1 in t2 or t2 in t1:
            return 0.9
        
        # 序列相似度
        return SequenceMatcher(None, t1, t2).ratio()
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """
        计算语义相似度
        
        简化实现：基于词重叠和词序
        可扩展为使用预训练词向量（如 Word2Vec、BERT）
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard 相似度
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _context_similarity(self, doc_id1: int, doc_id2: int) -> float:
        """
        计算上下文相似度
        
        基于文档是否相同或相关
        """
        if doc_id1 == doc_id2:
            return 1.0
        
        # 可扩展：检查文档标签、知识库等
        return 0.5
    
    def _hierarchical_clustering(
        self, 
        entities: List[DocumentEntity], 
        similarity_matrix: np.ndarray
    ) -> List[List[DocumentEntity]]:
        """
        层次聚类
        
        使用自底向上的聚合聚类，将相似实体分到同一组
        """
        n = len(entities)
        if n == 0:
            return []
        
        if n == 1:
            return [[entities[0]]]
        
        # 初始化：每个实体为一个簇
        clusters = [[i] for i in range(n)]
        
        # 自底向上合并
        merged = True
        while merged and len(clusters) > 1:
            merged = False
            best_merge = None
            best_similarity = self.text_similarity_threshold
            
            # 找到最相似的簇对
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = self._cluster_similarity(
                        clusters[i], clusters[j], similarity_matrix
                    )
                    if sim > best_similarity:
                        best_similarity = sim
                        best_merge = (i, j)
            
            # 合并最相似的簇
            if best_merge:
                i, j = best_merge
                clusters[i] = clusters[i] + clusters[j]
                clusters.pop(j)
                merged = True
        
        # 转换索引为实体
        return [[entities[idx] for idx in cluster] for cluster in clusters]
    
    def _cluster_similarity(
        self, 
        cluster1: List[int], 
        cluster2: List[int], 
        similarity_matrix: np.ndarray
    ) -> float:
        """计算两个簇的相似度（平均链接）"""
        total_sim = 0.0
        count = 0
        
        for i in cluster1:
            for j in cluster2:
                total_sim += similarity_matrix[i][j]
                count += 1
        
        return total_sim / count if count > 0 else 0.0
    
    def _create_kb_entity(
        self, 
        knowledge_base_id: int, 
        entity_type: str, 
        entity_cluster: List[DocumentEntity]
    ) -> KBEntity:
        """
        从实体聚类创建KB级实体
        """
        # 选择规范名称（出现次数最多的）
        name_counts = defaultdict(int)
        for entity in entity_cluster:
            name_counts[entity.entity_text] += 1
        
        canonical_name = max(name_counts.keys(), key=lambda x: name_counts[x])
        
        # 收集别名
        aliases = list(set([
            entity.entity_text 
            for entity in entity_cluster 
            if entity.entity_text != canonical_name
        ]))
        
        # 统计信息
        document_ids = set(entity.document_id for entity in entity_cluster)
        
        # 创建KB实体
        kb_entity = KBEntity(
            knowledge_base_id=knowledge_base_id,
            canonical_name=canonical_name,
            entity_type=entity_type,
            aliases=aliases,
            document_count=len(document_ids),
            occurrence_count=len(entity_cluster)
        )
        
        self.db.add(kb_entity)
        self.db.flush()  # 获取ID
        
        # 更新文档实体的关联
        for entity in entity_cluster:
            entity.kb_entity_id = kb_entity.id
        
        return kb_entity
```

### 3.2 跨库实体链接服务

```python
# app/services/knowledge/cross_kb_linking_service.py

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    KBEntity, GlobalEntity
)
from app.services.knowledge.entity_alignment_service import EntityAlignmentService

logger = logging.getLogger(__name__)


class CrossKBEntityLinkingService:
    """
    跨知识库实体链接服务
    
    用于将不同知识库的KB级实体链接到全局级实体
    核心功能：实体链接、全局消歧、跨库关系发现
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.alignment_service = EntityAlignmentService(db)
        self.name_similarity_threshold = 0.60
        self.semantic_similarity_threshold = 0.70
    
    def link_entities_global(self) -> Dict[str, Any]:
        """
        对所有知识库的KB实体进行全局链接
        
        Returns:
            {
                "success": bool,
                "global_entities_created": int,
                "kb_entities_linked": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取所有KB实体
            kb_entities = self.db.query(KBEntity).all()
            
            if not kb_entities:
                return {
                    "success": True,
                    "global_entities_created": 0,
                    "kb_entities_linked": 0,
                    "message": "没有KB级实体需要链接"
                }
            
            # 2. 按实体类型分组
            entity_groups = self._group_by_type(kb_entities)
            
            total_global_entities = 0
            total_linked = 0
            
            # 3. 对每个类型组进行链接
            for entity_type, type_entities in entity_groups.items():
                global_entities, linked_count = self._link_entity_group(
                    entity_type, type_entities
                )
                total_global_entities += len(global_entities)
                total_linked += linked_count
            
            return {
                "success": True,
                "global_entities_created": total_global_entities,
                "kb_entities_linked": total_linked
            }
            
        except Exception as e:
            logger.error(f"跨库实体链接失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _group_by_type(self, entities: List[KBEntity]) -> Dict[str, List[KBEntity]]:
        """按实体类型分组"""
        groups = defaultdict(list)
        for entity in entities:
            groups[entity.entity_type].append(entity)
        return dict(groups)
    
    def _link_entity_group(
        self, 
        entity_type: str, 
        entities: List[KBEntity]
    ) -> Tuple[List[GlobalEntity], int]:
        """
        链接同一类型的KB实体组
        
        Args:
            entity_type: 实体类型
            entities: KB实体列表
            
        Returns:
            (GlobalEntity列表, 链接的实体数量)
        """
        if len(entities) == 0:
            return [], 0
        
        # 1. 构建候选链接
        candidate_links = self._build_candidate_links(entities)
        
        # 2. 验证链接
        verified_groups = self._verify_links(entities, candidate_links)
        
        # 3. 为每个验证组创建全局实体
        global_entities = []
        linked_count = 0
        
        for group in verified_groups:
            global_entity = self._create_global_entity(entity_type, group)
            global_entities.append(global_entity)
            linked_count += len(group)
        
        return global_entities, linked_count
    
    def _build_candidate_links(
        self, 
        entities: List[KBEntity]
    ) -> Dict[int, List[int]]:
        """
        构建候选链接
        
        基于名称相似度快速筛选候选
        """
        candidates = defaultdict(list)
        n = len(entities)
        
        for i in range(n):
            for j in range(i + 1, n):
                # 名称相似度检查
                name_sim = self._name_similarity(
                    entities[i].canonical_name,
                    entities[j].canonical_name
                )
                
                if name_sim >= self.name_similarity_threshold:
                    candidates[entities[i].id].append(entities[j].id)
                    candidates[entities[j].id].append(entities[i].id)
        
        return dict(candidates)
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度"""
        from difflib import SequenceMatcher
        
        if not name1 or not name2:
            return 0.0
        
        t1 = name1.lower().strip()
        t2 = name2.lower().strip()
        
        if t1 == t2:
            return 1.0
        
        return SequenceMatcher(None, t1, t2).ratio()
    
    def _verify_links(
        self, 
        entities: List[KBEntity], 
        candidate_links: Dict[int, List[int]]
    ) -> List[List[KBEntity]]:
        """
        验证候选链接，形成链接组
        
        使用并查集（Union-Find）算法进行实体聚类
        """
        entity_map = {e.id: e for e in entities}
        
        # 初始化并查集
        parent = {e.id: e.id for e in entities}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # 合并验证通过的链接
        for entity_id, candidates in candidate_links.items():
            entity = entity_map.get(entity_id)
            if not entity:
                continue
            
            for candidate_id in candidates:
                candidate = entity_map.get(candidate_id)
                if not candidate:
                    continue
                
                # 验证规则
                if self._verify_link(entity, candidate):
                    union(entity_id, candidate_id)
        
        # 收集链接组
        groups = defaultdict(list)
        for entity in entities:
            root = find(entity.id)
            groups[root].append(entity)
        
        return list(groups.values())
    
    def _verify_link(self, entity1: KBEntity, entity2: KBEntity) -> bool:
        """
        验证两个实体是否应该链接
        
        验证规则：
        1. 类型必须一致
        2. 名称相似度阈值
        3. 语义相似度阈值
        4. 别名重叠检查
        """
        # 规则1: 类型一致
        if entity1.entity_type != entity2.entity_type:
            return False
        
        # 规则2: 名称相似度
        name_sim = self._name_similarity(
            entity1.canonical_name,
            entity2.canonical_name
        )
        if name_sim < self.name_similarity_threshold:
            return False
        
        # 规则3: 语义相似度
        semantic_sim = self._semantic_similarity(entity1, entity2)
        if semantic_sim < self.semantic_similarity_threshold:
            return False
        
        # 规则4: 别名重叠（可选）
        aliases1 = set(entity1.aliases or [])
        aliases2 = set(entity2.aliases or [])
        if aliases1 and aliases2:
            alias_overlap = len(aliases1 & aliases2) / max(len(aliases1), len(aliases2))
            if alias_overlap > 0.3:  # 30% 别名重叠
                return True
        
        return name_sim >= 0.8 or semantic_sim >= 0.8
    
    def _semantic_similarity(self, entity1: KBEntity, entity2: KBEntity) -> float:
        """
        计算两个KB实体的语义相似度
        
        基于名称和别名的词重叠
        """
        words1 = set(entity1.canonical_name.lower().split())
        words2 = set(entity2.canonical_name.lower().split())
        
        # 添加别名词
        for alias in entity1.aliases or []:
            words1.update(alias.lower().split())
        for alias in entity2.aliases or []:
            words2.update(alias.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _create_global_entity(
        self, 
        entity_type: str, 
        kb_entity_group: List[KBEntity]
    ) -> GlobalEntity:
        """
        从KB实体组创建全局实体
        """
        # 选择全局名称（跨知识库出现次数最多的）
        name_counts = defaultdict(int)
        for entity in kb_entity_group:
            name_counts[entity.canonical_name] += entity.occurrence_count
        
        global_name = max(name_counts.keys(), key=lambda x: name_counts[x])
        
        # 收集所有别名
        all_aliases = set()
        for entity in kb_entity_group:
            all_aliases.add(entity.canonical_name)
            all_aliases.update(entity.aliases or [])
        all_aliases.discard(global_name)
        
        # 统计信息
        kb_ids = set(entity.knowledge_base_id for entity in kb_entity_group)
        doc_count = sum(entity.document_count for entity in kb_entity_group)
        
        # 创建全局实体
        global_entity = GlobalEntity(
            global_name=global_name,
            entity_type=entity_type,
            all_aliases=list(all_aliases),
            kb_count=len(kb_ids),
            document_count=doc_count
        )
        
        self.db.add(global_entity)
        self.db.flush()  # 获取ID
        
        # 更新KB实体的关联
        for entity in kb_entity_group:
            entity.global_entity_id = global_entity.id
            # 同时更新文档实体
            for doc_entity in entity.document_entities:
                doc_entity.global_entity_id = global_entity.id
        
        return global_entity
```

### 3.3 关系聚合服务

```python
# app/services/knowledge/relationship_aggregation_service.py

from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    EntityRelationship, KBRelationship, GlobalRelationship,
    DocumentEntity, KBEntity, GlobalEntity
)

logger = logging.getLogger(__name__)


class RelationshipAggregationService:
    """
    关系聚合服务
    
    用于将文档级关系聚合到知识库级和全局级
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def aggregate_relationships_for_kb(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        聚合指定知识库的关系
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            {
                "success": bool,
                "kb_relationships_created": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取知识库内所有文档关系
            doc_relationships = self.db.query(EntityRelationship).join(
                DocumentEntity, EntityRelationship.source_id == DocumentEntity.id
            ).join(
                KnowledgeDocument, DocumentEntity.document_id == KnowledgeDocument.id
            ).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).all()
            
            if not doc_relationships:
                return {
                    "success": True,
                    "kb_relationships_created": 0,
                    "message": "知识库中没有文档关系"
                }
            
            # 2. 按KB实体对分组
            relationship_groups = self._group_by_kb_entities(doc_relationships)
            
            # 3. 创建KB级关系
            kb_relationships = []
            for (source_kb_id, target_kb_id, rel_type), rels in relationship_groups.items():
                kb_rel = self._create_kb_relationship(
                    knowledge_base_id, source_kb_id, target_kb_id, rel_type, rels
                )
                kb_relationships.append(kb_rel)
            
            return {
                "success": True,
                "kb_relationships_created": len(kb_relationships)
            }
            
        except Exception as e:
            logger.error(f"关系聚合失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _group_by_kb_entities(
        self, 
        relationships: List[EntityRelationship]
    ) -> Dict[Tuple[int, int, str], List[EntityRelationship]]:
        """按KB实体对和关系类型分组"""
        groups = defaultdict(list)
        
        for rel in relationships:
            # 获取源实体和目标实体的KB实体ID
            source_kb_id = rel.source_entity.kb_entity_id if rel.source_entity else None
            target_kb_id = rel.target_entity.kb_entity_id if rel.target_entity else None
            
            if source_kb_id and target_kb_id:
                key = (source_kb_id, target_kb_id, rel.relationship_type)
                groups[key].append(rel)
        
        return dict(groups)
    
    def _create_kb_relationship(
        self,
        knowledge_base_id: int,
        source_kb_id: int,
        target_kb_id: int,
        relationship_type: str,
        doc_relationships: List[EntityRelationship]
    ) -> KBRelationship:
        """创建KB级关系"""
        # 收集来源文档关系ID
        source_rel_ids = [rel.id for rel in doc_relationships]
        
        # 检查是否已存在
        existing = self.db.query(KBRelationship).filter(
            KBRelationship.knowledge_base_id == knowledge_base_id,
            KBRelationship.source_kb_entity_id == source_kb_id,
            KBRelationship.target_kb_entity_id == target_kb_id,
            KBRelationship.relationship_type == relationship_type
        ).first()
        
        if existing:
            # 更新现有关系
            existing.aggregated_count = len(doc_relationships)
            existing.source_relationships = source_rel_ids
            return existing
        
        # 创建新关系
        kb_rel = KBRelationship(
            knowledge_base_id=knowledge_base_id,
            source_kb_entity_id=source_kb_id,
            target_kb_entity_id=target_kb_id,
            relationship_type=relationship_type,
            aggregated_count=len(doc_relationships),
            source_relationships=source_rel_ids
        )
        
        self.db.add(kb_rel)
        return kb_rel
    
    def aggregate_relationships_global(self) -> Dict[str, Any]:
        """
        聚合全局关系
        
        Returns:
            {
                "success": bool,
                "global_relationships_created": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取所有KB关系
            kb_relationships = self.db.query(KBRelationship).all()
            
            if not kb_relationships:
                return {
                    "success": True,
                    "global_relationships_created": 0,
                    "message": "没有KB级关系需要聚合"
                }
            
            # 2. 按全局实体对分组
            relationship_groups = self._group_by_global_entities(kb_relationships)
            
            # 3. 创建全局关系
            global_relationships = []
            for (source_global_id, target_global_id, rel_type), rels in relationship_groups.items():
                global_rel = self._create_global_relationship(
                    source_global_id, target_global_id, rel_type, rels
                )
                global_relationships.append(global_rel)
            
            return {
                "success": True,
                "global_relationships_created": len(global_relationships)
            }
            
        except Exception as e:
            logger.error(f"全局关系聚合失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _group_by_global_entities(
        self, 
        relationships: List[KBRelationship]
    ) -> Dict[Tuple[int, int, str], List[KBRelationship]]:
        """按全局实体对和关系类型分组"""
        groups = defaultdict(list)
        
        for rel in relationships:
            # 获取源实体和目标实体的全局实体ID
            source_global_id = rel.source_entity.global_entity_id if rel.source_entity else None
            target_global_id = rel.target_entity.global_entity_id if rel.target_entity else None
            
            if source_global_id and target_global_id:
                key = (source_global_id, target_global_id, rel.relationship_type)
                groups[key].append(rel)
        
        return dict(groups)
    
    def _create_global_relationship(
        self,
        source_global_id: int,
        target_global_id: int,
        relationship_type: str,
        kb_relationships: List[KBRelationship]
    ) -> GlobalRelationship:
        """创建全局关系"""
        # 收集来源知识库ID
        source_kb_ids = list(set(rel.knowledge_base_id for rel in kb_relationships))
        total_count = sum(rel.aggregated_count for rel in kb_relationships)
        
        # 检查是否已存在
        existing = self.db.query(GlobalRelationship).filter(
            GlobalRelationship.source_global_entity_id == source_global_id,
            GlobalRelationship.target_global_entity_id == target_global_id,
            GlobalRelationship.relationship_type == relationship_type
        ).first()
        
        if existing:
            # 更新现有关系
            existing.aggregated_count = total_count
            existing.source_kbs = source_kb_ids
            return existing
        
        # 创建新关系
        global_rel = GlobalRelationship(
            source_global_entity_id=source_global_id,
            target_global_entity_id=target_global_id,
            relationship_type=relationship_type,
            aggregated_count=total_count,
            source_kbs=source_kb_ids
        )
        
        self.db.add(global_rel)
        return global_rel
```

---

## 4. 分层构建流程

### 4.1 构建调度服务

```python
# app/services/knowledge/hierarchical_build_service.py

from typing import Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeDocument, KnowledgeBase
)
from app.services.knowledge.entity_alignment_service import EntityAlignmentService
from app.services.knowledge.cross_kb_linking_service import CrossKBEntityLinkingService
from app.services.knowledge.relationship_aggregation_service import RelationshipAggregationService

logger = logging.getLogger(__name__)


class BuildLevel(Enum):
    """构建层级"""
    DOCUMENT = "document"
    KNOWLEDGE_BASE = "knowledge_base"
    GLOBAL = "global"


class HierarchicalBuildService:
    """
    分层构建调度服务
    
    协调三层知识图谱的构建流程
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.alignment_service = EntityAlignmentService(db)
        self.linking_service = CrossKBEntityLinkingService(db)
        self.relationship_service = RelationshipAggregationService(db)
    
    def build_document_level(self, document_id: int) -> Dict[str, Any]:
        """
        构建文档级图谱
        
        在文档上传/更新时触发，实时构建
        """
        try:
            from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
            
            service = KnowledgeGraphService()
            document = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            
            if not document:
                return {"success": False, "error": "文档不存在"}
            
            # 使用现有服务提取实体和关系
            result = service.extract_and_store_entities(self.db, document)
            
            return result
            
        except Exception as e:
            logger.error(f"文档级构建失败: {e}")
            return {"success": False, "error": str(e)}
    
    def build_knowledge_base_level(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        构建知识库级图谱
        
        包括：
        1. 实体对齐
        2. 关系聚合
        """
        try:
            logger.info(f"开始构建知识库 {knowledge_base_id} 的图谱")
            
            # 1. 实体对齐
            alignment_result = self.alignment_service.align_entities_for_kb(knowledge_base_id)
            if not alignment_result["success"]:
                return alignment_result
            
            # 2. 关系聚合
            relationship_result = self.relationship_service.aggregate_relationships_for_kb(knowledge_base_id)
            if not relationship_result["success"]:
                return relationship_result
            
            self.db.commit()
            
            return {
                "success": True,
                "level": BuildLevel.KNOWLEDGE_BASE.value,
                "knowledge_base_id": knowledge_base_id,
                "kb_entities_created": alignment_result.get("kb_entities_created", 0),
                "entities_aligned": alignment_result.get("entities_aligned", 0),
                "kb_relationships_created": relationship_result.get("kb_relationships_created", 0)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"知识库级构建失败: {e}")
            return {"success": False, "error": str(e)}
    
    def build_global_level(self) -> Dict[str, Any]:
        """
        构建全局级图谱
        
        包括：
        1. 跨库实体链接
        2. 全局关系聚合
        """
        try:
            logger.info("开始构建全局级图谱")
            
            # 1. 跨库实体链接
            linking_result = self.linking_service.link_entities_global()
            if not linking_result["success"]:
                return linking_result
            
            # 2. 全局关系聚合
            relationship_result = self.relationship_service.aggregate_relationships_global()
            if not relationship_result["success"]:
                return relationship_result
            
            self.db.commit()
            
            return {
                "success": True,
                "level": BuildLevel.GLOBAL.value,
                "global_entities_created": linking_result.get("global_entities_created", 0),
                "kb_entities_linked": linking_result.get("kb_entities_linked", 0),
                "global_relationships_created": relationship_result.get("global_relationships_created", 0)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"全局级构建失败: {e}")
            return {"success": False, "error": str(e)}
    
    def build_all(self, knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
        """
        构建所有层级
        
        Args:
            knowledge_base_id: 如果指定，只构建该知识库；否则构建所有
        """
        results = {
            "success": True,
            "document_level": [],
            "knowledge_base_level": [],
            "global_level": None
        }
        
        try:
            if knowledge_base_id:
                # 构建指定知识库
                kb_result = self.build_knowledge_base_level(knowledge_base_id)
                results["knowledge_base_level"].append(kb_result)
            else:
                # 构建所有知识库
                knowledge_bases = self.db.query(KnowledgeBase).all()
                for kb in knowledge_bases:
                    kb_result = self.build_knowledge_base_level(kb.id)
                    results["knowledge_base_level"].append(kb_result)
            
            # 构建全局级
            global_result = self.build_global_level()
            results["global_level"] = global_result
            
            return results
            
        except Exception as e:
            logger.error(f"全量构建失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_build_status(self, knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
        """获取构建状态统计"""
        from sqlalchemy import func
        
        status = {
            "document_level": {},
            "knowledge_base_level": {},
            "global_level": {}
        }
        
        # 文档级统计
        doc_query = self.db.query(func.count(DocumentEntity.id))
        if knowledge_base_id:
            doc_query = doc_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        status["document_level"]["entity_count"] = doc_query.scalar() or 0
        
        # 知识库级统计
        kb_query = self.db.query(func.count(KBEntity.id))
        if knowledge_base_id:
            kb_query = kb_query.filter(KBEntity.knowledge_base_id == knowledge_base_id)
        status["knowledge_base_level"]["entity_count"] = kb_query.scalar() or 0
        
        # 全局级统计
        status["global_level"]["entity_count"] = self.db.query(func.count(GlobalEntity.id)).scalar() or 0
        
        return status
```

---

## 5. API接口实现

### 5.1 分层查询API

```python
# app/modules/knowledge/api/hierarchical_graph_api.py

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeDocument, KnowledgeBase,
    DocumentEntity, EntityRelationship,
    KBEntity, KBRelationship,
    GlobalEntity, GlobalRelationship
)
from app.services.knowledge.hierarchical_build_service import HierarchicalBuildService

router = APIRouter()


# ============ 请求/响应模型 ============

class GraphQueryParams(BaseModel):
    include_documents: bool = False
    include_kbs: bool = False
    entity_types: Optional[List[str]] = None
    max_nodes: int = 1000


class HierarchyNavigationResponse(BaseModel):
    level: str
    entity: Dict[str, Any]
    parent: Optional[Dict[str, Any]] = None
    children: List[Dict[str, Any]] = []


class EntitySearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_count: int


# ============ 文档级图谱API ============

@router.get("/documents/{document_id}/graph")
async def get_document_graph(
    document_id: int,
    params: GraphQueryParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    获取文档级知识图谱
    
    返回文档内的所有实体和关系
    """
    try:
        # 验证文档存在
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 查询实体
        entities_query = db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        )
        
        if params.entity_types:
            entities_query = entities_query.filter(
                DocumentEntity.entity_type.in_(params.entity_types)
            )
        
        entities = entities_query.limit(params.max_nodes).all()
        
        # 查询关系
        entity_ids = [e.id for e in entities]
        relationships = db.query(EntityRelationship).filter(
            EntityRelationship.document_id == document_id,
            EntityRelationship.source_id.in_(entity_ids),
            EntityRelationship.target_id.in_(entity_ids)
        ).all()
        
        # 构建响应
        nodes = []
        for entity in entities:
            nodes.append({
                "id": f"doc_ent_{entity.id}",
                "entity_id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "level": "document",
                "confidence": entity.confidence,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos
            })
        
        edges = []
        for rel in relationships:
            edges.append({
                "id": f"doc_rel_{rel.id}",
                "source": f"doc_ent_{rel.source_id}",
                "target": f"doc_ent_{rel.target_id}",
                "type": rel.relationship_type,
                "level": "document",
                "confidence": rel.confidence
            })
        
        return {
            "level": "document",
            "document_id": document_id,
            "document_title": document.title,
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "entity_types": list(set(e.entity_type for e in entities))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档图谱失败: {str(e)}")


# ============ 知识库级图谱API ============

@router.get("/knowledge-bases/{kb_id}/graph")
async def get_knowledge_base_graph(
    kb_id: int,
    include_documents: bool = Query(False, description="是否包含下层文档节点"),
    entity_types: Optional[List[str]] = Query(None, description="筛选实体类型"),
    max_nodes: int = Query(1000, description="最大节点数"),
    db: Session = Depends(get_db)
):
    """
    获取知识库级知识图谱
    
    返回知识库内的KB级实体和关系
    可选包含下层文档级实体
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        nodes = []
        edges = []
        
        # 查询KB级实体
        kb_entities_query = db.query(KBEntity).filter(
            KBEntity.knowledge_base_id == kb_id
        )
        
        if entity_types:
            kb_entities_query = kb_entities_query.filter(
                KBEntity.entity_type.in_(entity_types)
            )
        
        kb_entities = kb_entities_query.limit(max_nodes).all()
        
        # 添加KB级节点
        for entity in kb_entities:
            nodes.append({
                "id": f"kb_ent_{entity.id}",
                "entity_id": entity.id,
                "text": entity.canonical_name,
                "type": entity.entity_type,
                "level": "knowledge_base",
                "aliases": entity.aliases,
                "document_count": entity.document_count,
                "occurrence_count": entity.occurrence_count
            })
        
        # 查询KB级关系
        kb_entity_ids = [e.id for e in kb_entities]
        kb_relationships = db.query(KBRelationship).filter(
            KBRelationship.knowledge_base_id == kb_id,
            KBRelationship.source_kb_entity_id.in_(kb_entity_ids),
            KBRelationship.target_kb_entity_id.in_(kb_entity_ids)
        ).all()
        
        for rel in kb_relationships:
            edges.append({
                "id": f"kb_rel_{rel.id}",
                "source": f"kb_ent_{rel.source_kb_entity_id}",
                "target": f"kb_ent_{rel.target_kb_entity_id}",
                "type": rel.relationship_type,
                "level": "knowledge_base",
                "aggregated_count": rel.aggregated_count
            })
        
        # 如果需要，包含文档级实体
        if include_documents:
            for kb_entity in kb_entities:
                doc_entities = db.query(DocumentEntity).filter(
                    DocumentEntity.kb_entity_id == kb_entity.id
                ).all()
                
                for doc_entity in doc_entities:
                    nodes.append({
                        "id": f"doc_ent_{doc_entity.id}",
                        "entity_id": doc_entity.id,
                        "text": doc_entity.entity_text,
                        "type": doc_entity.entity_type,
                        "level": "document",
                        "confidence": doc_entity.confidence,
                        "document_id": doc_entity.document_id
                    })
                    
                    # 添加层级边
                    edges.append({
                        "id": f"hierarchy_{kb_entity.id}_{doc_entity.id}",
                        "source": f"kb_ent_{kb_entity.id}",
                        "target": f"doc_ent_{doc_entity.id}",
                        "type": "belongs_to",
                        "level": "hierarchy"
                    })
        
        return {
            "level": "knowledge_base",
            "knowledge_base_id": kb_id,
            "knowledge_base_name": kb.name,
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "kb_entity_count": len(kb_entities),
                "entity_types": list(set(e.entity_type for e in kb_entities))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库图谱失败: {str(e)}")


# ============ 全局级图谱API ============

@router.get("/graph/global")
async def get_global_graph(
    include_kbs: bool = Query(False, description="是否包含知识库节点"),
    include_documents: bool = Query(False, description="是否包含文档节点"),
    entity_types: Optional[List[str]] = Query(None, description="筛选实体类型"),
    max_nodes: int = Query(500, description="最大节点数"),
    db: Session = Depends(get_db)
):
    """
    获取全局级知识图谱
    
    返回跨知识库的全局实体和关系
    可选包含下层知识库和文档级实体
    """
    try:
        nodes = []
        edges = []
        
        # 查询全局实体
        global_entities_query = db.query(GlobalEntity)
        
        if entity_types:
            global_entities_query = global_entities_query.filter(
                GlobalEntity.entity_type.in_(entity_types)
            )
        
        global_entities = global_entities_query.limit(max_nodes).all()
        
        # 添加全局节点
        for entity in global_entities:
            nodes.append({
                "id": f"global_ent_{entity.id}",
                "entity_id": entity.id,
                "text": entity.global_name,
                "type": entity.entity_type,
                "level": "global",
                "aliases": entity.all_aliases,
                "kb_count": entity.kb_count,
                "document_count": entity.document_count
            })
        
        # 查询全局关系
        global_entity_ids = [e.id for e in global_entities]
        global_relationships = db.query(GlobalRelationship).filter(
            GlobalRelationship.source_global_entity_id.in_(global_entity_ids),
            GlobalRelationship.target_global_entity_id.in_(global_entity_ids)
        ).all()
        
        for rel in global_relationships:
            edges.append({
                "id": f"global_rel_{rel.id}",
                "source": f"global_ent_{rel.source_global_entity_id}",
                "target": f"global_ent_{rel.target_global_entity_id}",
                "type": rel.relationship_type,
                "level": "global",
                "aggregated_count": rel.aggregated_count,
                "source_kbs": rel.source_kbs
            })
        
        # 如果需要，包含下层实体
        if include_kbs or include_documents:
            for global_entity in global_entities:
                kb_entities = db.query(KBEntity).filter(
                    KBEntity.global_entity_id == global_entity.id
                ).all()
                
                for kb_entity in kb_entities:
                    if include_kbs:
                        nodes.append({
                            "id": f"kb_ent_{kb_entity.id}",
                            "entity_id": kb_entity.id,
                            "text": kb_entity.canonical_name,
                            "type": kb_entity.entity_type,
                            "level": "knowledge_base",
                            "knowledge_base_id": kb_entity.knowledge_base_id
                        })
                        
                        edges.append({
                            "id": f"hierarchy_global_kb_{global_entity.id}_{kb_entity.id}",
                            "source": f"global_ent_{global_entity.id}",
                            "target": f"kb_ent_{kb_entity.id}",
                            "type": "belongs_to",
                            "level": "hierarchy"
                        })
                    
                    if include_documents:
                        doc_entities = db.query(DocumentEntity).filter(
                            DocumentEntity.kb_entity_id == kb_entity.id
                        ).all()
                        
                        for doc_entity in doc_entities:
                            nodes.append({
                                "id": f"doc_ent_{doc_entity.id}",
                                "entity_id": doc_entity.id,
                                "text": doc_entity.entity_text,
                                "type": doc_entity.entity_type,
                                "level": "document",
                                "document_id": doc_entity.document_id
                            })
                            
                            parent_id = f"kb_ent_{kb_entity.id}" if include_kbs else f"global_ent_{global_entity.id}"
                            edges.append({
                                "id": f"hierarchy_{parent_id}_{doc_entity.id}",
                                "source": parent_id,
                                "target": f"doc_ent_{doc_entity.id}",
                                "type": "belongs_to",
                                "level": "hierarchy"
                            })
        
        return {
            "level": "global",
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "global_entity_count": len(global_entities),
                "entity_types": list(set(e.entity_type for e in global_entities))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取全局图谱失败: {str(e)}")


# ============ 跨层导航API ============

@router.get("/entities/{entity_id}/hierarchy")
async def get_entity_hierarchy(
    entity_id: int,
    level: str = Query("document", description="实体层级: document|kb|global"),
    db: Session = Depends(get_db)
):
    """
    获取实体的层级结构
    
    向上导航：文档实体 -> KB实体 -> 全局实体
    """
    try:
        result = {
            "query": {"entity_id": entity_id, "level": level},
            "hierarchy": []
        }
        
        if level == "document":
            # 从文档实体开始
            doc_entity = db.query(DocumentEntity).filter(
                DocumentEntity.id == entity_id
            ).first()
            
            if not doc_entity:
                raise HTTPException(status_code=404, detail="文档实体不存在")
            
            result["hierarchy"].append({
                "level": "document",
                "entity": {
                    "id": doc_entity.id,
                    "text": doc_entity.entity_text,
                    "type": doc_entity.entity_type,
                    "document_id": doc_entity.document_id
                }
            })
            
            # 向上到KB实体
            if doc_entity.kb_entity_id:
                kb_entity = db.query(KBEntity).filter(
                    KBEntity.id == doc_entity.kb_entity_id
                ).first()
                
                if kb_entity:
                    result["hierarchy"].append({
                        "level": "knowledge_base",
                        "entity": {
                            "id": kb_entity.id,
                            "text": kb_entity.canonical_name,
                            "type": kb_entity.entity_type,
                            "knowledge_base_id": kb_entity.knowledge_base_id
                        }
                    })
                    
                    # 向上到全局实体
                    if kb_entity.global_entity_id:
                        global_entity = db.query(GlobalEntity).filter(
                            GlobalEntity.id == kb_entity.global_entity_id
                        ).first()
                        
                        if global_entity:
                            result["hierarchy"].append({
                                "level": "global",
                                "entity": {
                                    "id": global_entity.id,
                                    "text": global_entity.global_name,
                                    "type": global_entity.entity_type,
                                    "kb_count": global_entity.kb_count,
                                    "document_count": global_entity.document_count
                                }
                            })
        
        elif level == "kb":
            # 从KB实体开始
            kb_entity = db.query(KBEntity).filter(KBEntity.id == entity_id).first()
            
            if not kb_entity:
                raise HTTPException(status_code=404, detail="KB实体不存在")
            
            result["hierarchy"].append({
                "level": "knowledge_base",
                "entity": {
                    "id": kb_entity.id,
                    "text": kb_entity.canonical_name,
                    "type": kb_entity.entity_type,
                    "knowledge_base_id": kb_entity.knowledge_base_id
                }
            })
            
            # 向上到全局实体
            if kb_entity.global_entity_id:
                global_entity = db.query(GlobalEntity).filter(
                    GlobalEntity.id == kb_entity.global_entity_id
                ).first()
                
                if global_entity:
                    result["hierarchy"].append({
                        "level": "global",
                        "entity": {
                            "id": global_entity.id,
                            "text": global_entity.global_name,
                            "type": global_entity.entity_type,
                            "kb_count": global_entity.kb_count,
                            "document_count": global_entity.document_count
                        }
                    })
            
            # 向下到文档实体
            doc_entities = db.query(DocumentEntity).filter(
                DocumentEntity.kb_entity_id == entity_id
            ).all()
            
            result["children"] = [
                {
                    "level": "document",
                    "entity": {
                        "id": e.id,
                        "text": e.entity_text,
                        "type": e.entity_type,
                        "document_id": e.document_id
                    }
                }
                for e in doc_entities
            ]
        
        elif level == "global":
            # 从全局实体开始
            global_entity = db.query(GlobalEntity).filter(
                GlobalEntity.id == entity_id
            ).first()
            
            if not global_entity:
                raise HTTPException(status_code=404, detail="全局实体不存在")
            
            result["hierarchy"].append({
                "level": "global",
                "entity": {
                    "id": global_entity.id,
                    "text": global_entity.global_name,
                    "type": global_entity.entity_type,
                    "kb_count": global_entity.kb_count,
                    "document_count": global_entity.document_count
                }
            })
            
            # 向下到KB实体
            kb_entities = db.query(KBEntity).filter(
                KBEntity.global_entity_id == entity_id
            ).all()
            
            result["children"] = [
                {
                    "level": "knowledge_base",
                    "entity": {
                        "id": e.id,
                        "text": e.canonical_name,
                        "type": e.entity_type,
                        "knowledge_base_id": e.knowledge_base_id
                    }
                }
                for e in kb_entities
            ]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取层级结构失败: {str(e)}")


# ============ 实体搜索API ============

@router.get("/entities/search")
async def search_entities(
    q: str = Query(..., description="搜索关键词"),
    level: str = Query("all", description="搜索层级: document|kb|global|all"),
    kb_id: Optional[int] = Query(None, description="限制知识库"),
    limit: int = Query(20, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    跨层实体搜索
    
    在指定层级或所有层级搜索实体
    """
    try:
        results = []
        
        # 搜索文档级实体
        if level in ["all", "document"]:
            doc_query = db.query(DocumentEntity).filter(
                DocumentEntity.entity_text.ilike(f"%{q}%")
            )
            
            if kb_id:
                doc_query = doc_query.join(KnowledgeDocument).filter(
                    KnowledgeDocument.knowledge_base_id == kb_id
                )
            
            doc_entities = doc_query.limit(limit).all()
            
            for entity in doc_entities:
                results.append({
                    "level": "document",
                    "entity": {
                        "id": entity.id,
                        "text": entity.entity_text,
                        "type": entity.entity_type,
                        "document_id": entity.document_id,
                        "confidence": entity.confidence
                    }
                })
        
        # 搜索知识库级实体
        if level in ["all", "kb"]:
            kb_query = db.query(KBEntity).filter(
                KBEntity.canonical_name.ilike(f"%{q}%")
            )
            
            if kb_id:
                kb_query = kb_query.filter(KBEntity.knowledge_base_id == kb_id)
            
            kb_entities = kb_query.limit(limit).all()
            
            for entity in kb_entities:
                results.append({
                    "level": "knowledge_base",
                    "entity": {
                        "id": entity.id,
                        "text": entity.canonical_name,
                        "type": entity.entity_type,
                        "knowledge_base_id": entity.knowledge_base_id,
                        "aliases": entity.aliases
                    }
                })
        
        # 搜索全局级实体
        if level in ["all", "global"]:
            global_entities = db.query(GlobalEntity).filter(
                GlobalEntity.global_name.ilike(f"%{q}%")
            ).limit(limit).all()
            
            for entity in global_entities:
                results.append({
                    "level": "global",
                    "entity": {
                        "id": entity.id,
                        "text": entity.global_name,
                        "type": entity.entity_type,
                        "kb_count": entity.kb_count,
                        "aliases": entity.all_aliases
                    }
                })
        
        return {
            "query": q,
            "level": level,
            "results": results[:limit],
            "total_count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


# ============ 构建触发API ============

@router.post("/build/knowledge-base/{kb_id}")
async def build_knowledge_base_graph(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """
    触发知识库级图谱构建
    
    异步构建指定知识库的图谱
    """
    try:
        build_service = HierarchicalBuildService(db)
        result = build_service.build_knowledge_base_level(kb_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "构建失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.post("/build/global")
async def build_global_graph(
    db: Session = Depends(get_db)
):
    """
    触发全局级图谱构建
    
    异步构建全局图谱
    """
    try:
        build_service = HierarchicalBuildService(db)
        result = build_service.build_global_level()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "构建失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.post("/build/all")
async def build_all_graphs(
    kb_id: Optional[int] = Query(None, description="指定知识库ID，不指定则构建所有"),
    db: Session = Depends(get_db)
):
    """
    触发全量构建
    
    构建所有层级的图谱
    """
    try:
        build_service = HierarchicalBuildService(db)
        result = build_service.build_all(kb_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "构建失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.get("/build/status")
async def get_build_status(
    kb_id: Optional[int] = Query(None, description="指定知识库ID"),
    db: Session = Depends(get_db)
):
    """
    获取构建状态统计
    """
    try:
        build_service = HierarchicalBuildService(db)
        status = build_service.get_build_status(kb_id)
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
```

---

## 6. 实施计划

### 6.1 实施阶段

#### Phase 1: 基础架构 (第1-2周)

**任务清单：**
1. **数据库表结构实现**
   - [ ] 创建全局实体表 (global_entities)
   - [ ] 创建知识库级实体表 (kb_entities)
   - [ ] 创建知识库级关系表 (kb_relationships)
   - [ ] 创建全局级关系表 (global_relationships)
   - [ ] 修改 document_entities 表，添加层级关联字段
   - [ ] 编写 Alembic 迁移脚本

2. **实体分层模型实现**
   - [ ] 在 knowledge_document.py 中添加 KBEntity 模型
   - [ ] 在 knowledge_document.py 中添加 GlobalEntity 模型
   - [ ] 在 knowledge_document.py 中添加 KBRelationship 模型
   - [ ] 在 knowledge_document.py 中添加 GlobalRelationship 模型
   - [ ] 修改 DocumentEntity 模型，添加层级关联
   - [ ] 修改 KnowledgeBase 模型，添加关系

3. **基础服务实现**
   - [ ] 创建 entity_alignment_service.py
   - [ ] 创建 cross_kb_linking_service.py
   - [ ] 创建 relationship_aggregation_service.py
   - [ ] 创建 hierarchical_build_service.py

#### Phase 2: 核心算法 (第3-4周)

**任务清单：**
1. **实体对齐算法**
   - [ ] 实现实体分组功能
   - [ ] 实现相似度矩阵计算
   - [ ] 实现层次聚类算法
   - [ ] 实现 KB 实体创建
   - [ ] 单元测试

2. **跨库实体链接算法**
   - [ ] 实现候选链接构建
   - [ ] 实现并查集链接验证
   - [ ] 实现全局实体创建
   - [ ] 单元测试

3. **关系聚合算法**
   - [ ] 实现 KB 级关系聚合
   - [ ] 实现全局级关系聚合
   - [ ] 单元测试

#### Phase 3: API接口 (第5周)

**任务清单：**
1. **分层查询API**
   - [ ] 实现文档级图谱查询
   - [ ] 实现知识库级图谱查询
   - [ ] 实现全局级图谱查询

2. **跨层导航API**
   - [ ] 实现实体层级查询
   - [ ] 实现实体搜索

3. **构建触发API**
   - [ ] 实现知识库级构建触发
   - [ ] 实现全局级构建触发
   - [ ] 实现全量构建触发
   - [ ] 实现构建状态查询

#### Phase 4: 集成与测试 (第6周)

**任务清单：**
1. **集成测试**
   - [ ] 端到端构建流程测试
   - [ ] API 接口测试
   - [ ] 性能测试

2. **前端适配**
   - [ ] 更新前端图谱可视化组件
   - [ ] 实现层级切换功能
   - [ ] 实现下钻/上卷功能

3. **文档编写**
   - [ ] API 文档
   - [ ] 使用手册
   - [ ] 部署文档

### 6.2 文件清单

```
backend/
├── alembic/versions/
│   └── xxx_add_hierarchical_knowledge_graph.py    # 数据库迁移脚本
├── app/
│   ├── modules/knowledge/
│   │   ├── models/
│   │   │   └── knowledge_document.py              # 扩展模型（新增4个模型）
│   │   └── api/
│   │       └── hierarchical_graph_api.py          # 分层图谱API
│   └── services/knowledge/
│       ├── entity_alignment_service.py            # 实体对齐服务
│       ├── cross_kb_linking_service.py            # 跨库链接服务
│       ├── relationship_aggregation_service.py    # 关系聚合服务
│       └── hierarchical_build_service.py          # 构建调度服务
└── HIERARCHICAL_KNOWLEDGE_GRAPH_IMPLEMENTATION.md  # 本实施方案
```

### 6.3 关键配置

```python
# app/core/config.py 中添加

class Settings:
    # ... 现有配置 ...
    
    # 分层知识图谱配置
    ENTITY_ALIGNMENT_THRESHOLD = 0.75        # 实体对齐相似度阈值
    CROSS_KB_LINKING_THRESHOLD = 0.70        # 跨库链接相似度阈值
    NAME_SIMILARITY_THRESHOLD = 0.60         # 名称相似度阈值
    MAX_HIERARCHY_NODES = 1000               # 最大返回节点数
    KB_BUILD_BATCH_SIZE = 100                # KB构建批处理大小
```

### 6.4 定时任务配置

```python
# app/tasks/hierarchical_graph_tasks.py

from celery import Celery
from app.core.config import settings

# 配置 Celery
celery_app = Celery(
    "hierarchical_graph",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)


@celery_app.task
def build_knowledge_base_graph_task(knowledge_base_id: int):
    """异步构建知识库级图谱"""
    from app.core.database import SessionLocal
    from app.services.knowledge.hierarchical_build_service import HierarchicalBuildService
    
    db = SessionLocal()
    try:
        service = HierarchicalBuildService(db)
        result = service.build_knowledge_base_level(knowledge_base_id)
        return result
    finally:
        db.close()


@celery_app.task
def build_global_graph_task():
    """异步构建全局级图谱"""
    from app.core.database import SessionLocal
    from app.services.knowledge.hierarchical_build_service import HierarchicalBuildService
    
    db = SessionLocal()
    try:
        service = HierarchicalBuildService(db)
        result = service.build_global_level()
        return result
    finally:
        db.close()


# 定时任务配置
celery_app.conf.beat_schedule = {
    "build-global-graph-daily": {
        "task": "app.tasks.hierarchical_graph_tasks.build_global_graph_task",
        "schedule": 86400.0,  # 每天执行一次
    },
}
```

---

## 7. 测试策略

### 7.1 单元测试

```python
# tests/test_entity_alignment.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.modules.knowledge.models.knowledge_document import Base, DocumentEntity, KBEntity
from app.services.knowledge.entity_alignment_service import EntityAlignmentService


class TestEntityAlignment:
    """实体对齐服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.service = EntityAlignmentService(self.db)
    
    def test_text_similarity_exact_match(self):
        """测试完全匹配"""
        sim = self.service._text_similarity("人工智能", "人工智能")
        assert sim == 1.0
    
    def test_text_similarity_partial_match(self):
        """测试部分匹配"""
        sim = self.service._text_similarity("AI", "人工智能")
        assert sim > 0.5
    
    def test_group_by_type(self):
        """测试按类型分组"""
        entities = [
            DocumentEntity(entity_text="张三", entity_type="PERSON"),
            DocumentEntity(entity_text="李四", entity_type="PERSON"),
            DocumentEntity(entity_text="北京", entity_type="LOC"),
        ]
        
        groups = self.service._group_by_type(entities)
        
        assert len(groups) == 2
        assert len(groups["PERSON"]) == 2
        assert len(groups["LOC"]) == 1
```

### 7.2 集成测试

```python
# tests/test_hierarchical_graph_integration.py

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestHierarchicalGraphAPI:
    """分层图谱API集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
    
    def test_get_document_graph(self):
        """测试获取文档级图谱"""
        response = self.client.get("/api/knowledge/documents/1/graph")
        assert response.status_code == 200
        
        data = response.json()
        assert data["level"] == "document"
        assert "nodes" in data
        assert "edges" in data
    
    def test_get_knowledge_base_graph(self):
        """测试获取知识库级图谱"""
        response = self.client.get("/api/knowledge/knowledge-bases/1/graph")
        assert response.status_code == 200
        
        data = response.json()
        assert data["level"] == "knowledge_base"
        assert "nodes" in data
        assert "edges" in data
    
    def test_entity_hierarchy_navigation(self):
        """测试实体层级导航"""
        response = self.client.get("/api/knowledge/entities/1/hierarchy?level=document")
        assert response.status_code == 200
        
        data = response.json()
        assert "hierarchy" in data
```

---

## 8. 风险评估与缓解

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 实体对齐准确率低 | 中 | 中 | 多维度相似度计算 + 可调整阈值 |
| 大规模数据性能问题 | 高 | 中 | 批处理 + 异步构建 + 数据库索引优化 |
| 存储空间膨胀 | 中 | 高 | 定期清理 + 数据压缩 + 分层存储策略 |
| 跨库实体歧义 | 中 | 中 | 置信度阈值 + 歧义消解策略 |
| 并发构建冲突 | 高 | 低 | 分布式锁 + 队列机制 |

---

## 9. 后续扩展

1. **时序知识图谱**: 支持实体和关系的时间维度追踪
2. **多语言支持**: 跨语言实体链接和对齐
3. **主动学习**: 基于用户反馈优化对齐质量
4. **图神经网络**: 利用 GNN 进行关系推理和预测
5. **知识推理**: 基于图谱进行知识发现和推理

---

## 10. 总结

本实施方案详细描述了分层知识图谱的完整实现方案，包括：

1. **数据库设计**: 新增4个表，扩展2个现有表
2. **核心算法**: 实体对齐、跨库链接、关系聚合
3. **构建流程**: 三层级联构建，支持异步处理
4. **API接口**: 分层查询、跨层导航、搜索、构建触发
5. **实施计划**: 6周分阶段实施，包含详细任务清单

通过本方案的实施，将实现从文档级到全局级的三层知识图谱体系，支持层次清晰、关联完整、查询灵活的知识管理需求。
