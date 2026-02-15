#!/usr/bin/env python3
"""
创建模型选择视图的脚本
"""
import sqlite3
import os

def create_model_view():
    """创建模型选择视图"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
    
    print(f"连接数据库: {db_path}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 先删除旧视图（如果存在）
        cursor.execute("DROP VIEW IF EXISTS model_select_view")
        
        # 创建视图
        view_sql = '''
        CREATE VIEW IF NOT EXISTS model_select_view AS
        SELECT 
            m.id,
            m.model_id,
            m.model_name,
            COALESCE(m.description, '') AS description,
            -- 处理模型Logo路径
            CASE 
                WHEN m.logo IS NOT NULL AND m.logo != '' THEN 
                    CASE 
                        WHEN m.logo LIKE 'http%' OR m.logo LIKE '/%' THEN m.logo
                        ELSE 'logos/models/' || m.logo
                    END
                ELSE NULL
            END AS logo,
            m.supplier_id,
            s.name AS supplier_name,
            COALESCE(s.display_name, s.name) AS supplier_display_name,
            -- 处理供应商Logo路径
            CASE 
                WHEN s.logo IS NOT NULL AND s.logo != '' THEN 
                    CASE 
                        WHEN s.logo LIKE 'http%' OR s.logo LIKE '/%' THEN s.logo
                        ELSE 'logos/providers/' || s.logo
                    END
                ELSE 'logos/providers/default.png'
            END AS supplier_logo,
            COALESCE(m.is_default, 0) AS is_default,
            m.model_type_id,
            COALESCE(mc.name, '') AS model_type_name,
            '[]' AS capabilities
        FROM models m
        LEFT JOIN suppliers s ON m.supplier_id = s.id
        LEFT JOIN model_categories mc ON m.model_type_id = mc.id
        ORDER BY 
            m.is_default DESC,
            s.name ASC,
            m.model_name ASC
        '''
        
        cursor.execute(view_sql)
        conn.commit()
        
        print("视图创建成功!")
        
        # 测试视图
        cursor.execute("SELECT COUNT(*) FROM model_select_view")
        count = cursor.fetchone()[0]
        print(f"视图中有 {count} 条记录")
        
        # 查看前5条记录
        cursor.execute("SELECT id, model_name, supplier_name FROM model_select_view LIMIT 5")
        print("\n前5条记录:")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, 模型: {row[1]}, 供应商: {row[2]}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_model_view()
