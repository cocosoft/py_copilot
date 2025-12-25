import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.modules.knowledge.models.knowledge_document import KnowledgeBase, KnowledgeDocument, KnowledgeTag
from app.services.knowledge.document_parser import DocumentParser
from app.services.knowledge.text_processor import KnowledgeTextProcessor
from app.services.knowledge.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        self.document_parser = DocumentParser()
        self.text_processor = KnowledgeTextProcessor()
        self.retrieval_service = RetrievalService()
    
    def is_supported_format(self, filename: str) -> bool:
        """检查文件格式是否支持"""
        return self.document_parser.is_supported_format(filename)
    
    def create_knowledge_base(self, name: str, description: str, db: Session) -> KnowledgeBase:
        """创建新的知识库"""
        knowledge_base = KnowledgeBase(
            name=name,
            description=description
        )
        db.add(knowledge_base)
        db.commit()
        db.refresh(knowledge_base)
        return knowledge_base
    
    def get_knowledge_base(self, knowledge_base_id: int, db: Session) -> Optional[KnowledgeBase]:
        """获取知识库详情"""
        return db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    
    def list_knowledge_bases(self, db: Session, skip: int = 0, limit: int = 10) -> List[KnowledgeBase]:
        """获取知识库列表"""
        return db.query(KnowledgeBase).offset(skip).limit(limit).all()
    
    def update_knowledge_base(self, knowledge_base_id: int, name: Optional[str], description: Optional[str], db: Session) -> Optional[KnowledgeBase]:
        """更新知识库信息"""
        knowledge_base = self.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            return None
        
        if name is not None:
            knowledge_base.name = name
        if description is not None:
            knowledge_base.description = description
        
        db.commit()
        db.refresh(knowledge_base)
        return knowledge_base
    
    def delete_knowledge_base(self, knowledge_base_id: int, db: Session) -> bool:
        """删除知识库"""
        knowledge_base = self.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            return False
        
        # 删除知识库时会自动删除所有关联的文档（通过cascade设置）
        db.delete(knowledge_base)
        db.commit()
        return True
    
    async def process_uploaded_file(self, file: UploadFile, knowledge_base_id: int, db: Session) -> KnowledgeDocument:
        """处理上传的文件"""
        # 检查文件格式
        if not self.is_supported_format(file.filename):
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 检查文件大小（限制50MB）
        if file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小超过50MB限制")
        
        # 检查知识库是否存在
        knowledge_base = self.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 保存文件到永久存储
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建backend目录下的uploads目录路径
        # 从knowledge_service.py向上走4层：services → knowledge → modules → app → backend
        backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
        upload_dir = os.path.join(backend_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
        
        try:
            # 保存文件
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 创建数据库记录
            document = KnowledgeDocument(
                title=file.filename,
                knowledge_base_id=knowledge_base_id,
                file_path=file_path,
                file_type=os.path.splitext(file.filename)[1].lower(),
                content="",  # 初始为空，将在处理过程中填充
                document_metadata={
                    "original_filename": file.filename,
                    "file_size": file.size,
                    "knowledge_base_id": knowledge_base_id,
                    "knowledge_base_name": knowledge_base.name
                }
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # 使用DocumentProcessor进行完整文档处理（包括图谱化）
            from app.services.knowledge.document_processor import DocumentProcessor
            document_processor = DocumentProcessor()
            
            # 同步处理文档（因为异步处理在FastAPI中可能有问题）
            processing_result = document_processor.process_document_sync(
                file_path, 
                document.file_type, 
                document.id, 
                db
            )
            
            if processing_result.get("success"):
                # 更新文档内容
                document.content = processing_result.get("text", "")
                document.document_metadata["chunks_count"] = len(processing_result.get("chunks", []))
                document.document_metadata["entities_count"] = len(processing_result.get("entities", []))
                document.document_metadata["relationships_count"] = len(processing_result.get("relationships", []))
                document.document_metadata["graph_data_available"] = processing_result.get("graph_data") is not None
                
                # 更新向量ID
                document.vector_id = f"doc_{document.id}"
                db.commit()
                
                logger.info(f"文档处理完成，包含 {len(processing_result.get('chunks', []))} 个片段和 {len(processing_result.get('entities', []))} 个实体")
                
                if processing_result.get("graph_data"):
                    logger.info(f"图谱化完成，构建了包含 {len(processing_result['graph_data'].get('nodes', []))} 个节点的知识图谱")
            else:
                # 处理失败，记录错误信息
                error_msg = processing_result.get("error", "未知错误")
                document.document_metadata["processing_error"] = error_msg
                document.vector_id = None
                db.commit()
                logger.error(f"文档处理失败: {error_msg}")
            
            return document
            
        except Exception as e:
            # 清理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
        finally:
            # 不需要清理文件，因为已经保存到永久存储
            pass

    def search_documents(self, query: str, limit: int = 10, knowledge_base_id: Optional[int] = None, db: Session = None) -> List[Dict[str, Any]]:
        """搜索知识库文档"""
        try:
            # 首先尝试向量检索
            vector_results = self.retrieval_service.search_documents(query, limit, knowledge_base_id)
            if vector_results and len(vector_results) > 0:
                return vector_results
        except Exception as e:
            # 向量搜索失败，使用文本搜索
            print(f"向量搜索失败，使用文本搜索: {str(e)}")
        
        # 降级方案：基于数据库的文本搜索
        if not db:
            return []
            
        from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
        
        # 构建查询
        db_query = db.query(KnowledgeDocument)
        
        # 过滤知识库
        if knowledge_base_id:
            db_query = db_query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        # 文本搜索（标题或内容包含查询词）
        db_query = db_query.filter(
            (KnowledgeDocument.title.ilike(f"%{query}%") | 
             KnowledgeDocument.content.ilike(f"%{query}%"))
        )
        
        # 限制结果数量
        db_results = db_query.limit(limit).all()
        
        # 转换为与向量搜索结果格式一致的字典列表
        text_results = []
        for doc in db_results:
            text_results.append({
                "id": doc.id,
                "title": doc.title,
                "content": doc.content or "",
                "file_path": doc.file_path,
                "file_type": doc.file_type,
                "knowledge_base_id": doc.knowledge_base_id,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "score": 1.0,  # 文本搜索默认分数
                "source": "text_search"  # 标记为文本搜索结果
            })
        
        return text_results
    
    def list_documents(self, db: Session, skip: int = 0, limit: int = 10, knowledge_base_id: Optional[int] = None) -> List[KnowledgeDocument]:
        """获取知识库文档列表"""
        query = db.query(KnowledgeDocument)
        if knowledge_base_id is not None:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        return query.offset(skip).limit(limit).all()
    
    def get_document_count(self, db: Session, knowledge_base_id: Optional[int] = None) -> int:
        """获取文档总数"""
        query = db.query(KnowledgeDocument)
        if knowledge_base_id is not None:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        return query.count()
    
    def delete_document(self, db: Session, document_id: int) -> bool:
        """删除文档"""
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not document:
            return False
        
        # 从向量索引中删除
        if document.vector_id:
            # 根据document_id删除所有相关chunk
            try:
                # 使用元数据过滤器删除该文档的所有chunk
                self.retrieval_service.delete_documents_by_metadata({
                    "document_id": document.id
                })
            except Exception as e:
                print(f"向量索引删除失败: {str(e)}")
        
        # 删除实际文件
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                print(f"文件删除失败: {str(e)}")
        
        db.delete(document)
        db.commit()
        return True
    
    def get_document_by_id(self, document_id: int, db: Session) -> Optional[KnowledgeDocument]:
        """根据ID获取文档详情"""
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    
    def vectorize_document(self, document_id: int, db: Session) -> bool:
        """对文档进行向量化处理"""
        # 获取文档信息
        document = self.get_document_by_id(document_id, db)
        if not document:
            print(f"文档向量化失败: 文档ID {document_id} 不存在")
            return False
        
        try:
            # 检查文件是否存在，支持多种路径格式
            file_path = document.file_path
            
            # 如果文件不存在，尝试从不同目录查找
            if not os.path.exists(file_path):
                # 获取当前文件所在目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # 构建backend目录路径
                backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
                
                # 情况1: 相对路径 temp_uploads/... 或 temp_uploads\... → 尝试绝对路径
                if file_path.startswith(("temp_uploads", "temp_uploads\\")):
                    # 尝试1: 在backend目录下查找
                    temp_path = os.path.join(backend_dir, file_path)
                    if os.path.exists(temp_path):
                        file_path = temp_path
                        print(f"找到文件: {file_path}")
                    else:
                        # 尝试2: 在backend/uploads目录下查找（文件名不变）
                        upload_dir = os.path.join(backend_dir, "uploads")
                        filename = os.path.basename(file_path)
                        temp_path = os.path.join(upload_dir, filename)
                        if os.path.exists(temp_path):
                            file_path = temp_path
                            print(f"找到文件: {file_path}")
                        else:
                            print(f"文档向量化失败: 文件 {document.file_path} 不存在")
                            return False
                # 情况2: 相对路径 uploads/... 或 uploads\... → 尝试绝对路径
                elif file_path.startswith(("uploads", "uploads\\")):
                    # 尝试1: 在backend目录下查找
                    temp_path = os.path.join(backend_dir, file_path)
                    if os.path.exists(temp_path):
                        file_path = temp_path
                        print(f"找到文件: {file_path}")
                    else:
                        # 尝试2: 在backend/app/uploads目录下查找
                        app_upload_dir = os.path.join(backend_dir, "app", "uploads")
                        filename = os.path.basename(file_path)
                        temp_path = os.path.join(app_upload_dir, filename)
                        if os.path.exists(temp_path):
                            file_path = temp_path
                            print(f"找到文件: {file_path}")
                        else:
                            print(f"文档向量化失败: 文件 {document.file_path} 不存在")
                            return False
                # 情况3: 其他相对路径 → 尝试在backend/app/uploads目录下查找
                else:
                    # 尝试在backend/app/uploads目录下查找
                    app_upload_dir = os.path.join(backend_dir, "app", "uploads")
                    filename = os.path.basename(file_path)
                    temp_path = os.path.join(app_upload_dir, filename)
                    if os.path.exists(temp_path):
                        file_path = temp_path
                        print(f"找到文件: {file_path}")
                    else:
                        # 尝试在backend/uploads目录下查找
                        upload_dir = os.path.join(backend_dir, "uploads")
                        temp_path = os.path.join(upload_dir, filename)
                        if os.path.exists(temp_path):
                            file_path = temp_path
                            print(f"找到文件: {file_path}")
                        else:
                            # 情况4: 尝试在uploads目录中查找匹配UUID前缀的文件
                            # 这是针对中文特殊字符问题的修复
                            upload_dir = os.path.join(backend_dir, "uploads")
                            if os.path.exists(upload_dir):
                                # 提取UUID前缀（文件名的前36个字符）
                                original_filename = os.path.basename(file_path)
                                if len(original_filename) >= 36 and original_filename[8] == '-':
                                    uuid_prefix = original_filename[:36]
                                    # 在uploads目录中查找以该UUID开头的文件
                                    for filename in os.listdir(upload_dir):
                                        if filename.startswith(uuid_prefix):
                                            temp_path = os.path.join(upload_dir, filename)
                                            if os.path.exists(temp_path):
                                                file_path = temp_path
                                                print(f"通过UUID前缀匹配找到文件: {file_path}")
                                                break
                                    else:
                                        print(f"文档向量化失败: 文件 {document.file_path} 不存在")
                                        return False
                                else:
                                    print(f"文档向量化失败: 文件 {document.file_path} 不存在")
                                    return False
                            else:
                                print(f"文档向量化失败: 文件 {document.file_path} 不存在")
                                return False
            
            print(f"开始向量化文档: {document.title} (ID: {document_id})")
            print(f"文件路径: {file_path}")
            
            # 重新解析文档
            text_content = self.document_parser.parse_document(file_path)
            print(f"文档解析成功，内容长度: {len(text_content)}")
            
            # 处理文本为chunks
            chunks = self.text_processor.process_document_text(text_content)
            print(f"文本处理成功，生成 {len(chunks)} 个chunks")
            
            # 添加到向量索引
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                metadata = {
                    "title": document.title,
                    "document_id": document.id,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                print(f"添加chunk {i+1}/{len(chunks)} 到向量索引")
                self.retrieval_service.add_document_to_index(chunk_id, chunk, metadata)
            
            # 更新文档信息
            document.vector_id = f"doc_{document.id}"
            document.is_vectorized = 1
            db.commit()
            print(f"文档向量化成功: {document.title} (ID: {document_id})")
            
            return True
        except Exception as e:
            print(f"文档向量化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def download_document(self, db: Session, document_id: int) -> tuple[str, str]:
        """下载文档"""
        # 获取文档信息
        document = self.get_document_by_id(document_id, db)
        if not document:
            return None, None
        
        # 检查文件是否存在，支持多种路径格式
        file_path = document.file_path
        
        # 如果文件不存在，尝试从不同目录查找
        if not os.path.exists(file_path):
            # 情况1: 相对路径 temp_uploads/... → 尝试绝对路径
            if file_path.startswith("temp_uploads"):
                # 获取当前文件所在目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # 构建backend目录路径
                backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
                # 尝试在backend目录下查找
                temp_path = os.path.join(backend_dir, file_path)
                if os.path.exists(temp_path):
                    file_path = temp_path
                    print(f"找到文件: {file_path}")
                else:
                    # 尝试在backend/uploads目录下查找（文件名不变）
                    upload_dir = os.path.join(backend_dir, "uploads")
                    filename = os.path.basename(file_path)
                    temp_path = os.path.join(upload_dir, filename)
                    if os.path.exists(temp_path):
                        file_path = temp_path
                        print(f"找到文件: {file_path}")
                    else:
                        return None, None
            # 情况2: 相对路径 uploads/... → 尝试绝对路径
            elif file_path.startswith("uploads"):
                # 获取当前文件所在目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # 构建backend目录路径
                backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
                # 尝试在backend目录下查找
                temp_path = os.path.join(backend_dir, file_path)
                if os.path.exists(temp_path):
                    file_path = temp_path
                    print(f"找到文件: {file_path}")
                else:
                    return None, None
            else:
                return None, None
        
        # 返回文件路径和原始文件名
        return file_path, document.title
    
    def get_all_tags(self, db: Session, knowledge_base_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有标签，可选按知识库过滤"""
        query = db.query(KnowledgeTag)
        
        if knowledge_base_id:
            # 如果指定了知识库ID，获取该知识库下所有文档的标签
            query = query.join(KnowledgeTag.documents).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).distinct()
        
        tags = query.all()
        
        # 计算每个标签的文档数量
        tag_list = []
        for tag in tags:
            if knowledge_base_id:
                doc_count = db.query(KnowledgeDocument).join(KnowledgeDocument.tags).filter(
                    KnowledgeDocument.knowledge_base_id == knowledge_base_id,
                    KnowledgeTag.id == tag.id
                ).count()
            else:
                doc_count = len(tag.documents)
            
            tag_list.append({
                "id": tag.id,
                "name": tag.name,
                "created_at": tag.created_at,
                "document_count": doc_count
            })
        
        return tag_list
    
    def add_tag(self, tag_name: str, db: Session) -> KnowledgeTag:
        """添加新标签，如果标签已存在则返回现有标签"""
        tag = db.query(KnowledgeTag).filter(KnowledgeTag.name == tag_name).first()
        if tag:
            return tag
        
        tag = KnowledgeTag(name=tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    
    def get_document_tags(self, document_id: int, db: Session) -> List[KnowledgeTag]:
        """获取文档的所有标签"""
        document = self.get_document_by_id(document_id, db)
        if not document:
            return []
        return document.tags
    
    def add_document_tag(self, document_id: int, tag_name: str, db: Session) -> KnowledgeTag:
        """为文档添加标签"""
        document = self.get_document_by_id(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取或创建标签
        tag = self.add_tag(tag_name, db)
        
        # 如果文档已有该标签，则直接返回
        if tag in document.tags:
            return tag
        
        # 添加标签到文档
        document.tags.append(tag)
        db.commit()
        db.refresh(document)
        return tag
    
    def remove_document_tag(self, document_id: int, tag_id: int, db: Session) -> bool:
        """从文档中移除标签"""
        document = self.get_document_by_id(document_id, db)
        if not document:
            return False
        
        tag = db.query(KnowledgeTag).filter(KnowledgeTag.id == tag_id).first()
        if not tag:
            return False
        
        if tag in document.tags:
            document.tags.remove(tag)
            db.commit()
            db.refresh(document)
            return True
        
        return False
    
    def search_documents_by_tag(self, tag_id: int, db: Session, knowledge_base_id: Optional[int] = None) -> List[KnowledgeDocument]:
        """根据标签搜索文档"""
        query = db.query(KnowledgeDocument).join(KnowledgeDocument.tags).filter(
            KnowledgeTag.id == tag_id
        )
        
        if knowledge_base_id:
            query = query.filter(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        
        return query.all()
    
    def delete_tag(self, tag_id: int, db: Session) -> bool:
        """删除标签"""
        tag = db.query(KnowledgeTag).filter(KnowledgeTag.id == tag_id).first()
        if not tag:
            return False
        
        db.delete(tag)
        db.commit()
        return True
    
    def get_document_chunks(self, document_id: int, db: Session) -> List[Dict[str, Any]]:
        """获取指定文档的所有向量片段"""
        try:
            # 检查文档是否存在
            document = self.get_document_by_id(document_id, db)
            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            # 获取向量片段
            chunks = self.retrieval_service.get_document_chunks(document_id)
            return chunks
        except HTTPException:
            raise
        except Exception as e:
            print(f"获取文档向量片段失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取文档向量片段失败")

    # Document Version Control Methods
    def get_document_versions(self, document_id: int, db: Session) -> List[KnowledgeDocument]:
        """获取文档的所有版本"""
        # 获取所有具有相同知识库ID和标题的文档（同一文档的不同版本）
        current_doc = self.get_document_by_id(document_id, db)
        if not current_doc:
            return []
        
        # 查找所有具有相同知识库ID和相似标题的文档
        # 这里我们假设同一文档的不同版本具有相同的知识库ID和相似的文件名
        versions = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == current_doc.knowledge_base_id,
            KnowledgeDocument.title.like(f"%{current_doc.title.split('.')[0]}%")
        ).order_by(KnowledgeDocument.version.desc()).all()
        
        return versions

    def update_document_with_version(self, document_id: int, update_data: dict, db: Session) -> Optional[KnowledgeDocument]:
        """更新文档并创建新版本"""
        # 获取当前文档
        current_doc = self.get_document_by_id(document_id, db)
        if not current_doc:
            return None
        
        # 标记当前版本为历史版本
        current_doc.is_current = False
        db.commit()
        
        # 创建新版本文档
        new_version = KnowledgeDocument(
            title=update_data.get("title", current_doc.title),
            file_path=update_data.get("file_path", current_doc.file_path),
            file_type=current_doc.file_type,
            content=update_data.get("content", current_doc.content),
            knowledge_base_id=current_doc.knowledge_base_id,
            version=current_doc.version + 1,
            is_current=True,
            is_vectorized=0,  # 新版本需要重新向量化
            vector_id=None,   # 清空向量ID
            document_metadata=current_doc.document_metadata
        )
        
        # 复制标签
        new_version.tags = current_doc.tags
        
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        return new_version

    def get_document_version(self, document_id: int, version_id: int, db: Session) -> Optional[KnowledgeDocument]:
        """获取特定版本的文档"""
        # 首先获取当前文档以确定知识库ID
        current_doc = self.get_document_by_id(document_id, db)
        if not current_doc:
            return None
        
        # 查找指定版本的文档
        version_doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == current_doc.knowledge_base_id,
            KnowledgeDocument.version == version_id,
            KnowledgeDocument.title.like(f"%{current_doc.title.split('.')[0]}%")
        ).first()
        
        return version_doc

    def restore_document_version(self, document_id: int, version_id: int, db: Session) -> Optional[KnowledgeDocument]:
        """恢复文档到指定版本"""
        # 获取要恢复的版本
        target_version = self.get_document_version(document_id, version_id, db)
        if not target_version:
            return None
        
        # 获取当前文档
        current_doc = self.get_document_by_id(document_id, db)
        if not current_doc:
            return None
        
        # 获取该文档的所有版本以确定最大版本号
        all_versions = self.get_document_versions(document_id, db)
        max_version = max([v.version for v in all_versions]) if all_versions else 0
        
        # 标记当前版本为历史版本
        current_doc.is_current = False
        db.commit()
        
        # 创建恢复版本（基于目标版本创建新版本）
        restored_version = KnowledgeDocument(
            title=target_version.title,
            file_path=target_version.file_path,
            file_type=target_version.file_type,
            content=target_version.content,
            knowledge_base_id=target_version.knowledge_base_id,
            version=max_version + 1,  # 新版本号，基于最大版本号+1
            is_current=True,
            is_vectorized=0,  # 需要重新向量化
            vector_id=None,   # 清空向量ID
            document_metadata=target_version.document_metadata
        )
        
        # 复制标签
        restored_version.tags = target_version.tags
        
        db.add(restored_version)
        db.commit()
        db.refresh(restored_version)
        
        return restored_version