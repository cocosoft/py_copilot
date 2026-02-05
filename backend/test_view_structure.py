#!/usr/bin/env python3
"""
测试视图结构的脚本
"""
import sqlite3
import os

def test_view_structure():
    """测试视图结构"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
    
    print(f"连接数据库: {db_path}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取视图结构
        cursor.execute("PRAGMA table_info(model_select_view)")
        columns = cursor.fetchall()
        
        print("\n视图字段结构:")
        for column in columns:
            print(f"字段名: {column[1]}, 类型: {column[2]}, 非空: {column[3]}")
        
        # 测试查询所有字段
        cursor.execute("SELECT * FROM model_select_view LIMIT 3")
        rows = cursor.fetchall()
        
        print("\n前3条完整记录:")
        for i, row in enumerate(rows):
            print(f"\n记录 {i+1}:")
            print(f"  ID: {row[0]}")
            print(f"  Model ID: {row[1]}")
            print(f"  Model Name: {row[2]}")
            print(f"  Description: {row[3]}")
            print(f"  Logo: {row[4]}")
            print(f"  Supplier ID: {row[5]}")
            print(f"  Supplier Name: {row[6]}")
            print(f"  Supplier Display Name: {row[7]}")
            print(f"  Supplier Logo: {row[8]}")
            print(f"  Is Default: {row[9]}")
            print(f"  Capabilities: {row[10]}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_view_structure()
