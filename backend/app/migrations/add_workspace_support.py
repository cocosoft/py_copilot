"""
工作空间支持迁移脚本

添加工作空间表和相关字段
支持多用户独立工作空间功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def migrate():
    """
    执行数据库迁移

    1. 创建workspaces表
    2. 添加users.current_workspace_id字段
    3. 添加file_records.workspace_id字段
    4. 为现有用户创建默认工作空间
    5. 迁移现有文件记录到默认工作空间
    """
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("开始执行工作空间迁移...")

        # 1. 创建workspaces表
        print("1. 创建workspaces表...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                user_id INTEGER NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                max_storage_bytes INTEGER DEFAULT 1073741824,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # 创建工作空间表的索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_user_default ON workspaces(user_id, is_default)
        """))
        print("   workspaces表创建完成")

        # 2. 添加users.current_workspace_id字段
        print("2. 添加users.current_workspace_id字段...")
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN current_workspace_id INTEGER
            """))
            print("   current_workspace_id字段添加完成")
        except Exception as e:
            print(f"   字段可能已存在: {e}")

        # 3. 添加file_records.workspace_id字段
        print("3. 添加file_records.workspace_id字段...")
        try:
            # 检查file_records表是否存在
            result = session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='file_records'
            """))
            if result.fetchone():
                session.execute(text("""
                    ALTER TABLE file_records ADD COLUMN workspace_id INTEGER
                """))
                # 创建索引
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_file_records_workspace_id ON file_records(workspace_id)
                """))
                print("   workspace_id字段添加完成")
            else:
                print("   file_records表不存在，跳过此步骤")
        except Exception as e:
            print(f"   字段可能已存在: {e}")

        # 4. 为现有用户创建默认工作空间
        print("4. 为现有用户创建默认工作空间...")
        result = session.execute(text("""
            SELECT id, username FROM users WHERE id NOT IN (
                SELECT DISTINCT user_id FROM workspaces
            )
        """))
        users_without_workspace = result.fetchall()

        for user in users_without_workspace:
            session.execute(text("""
                INSERT INTO workspaces (name, description, user_id, is_default, max_storage_bytes)
                VALUES (:name, :description, :user_id, 1, 1073741824)
            """), {
                'name': f'{user[1]}的默认工作空间',
                'description': '系统自动创建的默认工作空间',
                'user_id': user[0]
            })
            print(f"   为用户 {user[1]}(ID:{user[0]}) 创建了默认工作空间")

        # 5. 迁移现有文件记录到默认工作空间
        print("5. 迁移现有文件记录到默认工作空间...")
        # 检查file_records表是否存在
        result = session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='file_records'
        """))
        if result.fetchone():
            session.execute(text("""
                UPDATE file_records
                SET workspace_id = (
                    SELECT id FROM workspaces
                    WHERE workspaces.user_id = file_records.user_id
                    AND workspaces.is_default = 1
                    LIMIT 1
                )
                WHERE workspace_id IS NULL
            """))
            print("   文件记录迁移完成")
        else:
            print("   file_records表不存在，跳过此步骤")

        # 6. 更新用户的current_workspace_id
        print("6. 更新用户的current_workspace_id...")
        session.execute(text("""
            UPDATE users
            SET current_workspace_id = (
                SELECT id FROM workspaces
                WHERE workspaces.user_id = users.id
                AND workspaces.is_default = 1
                LIMIT 1
            )
            WHERE current_workspace_id IS NULL
        """))
        print("   用户当前工作空间更新完成")

        # 提交事务
        session.commit()
        print("\n✅ 工作空间迁移完成！")

    except Exception as e:
        session.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        session.close()
        engine.dispose()


def rollback():
    """
    回滚迁移（谨慎使用）

    删除工作空间相关表和字段
    """
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("开始回滚工作空间迁移...")

        # 1. 删除file_records.workspace_id字段
        print("1. 删除file_records.workspace_id字段...")
        try:
            # SQLite不支持直接删除列，需要重建表
            session.execute(text("""
                DROP INDEX IF EXISTS idx_file_records_workspace_id
            """))
            print("   索引已删除")
        except Exception as e:
            print(f"   回滚索引时出错: {e}")

        # 2. 删除users.current_workspace_id字段
        print("2. 删除users.current_workspace_id字段...")
        try:
            session.execute(text("""
                DROP INDEX IF EXISTS idx_workspaces_user_id
            """))
            session.execute(text("""
                DROP INDEX IF EXISTS idx_workspaces_user_default
            """))
            print("   索引已删除")
        except Exception as e:
            print(f"   回滚索引时出错: {e}")

        # 3. 删除workspaces表
        print("3. 删除workspaces表...")
        try:
            session.execute(text("""
                DROP TABLE IF EXISTS workspaces
            """))
            print("   workspaces表已删除")
        except Exception as e:
            print(f"   删除表时出错: {e}")

        session.commit()
        print("\n✅ 回滚完成！")

    except Exception as e:
        session.rollback()
        print(f"\n❌ 回滚失败: {e}")
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="工作空间数据库迁移脚本")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="执行回滚操作"
    )

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
