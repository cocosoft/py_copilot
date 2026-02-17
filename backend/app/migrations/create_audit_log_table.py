"""创建审计日志表"""
from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """创建审计日志表"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                resource_type VARCHAR(50) NOT NULL,
                resource_id INTEGER NOT NULL,
                old_values TEXT,
                new_values TEXT,
                ip_address VARCHAR(50),
                user_agent VARCHAR(500),
                created_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)"))
        conn.commit()


def downgrade():
    """删除审计日志表"""
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_logs_created_at"))
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_logs_resource_id"))
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_logs_resource_type"))
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_logs_action"))
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_logs_user_id"))
        conn.execute(text("DROP TABLE IF EXISTS audit_logs"))
        conn.commit()
