"""
数据库迁移执行脚本
用于执行模型管理模块的数据库迁移
"""

import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationRunner:
    """数据库迁移执行器"""
    
    def __init__(self, db_path: str):
        """
        初始化迁移执行器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent
        self.migration_files = [
            "001_webhook_tables.sql",
            "002_config_tables.sql",
            "003_lifecycle_tables.sql"
        ]
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def ensure_migration_table(self, conn: sqlite3.Connection) -> None:
        """
        确保迁移记录表存在
        
        Args:
            conn: 数据库连接
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(50) NOT NULL UNIQUE,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    def get_applied_migrations(self, conn: sqlite3.Connection) -> set:
        """
        获取已应用的迁移列表
        
        Args:
            conn: 数据库连接
        
        Returns:
            已应用的迁移版本集合
        """
        cursor = conn.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}
    
    def apply_migration(
        self,
        conn: sqlite3.Connection,
        migration_file: str
    ) -> bool:
        """
        应用单个迁移文件
        
        Args:
            conn: 数据库连接
            migration_file: 迁移文件名
        
        Returns:
            是否应用成功
        """
        migration_path = self.migrations_dir / migration_file
        
        if not migration_path.exists():
            logger.error(f"迁移文件不存在: {migration_file}")
            return False
        
        # 读取迁移SQL
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 提取版本号
        version = migration_file.split('_')[0]
        
        try:
            # 执行迁移SQL
            # 分割SQL语句（按分号分割）
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    conn.execute(statement)
            
            # 记录迁移
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,)
            )
            
            conn.commit()
            
            logger.info(f"迁移应用成功: {migration_file}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"迁移应用失败: {migration_file}, 错误: {str(e)}")
            return False
    
    def run_migrations(self) -> bool:
        """
        运行所有待应用的迁移
        
        Returns:
            是否全部成功
        """
        conn = self.get_connection()
        
        try:
            # 确保迁移表存在
            self.ensure_migration_table(conn)
            
            # 获取已应用的迁移
            applied = self.get_applied_migrations(conn)
            
            # 应用待执行的迁移
            success = True
            for migration_file in self.migration_files:
                version = migration_file.split('_')[0]
                
                if version not in applied:
                    logger.info(f"应用迁移: {migration_file}")
                    if not self.apply_migration(conn, migration_file):
                        success = False
                        break
                else:
                    logger.info(f"迁移已应用，跳过: {migration_file}")
            
            return success
            
        finally:
            conn.close()


def main():
    """主函数"""
    # 获取数据库路径
    from app.core.config import settings
    
    db_path = settings.database_url.replace('sqlite:///', '')
    
    logger.info(f"开始执行数据库迁移，数据库路径: {db_path}")
    
    # 创建迁移执行器
    runner = MigrationRunner(db_path)
    
    # 运行迁移
    success = runner.run_migrations()
    
    if success:
        logger.info("数据库迁移全部完成")
        return 0
    else:
        logger.error("数据库迁移失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
