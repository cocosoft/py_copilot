#!/usr/bin/env python3
"""
数据库迁移脚本：添加暂停相关字段到 entity_extraction_tasks 表
"""

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """执行迁移"""
    # 获取数据库URL
    database_url = settings.database_url
    print(f"连接到数据库: {database_url}")
    
    # 创建引擎
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # 检查列是否已存在
        result = conn.execute(text("""
            PRAGMA table_info(entity_extraction_tasks)
        """))
        columns = [row[1] for row in result]
        
        print(f"现有列: {columns}")
        
        # 添加新列
        new_columns = []
        
        if 'paused_at' not in columns:
            conn.execute(text("""
                ALTER TABLE entity_extraction_tasks 
                ADD COLUMN paused_at DATETIME
            """))
            new_columns.append('paused_at')
            print("✓ 添加列: paused_at")
        
        if 'resumed_at' not in columns:
            conn.execute(text("""
                ALTER TABLE entity_extraction_tasks 
                ADD COLUMN resumed_at DATETIME
            """))
            new_columns.append('resumed_at')
            print("✓ 添加列: resumed_at")
        
        if 'pause_count' not in columns:
            conn.execute(text("""
                ALTER TABLE entity_extraction_tasks 
                ADD COLUMN pause_count INTEGER DEFAULT 0
            """))
            new_columns.append('pause_count')
            print("✓ 添加列: pause_count")
        
        conn.commit()
        
        if new_columns:
            print(f"\n迁移完成！添加了 {len(new_columns)} 个新列: {', '.join(new_columns)}")
        else:
            print("\n所有列已存在，无需迁移")

if __name__ == "__main__":
    migrate()
