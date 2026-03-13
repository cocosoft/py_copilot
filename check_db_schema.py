#!/usr/bin/env python3
"""
检查数据库表结构
"""
import sqlite3
import os

def check_schema():
    """检查表结构"""
    db_path = os.path.join(os.path.dirname(__file__), "backend", "py_copilot.db")
    print(f"数据库路径: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查看表结构
        cursor.execute("PRAGMA table_info(knowledge_documents)")
        columns = cursor.fetchall()
        print("\nknowledge_documents 表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        conn.close()

    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_schema()
