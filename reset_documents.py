#!/usr/bin/env python3
"""
重置所有文档状态为待处理
"""
import sqlite3
import os

def reset_document_status():
    """重置所有文档状态"""
    db_path = os.path.join(os.path.dirname(__file__), "backend", "py_copilot.db")
    print(f"数据库路径: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查看当前文档数量
        cursor.execute("SELECT COUNT(*) FROM knowledge_documents")
        count = cursor.fetchone()[0]
        print(f"\n当前文档总数: {count}")

        # 查看当前向量化状态
        cursor.execute("SELECT is_vectorized, COUNT(*) FROM knowledge_documents GROUP BY is_vectorized")
        status_counts = cursor.fetchall()
        print("\n向量化状态分布:")
        for status, cnt in status_counts:
            print(f"  is_vectorized={status}: {cnt} 个文档")

        # 重置所有文档状态
        sql = "UPDATE knowledge_documents SET is_vectorized = 0, vector_id = NULL"
        cursor.execute(sql)

        conn.commit()
        print(f"\n✓ 已重置 {cursor.rowcount} 个文档状态")

        # 验证重置结果
        cursor.execute("SELECT is_vectorized, COUNT(*) FROM knowledge_documents GROUP BY is_vectorized")
        status_counts = cursor.fetchall()
        print("\n重置后状态分布:")
        for status, cnt in status_counts:
            print(f"  is_vectorized={status}: {cnt} 个文档")

        conn.close()
        print("\n✓ 文档状态重置完成")
        return True

    except Exception as e:
        print(f"✗ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("重置文档状态")
    print("=" * 60)
    reset_document_status()
