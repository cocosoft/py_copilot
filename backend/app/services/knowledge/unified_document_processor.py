"""
统一文档处理器 - 整合所有文档处理功能

基于现有文档处理器进行整合，解决功能重复问题：
- 整合 DocumentProcessor (core/document_processor.py)
- 整合 DocumentProcessor (document_processor.py) 
- 整合 AdaptiveDocumentProcessor (adaptive_document_processor.py)
- 整合核心解析和文本处理功能

设计原则：
1. 模块化设计，功能清晰分离
2. 向下兼容现有API调用
3. 支持同步和异步处理
4. 集成智能批次处理
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from pathlib import Path

# 导入现有核心模块
from app.services.knowledge.core.document_parser import DocumentParser
from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
from app.services.knowledge.vectorization.chroma_service import ChromaService
from app.services.knowledge.retrieval.retrieval_service import RetrievalService
from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService
from app.services.knowledge.processing_progress_service import processing_progress_service
from app.services.knowledge.adaptive_batch_processor import AdaptiveBatchProcessor, BatchConfig

logger = logging.getLogger(__name__)


class UnifiedDocumentProcessor:
    """统一文档处理器 - 整合所有文档处理功能"""
    
    def __init__(self, batch_config: Optional[BatchConfig] = None):
        """
        初始化统一文档处理器
        
        Args:
            batch_config: 批次配置，使用默认配置如果未提供
        """
        # 核心解析模块 - 使用现有的DocumentParser
        self.parser = DocumentParser()
        
        # 文本处理模块 - 使用现有的AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()
        
        # 文本分块模块 - 使用现有的KnowledgeTextProcessor
        from app.services.knowledge.text_processor import KnowledgeTextProcessor
        self.chunk_processor = KnowledgeTextProcessor()
        
        # 向量化服务 - 使用现有的ChromaService
        self.chroma_service = ChromaService()
        
        # 检索服务 - 使用现有的RetrievalService
        self.retrieval_service = RetrievalService()
        
        # 知识图谱服务 - 使用现有的KnowledgeGraphService
        self.knowledge_graph_service = KnowledgeGraphService()
        
        # 批次处理模块 - 使用现有的AdaptiveBatchProcessor
        self.batch_processor = AdaptiveBatchProcessor(
            batch_config or BatchConfig()
        )
        
        # 进度服务
        self.progress_service = processing_progress_service
    
    def process_document(self, file_path: str, file_type: str, document_id: int,
                        knowledge_base_id: Optional[int] = None, db: Session = None,
                        document_uuid: Optional[str] = None, document_name: str = None) -> Dict[str, Any]:
        """
        同步文档处理流程 - 整合现有处理器的核心功能
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            db: 数据库会话
            document_uuid: 文档UUID
            document_name: 文档名称
            
        Returns:
            处理结果字典
        """
        # 使用uuid作为进度追踪ID
        doc_id_str = document_uuid if document_uuid else str(document_id)
        
        try:
            # 1. 文档解析 - 使用现有解析器
            logger.info(f"开始解析文档: {file_path}")
            self.progress_service.update_progress(doc_id_str, "parsing", 10)
            
            parsed_content = self.parser.parse_document(file_path)
            
            # 2. 文本处理 - 使用现有文本处理器
            logger.info("开始文本处理")
            self.progress_service.update_progress(doc_id_str, "text_processing", 30)
            
            processed_text = self.text_processor.process(parsed_content)
            
            # 3. 向量化 - 使用现有向量化服务
            logger.info("开始向量化处理")
            self.progress_service.update_progress(doc_id_str, "vectorization", 60)
            
            vectors = self.chroma_service.add_documents(
                documents=[processed_text],
                metadatas=[{
                    'document_id': document_id,
                    'knowledge_base_id': knowledge_base_id,
                    'document_name': document_name
                }]
            )
            
            # 4. 知识图谱构建 - 使用现有知识图谱服务
            logger.info("开始知识图谱构建")
            self.progress_service.update_progress(doc_id_str, "graph_building", 80)
            
            graph_result = self.knowledge_graph_service.build_graph_from_text(
                processed_text, document_id, knowledge_base_id
            )
            
            # 5. 完成处理
            self.progress_service.update_progress(doc_id_str, "completed", 100)
            
            return {
                'success': True,
                'document_id': document_id,
                'content': processed_text,
                'vectors': vectors,
                'graph': graph_result,
                'metadata': {
                    'file_path': file_path,
                    'file_type': file_type,
                    'knowledge_base_id': knowledge_base_id
                }
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            self.progress_service.update_progress(doc_id_str, "failed", 0)
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
    
    async def process_document_async(self, file_path: str, file_type: str, document_id: int,
                                   knowledge_base_id: Optional[int] = None, db: Session = None,
                                   document_uuid: Optional[str] = None, document_name: str = None) -> Dict[str, Any]:
        """
        异步文档处理流程 - 支持异步处理
        
        Args:
            同同步处理参数
            
        Returns:
            处理结果字典
        """
        # 在异步环境中运行同步处理
        return await asyncio.get_event_loop().run_in_executor(
            None, self.process_document, 
            file_path, file_type, document_id, knowledge_base_id, db, document_uuid, document_name
        )
    
    async def process_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量文档处理 - 使用现有的AdaptiveBatchProcessor
        
        Args:
            documents: 文档列表，每个文档包含处理参数
            
        Returns:
            批量处理结果列表
        """
        return await self.batch_processor.process_batch(documents)
    
    def process_document_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        纯文本处理 - 整合现有文本处理功能
        
        Args:
            text: 输入文本
            chunk_size: 分块大小
            
        Returns:
            处理后的文本块列表
        """
        # 使用现有文本处理器的分块功能
        return self.chunk_processor.chunk_text(text, chunk_size)
    
    def get_processing_status(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        获取处理状态 - 统一状态查询接口
        
        Args:
            document_id: 文档ID或UUID
            
        Returns:
            处理状态信息
        """
        return self.progress_service.get_progress(str(document_id))


# 创建全局实例，便于现有代码迁移
unified_document_processor = UnifiedDocumentProcessor()