#!/usr/bin/env python3
"""
清理ChromaDB中的所有向量片段并重置文档状态
"""
import chromadb
import requests
import os

# ChromaDB存储路径
storage_path = os.path.join(os.path.dirname(__file__), "frontend", "public", "knowledges", "chromadb")
storage_path = os.path.normpath(storage_path)

def clear_chroma_collection_direct(collection_name="documents"):
    """直接操作ChromaDB文件清空集合"""
    print(f"\n=== 清空ChromaDB集合: {collection_name} ===")

    try:
        client = chromadb.PersistentClient(path=storage_path)

        # 获取集合
        try:
            collection = client.get_collection(collection_name)
            count_before = collection.count()
            print(f"  当前文档数量: {count_before}")

            # 获取所有文档ID
            if count_before > 0:
                all_results = collection.get()
                all_ids = all_results.get('ids', [])
                print(f"  获取到 {len(all_ids)} 个文档ID")

                # 分批删除（避免一次性删除太多）
                batch_size = 100
                for i in range(0, len(all_ids), batch_size):
                    batch_ids = all_ids[i:i+batch_size]
                    collection.delete(ids=batch_ids)
                    print(f"  已删除 {i+len(batch_ids)}/{len(all_ids)} 个文档")

                count_after = collection.count()
                print(f"✓ 集合 {collection_name} 已清空 (剩余: {count_after})")
                return True
            else:
                print(f"  集合 {collection_name} 已经是空的")
                return True

        except Exception as e:
            print(f"  集合 {collection_name} 不存在或获取失败: {e}")
            return True  # 集合不存在也算成功

    except Exception as e:
        print(f"✗ 清空集合异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_collection(collection_name):
    """删除整个集合"""
    print(f"\n=== 删除ChromaDB集合: {collection_name} ===")

    try:
        client = chromadb.PersistentClient(path=storage_path)

        try:
            client.delete_collection(collection_name)
            print(f"✓ 集合 {collection_name} 已删除")
            return True
        except Exception as e:
            print(f"  集合 {collection_name} 不存在或删除失败: {e}")
            return True

    except Exception as e:
        print(f"✗ 删除集合异常: {e}")
        return False

def reset_document_status_api():
    """通过API重置所有文档状态"""
    print("\n=== 重置所有文档状态为待处理 ===")

    try:
        # 先获取所有文档
        response = requests.get(
            "http://localhost:5173/api/v1/knowledge/documents?skip=0&limit=1000",
            timeout=30
        )

        if response.status_code != 200:
            print(f"✗ 获取文档列表失败: {response.text}")
            return False

        documents = response.json()
        print(f"  获取到 {len(documents)} 个文档")

        # 逐个重置文档状态
        reset_count = 0
        for doc in documents:
            doc_id = doc.get('id')
            if doc_id:
                try:
                    # 更新文档状态
                    update_response = requests.put(
                        f"http://localhost:5173/api/v1/knowledge/documents/{doc_id}",
                        json={
                            "is_vectorized": False,
                            "processing_status": "pending"
                        },
                        timeout=10
                    )
                    if update_response.status_code == 200:
                        reset_count += 1
                        print(f"  已重置文档 {doc_id}: {doc.get('title', 'Unknown')[:30]}...")
                    else:
                        print(f"  重置文档 {doc_id} 失败: {update_response.text}")
                except Exception as e:
                    print(f"  重置文档 {doc_id} 异常: {e}")

        print(f"✓ 成功重置 {reset_count}/{len(documents)} 个文档状态")
        return True

    except Exception as e:
        print(f"✗ 重置文档状态异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("开始清理向量库并重置文档状态")
    print("=" * 60)
    print(f"ChromaDB存储路径: {storage_path}")

    # 1. 删除并重建 documents 集合
    delete_collection("documents")

    # 2. 删除 default_collection 集合
    delete_collection("default_collection")

    # 3. 重置文档状态
    reset_document_status_api()

    print("\n" + "=" * 60)
    print("清理完成!")
    print("=" * 60)
    print("\n所有向量片段已删除，文档状态已重置为待处理")
    print("现在可以重新进行向量化处理了")
