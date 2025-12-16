from typing import List, Dict, Any
import logging
from .chroma_service import ChromaService

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.chroma_service = ChromaService()
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """基础向量检索"""
        # 纯向量检索，适合桌面应用
        results = self.chroma_service.search_similar(query, limit)
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