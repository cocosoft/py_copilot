"""
添加current_workspace_id字段到users表的迁移脚本
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

        # 检查current_workspace_id字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'current_workspace_id' in columns:
            print("current_workspace_id字段已存在，无需迁移")
            conn.close()
            return True

        print("添加current_workspace_id字段到users表...")

        # 添加current_workspace_id字段
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN current_workspace_id INTEGER
            REFERENCES workspaces(id)
            ON DELETE SET NULL
        """)

        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_current_workspace_id
            ON users(current_workspace_id)
        """)

        # 提交更改
        conn.commit()

        print("数据库迁移完成！")
        print("已添加current_workspace_id字段到users表")
        print("已创建idx_users_current_workspace_id索引")

        conn.close()
        return True

    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
