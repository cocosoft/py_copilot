import sqlite3

# 连接到数据库
conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

# 检查并修复model_categories表中的NULL时间戳
print('检查model_categories表中的NULL时间戳...')

# 检查created_at为NULL的记录
cursor.execute('SELECT id, name FROM model_categories WHERE created_at IS NULL')
null_created_at = cursor.fetchall()

if null_created_at:
    print(f'发现 {len(null_created_at)} 条记录的created_at为NULL，正在修复...')
    for record in null_created_at:
        cursor.execute('UPDATE model_categories SET created_at = CURRENT_TIMESTAMP WHERE id = ?', (record[0],))
    conn.commit()
    print('修复完成！')
else:
    print('没有发现created_at为NULL的记录')

# 检查updated_at为NULL的记录
cursor.execute('SELECT id, name FROM model_categories WHERE updated_at IS NULL')
null_updated_at = cursor.fetchall()

if null_updated_at:
    print(f'发现 {len(null_updated_at)} 条记录的updated_at为NULL，正在修复...')
    for record in null_updated_at:
        cursor.execute('UPDATE model_categories SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (record[0],))
    conn.commit()
    print('修复完成！')
else:
    print('没有发现updated_at为NULL的记录')

# 关闭连接
conn.close()
print('所有修复操作已完成！')
