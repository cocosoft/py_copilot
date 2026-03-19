"""
智能片段分割服务

实现智能的文档片段分割策略，支持语义分割、实体感知分割等

@task DB-001
@phase 基础架构重构
"""

from typing import List, Dict, Any, Optional
from app.modules.knowledge.models.knowledge_document import DocumentChunk, KnowledgeDocument


class SemanticSegmenter:
    """
    基于语义的文档分割器
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        初始化语义分割器
        
        Args:
            chunk_size: 片段大小
            chunk_overlap: 片段重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def segment(self, document: KnowledgeDocument) -> List[Dict[str, Any]]:
        """
        基于语义边界分割文档
        
        Args:
            document: 知识库文档
            
        Returns:
            分割后的片段列表
        """
        chunks = []
        content = document.content
        
        if not content:
            return chunks
        
        # 基于段落分割
        paragraphs = self._split_into_paragraphs(content)
        
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            para_size = len(paragraph)
            
            if current_size + para_size <= self.chunk_size:
                # 添加到当前片段
                current_chunk.append(paragraph)
                current_size += para_size
            else:
                # 保存当前片段
                if current_chunk:
                    chunks.append({
                        'text': '\n'.join(current_chunk),
                        'size': current_size,
                        'type': 'semantic'
                    })
                
                # 开始新片段
                current_chunk = [paragraph]
                current_size = para_size
        
        # 保存最后一个片段
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'size': current_size,
                'type': 'semantic'
            })
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        将文本分割为段落
        """
        return [p.strip() for p in text.split('\n\n') if p.strip()]


class EntityAwareChunker:
    """
    基于实体感知的文档分割器
    """
    
    def __init__(self, min_chunk_size: int = 500, max_chunk_size: int = 1500):
        """
        初始化实体感知分割器
        
        Args:
            min_chunk_size: 最小片段大小
            max_chunk_size: 最大片段大小
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, document: KnowledgeDocument) -> List[Dict[str, Any]]:
        """
        基于实体感知分割文档
        
        Args:
            document: 知识库文档
            
        Returns:
            分割后的片段列表
        """
        chunks = []
        content = document.content
        
        if not content:
            return chunks
        
        # 获取文档中的实体
        entities = document.entities
        entity_positions = [(e.start_pos, e.end_pos, e.entity_text) for e in entities]
        entity_positions.sort(key=lambda x: x[0])
        
        # 基于实体位置分割
        current_start = 0
        current_end = 0
        
        for i, (start, end, text) in enumerate(entity_positions):
            # 如果当前片段加上实体后的大小超过最大限制
            if end - current_start > self.max_chunk_size:
                # 保存当前片段
                chunks.append({
                    'text': content[current_start:current_end],
                    'size': current_end - current_start,
                    'type': 'entity_aware',
                    'entities': self._get_entities_in_range(entity_positions, current_start, current_end)
                })
                current_start = start
            
            current_end = end
        
        # 保存最后一个片段
        if current_end > current_start:
            chunks.append({
                'text': content[current_start:current_end],
                'size': current_end - current_start,
                'type': 'entity_aware',
                'entities': self._get_entities_in_range(entity_positions, current_start, current_end)
            })
        
        return chunks
    
    def _get_entities_in_range(self, entity_positions: List[tuple], start: int, end: int) -> List[str]:
        """
        获取指定范围内的实体
        """
        entities = []
        for s, e, text in entity_positions:
            if s >= start and e <= end:
                entities.append(text)
        return entities


class ChunkQualityAssessor:
    """
    片段质量评估器
    """
    
    def assess_chunk_quality(self, chunk: Dict[str, Any]) -> Dict[str, float]:
        """
        评估片段质量
        
        Args:
            chunk: 片段字典
            
        Returns:
            质量评分字典
        """
        quality_scores = {}
        
        # 1. 语义完整性评估
        semantic_score = self.assess_semantic_integrity(chunk)
        quality_scores['semantic_integrity'] = semantic_score
        
        # 2. 信息密度评估
        information_density = self.assess_information_density(chunk)
        quality_scores['information_density'] = information_density
        
        # 3. 实体丰富度评估
        entity_richness = self.assess_entity_richness(chunk)
        quality_scores['entity_richness'] = entity_richness
        
        # 4. 上下文连贯性评估
        coherence_score = self.assess_context_coherence(chunk)
        quality_scores['context_coherence'] = coherence_score
        
        # 综合质量分数
        total_score = sum(quality_scores.values()) / len(quality_scores)
        quality_scores['overall_quality'] = total_score
        
        return quality_scores
    
    def assess_semantic_integrity(self, chunk: Dict[str, Any]) -> float:
        """
        评估语义完整性
        """
        # 基于段落完整性、句子完整性等评估
        text = chunk.get('text', '')
        
        # 检查是否以完整句子结束
        ends_with_punctuation = text.endswith(('.', '!', '?', '。', '！', '？'))
        
        # 检查段落完整性
        has_complete_paragraph = '\n' in text or len(text.split(' ')) > 10
        
        score = 0.5
        if ends_with_punctuation:
            score += 0.3
        if has_complete_paragraph:
            score += 0.2
        
        return min(1.0, score)
    
    def assess_information_density(self, chunk: Dict[str, Any]) -> float:
        """
        评估信息密度
        """
        text = chunk.get('text', '')
        words = text.split()
        
        # 计算词密度
        if len(text) > 0:
            density = len(words) / len(text) * 100
            # 归一化到0-1
            score = min(1.0, density / 20)  # 假设20是理想密度
        else:
            score = 0.0
        
        return score
    
    def assess_entity_richness(self, chunk: Dict[str, Any]) -> float:
        """
        评估实体丰富度
        """
        entities = chunk.get('entities', [])
        text = chunk.get('text', '')
        
        if len(text) > 0:
            entity_density = len(entities) / len(text.split())
            # 归一化到0-1
            score = min(1.0, entity_density * 5)  # 假设5个实体/100词是理想密度
        else:
            score = 0.0
        
        return score
    
    def assess_context_coherence(self, chunk: Dict[str, Any]) -> float:
        """
        评估上下文连贯性
        """
        text = chunk.get('text', '')
        
        # 基于句子数量和连接词评估
        sentences = text.split('.')
        connectives = ['and', 'but', 'however', 'therefore', 'because', '所以', '但是', '然而', '因此']
        
        connective_count = sum(1 for c in connectives if c in text.lower())
        
        if len(sentences) > 1:
            coherence = connective_count / len(sentences)
            score = min(1.0, coherence * 2)  # 归一化
        else:
            score = 0.5  # 单个句子的连贯性
        
        return score


class ChunkEntityLinker:
    """
    片段实体关联器
    """
    
    def link_chunks_to_entities(self, chunks: List[Dict[str, Any]], entities: List) -> List[Dict[str, Any]]:
        """
        关联片段和实体
        
        Args:
            chunks: 片段列表
            entities: 实体列表
            
        Returns:
            关联后的片段列表
        """
        linked_chunks = []
        
        for chunk in chunks:
            # 提取片段中的实体
            chunk_entities = self.extract_entities_from_chunk(chunk, entities)
            
            # 关联实体信息
            chunk['entities'] = chunk_entities
            chunk['entity_density'] = len(chunk_entities) / len(chunk['text'].split()) if chunk['text'] else 0
            
            # 计算实体相关性分数
            chunk['entity_relevance_score'] = self.calculate_entity_relevance(chunk_entities)
            
            linked_chunks.append(chunk)
        
        return linked_chunks
    
    def extract_entities_from_chunk(self, chunk: Dict[str, Any], entities: List) -> List:
        """
        从片段中提取实体
        """
        # 实现实体提取逻辑
        return []
    
    def calculate_entity_relevance(self, entities: List) -> float:
        """
        计算实体相关性分数
        """
        # 实现相关性计算逻辑
        return 0.5


class SmartChunkingService:
    """
    智能片段分割服务
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        初始化智能分割服务
        
        Args:
            chunk_size: 片段大小
            chunk_overlap: 片段重叠大小
        """
        self.semantic_segmenter = SemanticSegmenter(chunk_size, chunk_overlap)
        self.entity_aware_chunker = EntityAwareChunker()
        self.quality_assessor = ChunkQualityAssessor()
        self.entity_linker = ChunkEntityLinker()
    
    def chunk_document(self, document: KnowledgeDocument, chunk_strategy: str = 'semantic') -> List[Dict[str, Any]]:
        """
        智能分割文档
        
        Args:
            document: 知识库文档
            chunk_strategy: 分割策略 (semantic/entity_aware/hybrid)
            
        Returns:
            分割后的片段列表
        """
        if chunk_strategy == 'semantic':
            # 基于语义边界的分割
            chunks = self.semantic_segmenter.segment(document)
        
        elif chunk_strategy == 'entity_aware':
            # 基于实体感知的分割
            chunks = self.entity_aware_chunker.chunk(document)
        
        elif chunk_strategy == 'hybrid':
            # 混合分割策略
            semantic_chunks = self.semantic_segmenter.segment(document)
            entity_chunks = self.entity_aware_chunker.chunk(document)
            chunks = self.merge_chunks(semantic_chunks, entity_chunks)
        
        else:
            # 默认使用语义分割
            chunks = self.semantic_segmenter.segment(document)
        
        # 质量评估和优化
        optimized_chunks = self.optimize_chunk_quality(chunks)
        
        # 关联实体
        linked_chunks = self.entity_linker.link_chunks_to_entities(optimized_chunks, document.entities)
        
        return linked_chunks
    
    def merge_chunks(self, semantic_chunks: List[Dict[str, Any]], entity_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并不同策略的片段
        """
        # 实现片段合并逻辑
        # 这里可以基于质量分数选择最佳片段
        merged_chunks = []
        
        # 简单策略：选择质量更高的片段
        all_chunks = semantic_chunks + entity_chunks
        for chunk in all_chunks:
            quality = self.quality_assessor.assess_chunk_quality(chunk)
            chunk['quality'] = quality
        
        # 按质量排序并去重
        all_chunks.sort(key=lambda x: x['quality']['overall_quality'], reverse=True)
        
        # 简单去重
        seen_texts = set()
        for chunk in all_chunks:
            text = chunk['text']
            if text not in seen_texts:
                seen_texts.add(text)
                merged_chunks.append(chunk)
        
        return merged_chunks
    
    def optimize_chunk_quality(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        优化片段质量
        """
        optimized_chunks = []
        
        for chunk in chunks:
            # 评估片段质量
            quality = self.quality_assessor.assess_chunk_quality(chunk)
            chunk['quality'] = quality
            
            # 过滤低质量片段
            if quality['overall_quality'] >= 0.5:
                optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def create_document_chunks(self, document: KnowledgeDocument, chunks: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        创建文档片段实体
        
        Args:
            document: 知识库文档
            chunks: 分割后的片段列表
            
        Returns:
            文档片段实体列表
        """
        document_chunks = []
        
        for i, chunk in enumerate(chunks):
            doc_chunk = DocumentChunk(
                document_id=document.id,
                chunk_text=chunk['text'],
                chunk_index=i,
                total_chunks=len(chunks),
                chunk_metadata={
                    'chunk_type': chunk.get('type', 'semantic'),
                    'quality_score': chunk.get('quality', {}).get('overall_quality', 0),
                    'entities': chunk.get('entities', []),
                    'entity_density': chunk.get('entity_density', 0)
                }
            )
            document_chunks.append(doc_chunk)
        
        return document_chunks