"""修复official_badge字段的数据"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

import json
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///py_copilot.db')

print("=== 修复skills表的official_badge字段 ===")
with engine.connect() as conn:
    # 获取所有有问题的记录
    result = conn.execute(text("SELECT id, name, official_badge FROM skills WHERE official_badge IS NOT NULL"))
    for row in result:
        badge = row[2]
        if badge is None:
            continue
        try:
            json.loads(badge)
            print(f"ID {row[0]} ({row[1]}): official_badge 已经是有效JSON")
        except json.JSONDecodeError:
            # 将字符串包装为JSON
            new_badge = json.dumps(badge)
            conn.execute(text("UPDATE skills SET official_badge = :badge WHERE id = :id"),
                        {"badge": new_badge, "id": row[0]})
            conn.commit()
            print(f"ID {row[0]} ({row[1]}): 修复 official_badge 从 {repr(badge)} 到 {repr(new_badge)}")

print("\n=== 修复tools表的official_badge字段 ===")
with engine.connect() as conn:
    # 获取所有有问题的记录
    result = conn.execute(text("SELECT id, name, official_badge FROM tools WHERE official_badge IS NOT NULL"))
    for row in result:
        badge = row[2]
        if badge is None:
            continue
        try:
            json.loads(badge)
            print(f"ID {row[0]} ({row[1]}): official_badge 已经是有效JSON")
        except json.JSONDecodeError:
            # 将字符串包装为JSON
            new_badge = json.dumps(badge)
            conn.execute(text("UPDATE tools SET official_badge = :badge WHERE id = :id"),
                        {"badge": new_badge, "id": row[0]})
            conn.commit()
            print(f"ID {row[0]} ({row[1]}): 修复 official_badge 从 {repr(badge)} 到 {repr(new_badge)}")

print("\n修复完成")
