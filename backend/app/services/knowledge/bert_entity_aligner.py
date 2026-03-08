#!/usr/bin/env python3
"""
BERT实体对齐器

使用预训练的BERT模型计算实体间的语义相似度，
支持实体对齐、消歧和跨知识库实体链接。
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import logging
from dataclasses import dataclass

# 可选导入torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)


@dataclass
class EntityEmbedding:
    """实体嵌入数据类"""
    entity_id: int
    entity_text: str
    entity_type: str
    embedding: np.ndarray
    context: str = ""


@dataclass
class AlignmentResult:
    """对齐结果数据类"""
    entity1_id: int
    entity2_id: int
    entity1_text: str
    entity2_text: str
    similarity: float
    alignment_type: str  # 'exact', 'semantic', 'partial'
    confidence: float


class BERTEntityAligner:
    """
    BERT实体对齐器

    使用BERT模型进行实体语义理解和相似度计算，
    支持以下功能：
    1. 实体语义嵌入生成
    2. 实体间语义相似度计算
    3. 实体聚类和消歧
    4. 跨知识库实体链接
    """

    def __init__(self, model_name: str = None, device: str = None):
        """
        初始化BERT实体对齐器

        Args:
            model_name: BERT模型名称，默认为中文BERT-base
            device: 计算设备 ('cuda' 或 'cpu')
        """
        self.model_name = model_name or 'bert-base-chinese'

        # 设置设备
        if device:
            self.device = device
        elif TORCH_AVAILABLE and torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'

        self.tokenizer = None
        self.model = None
        self._model_loaded = False

        # 相似度阈值
        self.exact_match_threshold = 0.95
        self.semantic_match_threshold = 0.85
        self.partial_match_threshold = 0.70

        logger.info(f"BERT实体对齐器初始化，模型: {self.model_name}, 设备: {self.device}")

    def _load_model(self):
        """延迟加载BERT模型"""
        if self._model_loaded:
            return

        try:
            from transformers import BertTokenizer, BertModel

            logger.info(f"正在加载BERT模型: {self.model_name}")
            self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
            self.model = BertModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self._model_loaded = True
            logger.info("BERT模型加载成功")

        except ImportError:
            logger.warning("transformers库未安装，BERT实体对齐器将使用回退方法")
            self._model_loaded = False
        except Exception as e:
            logger.error(f"BERT模型加载失败: {e}")
            self._model_loaded = False

    def encode_entities(self, entities: List[Dict[str, Any]],
                       batch_size: int = 32) -> List[EntityEmbedding]:
        """
        将实体列表编码为语义嵌入

        Args:
            entities: 实体列表，每个实体包含 id, text, type, context
            batch_size: 批处理大小

        Returns:
            实体嵌入列表
        """
        self._load_model()

        if not self._model_loaded:
            # 回退方法：使用简单的词袋模型
            return self._fallback_encode(entities)

        embeddings = []

        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            batch_embeddings = self._encode_batch(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def _encode_batch(self, entities: List[Dict[str, Any]]) -> List[EntityEmbedding]:
        """编码一批实体"""
        # 构建输入文本（实体名 + 上下文）
        texts = []
        for entity in entities:
            text = entity.get('text', '')
            context = entity.get('context', '')
            entity_type = entity.get('type', '')

            # 组合实体信息和上下文
            if context:
                input_text = f"{text}。这是一个{entity_type}类型的实体。上下文：{context}"
            else:
                input_text = f"{text}。这是一个{entity_type}类型的实体。"

            texts.append(input_text)

        # Tokenize
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors='pt'
        )

        # 移动到设备
        input_ids = encoded['input_ids'].to(self.device)
        attention_mask = encoded['attention_mask'].to(self.device)

        # 获取BERT嵌入
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            # 使用[CLS] token的表示作为句子嵌入
            cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        # 构建EntityEmbedding对象
        results = []
        for i, entity in enumerate(entities):
            embedding = EntityEmbedding(
                entity_id=entity.get('id', i),
                entity_text=entity.get('text', ''),
                entity_type=entity.get('type', ''),
                embedding=cls_embeddings[i],
                context=entity.get('context', '')
            )
            results.append(embedding)

        return results

    def _fallback_encode(self, entities: List[Dict[str, Any]]) -> List[EntityEmbedding]:
        """
        回退编码方法（当BERT模型不可用时）

        使用简单的字符级特征作为嵌入
        """
        results = []

        for i, entity in enumerate(entities):
            text = entity.get('text', '')

            # 简单的字符级特征：字符频率向量
            char_freq = defaultdict(int)
            for char in text:
                char_freq[char] += 1

            # 创建固定长度的特征向量
            embedding_dim = 768  # 与BERT输出维度一致
            embedding = np.zeros(embedding_dim)

            # 填充特征
            idx = 0
            for char, freq in sorted(char_freq.items()):
                if idx < embedding_dim:
                    embedding[idx] = freq
                    idx += 1

            # 归一化
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            entity_embedding = EntityEmbedding(
                entity_id=entity.get('id', i),
                entity_text=text,
                entity_type=entity.get('type', ''),
                embedding=embedding,
                context=entity.get('context', '')
            )
            results.append(entity_embedding)

        return results

    def compute_similarity_matrix(self, embeddings: List[EntityEmbedding]) -> np.ndarray:
        """
        计算实体间的语义相似度矩阵

        Args:
            embeddings: 实体嵌入列表

        Returns:
            相似度矩阵
        """
        n = len(embeddings)
        if n == 0:
            return np.array([])

        # 提取嵌入向量
        vectors = np.array([e.embedding for e in embeddings])

        # 归一化
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 避免除零
        vectors_normalized = vectors / norms

        # 计算余弦相似度
        similarity_matrix = np.dot(vectors_normalized, vectors_normalized.T)

        return similarity_matrix

    def align_entities(self, embeddings: List[EntityEmbedding],
                      threshold: float = None) -> List[AlignmentResult]:
        """
        对齐实体列表，找出相似实体对

        Args:
            embeddings: 实体嵌入列表
            threshold: 相似度阈值

        Returns:
            对齐结果列表
        """
        if threshold is None:
            threshold = self.semantic_match_threshold

        similarity_matrix = self.compute_similarity_matrix(embeddings)
        n = len(embeddings)

        alignments = []

        for i in range(n):
            for j in range(i + 1, n):
                similarity = similarity_matrix[i][j]

                if similarity >= threshold:
                    # 确定对齐类型
                    if similarity >= self.exact_match_threshold:
                        alignment_type = 'exact'
                        confidence = 0.95
                    elif similarity >= self.semantic_match_threshold:
                        alignment_type = 'semantic'
                        confidence = 0.85
                    else:
                        alignment_type = 'partial'
                        confidence = 0.70

                    alignment = AlignmentResult(
                        entity1_id=embeddings[i].entity_id,
                        entity2_id=embeddings[j].entity_id,
                        entity1_text=embeddings[i].entity_text,
                        entity2_text=embeddings[j].entity_text,
                        similarity=float(similarity),
                        alignment_type=alignment_type,
                        confidence=confidence
                    )
                    alignments.append(alignment)

        # 按相似度排序
        alignments.sort(key=lambda x: x.similarity, reverse=True)

        return alignments

    def find_similar_pairs(self, embeddings: List[EntityEmbedding],
                          threshold: float = None) -> List[Dict[str, Any]]:
        """
        查找相似的实体对

        Args:
            embeddings: 实体嵌入列表
            threshold: 相似度阈值

        Returns:
            相似实体对列表
        """
        if threshold is None:
            threshold = self.semantic_match_threshold

        similarity_matrix = self.compute_similarity_matrix(embeddings)
        n = len(embeddings)

        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                similarity = similarity_matrix[i][j]
                if similarity >= threshold:
                    pairs.append({
                        'entity1_idx': i,
                        'entity2_idx': j,
                        'similarity': float(similarity)
                    })

        # 按相似度排序
        pairs.sort(key=lambda x: x['similarity'], reverse=True)
        return pairs

    def cluster_entities(self, embeddings: List[EntityEmbedding],
                        threshold: float = None) -> List[List[EntityEmbedding]]:
        """
        对实体进行聚类（层次聚类）

        Args:
            embeddings: 实体嵌入列表
            threshold: 相似度阈值

        Returns:
            聚类结果，每个聚类是一个实体列表
        """
        if threshold is None:
            threshold = self.semantic_match_threshold

        n = len(embeddings)
        if n == 0:
            return []

        if n == 1:
            return [[embeddings[0]]]

        similarity_matrix = self.compute_similarity_matrix(embeddings)

        # 层次聚类
        clusters = [[i] for i in range(n)]

        merged = True
        while merged and len(clusters) > 1:
            merged = False
            best_merge = None
            best_similarity = threshold

            # 找到最相似的簇对
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = self._compute_cluster_similarity(
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
        return [[embeddings[idx] for idx in cluster] for cluster in clusters]

    def _compute_cluster_similarity(self, cluster1: List[int],
                                   cluster2: List[int],
                                   similarity_matrix: np.ndarray) -> float:
        """计算两个簇的平均相似度"""
        total_sim = 0.0
        count = 0

        for i in cluster1:
            for j in cluster2:
                total_sim += similarity_matrix[i][j]
                count += 1

        return total_sim / count if count > 0 else 0.0

    def find_canonical_entity(self, cluster: List[EntityEmbedding]) -> EntityEmbedding:
        """
        在聚类中找到规范实体（中心实体）

        选择与其他实体平均相似度最高的实体作为规范实体
        """
        if len(cluster) == 1:
            return cluster[0]

        similarity_matrix = self.compute_similarity_matrix(cluster)

        # 计算每个实体的平均相似度
        avg_similarities = []
        for i in range(len(cluster)):
            # 计算与其他所有实体的平均相似度
            others = [j for j in range(len(cluster)) if j != i]
            if others:
                avg_sim = np.mean([similarity_matrix[i][j] for j in others])
            else:
                avg_sim = 0
            avg_similarities.append(avg_sim)

        # 选择平均相似度最高的实体
        best_idx = np.argmax(avg_similarities)
        return cluster[best_idx]

    def cross_kb_align(self, source_entities: List[Dict[str, Any]],
                      target_entities: List[Dict[str, Any]],
                      threshold: float = None) -> List[AlignmentResult]:
        """
        跨知识库实体对齐

        Args:
            source_entities: 源知识库实体列表
            target_entities: 目标知识库实体列表
            threshold: 相似度阈值

        Returns:
            跨知识库对齐结果
        """
        if threshold is None:
            threshold = self.semantic_match_threshold

        # 编码两个知识库的实体
        source_embeddings = self.encode_entities(source_entities)
        target_embeddings = self.encode_entities(target_entities)

        alignments = []

        # 计算跨知识库的相似度
        for src_emb in source_embeddings:
            for tgt_emb in target_embeddings:
                similarity = self._compute_cosine_similarity(
                    src_emb.embedding, tgt_emb.embedding
                )

                if similarity >= threshold:
                    if similarity >= self.exact_match_threshold:
                        alignment_type = 'exact'
                        confidence = 0.95
                    elif similarity >= self.semantic_match_threshold:
                        alignment_type = 'semantic'
                        confidence = 0.85
                    else:
                        alignment_type = 'partial'
                        confidence = 0.70

                    alignment = AlignmentResult(
                        entity1_id=src_emb.entity_id,
                        entity2_id=tgt_emb.entity_id,
                        entity1_text=src_emb.entity_text,
                        entity2_text=tgt_emb.entity_text,
                        similarity=float(similarity),
                        alignment_type=alignment_type,
                        confidence=confidence
                    )
                    alignments.append(alignment)

        # 按相似度排序
        alignments.sort(key=lambda x: x.similarity, reverse=True)

        return alignments

    def _compute_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def disambiguate_entity(self, entity_text: str,
                           candidates: List[Dict[str, Any]],
                           context: str = None) -> Optional[Dict[str, Any]]:
        """
        实体消歧

        在多个候选实体中选择最匹配的一个

        Args:
            entity_text: 待消歧的实体文本
            candidates: 候选实体列表
            context: 上下文信息

        Returns:
            最佳匹配的候选实体
        """
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # 编码查询实体
        query_entity = {
            'id': -1,
            'text': entity_text,
            'type': candidates[0].get('type', 'UNKNOWN'),
            'context': context or ''
        }

        query_embedding = self.encode_entities([query_entity])[0]

        # 编码候选实体
        candidate_embeddings = self.encode_entities(candidates)

        # 计算相似度
        best_candidate = None
        best_similarity = 0.0

        for cand_emb in candidate_embeddings:
            similarity = self._compute_cosine_similarity(
                query_embedding.embedding, cand_emb.embedding
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_candidate = cand_emb

        # 找到对应的候选实体
        if best_candidate and best_similarity >= self.partial_match_threshold:
            for candidate in candidates:
                if candidate.get('id') == best_candidate.entity_id:
                    candidate['similarity'] = best_similarity
                    return candidate

        return None


# 单例模式
_bert_aligner = None


def get_bert_aligner(model_name: str = None, device: str = None) -> BERTEntityAligner:
    """获取BERT实体对齐器单例"""
    global _bert_aligner
    if _bert_aligner is None:
        _bert_aligner = BERTEntityAligner(model_name, device)
    return _bert_aligner
