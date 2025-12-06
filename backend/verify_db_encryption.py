#!/usr/bin/env python3
"""
直接查询数据库验证API密钥加密存储脚本
此脚本将直接连接SQLite数据库，查看suppliers表中api_key字段的原始存储值
"""
import sqlite3
import os
from app.core.encryption import encrypt_string, decrypt_string

def verify_api_key_encryption():
    """验证API密钥在数据库中的加密存储状态"""
    # 获取数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
    
    print(f"\n🔍 正在连接数据库: {db_path}")
    
    try:
        # 直接连接SQLite数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 直接查询数据库中的原始数据
        cursor.execute("SELECT id, name, api_key FROM suppliers WHERE api_key IS NOT NULL")
        results = cursor.fetchall()
        
        print(f"\n📊 查询到 {len(results)} 条包含API密钥的供应商记录")
        print("=" * 80)
        
        if results:
            for row in results:
                supplier_id, supplier_name, db_api_key = row
                
                print(f"\n供应商ID: {supplier_id}")
                print(f"供应商名称: {supplier_name}")
                print(f"数据库原始存储值: {db_api_key}")
                print(f"存储值类型: {type(db_api_key)}")
                print(f"存储值长度: {len(db_api_key)}")
                
                try:
                    # 尝试解密查看
                    decrypted_key = decrypt_string(db_api_key)
                    print(f"解密后的值: {decrypted_key}")
                    
                    # 验证加密是否正常
                    if db_api_key != decrypted_key:
                        print("✅ 确认: 数据库中存储的是加密后的密文")
                    else:
                        print("⚠️  注意: 数据库中存储的是明文")
                        
                except Exception as e:
                    print(f"❌ 解密失败: {e}")
                    print(f"⚠️  可能是旧的明文数据或加密格式问题")
                
                print("-" * 50)
        else:
            print("\nℹ️  数据库中没有找到包含API密钥的供应商记录")
            print("请先在前端添加供应商API密钥后再进行验证")
        
        # 显示表结构确认字段存在
        print("\n📋 表结构确认:")
        cursor.execute("PRAGMA table_info(suppliers)")
        columns = cursor.fetchall()
        for col in columns:
            if 'api_key' in col[1]:
                print(f"字段名: {col[1]}, 类型: {col[2]}")
        
    except sqlite3.Error as e:
        print(f"\n❌ 数据库操作错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            print(f"\n✅ 数据库连接已关闭")

if __name__ == "__main__":
    verify_api_key_encryption()
