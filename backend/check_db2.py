import sqlite3
conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

# 检查tools表的列
cursor.execute('PRAGMA table_info(tools)')
columns = cursor.fetchall()
print('Tools表列:')
for col in columns:
    print(f'  {col[1]}: {col[2]}')

# 检查tools表数据
cursor.execute('SELECT id, name, display_name, category, is_official, status FROM tools')
tools = cursor.fetchall()
print(f'\nTools表数据 ({len(tools)} 条):')
for tool in tools:
    print(f'  {tool[0]}: {tool[1]} ({tool[2]}) - {tool[3]} - Official:{tool[4]} - {tool[5]}')

# 检查agent_tool_associations表的列
cursor.execute('PRAGMA table_info(agent_tool_associations)')
columns = cursor.fetchall()
print('\nAgent_tool_associations表列:')
for col in columns:
    print(f'  {col[1]}: {col[2]}')

# 检查官方技能数据
cursor.execute('SELECT id, name, display_name, is_official, status FROM skills WHERE is_official = 1')
skills = cursor.fetchall()
print(f'\n官方技能数据 ({len(skills)} 条):')
for skill in skills:
    print(f'  {skill[0]}: {skill[1]} ({skill[2]}) - Official:{skill[3]} - {skill[4]}')

conn.close()
