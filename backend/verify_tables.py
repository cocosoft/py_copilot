import sqlite3

# 连接到数据库
conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

# 检查新创建的表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name IN ("translation_history", "languages")')
tables = cursor.fetchall()
print('新创建的表:')
for table in tables:
    print(f'  - {table[0]}')
    
    # 检查表结构
    cursor.execute(f'PRAGMA table_info({table[0]})')
    columns = cursor.fetchall()
    print(f'    列结构:')
    for col in columns:
        print(f'      {col[1]} ({col[2]})')
    print()

# 检查语言数据
cursor.execute('SELECT COUNT(*) FROM languages')
lang_count = cursor.fetchone()[0]
print(f'语言表中有 {lang_count} 条记录')

cursor.execute('SELECT code, name, native_name, is_default FROM languages ORDER BY sort_order')
languages = cursor.fetchall()
print('语言数据:')
for lang in languages:
    print(f'  {lang[0]}: {lang[1]} ({lang[2]}) - 默认: {"是" if lang[3] else "否"}')

conn.close()