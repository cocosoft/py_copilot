"""检查skills和tools表的所有字段"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

import json
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///py_copilot.db')

# 检查skills表的所有字段
print("=== 检查skills表的所有字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(skills)"))
    columns = [(row[1], row[2]) for row in result]  # (name, type)
    print(f"列: {[c[0] for c in columns]}")
    
    # 获取所有数据
    result = conn.execute(text("SELECT * FROM skills"))
    rows = list(result)
    print(f"\n共 {len(rows)} 条记录")
    
    # 检查每条记录的每个字段
    for row in rows:
        row_dict = dict(zip([c[0] for c in columns], row))
        for col_name, val in row_dict.items():
            if val is None:
                continue
            if isinstance(val, str):
                # 尝试解析为JSON
                try:
                    json.loads(val)
                except json.JSONDecodeError:
                    # 不是有效的JSON，检查是否是空字符串
                    if val.strip() == '':
                        print(f"ID {row_dict.get('id')} ({row_dict.get('name')}): {col_name} 是空字符串")
                    elif val in ['true', 'false', 'null']:
                        pass  # 有效的JSON字面量
                    else:
                        # 可能是普通字符串，不是JSON
                        pass

# 检查tools表的所有字段
print("\n=== 检查tools表的所有字段 ===")
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(tools)"))
    columns = [(row[1], row[2]) for row in result]  # (name, type)
    print(f"列: {[c[0] for c in columns]}")
    
    # 获取所有数据
    result = conn.execute(text("SELECT * FROM tools"))
    rows = list(result)
    print(f"\n共 {len(rows)} 条记录")
    
    # 检查每条记录的每个字段
    for row in rows:
        row_dict = dict(zip([c[0] for c in columns], row))
        for col_name, val in row_dict.items():
            if val is None:
                continue
            if isinstance(val, str):
                # 尝试解析为JSON
                try:
                    json.loads(val)
                except json.JSONDecodeError:
                    # 不是有效的JSON，检查是否是空字符串
                    if val.strip() == '':
                        print(f"ID {row_dict.get('id')} ({row_dict.get('name')}): {col_name} 是空字符串")

print("\n检查完成")
