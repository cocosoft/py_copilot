import sqlite3
import os

# 数据库路径
db_path = 'backend/py_copilot.db'

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

print(f"连接到数据库: {db_path}")

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看所有表
print("\n数据库中的表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

# 查看技能相关表的数据
print("\n技能相关表数据:")

# 检查技能表
skill_tables = ['skills', 'skill_metadata', 'skill_versions']
for table in skill_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"\n表 {table}: {count} 条记录")
        
        # 如果有数据，查看前5条
        if count > 0:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"列: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
            
            cursor.execute(f"SELECT * FROM {table} LIMIT 5;")
            rows = cursor.fetchall()
            for i, row in enumerate(rows):
                print(f"记录 {i+1}: {row[:3]}...")
    except sqlite3.OperationalError as e:
        print(f"表 {table} 不存在: {e}")

# 关闭连接
conn.close()
print("\n数据库检查完成")
