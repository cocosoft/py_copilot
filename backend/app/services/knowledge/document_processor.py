import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理核心模块，负责文档解析、分块、向量化和图谱化"""
    
    def __init__(self):
        # 使用现有的文档解析器
        from app.services.knowledge.document_parser import DocumentParser
        self.parser = DocumentParser()
        
        # 使用高级文本处理器（支持spacy）
        from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()
        
        # 使用现有的ChromaService
        from app.services.knowledge.chroma_service import ChromaService
        self.chroma_service = ChromaService()
        
        # 使用现有的检索服务
        from app.services.knowledge.retrieval_service import RetrievalService
        self.retrieval_service = RetrievalService()
        
        # 使用知识图谱服务
        from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
        self.knowledge_graph_service = KnowledgeGraphService()
    
    def process_document(self, file_path: str, file_type: str, document_id: int, knowledge_base_id: Optional[int] = None, db: Session = None) -> Dict[str, Any]:
        """完整文档处理流程 - 集成图谱化操作"""
        try:
            # 1. 解析文档
            raw_text = self.parser.parse_document(file_path)
            if not raw_text:
                raise ValueError(f"无法解析文档: {file_path}")
            
            logger.info(f"文档解析完成，内容长度: {len(raw_text)} 字符")
            
            # 2. 文本预处理与清理
            cleaned_text = self.text_processor.clean_text(raw_text)
            
            # 3. 智能分块
            chunks = self.text_processor.semantic_chunking(cleaned_text)
            logger.info(f"文档分块完成，共 {len(chunks)} 个块")
            
            # 4. 实体识别与关系提取
            entities, relationships = self.text_processor.extract_entities_relationships(cleaned_text)
            logger.info(f"实体识别完成，识别到 {len(entities)} 个实体和 {len(relationships)} 个关系")
            
            # 5. 向量化处理 - 使用现有的ChromaService
            vector_results = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                metadata = {
                    "document_id": document_id,
                    "knowledge_base_id": knowledge_base_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "title": f"文档 {document_id} 第 {i+1} 块"
                }
                
                # 添加到向量数据库
                self.chroma_service.add_document(chunk_id, chunk, metadata)
                vector_results.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "vector_id": chunk_id,
                    "content": chunk[:200] + "..." if len(chunk) > 200 else chunk
                })
            
            logger.info(f"向量化处理完成，共处理 {len(vector_results)} 个块")
            
            # 6. ✨ 新增：图谱化操作（如果提供了数据库连接）
            graph_data = None
            if db:
                try:
                    # 导入KnowledgeDocument模型
                    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
                    
                    # 获取文档对象
                    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
                    if document:
                        # 提取并存储实体关系
                        entity_result = self.knowledge_graph_service.extract_and_store_entities(db, document)
                        
                        if entity_result.get("success"):
                            # 构建知识图谱
                            graph_data = self.knowledge_graph_service.build_document_graph(document_id, db)
                            
                            if "error" not in graph_data:
                                logger.info(f"图谱化操作完成，构建了包含 {len(graph_data.get('nodes', []))} 个节点和 {len(graph_data.get('edges', []))} 条边的知识图谱")
                            else:
                                logger.warning(f"图谱构建失败: {graph_data.get('error')}")
                        else:
                            logger.warning(f"实体提取失败: {entity_result.get('error')}")
                    else:
                        logger.warning(f"未找到文档 {document_id}，跳过图谱化操作")
                        
                except Exception as graph_error:
                    logger.error(f"图谱化操作失败: {graph_error}")
                    # 图谱化失败不影响文档处理流程继续
            else:
                logger.info("未提供数据库连接，跳过图谱化操作")
            
            return {
                "text": cleaned_text,
                "chunks": chunks,
                "entities": entities,
                "relationships": relationships,
                "vectors": vector_results,
                "graph_data": graph_data,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_documents(self, query: str, n_results: int = 10, 
                        knowledge_base_id: Optional[int] = None, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """搜索文档"""
        try:
            # 构建过滤条件
            where_filter = {}
            if knowledge_base_id:
                where_filter["knowledge_base_id"] = knowledge_base_id
            
            if filters:
                where_filter.update(filters)
            
            # 使用ChromaService进行向量搜索
            results = self.chroma_service.search_similar(query, n_results, where_filter)
            
            # 处理搜索结果
            processed_results = []
            for result in results:
                processed_results.append({
                    "id": result.get("id", ""),
                    "title": result.get("metadata", {}).get("title", ""),
                    "content": result.get("document", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """提取关键词"""
        return self.text_processor.extract_keywords(text, top_n)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        return self.text_processor.calculate_similarity(text1, text2)
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """获取文档的分块信息"""
        try:
            # 构建查询条件
            where_filter = {"document_id": document_id}
            
            # 从向量数据库获取文档块
            results = self.chroma_service.get_documents_by_filter(where_filter)
            
            chunks = []
            for result in results:
                chunks.append({
                    "chunk_id": result.get("id", ""),
                    "content": result.get("document", ""),
                    "metadata": result.get("metadata", {})
                })
            
            # 按块索引排序
            chunks.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
            
            return chunks
            
        except Exception as e:
            logger.error(f"获取文档块失败: {e}")
            return []
    
    def delete_document_vectors(self, document_id: int) -> bool:
        """删除文档的向量数据"""
        try:
            # 构建查询条件
            where_filter = {"document_id": document_id}
            
            # 从向量数据库删除文档块
            self.chroma_service.delete_documents_by_filter(where_filter)
            
            logger.info(f"成功删除文档 {document_id} 的向量数据")
            return True
            
        except Exception as e:
            logger.error(f"删除文档向量数据失败: {e}")
            return False
    
    def update_document_vectors(self, document_id: int, new_content: str) -> Dict[str, Any]:
        """更新文档的向量数据"""
        try:
            # 1. 删除旧的向量数据
            self.delete_document_vectors(document_id)
            
            # 2. 重新处理文档内容
            # 智能分块
            chunks = self.text_processor.semantic_chunking(new_content)
            
            # 3. 重新向量化
            vector_results = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "title": f"文档 {document_id} 第 {i+1} 块"
                }
                
                # 添加到向量数据库
                self.chroma_service.add_document(chunk_id, chunk, metadata)
                vector_results.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "vector_id": chunk_id
                })
            
            logger.info(f"文档 {document_id} 向量数据更新完成，共处理 {len(vector_results)} 个块")
            
            return {
                "success": True,
                "chunks_count": len(vector_results)
            }
            
        except Exception as e:
            logger.error(f"更新文档向量数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_document_text(self, text: str) -> List[str]:
        """处理纯文本文档，返回分块结果"""
        try:
            # 文本预处理与清理
            cleaned_text = self.text_processor.clean_text(text)
            
            # 智能分块
            chunks = self.text_processor.semantic_chunking(cleaned_text)
            
            logger.info(f"文档文本处理完成，共 {len(chunks)} 个块")
            return chunks
            
        except Exception as e:
            logger.error(f"文档文本处理失败: {e}")
            return []