#!/usr/bin/env python3
"""
参数模板表创建迁移脚本
这是一个简化的迁移脚本，直接连接到SQLite数据库，不依赖于复杂的模块导入。
"""
import sqlite3
import json
import os
import sys

# 数据库文件路径 - 根据项目配置，数据库文件位于项目根目录
# 从backend目录向上两级到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(project_root, "py_copilot.db")

def create_tables():
    """创建参数模板相关表"""
    print(f"连接到数据库: {db_path}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"警告: 数据库文件 {db_path} 不存在!")
        return
    
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建 parameter_templates 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parameter_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                scene VARCHAR(100) NOT NULL,
                is_default BOOLEAN NOT NULL DEFAULT 0,
                parameters TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)
        print("parameter_templates 表创建成功或已存在")
        
        # 创建 parameter_template_versions 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parameter_template_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                parameters TEXT NOT NULL,
                changelog TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES parameter_templates(id) ON DELETE CASCADE
            )
        """)
        print("parameter_template_versions 表创建成功或已存在")
        
        # 检查 default_models 表中是否有 parameter_template_id 字段
        cursor.execute("PRAGMA table_info(default_models)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "parameter_template_id" not in columns:
            print("添加 parameter_template_id 字段到 default_models 表...")
            cursor.execute("ALTER TABLE default_models ADD COLUMN parameter_template_id INTEGER")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_default_models_parameter_template_id 
                ON default_models(parameter_template_id)
            """)
            print("parameter_template_id 字段添加成功")
        else:
            print("default_models 表已有 parameter_template_id 字段")
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameter_templates_scene ON parameter_templates(scene)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameter_templates_is_default ON parameter_templates(is_default)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameter_template_versions_template_id ON parameter_template_versions(template_id)")
        
        print("索引创建成功")
        
        # 提交事务
        conn.commit()
        print("参数模板表迁移完成")
        
    except Exception as e:
        conn.rollback()
        print(f"执行迁移时出错: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()