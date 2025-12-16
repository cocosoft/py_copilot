import os
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
from app.services.knowledge.document_parser import DocumentParser
from app.services.knowledge.text_processor import KnowledgeTextProcessor
from app.services.knowledge.retrieval_service import RetrievalService

class KnowledgeService:
    def __init__(self):
        self.document_parser = DocumentParser()
        self.text_processor = KnowledgeTextProcessor()
        self.retrieval_service = RetrievalService()
    
    def is_supported_format(self, filename: str) -> bool:
        """检查文件格式是否支持"""
        return self.document_parser.is_supported_format(filename)
    
    async def process_uploaded_file(self, file: UploadFile, db: Session) -> KnowledgeDocument:
        """处理上传的文件"""
        # 检查文件格式
        if not self.is_supported_format(file.filename):
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 检查文件大小（限制10MB）
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小超过10MB限制")
        
        # 保存临时文件
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        
        try:
            # 保存文件
            content = await file.read()
            with open(temp_file_path, 'wb') as f:
                f.write(content)
            
            # 解析文档
            text_content = self.document_parser.parse_document(temp_file_path)
            
            # 处理文本
            chunks = self.text_processor.process_document_text(text_content)
            
            # 创建数据库记录
            document = KnowledgeDocument(
                title=file.filename,
                file_path=temp_file_path,
                file_type=os.path.splitext(file.filename)[1].lower(),
                content=text_content[:1000],  # 保存前1000字符用于预览
                document_metadata={
                    "original_filename": file.filename,
                    "file_size": file.size,
                    "chunks_count": len(chunks)
                }
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # 添加到向量索引（每个chunk作为一个文档）
            try:
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{document.id}_chunk_{i}"
                    metadata = {
                        "title": file.filename,
                        "document_id": document.id,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                    self.retrieval_service.add_document_to_index(chunk_id, chunk, metadata)
                
                # 更新向量ID
                document.vector_id = f"doc_{document.id}"
                db.commit()
            except Exception as e:
                # 向量索引失败，但文档仍然保存到数据库
                print(f"向量索引失败，但文档已保存到数据库: {str(e)}")
                document.vector_id = None
                db.commit()
            
            return document
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索知识库文档"""
        try:
            # 首先尝试向量检索
            vector_results = self.retrieval_service.search_documents(query, limit)
            if vector_results and len(vector_results) > 0:
                return vector_results
        except Exception as e:
            print(f"向量搜索失败，使用文本搜索: {str(e)}")
        
        # 降级方案：基于数据库的文本搜索
        return []  # 暂时返回空结果，后续可以添加文本搜索实现
    
    def list_documents(self, db: Session, skip: int = 0, limit: int = 10) -> List[KnowledgeDocument]:
        """获取知识库文档列表"""
        return db.query(KnowledgeDocument).offset(skip).limit(limit).all()
    
    def get_document_count(self, db: Session) -> int:
        """获取文档总数"""
        return db.query(KnowledgeDocument).count()
    
    def delete_document(self, db: Session, document_id: int) -> bool:
        """删除文档"""
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not document:
            return False
        
        # 从向量索引中删除
        if document.vector_id:
            # 删除所有相关的chunk
            document_count = self.retrieval_service.get_document_count()
            # 这里简化处理，实际应该根据document_id删除所有相关chunk
            # 由于ChromaDB的限制，需要更复杂的逻辑来批量删除
            pass
        
        db.delete(document)
        db.commit()
        return True