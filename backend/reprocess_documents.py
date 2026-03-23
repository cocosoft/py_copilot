# -*- coding: utf-8 -*-
"""重新处理失败的文档"""
import sqlite3
import json
import requests
import time

# 后端API地址
BASE_URL = "http://localhost:8007/api/knowledge"

# 需要重新处理的文档ID
doc_ids = [105, 106, 115]

conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

print("=" * 100)
print("重新处理文档")
print("=" * 100)

for doc_id in doc_ids:
    # 获取文档信息
    cursor.execute('SELECT title, document_metadata FROM knowledge_documents WHERE id = ?', (doc_id,))
    doc = cursor.fetchone()
    
    if doc:
        title, metadata = doc
        print(f"\n文档ID: {doc_id} - {title}")
        print("-" * 80)
        
        # 重置文档状态
        if metadata:
            meta = json.loads(metadata)
        else:
            meta = {}
        
        # 清除错误信息和处理状态
        meta['processing_status'] = 'idle'
        meta['error_message'] = None
        meta['retry_count'] = 0
        meta['process_progress'] = 0
        meta['process_stage'] = None
        
        cursor.execute('''
            UPDATE knowledge_documents 
            SET is_vectorized = 0, 
                vector_id = NULL,
                document_metadata = ?,
                updated_at = datetime('now')
            WHERE id = ?
        ''', (json.dumps(meta), doc_id))
        
        conn.commit()
        print(f"  ✅ 文档状态已重置")
        
        # 调用API触发重新处理
        try:
            response = requests.post(f"{BASE_URL}/documents/{doc_id}/vectorize", timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ 重新处理已启动: {result.get('message', '成功')}")
                print(f"     状态: {result.get('status', 'unknown')}")
            else:
                print(f"  ❌ API调用失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ API调用异常: {e}")
    else:
        print(f"\n文档ID: {doc_id} - 未找到")

conn.close()

print("\n" + "=" * 100)
print("重新处理请求已发送，请等待处理完成")
print("=" * 100)
