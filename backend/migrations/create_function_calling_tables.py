"""Function Calling数据库迁移脚本"""
import sqlite3
import os
from pathlib import Path

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "py_copilot.db")


def migrate_function_calling_tables():
    """创建Function Calling相关表"""
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 创建Tool表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                version TEXT DEFAULT '1.0.0',
                author TEXT,
                icon TEXT DEFAULT '🔧',
                tags TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建ToolExecution表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id INTEGER NOT NULL,
                user_id INTEGER,
                conversation_id INTEGER,
                parameters TEXT,
                result TEXT,
                error TEXT,
                execution_time REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tool_id) REFERENCES tools(id)
            )
        """)
        
        # 创建ToolUsageStats表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                call_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tool_id) REFERENCES tools(id),
                UNIQUE(tool_id, date)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_active ON tools(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_id ON tool_executions(tool_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_executions_user_id ON tool_executions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_executions_created_at ON tool_executions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_usage_stats_tool_id ON tool_usage_stats(tool_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_usage_stats_date ON tool_usage_stats(date)")
        
        # 提交事务
        conn.commit()
        
        print("✅ Function Calling数据库表创建成功！")
        print("   - tools")
        print("   - tool_executions")
        print("   - tool_usage_stats")
        print("   - 所有索引创建成功")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 创建Function Calling数据库表失败: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_function_calling_tables()
