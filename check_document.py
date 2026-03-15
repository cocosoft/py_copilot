#!/usr/bin/env python3
"""
验证文档ID 71是否存在于数据库中
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import SessionLocal
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument

def check_document_exists(document_id):
    """
    检查文档是否存在
    """
    db = SessionLocal()
    try:
        # 查询文档
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        
        if document:
            print(f"文档存在！")
            print(f"ID: {document.id}")
            print(f"标题: {document.title}")
            print(f"知识库ID: {document.knowledge_base_id}")
            print(f"文件路径: {document.file_path}")
            print(f"是否向量化: {document.is_vectorized}")
            print(f"创建时间: {document.created_at}")
            return True
        else:
            print(f"文档ID {document_id} 不存在")
            return False
    except Exception as e:
        print(f"查询数据库时出错: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    document_id = 71
    print(f"正在检查文档ID {document_id}...")
    check_document_exists(document_id)
