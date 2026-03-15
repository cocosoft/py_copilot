#!/usr/bin/env python3
"""
验证文档ID 71是否存在于数据库中（使用SQLAlchemy核心）
"""
import sys
import os
import sqlite3

# 获取数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'py_copilot.db')

def check_document_exists(document_id):
    """
    检查文档是否存在
    """
    try:
        # 连接SQLite数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询文档
        cursor.execute("""
            SELECT id, title, knowledge_base_id, file_path, is_vectorized, created_at 
            FROM knowledge_documents 
            WHERE id = ?
        """, (document_id,))
        
        result = cursor.fetchone()
        
        if result:
            print(f"文档存在！")
            print(f"ID: {result[0]}")
            print(f"标题: {result[1]}")
            print(f"知识库ID: {result[2]}")
            print(f"文件路径: {result[3]}")
            print(f"是否向量化: {result[4]}")
            print(f"创建时间: {result[5]}")
            return True
        else:
            print(f"文档ID {document_id} 不存在")
            return False
    except Exception as e:
        print(f"查询数据库时出错: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    document_id = 71
    print(f"正在检查文档ID {document_id}...")
    print(f"数据库路径: {db_path}")
    check_document_exists(document_id)
