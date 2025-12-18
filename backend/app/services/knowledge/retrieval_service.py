from typing import List, Dict, Any, Optional
import logging
from .chroma_service import ChromaService

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.chroma_service = ChromaService()
    
    def search_documents(self, query: str, limit: int = 10, knowledge_base_id: int = None) -> List[Dict[str, Any]]:
        """基础向量检索"""
        # 纯向量检索，适合桌面应用
        where_filter = None
        if knowledge_base_id:
            where_filter = {"knowledge_base_id": knowledge_base_id}
        results = self.chroma_service.search_similar(query, limit, where_filter)
        return self.format_results(results)
    
    def format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化检索结果"""
        formatted = []
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return formatted
        
        for i, doc_id in enumerate(results['ids'][0]):
            formatted.append({
                'id': doc_id,
                'title': results['metadatas'][0][i].get('title', '无标题'),
                'content': results['documents'][0][i],
                'score': 1 - results['distances'][0][i] if 'distances' in results and results['distances'][0] else 0.0
            })
        
        # 按相似度排序（从高到低）
        formatted.sort(key=lambda x: x['score'], reverse=True)
        return formatted
    
    def add_document_to_index(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """将文档添加到索引"""
        self.chroma_service.add_document(document_id, text, metadata)
    
    def delete_document_from_index(self, document_id: str) -> None:
        """从索引中删除文档"""
        self.chroma_service.delete_document(document_id)
    
    def get_document_count(self) -> int:
        """获取索引中的文档数量"""
        return self.chroma_service.get_document_count()
    
    def delete_documents_by_metadata(self, metadata_filter: Dict[str, Any]) -> None:
        """根据元数据删除文档"""
        self.chroma_service.delete_documents_by_metadata(metadata_filter)
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """获取指定文档的所有向量片段"""
        where_filter = {"document_id": document_id}
        results = self.chroma_service.search_documents_by_metadata(where_filter)
        return self.format_chunks(results)
    
    def format_chunks(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化向量片段结果"""
        formatted = []
        
        if not results or not results.get('ids'):
            return formatted
        
        for i, chunk_id in enumerate(results['ids']):
            formatted.append({
                'id': chunk_id,
                'title': results['metadatas'][i].get('title', '无标题'),
                'content': results['documents'][i],
                'chunk_index': results['metadatas'][i].get('chunk_index', 0),
                'total_chunks': results['metadatas'][i].get('total_chunks', 0)
            })
        
        # 按片段索引排序
        formatted.sort(key=lambda x: x['chunk_index'])
        return formatted


class AdvancedRetrievalService:
    """高级检索服务，提供增强的搜索功能"""
    
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.chroma_service = ChromaService()
    
    def advanced_search(self, query: str, n_results: int = 10, 
                       knowledge_base_id: Optional[int] = None, 
                       tags: Optional[List[str]] = None, 
                       filters: Optional[Dict[str, Any]] = None, 
                       sort_by: str = "relevance", 
                       entity_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """高级搜索功能"""
        
        # 1. 构建基础搜索条件
        where_filter = {}
        if knowledge_base_id:
            where_filter["knowledge_base_id"] = knowledge_base_id
        
        # 2. 添加标签过滤
        if tags:
            where_filter["tags"] = {"$in": tags}
        
        # 3. 添加其他过滤条件
        if filters:
            where_filter.update(filters)
        
        # 4. 执行向量搜索
        results = self.chroma_service.search_similar(query, n_results, where_filter)
        
        # 5. 结果后处理与排序
        processed_results = self._post_process_results(results)
        
        # 6. 按指定条件排序
        sorted_results = self._sort_results(processed_results, sort_by)
        
        return sorted_results
    
    def hybrid_search(self, query: str, n_results: int = 10, 
                     keyword_weight: float = 0.3, 
                     vector_weight: float = 0.7, 
                     **kwargs) -> List[Dict[str, Any]]:
        """混合搜索（关键词+向量）"""
        
        # 1. 执行关键词搜索
        keyword_results = self._keyword_search(query, n_results)
        
        # 2. 执行向量搜索
        vector_results = self.advanced_search(query, n_results, **kwargs)
        
        # 3. 结果融合
        fused_results = self._fuse_results(keyword_results, vector_results, 
                                         keyword_weight, vector_weight)
        
        return fused_results
    
    def _keyword_search(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        """基于关键词的搜索"""
        # 简单的关键词匹配实现
        # 在实际应用中，可以使用更复杂的关键词匹配算法
        
        # 获取所有文档
        all_documents = self.chroma_service.list_documents(limit=1000)
        
        keyword_results = []
        query_keywords = query.lower().split()
        
        for doc in all_documents:
            if not doc.get('content'):
                continue
                
            # 计算关键词匹配分数
            content_lower = doc['content'].lower()
            keyword_score = 0
            
            for keyword in query_keywords:
                if keyword in content_lower:
                    keyword_score += 1
            
            if keyword_score > 0:
                keyword_results.append({
                    'id': doc['id'],
                    'title': doc['metadata'].get('title', '无标题'),
                    'content': doc['content'],
                    'score': keyword_score / len(query_keywords)
                })
        
        # 按分数排序并限制结果数量
        keyword_results.sort(key=lambda x: x['score'], reverse=True)
        return keyword_results[:n_results]
    
    def _fuse_results(self, keyword_results: List[Dict[str, Any]], 
                     vector_results: List[Dict[str, Any]], 
                     keyword_weight: float, vector_weight: float) -> List[Dict[str, Any]]:
        """融合关键词和向量搜索结果"""
        
        # 创建结果映射
        result_map = {}
        
        # 处理关键词结果
        for result in keyword_results:
            result_id = result['id']
            result_map[result_id] = {
                'id': result_id,
                'title': result['title'],
                'content': result['content'],
                'keyword_score': result['score'],
                'vector_score': 0.0
            }
        
        # 处理向量结果
        for result in vector_results:
            result_id = result['id']
            if result_id in result_map:
                result_map[result_id]['vector_score'] = result['score']
            else:
                result_map[result_id] = {
                    'id': result_id,
                    'title': result['title'],
                    'content': result['content'],
                    'keyword_score': 0.0,
                    'vector_score': result['score']
                }
        
        # 计算融合分数
        fused_results = []
        for result in result_map.values():
            fused_score = (result['keyword_score'] * keyword_weight + 
                          result['vector_score'] * vector_weight)
            
            fused_results.append({
                'id': result['id'],
                'title': result['title'],
                'content': result['content'],
                'score': fused_score,
                'keyword_score': result['keyword_score'],
                'vector_score': result['vector_score']
            })
        
        # 按融合分数排序
        fused_results.sort(key=lambda x: x['score'], reverse=True)
        return fused_results
    
    def _post_process_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """后处理搜索结果"""
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return []
        
        processed = []
        
        for i, doc_id in enumerate(results['ids'][0]):
            processed.append({
                'id': doc_id,
                'title': results['metadatas'][0][i].get('title', '无标题'),
                'content': results['documents'][0][i],
                'score': 1 - results['distances'][0][i] if 'distances' in results and results['distances'][0] else 0.0,
                'knowledge_base_id': results['metadatas'][0][i].get('knowledge_base_id'),
                'file_type': results['metadatas'][0][i].get('file_type'),
                'created_at': results['metadatas'][0][i].get('created_at')
            })
        
        return processed
    
    def _sort_results(self, results: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """按指定条件排序结果"""
        
        if sort_by == "relevance":
            results.sort(key=lambda x: x['score'], reverse=True)
        elif sort_by == "date_asc":
            results.sort(key=lambda x: x.get('created_at', ''))
        elif sort_by == "date_desc":
            results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == "title":
            results.sort(key=lambda x: x.get('title', ''))
        
        return results