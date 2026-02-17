"""添加智能体软删除字段"""
from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """添加软删除字段"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE agents ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_is_deleted ON agents(is_deleted)"))
        conn.execute(text("ALTER TABLE agents ADD COLUMN deleted_at DATETIME"))
        conn.execute(text("ALTER TABLE agents ADD COLUMN deleted_by INTEGER"))
        conn.commit()


def downgrade():
    """移除软删除字段"""
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_agents_is_deleted"))
        conn.execute(text("ALTER TABLE agents DROP COLUMN deleted_by"))
        conn.execute(text("ALTER TABLE agents DROP COLUMN deleted_at"))
        conn.execute(text("ALTER TABLE agents DROP COLUMN is_deleted"))
        conn.commit()
