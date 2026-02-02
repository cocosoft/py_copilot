"""
添加topic_id字段到messages表的迁移脚本
"""
import sqlite3
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = "py_copilot.db"
    
    print(f"开始迁移数据库: {db_path}")
    print(f"时间: {datetime.now()}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查topic_id字段是否已存在
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'topic_id' in columns:
            print("topic_id字段已存在，无需迁移")
            conn.close()
            return
        
        print("添加topic_id字段到messages表...")
        
        # 添加topic_id字段
        cursor.execute("""
            ALTER TABLE messages 
            ADD COLUMN topic_id INTEGER 
            REFERENCES topics(id) 
            ON DELETE SET NULL
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_topic_id 
            ON messages(topic_id)
        """)
        
        # 提交更改
        conn.commit()
        
        print("数据库迁移完成！")
        print("已添加topic_id字段到messages表")
        print("已创建idx_messages_topic_id索引")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"messages表现在包含的字段: {columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"数据库迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_database()