#!/usr/bin/env python3
"""检查数据库中的表"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print('数据库中的表:')
for t in tables:
    print(f'  - {t[0]}')

print(f'\n共 {len(tables)} 个表')

conn.close()
