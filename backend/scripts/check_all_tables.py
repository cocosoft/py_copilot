"""检查所有表的JSON字段"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

import json
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///py_copilot.db')

# 获取所有表名
print("=== 获取所有表名 ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result]
    print(f"找到 {len(tables)} 个表: {tables}")

# 检查每个表的列
for table in tables:
    print(f"\n=== 检查表: {table} ===")
    with engine.connect() as conn:
        # 获取表结构
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        columns = [(row[1], row[2]) for row in result]  # (name, type)
        
        for col_name, col_type in columns:
            # 检查是否是JSON字段（通过检查数据内容）
            result = conn.execute(text(f"SELECT {col_name} FROM {table} WHERE {col_name} IS NOT NULL LIMIT 5"))
            rows = list(result)
            if not rows:
                continue
            
            # 检查是否有JSON数据
            has_json = False
            for (val,) in rows:
                if val and (val.startswith('[') or val.startswith('{') or val.startswith('"')):
                    has_json = True
                    break
            
            if has_json:
                print(f"\n  列 {col_name} ({col_type}) 可能包含JSON数据:")
                # 检查所有值
                result = conn.execute(text(f"SELECT id, {col_name} FROM {table} WHERE {col_name} IS NOT NULL"))
                for row_id, val in result:
                    if val is None:
                        continue
                    try:
                        json.loads(val)
                    except json.JSONDecodeError as e:
                        print(f"    ID {row_id}: INVALID - {repr(val[:50])} - {e}")

print("\n检查完成")
