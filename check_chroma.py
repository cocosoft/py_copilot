#!/usr/bin/env python3
"""
检查ChromaDB中的向量片段数据
"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os

# 初始化ChromaDB
storage_path = os.path.join(os.path.dirname(__file__), "frontend", "public", "knowledges", "chromadb")
storage_path = os.path.normpath(storage_path)
print(f"ChromaDB存储路径: {storage_path}")

client = chromadb.PersistentClient(path=storage_path)

# 列出所有集合
print("\n=== 所有集合 ===")
collections = client.list_collections()
for coll in collections:
    print(f"  - {coll.name}")

# 检查 documents 集合
try:
    collection = client.get_collection("documents")
    print(f"\n集合 'documents' 存在")
    print(f"文档数量: {collection.count()}")

    # 获取所有文档
    print("\n=== 获取所有文档（前10个）===")
    all_results = collection.get(limit=10)
    print(f"返回文档数: {len(all_results.get('ids', []))}")

    # 显示文档
    for i in range(len(all_results.get('ids', []))):
        doc_id = all_results['ids'][i]
        metadata = all_results['metadatas'][i] if all_results.get('metadatas') else {}
        document = all_results['documents'][i] if all_results.get('documents') else ""
        print(f"\n文档 {i+1}:")
        print(f"  ID: {doc_id}")
        print(f"  元数据类型: {type(metadata)}")
        print(f"  元数据: {metadata}")
        print(f"  内容预览: {document[:100]}...")

    # 查找包含"三体"的文档
    print("\n=== 搜索包含'三体'的文档 ===")
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name=os.path.join(os.path.dirname(__file__), "backend", "models", "BAAI", "bge-large-zh-v1.5")
    )
    collection_with_embed = client.get_collection("documents", embedding_function=embedding_function)
    search_results = collection_with_embed.query(query_texts=["三体"], n_results=5)
    if search_results.get('ids'):
        for j, doc_id in enumerate(search_results['ids'][0]):
            print(f"\n搜索结果 {j+1}:")
            print(f"  ID: {doc_id}")
            print(f"  距离: {search_results['distances'][0][j] if search_results.get('distances') else 'N/A'}")
            print(f"  元数据: {search_results['metadatas'][0][j] if search_results.get('metadatas') else {}}")
            print(f"  内容预览: {search_results['documents'][0][j][:100] if search_results.get('documents') else 'N/A'}...")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
