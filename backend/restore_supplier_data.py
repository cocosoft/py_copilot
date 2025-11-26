#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恢复供应商数据脚本
用于将api_supplier_response.json中的数据恢复到数据库中
"""

import json
import sqlite3
import os

# 数据库文件路径
DB_FILE = 'py_copilot.db'
# JSON数据文件路径
JSON_FILE = 'api_supplier_response.json'

def restore_supplier_data():
    """
    从JSON文件读取供应商数据并恢复到数据库
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(JSON_FILE):
            print(f"❌ 错误: 找不到数据文件 {JSON_FILE}")
            return
            
        if not os.path.exists(DB_FILE):
            print(f"❌ 错误: 找不到数据库文件 {DB_FILE}")
            return
            
        # 读取JSON数据
        print(f"📖 正在读取数据文件 {JSON_FILE}...")
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            suppliers_data = json.load(f)
            
        print(f"✅ 成功读取 {len(suppliers_data)} 条供应商数据")
        
        # 连接数据库
        print(f"🔄 正在连接数据库 {DB_FILE}...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 更新每个供应商的数据
        restored_count = 0
        failed_count = 0
        
        print("🚀 开始恢复供应商数据...")
        for supplier in suppliers_data:
            try:
                # 构建更新SQL语句
                update_sql = """
                UPDATE suppliers 
                SET name = ?, description = ?, logo = ?, category = ?, website = ?, 
                    api_endpoint = ?, api_docs = ?, api_key = ?, api_key_required = ?, is_active = ?
                WHERE id = ?
                """
                
                # 准备参数
                params = (
                    supplier['name'],
                    supplier['description'],
                    supplier['logo'],
                    supplier['category'],
                    supplier['website'],
                    supplier['api_endpoint'],
                    supplier['api_docs'],
                    supplier['api_key'],
                    supplier['api_key_required'],
                    supplier['is_active'],
                    supplier['id']
                )
                
                # 执行更新
                cursor.execute(update_sql, params)
                
                if cursor.rowcount > 0:
                    print(f"✅ 成功恢复供应商: {supplier['name']} (ID: {supplier['id']})")
                    restored_count += 1
                else:
                    print(f"⚠️  未找到供应商记录: {supplier['name']} (ID: {supplier['id']})")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ 恢复供应商失败 {supplier['name']}: {str(e)}")
                failed_count += 1
        
        # 提交事务
        conn.commit()
        print(f"\n📊 恢复统计:")
        print(f"✅ 成功恢复: {restored_count} 个供应商")
        print(f"❌ 恢复失败: {failed_count} 个供应商")
        print(f"🔄 数据库事务已提交")
        
    except Exception as e:
        print(f"\n❌ 恢复过程中发生错误: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            print("🔄 数据库事务已回滚")
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    print("==================================")
    print("    供应商数据恢复工具")
    print("==================================")
    restore_supplier_data()
    print("==================================")
    print("恢复操作已完成!")
    print("==================================")
