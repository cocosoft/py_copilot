"""修复空的JSON字段"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

import json
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///py_copilot.db')

# 修复skills表的artifact_types和execution_flow字段
print("=== 修复skills表的artifact_types和execution_flow字段 ===")
with engine.connect() as conn:
    # 查找空字符串的记录
    result = conn.execute(text("SELECT id, name, artifact_types, execution_flow FROM skills WHERE artifact_types = '' OR execution_flow = ''"))
    for row in result:
        id, name, artifact_types, execution_flow = row
        print(f"ID {id} ({name}):")
        
        if artifact_types == '':
            conn.execute(text("UPDATE skills SET artifact_types = '[]' WHERE id = :id"), {"id": id})
            conn.commit()
            print(f"  修复 artifact_types: '' -> '[]'")
        
        if execution_flow == '':
            conn.execute(text("UPDATE skills SET execution_flow = '{}' WHERE id = :id"), {"id": id})
            conn.commit()
            print(f"  修复 execution_flow: '' -> '{{}}'")

print("\n修复完成")
