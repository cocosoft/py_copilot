"""
初始化ChunkEntity表

由于项目没有配置alembic，使用SQLAlchemy直接创建表
"""

import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.modules.knowledge.models.knowledge_document import ChunkEntity


def create_chunk_entity_table():
    """创建chunk_entities表"""

    # 创建ChunkEntity表
    ChunkEntity.__table__.create(engine, checkfirst=True)

    print("✅ chunk_entities表创建成功！")


if __name__ == "__main__":
    create_chunk_entity_table()
