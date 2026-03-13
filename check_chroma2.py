#!/usr/bin/env python3
"""
检查ChromaDB中的向量片段数据 - 使用where过滤
"""
import chromadb
import os

# 初始化ChromaDB
storage_path = os.path.join(os.path.dirname(__file__), "frontend", "public", "knowledges", "chromadb")
storage_path = os.path.normpath(storage_path)
print(f"ChromaDB存储路径: {storage_path}")

client = chromadb.PersistentClient(path=storage_path)

# 检查 documents 集合
collection = client.get_collection("documents")
print(f"\n集合 'documents' 文档数量: {collection.count()}")

# 使用where过滤查询document_id=23
print("\n=== 使用 where={\"document_id\": 23} 查询 ===")
results = collection.get(where={"document_id": 23})
print(f"找到 {len(results.get('ids', []))} 个结果")
for i in range(min(3, len(results.get('ids', [])))):
    print(f"\n结果 {i+1}:")
    print(f"  ID: {results['ids'][i]}")
    print(f"  元数据: {results['metadatas'][i]}")
    print(f"  内容预览: {results['documents'][i][:80]}...")

# 使用where过滤查询document_id=23 (字符串)
print("\n=== 使用 where={\"document_id\": \"23\"} 查询 ===")
results = collection.get(where={"document_id": "23"})
print(f"找到 {len(results.get('ids', []))} 个结果")

# 使用where过滤查询document_id=4
print("\n=== 使用 where={\"document_id\": 4} 查询 ===")
results = collection.get(where={"document_id": 4})
print(f"找到 {len(results.get('ids', []))} 个结果")
for i in range(min(3, len(results.get('ids', [])))):
    print(f"\n结果 {i+1}:")
    print(f"  ID: {results['ids'][i]}")
    print(f"  元数据: {results['metadatas'][i]}")
    print(f"  内容预览: {results['documents'][i][:80]}...")
