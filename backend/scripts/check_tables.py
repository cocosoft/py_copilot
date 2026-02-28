"""检查数据库表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    # 检查所有表
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result.fetchall()]
    print('数据库表列表:')
    for t in sorted(tables):
        print(f'  - {t}')

    # 检查agent_skill_associations表
    if 'agent_skill_associations' in tables:
        print('\nagent_skill_associations 表存在')
    else:
        print('\nagent_skill_associations 表不存在')

    # 检查agent_tool_associations表
    if 'agent_tool_associations' in tables:
        print('agent_tool_associations 表存在')
    else:
        print('agent_tool_associations 表不存在')
