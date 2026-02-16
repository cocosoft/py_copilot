"""
添加任务相关表的数据库迁移脚本（优化版）
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.task import Task, TaskSkill


def upgrade():
    """创建任务相关表"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 任务相关表创建成功")
        print("   - tasks 表")
        print("   - task_skills 表")
    except Exception as e:
        print(f"❌ 任务相关表创建失败: {e}")
        raise


def downgrade():
    """删除任务相关表"""
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS task_skills"))
            conn.execute(text("DROP TABLE IF EXISTS tasks"))
            conn.commit()
        print("✅ 任务相关表删除成功")
    except Exception as e:
        print(f"❌ 任务相关表删除失败: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
