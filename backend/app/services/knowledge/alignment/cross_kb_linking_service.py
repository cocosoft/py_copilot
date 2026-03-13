"""跨知识库实体链接服务模块"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
import logging
import numpy as np

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    KBEntity, GlobalEntity
)
from app.services.knowledge.alignment.bert_entity_aligner import (
    BERTEntityAligner, get_bert_aligner
)
from app.services.knowledge.vectorization.faiss_index_service import (
    FAISSIndexService, IndexConfig, get_multi_index_service
)

logger = logging.getLogger(__name__)


class CrossKBEntityLinkingService:
    """
    跨知识库实体链接服务

    用于将不同知识库的KB级实体链接到全局级实体
    核心功能：实体链接、全局消歧、跨库关系发现

    增强功能：
    - 集成BERT语义理解
    - 使用FAISS索引加速相似度搜索
    - 支持增量链接
    """

    def __init__(self, db: Session, use_bert: bool = True, use_faiss: bool = True):
        self.db = db
        self.name_similarity_threshold = 0.60
        self.semantic_similarity_threshold = 0.70

        # 初始化BERT对齐器
        self.bert_aligner = None
        if use_bert:
            try:
                self.bert_aligner = get_bert_aligner()
                logger.info("跨库链接服务：BERT对齐器初始化成功")
            except Exception as e:
                logger.warning(f"跨库链接服务：BERT对齐器初始化失败: {e}")

        # 初始化FAISS索引
        self.faiss_index = None
        if use_faiss:
            try:
                multi_index_service = get_multi_index_service()
                config = IndexConfig(
                    dimension=768,
                    index_type="IVF_FLAT",
                    nlist=100,
                    nprobe=10
                )
                self.faiss_index = multi_index_service.get_index("cross_kb_entities", config)
                logger.info("跨库链接服务：FAISS索引初始化成功")
            except Exception as e:
                logger.warning(f"跨库链接服务：FAISS索引初始化失败: {e}")

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

    def link_entities_global_enhanced(self) -> Dict[str, Any]:
        """
        增强版跨知识库实体链接

        使用BERT语义理解和FAISS索引加速
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

            logger.info(f"开始增强版跨库链接，共 {len(kb_entities)} 个KB实体")

            # 2. 使用BERT编码实体
            entity_embeddings = self._encode_kb_entities(kb_entities)

            # 3. 使用FAISS索引加速相似度搜索
            if self.faiss_index and entity_embeddings:
                self._build_faiss_index(kb_entities, entity_embeddings)

            # 4. 按类型分组进行链接
            entity_groups = self._group_by_type(kb_entities)

            total_global_entities = 0
            total_linked = 0

            for entity_type, type_entities in entity_groups.items():
                global_entities, linked_count = self._link_entity_group_enhanced(
                    entity_type, type_entities, entity_embeddings
                )
                total_global_entities += len(global_entities)
                total_linked += linked_count

            return {
                "success": True,
                "global_entities_created": total_global_entities,
                "kb_entities_linked": total_linked,
                "method": "enhanced_with_bert_faiss"
            }

        except Exception as e:
            logger.error(f"增强版跨库实体链接失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _encode_kb_entities(self, entities: List[KBEntity]) -> Dict[int, np.ndarray]:
        """
        使用BERT编码KB实体

        Returns:
            实体ID到嵌入向量的映射
        """
        if not self.bert_aligner:
            return {}

        try:
            # 准备实体数据
            entity_dicts = []
            for entity in entities:
                # 组合实体名称和别名作为上下文
                context = " ".join(entity.aliases or [])
                entity_dicts.append({
                    'id': entity.id,
                    'text': entity.canonical_name,
                    'type': entity.entity_type,
                    'context': context
                })

            # 编码实体
            embeddings = self.bert_aligner.encode_entities(entity_dicts)

            # 构建映射
            embedding_map = {}
            for emb in embeddings:
                embedding_map[emb.entity_id] = emb.embedding

            logger.info(f"成功编码 {len(embedding_map)} 个KB实体")
            return embedding_map

        except Exception as e:
            logger.error(f"编码KB实体失败: {e}")
            return {}

    def _build_faiss_index(self, entities: List[KBEntity],
                          embeddings: Dict[int, np.ndarray]):
        """构建FAISS索引"""
        if not self.faiss_index:
            return

        try:
            ids = []
            vectors = []
            metadata = []

            for entity in entities:
                if entity.id in embeddings:
                    ids.append(str(entity.id))
                    vectors.append(embeddings[entity.id])
                    metadata.append({
                        'entity_id': entity.id,
                        'name': entity.canonical_name,
                        'type': entity.entity_type,
                        'kb_id': entity.knowledge_base_id
                    })

            if ids:
                vectors = np.array(vectors)
                self.faiss_index.add_vectors(ids, vectors, metadata)
                logger.info(f"FAISS索引构建完成，包含 {len(ids)} 个实体")

        except Exception as e:
            logger.error(f"构建FAISS索引失败: {e}")

    def _link_entity_group_enhanced(
        self,
        entity_type: str,
        entities: List[KBEntity],
        embeddings: Dict[int, np.ndarray]
    ) -> Tuple[List[GlobalEntity], int]:
        """
        增强版实体组链接

        使用BERT语义相似度和FAISS加速
        """
        if len(entities) == 0:
            return [], 0

        # 1. 使用FAISS快速查找相似实体
        if self.faiss_index and embeddings:
            candidate_links = self._find_candidates_with_faiss(entities, embeddings)
        else:
            # 回退到传统方法
            candidate_links = self._build_candidate_links(entities)

        # 2. 使用BERT验证链接
        verified_groups = self._verify_links_enhanced(entities, candidate_links, embeddings)

        # 3. 创建全局实体
        global_entities = []
        linked_count = 0

        for group in verified_groups:
            global_entity = self._create_global_entity(entity_type, group)
            global_entities.append(global_entity)
            linked_count += len(group)

        return global_entities, linked_count

    def _find_candidates_with_faiss(
        self,
        entities: List[KBEntity],
        embeddings: Dict[int, np.ndarray]
    ) -> Dict[int, List[int]]:
        """
        使用FAISS索引查找候选链接
        """
        candidates = defaultdict(list)

        for entity in entities:
            if entity.id not in embeddings:
                continue

            # 在FAISS中搜索相似实体
            query_vector = embeddings[entity.id]
            results = self.faiss_index.search(query_vector, k=10)

            for result in results:
                # 跳过自己
                if int(result.id) == entity.id:
                    continue

                # 检查相似度阈值
                if result.score >= self.semantic_similarity_threshold:
                    candidates[entity.id].append(int(result.id))

        return dict(candidates)

    def _verify_links_enhanced(
        self,
        entities: List[KBEntity],
        candidate_links: Dict[int, List[int]],
        embeddings: Dict[int, np.ndarray]
    ) -> List[List[KBEntity]]:
        """
        增强版链接验证

        使用BERT语义相似度进行验证
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

                # 使用BERT验证
                if self._verify_link_enhanced(entity, candidate, embeddings):
                    union(entity_id, candidate_id)

        # 收集链接组
        groups = defaultdict(list)
        for entity in entities:
            root = find(entity.id)
            groups[root].append(entity)

        return list(groups.values())

    def _verify_link_enhanced(
        self,
        entity1: KBEntity,
        entity2: KBEntity,
        embeddings: Dict[int, np.ndarray]
    ) -> bool:
        """
        增强版链接验证

        结合BERT语义相似度和传统方法
        """
        # 规则1: 类型一致
        if entity1.entity_type != entity2.entity_type:
            return False

        # 规则2: 名称相似度
        name_sim = self._name_similarity(
            entity1.canonical_name,
            entity2.canonical_name
        )

        # 规则3: BERT语义相似度
        bert_sim = 0.0
        if self.bert_aligner and entity1.id in embeddings and entity2.id in embeddings:
            emb1 = embeddings[entity1.id]
            emb2 = embeddings[entity2.id]

            # 计算余弦相似度
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            if norm1 > 0 and norm2 > 0:
                bert_sim = np.dot(emb1, emb2) / (norm1 * norm2)

        # 规则4: 别名重叠
        alias_sim = 0.0
        aliases1 = set(entity1.aliases or [])
        aliases2 = set(entity2.aliases or [])
        if aliases1 and aliases2:
            alias_sim = len(aliases1 & aliases2) / max(len(aliases1), len(aliases2))

        # 综合判断
        # 如果BERT相似度高，降低名称相似度要求
        if bert_sim >= 0.85:
            return True

        # 如果名称相似度高，降低BERT相似度要求
        if name_sim >= 0.85 and bert_sim >= 0.70:
            return True

        # 如果别名重叠高
        if alias_sim >= 0.5:
            return True

        # 综合分数
        combined_score = 0.3 * name_sim + 0.5 * bert_sim + 0.2 * alias_sim
        return combined_score >= 0.75
