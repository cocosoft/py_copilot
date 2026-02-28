"""调试tags字段"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 直接连接数据库
engine = create_engine('sqlite:///py_copilot.db')
Session = sessionmaker(bind=engine)
session = Session()

print("=== 检查技能表的tags字段 ===")
result = session.execute(text("SELECT id, name, tags FROM skills LIMIT 5"))
for row in result:
    print(f"ID: {row[0]}, Name: {row[1]}")
    print(f"  tags: {repr(row[2])}")
    print(f"  tags type: {type(row[2])}")
    print()

print("\n=== 检查工具表的tags字段 ===")
result = session.execute(text("SELECT id, name, tags FROM tools LIMIT 5"))
for row in result:
    print(f"ID: {row[0]}, Name: {row[1]}")
    print(f"  tags: {repr(row[2])}")
    print(f"  tags type: {type(row[2])}")
    print()

session.close()
print("完成")
