"""添加任务工作目录和命令执行字段"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """添加新字段"""
    with engine.connect() as conn:
        # 添加工作目录字段
        conn.execute(text("""
            ALTER TABLE tasks 
            ADD COLUMN working_directory VARCHAR(500)
        """))
        
        # 添加执行命令标志字段
        conn.execute(text("""
            ALTER TABLE tasks 
            ADD COLUMN execute_command BOOLEAN DEFAULT FALSE
        """))
        
        # 添加命令字段
        conn.execute(text("""
            ALTER TABLE tasks 
            ADD COLUMN command TEXT
        """))
        
        conn.commit()
    
    print("✅ 任务表字段添加成功")


def downgrade():
    """移除新字段"""
    with engine.connect() as conn:
        # 移除命令字段
        conn.execute(text("""
            ALTER TABLE tasks 
            DROP COLUMN command
        """))
        
        # 移除执行命令标志字段
        conn.execute(text("""
            ALTER TABLE tasks 
            DROP COLUMN execute_command
        """))
        
        # 移除工作目录字段
        conn.execute(text("""
            ALTER TABLE tasks 
            DROP COLUMN working_directory
        """))
        
        conn.commit()
    
    print("✅ 任务表字段移除成功")


if __name__ == "__main__":
    upgrade()
