"""
清除所有文档的向量化及实体数据，并重置文档状态为待处理
"""
import sqlite3
import os
import json

# 数据库文件路径
db_path = r'E:\PY\CODES\py copilot IV\backend\py_copilot.db'

print("=" * 60)
print("开始清理文档数据")
print("=" * 60)

if not os.path.exists(db_path):
    print(f"❌ 数据库文件不存在: {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    # 1. 清除 chunk_entities 表数据
    print("\n[1/6] 清除片段实体数据...")
    if 'chunk_entities' in tables:
        cursor.execute("SELECT COUNT(*) FROM chunk_entities")
        count = cursor.fetchone()[0]
        print(f"   原有片段实体数量: {count}")
        cursor.execute("DELETE FROM chunk_entities")
        conn.commit()
        print(f"   ✅ 已清除所有片段实体数据")
    else:
        print("   ℹ️ chunk_entities 表不存在，跳过")

    # 2. 清除 document_entities 表数据
    print("\n[2/6] 清除文档实体数据...")
    if 'document_entities' in tables:
        cursor.execute("SELECT COUNT(*) FROM document_entities")
        count = cursor.fetchone()[0]
        print(f"   原有文档实体数量: {count}")
        cursor.execute("DELETE FROM document_entities")
        conn.commit()
        print(f"   ✅ 已清除所有文档实体数据")
    else:
        print("   ℹ️ document_entities 表不存在，跳过")

    # 3. 清除知识库级实体数据
    print("\n[3/6] 清除知识库级实体数据...")
    if 'kb_entities' in tables:
        cursor.execute("SELECT COUNT(*) FROM kb_entities")
        count = cursor.fetchone()[0]
        print(f"   原有知识库实体数量: {count}")
        cursor.execute("DELETE FROM kb_entities")
        conn.commit()
        print(f"   ✅ 已清除所有知识库实体数据")
    else:
        print("   ℹ️ kb_entities 表不存在，跳过")

    # 4. 清除 document_chunks 表数据（向量数据）
    print("\n[4/6] 清除文档片段数据...")
    if 'document_chunks' in tables:
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]
        print(f"   原有文档片段数量: {count}")
        cursor.execute("DELETE FROM document_chunks")
        conn.commit()
        print(f"   ✅ 已清除所有文档片段数据")
    else:
        print("   ℹ️ document_chunks 表不存在，跳过")

    # 5. 重置文档向量化状态
    print("\n[5/6] 重置文档向量化状态...")
    if 'knowledge_documents' in tables:
        cursor.execute("SELECT COUNT(*) FROM knowledge_documents")
        count = cursor.fetchone()[0]
        print(f"   文档总数: {count}")

        # 检查文档表有哪些列
        cursor.execute("PRAGMA table_info(knowledge_documents)")
        columns = [col[1] for col in cursor.fetchall()]

        # 重置 is_vectorized 状态
        if 'is_vectorized' in columns:
            cursor.execute("UPDATE knowledge_documents SET is_vectorized = 0 WHERE is_vectorized = 1")
            updated = cursor.rowcount
            print(f"   ✅ 已重置 {updated} 个文档的 is_vectorized 状态")

        # 清空 vector_id
        if 'vector_id' in columns:
            cursor.execute("UPDATE knowledge_documents SET vector_id = NULL WHERE vector_id IS NOT NULL")
            print(f"   ✅ 已清空文档的 vector_id")

        # 清空 content（可选，如果需要重新处理）
        # cursor.execute("UPDATE knowledge_documents SET content = NULL WHERE content IS NOT NULL")

        conn.commit()
    else:
        print("   ❌ knowledge_documents 表不存在")

    # 6. 重置 document_metadata 中的 processing_status
    print("\n[6/6] 重置 document_metadata 中的 processing_status...")
    if 'knowledge_documents' in tables:
        # 获取所有文档的 metadata
        cursor.execute("SELECT id, document_metadata FROM knowledge_documents WHERE document_metadata IS NOT NULL")
        docs = cursor.fetchall()

        reset_count = 0
        for doc_id, metadata_json in docs:
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
                if metadata.get('processing_status') != 'idle':
                    metadata['processing_status'] = 'idle'
                    # 同时清除其他处理相关字段
                    metadata.pop('processing_error', None)
                    metadata.pop('retry_count', None)
                    metadata.pop('chunks_count', None)
                    metadata.pop('entities_count', None)
                    metadata.pop('relationships_count', None)
                    metadata.pop('graph_data_available', None)
                    metadata.pop('vectorization_rate', None)
                    metadata.pop('success_count', None)
                    metadata.pop('total_chunks', None)

                    # 更新数据库
                    cursor.execute(
                        "UPDATE knowledge_documents SET document_metadata = ? WHERE id = ?",
                        (json.dumps(metadata, ensure_ascii=False), doc_id)
                    )
                    reset_count += 1
            except Exception as e:
                print(f"   处理文档 {doc_id} 时出错: {e}")

        conn.commit()
        print(f"   ✅ 已重置 {reset_count} 个文档的 metadata processing_status")

    # 验证结果
    print("\n" + "=" * 60)
    print("清理结果验证")
    print("=" * 60)

    if 'chunk_entities' in tables:
        cursor.execute("SELECT COUNT(*) FROM chunk_entities")
        print(f"片段实体数量: {cursor.fetchone()[0]}")

    if 'document_entities' in tables:
        cursor.execute("SELECT COUNT(*) FROM document_entities")
        print(f"文档实体数量: {cursor.fetchone()[0]}")

    if 'kb_entities' in tables:
        cursor.execute("SELECT COUNT(*) FROM kb_entities")
        print(f"知识库实体数量: {cursor.fetchone()[0]}")

    if 'document_chunks' in tables:
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        print(f"文档片段数量: {cursor.fetchone()[0]}")

    if 'knowledge_documents' in tables:
        cursor.execute("SELECT is_vectorized, COUNT(*) FROM knowledge_documents GROUP BY is_vectorized")
        status_list = cursor.fetchall()
        print("\n文档向量化状态分布:")
        for status, count in status_list:
            status_str = "已向量化" if status == 1 else "未向量化"
            print(f"  {status_str}: {count}")

        # 检查 metadata 中的 processing_status
        cursor.execute("SELECT id, document_metadata FROM knowledge_documents LIMIT 5")
        print("\n前5个文档的 processing_status:")
        for doc_id, metadata_json in cursor.fetchall():
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
                status = metadata.get('processing_status', 'N/A')
                print(f"  文档 {doc_id}: {status}")
            except:
                print(f"  文档 {doc_id}: 解析失败")

    conn.close()

    print("\n" + "=" * 60)
    print("✅ 文档数据清理完成！")
    print("=" * 60)
    print("\n现在您可以测试知识库分层架构的功能了。")
    print("所有文档已重置为未向量化状态，可以重新进行向量化测试。")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
