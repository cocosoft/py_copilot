import sqlite3

# 连接到数据库
conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

# 查询created_at为None的记录
print('created_at为None的记录:')
cursor.execute('SELECT id, name, supplier_id FROM models WHERE created_at IS NULL')
null_records = cursor.fetchall()
for record in null_records:
    print(f"  ID: {record[0]}, 名称: {record[1]}, 供应商ID: {record[2]}")

# 如果有这样的记录，更新它们的created_at值
if null_records:
    print(f'\n找到 {len(null_records)} 条记录的created_at为None，正在更新...')
    for record in null_records:
        cursor.execute('UPDATE models SET created_at = CURRENT_TIMESTAMP WHERE id = ?', (record[0],))
    conn.commit()
    print('更新完成！')
else:
    print('\n没有找到created_at为None的记录')

conn.close()