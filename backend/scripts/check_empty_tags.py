"""检查是否有空字符串的tags"""
import sys
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')
sys.path.insert(0, 'e:/PY/CODES/py copilot IV/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///py_copilot.db')
Session = sessionmaker(bind=engine)
session = Session()

print("=== 检查技能表中tags为空字符串的记录 ===")
result = session.execute(text("SELECT id, name, tags FROM skills WHERE tags = '' OR tags IS NULL"))
rows = list(result)
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"  ID: {row[0]}, Name: {row[1]}, tags: {repr(row[2])}")

print("\n=== 检查工具表中tags为空字符串的记录 ===")
result = session.execute(text("SELECT id, name, tags FROM tools WHERE tags = '' OR tags IS NULL"))
rows = list(result)
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"  ID: {row[0]}, Name: {row[1]}, tags: {repr(row[2])}")

# 查看所有不同的tags值
print("\n=== 技能表所有不同的tags值 ===")
result = session.execute(text("SELECT DISTINCT tags FROM skills"))
for row in result:
    print(f"  {repr(row[0])}")

print("\n=== 工具表所有不同的tags值 ===")
result = session.execute(text("SELECT DISTINCT tags FROM tools"))
for row in result:
    print(f"  {repr(row[0])}")

session.close()
