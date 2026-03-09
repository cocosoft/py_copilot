import sqlite3

conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

# 检查知识库
cursor.execute("SELECT id, name, created_at FROM knowledge_bases")
knowledge_bases = cursor.fetchall()

print("知识库列表:")
for kb in knowledge_bases:
    print(f"  ID: {kb[0]}, 名称: {kb[1]}, 创建时间: {kb[2]}")
    
    # 检查每个知识库的文档数量
    cursor.execute("SELECT COUNT(*) FROM knowledge_documents WHERE knowledge_base_id = ?", (kb[0],))
    doc_count = cursor.fetchone()[0]
    print(f"    文档数量: {doc_count}")

conn.close()
print("\n查询完成！")