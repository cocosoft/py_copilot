import sqlite3

conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("数据库中的表:")
for table in sorted(tables):
    print(f"  - {table}")

graph_tables = [t for t in tables if 'graph' in t.lower()]
print(f"\n包含'graph'的表: {graph_tables}")

conn.close()