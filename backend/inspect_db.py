import sqlite3
import os

# 数据库文件路径
db_path = r'E:\PY\CODES\py copilot IV\backend\py_copilot.db'

print(f"数据库路径: {db_path}")
print(f"数据库存在: {os.path.exists(db_path)}")
print()

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        print(f"数据库表列表 (共 {len(tables)} 个表):")
        print("-" * 60)

        # 检查关键表
        key_tables = ['users', 'user_settings', 'workspaces', 'knowledge_documents', 'chunks', 'chunk_entities']
        table_names = [t[0] for t in tables]

        for table in sorted(table_names):
            status = ""
            if table in key_tables:
                status = " [关键表]"
            print(f"  - {table}{status}")

        print()
        print("=" * 60)
        print("关键表检查结果:")
        print("=" * 60)

        for key_table in key_tables:
            if key_table in table_names:
                print(f"✅ {key_table} 表存在")
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {key_table}")
                    count = cursor.fetchone()[0]
                    print(f"   记录数量: {count}")
                except Exception as e:
                    print(f"   无法查询记录数: {e}")
            else:
                print(f"❌ {key_table} 表不存在")

        conn.close()
        print()
        print("数据库检查完成!")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
else:
    print("数据库文件不存在!")
