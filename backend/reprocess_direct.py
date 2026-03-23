# -*- coding: utf-8 -*-
"""直接调用处理函数重新处理文档"""
import sys
import os
import asyncio
import json

sys.path.insert(0, r'e:\PY\CODES\py copilot IV\backend')

os.environ['PYTHONPATH'] = r'e:\PY\CODES\py copilot IV\backend'

from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.core.database import SessionLocal

async def reprocess_documents():
    """重新处理文档"""
    knowledge_service = KnowledgeService()
    db = SessionLocal()
    
    # 需要重新处理的文档ID
    doc_ids = [105, 106, 115]
    
    print("=" * 100)
    print("开始重新处理文档")
    print("=" * 100)
    
    for doc_id in doc_ids:
        try:
            # 获取文档
            from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
            document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
            
            if not document:
                print(f"\n❌ 文档ID {doc_id} 不存在")
                continue
            
            print(f"\n文档: {document.title} (ID: {doc_id})")
            print("-" * 80)
            
            # 重置文档状态
            if document.document_metadata is None:
                document.document_metadata = {}
            
            if isinstance(document.document_metadata, str):
                metadata = json.loads(document.document_metadata)
            else:
                metadata = document.document_metadata
            
            metadata['processing_status'] = 'processing'
            metadata['error_message'] = None
            metadata['retry_count'] = 0
            metadata['process_progress'] = 0
            metadata['process_stage'] = '开始处理'
            
            document.document_metadata = metadata
            document.is_vectorized = False
            document.vector_id = None
            db.commit()
            
            print(f"  ✅ 文档状态已重置为 'processing'")
            print(f"  🔄 开始异步处理...")
            
            # 启动异步处理
            asyncio.create_task(
                knowledge_service.process_document_async(doc_id, document.knowledge_base_id)
            )
            
            print(f"  ✅ 异步处理任务已创建")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
    
    print("\n" + "=" * 100)
    print("所有文档处理任务已启动")
    print("=" * 100)
    
    # 等待一段时间让任务开始执行
    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(reprocess_documents())
