"""检查所有JSON字段"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

import json
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///py_copilot.db')

# 检查skills表的tags字段
print("=== 检查skills表的tags字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, tags FROM skills"))
    for row in result:
        tags = row[2]
        if tags is None:
            print(f"ID {row[0]} ({row[1]}): tags is None")
        elif tags == '':
            print(f"ID {row[0]} ({row[1]}): tags is empty string")
        else:
            try:
                json.loads(tags)
                # print(f"ID {row[0]} ({row[1]}): tags OK")
            except json.JSONDecodeError as e:
                print(f"ID {row[0]} ({row[1]}): tags INVALID - {repr(tags[:50])} - {e}")

# 检查tools表的tags字段
print("\n=== 检查tools表的tags字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, tags FROM tools"))
    for row in result:
        tags = row[2]
        if tags is None:
            print(f"ID {row[0]} ({row[1]}): tags is None")
        elif tags == '':
            print(f"ID {row[0]} ({row[1]}): tags is empty string")
        else:
            try:
                json.loads(tags)
                # print(f"ID {row[0]} ({row[1]}): tags OK")
            except json.JSONDecodeError as e:
                print(f"ID {row[0]} ({row[1]}): tags INVALID - {repr(tags[:50])} - {e}")

# 检查skills表的official_badge字段
print("\n=== 检查skills表的official_badge字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, official_badge FROM skills"))
    for row in result:
        badge = row[2]
        if badge is None:
            print(f"ID {row[0]} ({row[1]}): official_badge is None")
        elif badge == '':
            print(f"ID {row[0]} ({row[1]}): official_badge is empty string")
        else:
            try:
                json.loads(badge)
                # print(f"ID {row[0]} ({row[1]}): official_badge OK")
            except json.JSONDecodeError as e:
                print(f"ID {row[0]} ({row[1]}): official_badge INVALID - {repr(badge[:50])} - {e}")

# 检查tools表的official_badge字段
print("\n=== 检查tools表的official_badge字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, official_badge FROM tools"))
    for row in result:
        badge = row[2]
        if badge is None:
            print(f"ID {row[0]} ({row[1]}): official_badge is None")
        elif badge == '':
            print(f"ID {row[0]} ({row[1]}): official_badge is empty string")
        else:
            try:
                json.loads(badge)
                # print(f"ID {row[0]} ({row[1]}): official_badge OK")
            except json.JSONDecodeError as e:
                print(f"ID {row[0]} ({row[1]}): official_badge INVALID - {repr(badge[:50])} - {e}")

print("\n检查完成")
