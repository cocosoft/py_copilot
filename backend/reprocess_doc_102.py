"""
重新处理文档 102
"""
import requests
import time

API_URL = "http://localhost:8010/api/v1"

print("=" * 70)
print("重新处理文档 102 (《三体》)")
print("=" * 70)

# 1. 检查当前状态
print("\n[1] 检查文档当前状态...")
resp = requests.get(f"{API_URL}/knowledge/documents/102", timeout=10)
if resp.status_code == 200:
    doc = resp.json()
    print(f"  标题: {doc.get('title')}")
    print(f"  当前状态: {doc.get('document_metadata', {}).get('processing_status', 'unknown')}")
else:
    print(f"  获取文档失败: {resp.status_code}")

# 2. 触发强制重新处理
print("\n[2] 触发强制重新处理...")
resp = requests.post(f"{API_URL}/knowledge/documents/102/process?force=true", timeout=120)
print(f"  状态码: {resp.status_code}")
print(f"  响应: {resp.text}")

# 3. 等待处理完成并检查分块
print("\n[3] 等待 30 秒后检查分块...")
time.sleep(30)

import sqlite3
conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, document_id, chunk_index, total_chunks, start_pos, end_pos, vector_id, created_at
    FROM document_chunks
    WHERE document_id = 102
    ORDER BY chunk_index
""")

chunks = cursor.fetchall()
print(f"\n  文档 102 的分块数量: {len(chunks)}")
print("  " + "-" * 66)

for chunk in chunks:
    id, doc_id, idx, total, start_pos, end_pos, vector_id, created_at = chunk
    print(f"  分块 {idx}: 位置 {start_pos}-{end_pos}, 向量ID: {vector_id}")

conn.close()

print("\n" + "=" * 70)
print("处理完成!")
print("=" * 70)
