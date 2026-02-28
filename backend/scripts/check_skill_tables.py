"""检查技能关联表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    # 检查所有与skill相关的表
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%skill%'"))
    skill_tables = [row[0] for row in result.fetchall()]
    print('技能相关表:')
    for t in sorted(skill_tables):
        print(f'  - {t}')

    # 检查skills表结构
    print('\nskills 表字段:')
    result = conn.execute(text("PRAGMA table_info(skills)"))
    for row in result.fetchall():
        print(f'  - {row[1]} ({row[2]})')

    # 检查是否有官方技能
    result = conn.execute(text("SELECT COUNT(*) FROM skills WHERE is_official = 1"))
    count = result.fetchone()[0]
    print(f'\n官方技能数量: {count}')

    # 检查是否有内置技能
    result = conn.execute(text("SELECT COUNT(*) FROM skills WHERE is_builtin = 1"))
    count = result.fetchone()[0]
    print(f'内置技能数量: {count}')
