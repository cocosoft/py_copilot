"""
添加用户设置表的数据库迁移脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text, inspect
from app.core.database import engine, Base
from app.models.setting import UserSetting


def upgrade():
    """创建用户设置表"""
    try:
        # 检查表是否已存在
        inspector = inspect(engine)
        if 'user_settings' in inspector.get_table_names():
            print("✅ user_settings 表已存在，跳过创建")
            return

        # 创建表
        UserSetting.__table__.create(engine)
        print("✅ 用户设置表创建成功")
        print("   - user_settings 表")
    except Exception as e:
        print(f"❌ 用户设置表创建失败: {e}")
        raise


def downgrade():
    """删除用户设置表"""
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS user_settings"))
            conn.commit()
        print("✅ 用户设置表删除成功")
    except Exception as e:
        print(f"❌ 用户设置表删除失败: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
