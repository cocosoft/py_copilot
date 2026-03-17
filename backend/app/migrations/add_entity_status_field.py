"""
添加文档实体状态字段的数据库迁移脚本

为 document_entities 表添加 status 字段，用于存储实体的确认状态
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text, inspect
from app.core.database import engine


def upgrade():
    """添加 status 字段到 document_entities 表"""
    try:
        # 检查字段是否已存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('document_entities')]
        
        if 'status' in columns:
            print("✅ document_entities.status 字段已存在，跳过创建")
            return

        # 添加 status 字段
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE document_entities 
                ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'
            """))
            
            # 创建索引
            conn.execute(text("""
                CREATE INDEX idx_document_entities_status 
                ON document_entities(status)
            """))
            
            conn.commit()
        
        print("✅ document_entities 表添加 status 字段成功")
        print("   - status 字段 (VARCHAR(20), NOT NULL, DEFAULT 'pending')")
        print("   - idx_document_entities_status 索引")
    except Exception as e:
        print(f"❌ document_entities 表添加 status 字段失败: {e}")
        raise


def downgrade():
    """删除 document_entities 表的 status 字段"""
    try:
        with engine.connect() as conn:
            # 删除索引
            conn.execute(text("""
                DROP INDEX IF EXISTS idx_document_entities_status
            """))
            
            # 删除字段
            conn.execute(text("""
                ALTER TABLE document_entities 
                DROP COLUMN IF EXISTS status
            """))
            
            conn.commit()
        
        print("✅ document_entities 表删除 status 字段成功")
    except Exception as e:
        print(f"❌ document_entities 表删除 status 字段失败: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
