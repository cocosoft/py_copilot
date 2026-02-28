"""再次检查所有JSON字段"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

import json
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///py_copilot.db')

# 检查所有表的JSON字段
print("=== 检查skills表的所有JSON字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, tags, official_badge FROM skills"))
    for row in result:
        id, name, tags, badge = row
        # 检查tags
        if tags is not None:
            try:
                json.loads(tags)
            except json.JSONDecodeError as e:
                print(f"ID {id} ({name}): tags INVALID - {repr(tags[:50])} - {e}")
        # 检查official_badge
        if badge is not None:
            try:
                json.loads(badge)
            except json.JSONDecodeError as e:
                print(f"ID {id} ({name}): official_badge INVALID - {repr(badge[:50])} - {e}")

print("\n=== 检查tools表的所有JSON字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, tags, official_badge FROM tools"))
    for row in result:
        id, name, tags, badge = row
        # 检查tags
        if tags is not None:
            try:
                json.loads(tags)
            except json.JSONDecodeError as e:
                print(f"ID {id} ({name}): tags INVALID - {repr(tags[:50])} - {e}")
        # 检查official_badge
        if badge is not None:
            try:
                json.loads(badge)
            except json.JSONDecodeError as e:
                print(f"ID {id} ({name}): official_badge INVALID - {repr(badge[:50])} - {e}")

print("\n检查完成")
