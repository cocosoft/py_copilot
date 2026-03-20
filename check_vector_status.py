#!/usr/bin/env python3
"""
检查文档向量化状态详情
"""
import os
import sys
import json

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = f"sqlite:///{os.path.join(backend_dir, 'py_copilot.db')}"

def check_status():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=== 文档状态详细检查 ===\n")
        
        # 获取所有知识库
        kbs = db.execute(text("SELECT id, name FROM knowledge_bases")).fetchall()
        
        for kb in kbs:
            kb_id = kb[0]
            kb_name = kb[1]
            
            print(f"\n【知识库: {kb_name} (ID: {kb_id})】")
            
            # 获取该知识库的所有文档
            docs = db.execute(text("""
                SELECT id, title, vector_id, document_metadata, content
                FROM knowledge_documents
                WHERE knowledge_base_id = :kb_id
            """), {'kb_id': kb_id}).fetchall()
            
            total = len(docs)
            has_vector = 0
            no_vector = 0
            status_completed = 0
            status_not_completed = 0
            
            # 详细分类
            completed_with_vector = 0
            completed_no_vector = 0
            not_completed_with_vector = 0
            not_completed_no_vector = 0
            
            for doc in docs:
                doc_id = doc[0]
                title = doc[1]
                vector_id = doc[2]
                metadata_str = doc[3]
                content = doc[4]
                
                # 解析metadata
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except:
                    metadata = {}
                
                status = metadata.get('processing_status', 'unknown')
                has_content = bool(content and content.strip())
                
                if vector_id:
                    has_vector += 1
                else:
                    no_vector += 1
                
                if status == 'completed':
                    status_completed += 1
                else:
                    status_not_completed += 1
                
                # 详细分类
                if status == 'completed' and vector_id:
                    completed_with_vector += 1
                elif status == 'completed' and not vector_id:
                    completed_no_vector += 1
                elif status != 'completed' and vector_id:
                    not_completed_with_vector += 1
                else:
                    not_completed_no_vector += 1
                
                # 显示异常文档
                if status != 'completed' or not vector_id:
                    print(f"  异常文档 ID:{doc_id} | 状态:{status} | 有vector_id:{bool(vector_id)} | 有content:{has_content} | {title[:40]}")
            
            print(f"\n  统计:")
            print(f"    总文档数: {total}")
            print(f"    有vector_id: {has_vector}, 无vector_id: {no_vector}")
            print(f"    状态completed: {status_completed}, 状态非completed: {status_not_completed}")
            print(f"    completed+有vector: {completed_with_vector}")
            print(f"    completed+无vector: {completed_no_vector}")
            print(f"    非completed+有vector: {not_completed_with_vector}")
            print(f"    非completed+无vector: {not_completed_no_vector}")
            
            # 计算向量化比例
            if total > 0:
                vector_ratio = (has_vector / total) * 100
                print(f"    向量化比例: {vector_ratio:.1f}%")
    
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_status()
