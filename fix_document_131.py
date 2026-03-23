#!/usr/bin/env python3
"""
修复文档131的处理状态

问题分析：
1. 文档131状态为pending，但没有content和vector_id
2. 前端API调用超时，说明后端处理可能卡住或根本没有开始
3. 可能原因：
   - 文档处理队列没有正确启动
   - 文档被标记为processing但实际未在处理
   - 后端服务重启导致处理中断

解决方案：
重置文档状态，允许重新处理
"""
import os
import sys
import json

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = f"sqlite:///{os.path.join(backend_dir, 'py_copilot.db')}"

def fix_document_131():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=== 修复文档131 ===\n")
        
        # 获取文档131的详细信息
        doc = db.execute(text("""
            SELECT id, title, vector_id, document_metadata, content, file_path, file_type
            FROM knowledge_documents
            WHERE id = 131
        """)).fetchone()
        
        if not doc:
            print("错误: 文档131不存在")
            return
        
        print(f"文档ID: {doc[0]}")
        print(f"标题: {doc[1]}")
        print(f"Vector ID: {doc[2]}")
        print(f"内容长度: {len(doc[4]) if doc[4] else 0}")
        print(f"文件路径: {doc[5]}")
        print(f"文件类型: {doc[6]}")
        
        # 解析metadata
        try:
            metadata = json.loads(doc[3]) if doc[3] else {}
        except:
            metadata = {}
        
        print(f"当前状态: {metadata.get('processing_status', 'unknown')}")
        print()
        
        # 检查文件是否存在
        if doc[5] and os.path.exists(doc[5]):
            file_size = os.path.getsize(doc[5])
            print(f"✓ 文件存在，大小: {file_size} bytes")
        else:
            print(f"✗ 文件不存在: {doc[5]}")
            print("警告: 文件丢失，无法重新处理")
            return
        
        # 重置文档状态
        print("\n正在重置文档状态...")
        
        # 更新metadata
        metadata['processing_status'] = 'idle'
        metadata['processing_error'] = None
        metadata['retry_count'] = 0
        
        # 如果之前有失败的记录，清理掉
        if 'processing_error' in metadata:
            del metadata['processing_error']
        
        db.execute(text("""
            UPDATE knowledge_documents
            SET document_metadata = :metadata,
                content = '',
                vector_id = NULL
            WHERE id = 131
        """), {'metadata': json.dumps(metadata)})
        
        db.commit()
        print("✓ 文档状态已重置为 'idle'")
        print("\n操作完成!")
        print("现在你可以在前端界面中手动启动该文档的处理。")
        
    except Exception as e:
        print(f"修复失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_document_131()
