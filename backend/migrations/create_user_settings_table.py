"""创建用户设置表"""
from sqlalchemy import text
from app.core.database import create_engine
from app.core.config import settings


def upgrade() -> None:
    """执行升级"""
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        # 创建user_settings表
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            setting_type VARCHAR(50) NOT NULL,
            setting_data JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id, setting_type)
        )
        """))
        conn.commit()


def downgrade() -> None:
    """执行降级"""
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        # 删除user_settings表
        conn.execute(text("DROP TABLE IF EXISTS user_settings"))
        conn.commit()