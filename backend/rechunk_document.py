#!/usr/bin/env python3
"""重新切片文档"""

import re
import json
import sys
sys.path.insert(0, 'e:\\PY\\CODES\\py copilot IV\\backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 连接数据库
engine = create_engine('sqlite:///py_copilot.db')
Session = sessionmaker(bind=engine)

def simple_chunking(text: str, max_chunk_size: int = 1500,
                    min_chunk_size: int = 300, overlap: int = 100) -> list:
    """基于规则的简单分块方法 - 修正版"""

    if not text:
        return []

    if len(text) <= max_chunk_size:
        return [{'text': text, 'start': 0, 'end': len(text)}]

    chunks = []
    position = 0

    while position < len(text):
        # 计算当前块的结束位置
        end_pos = min(position + max_chunk_size, len(text))

        # 如果不是最后一块，尝试在句子边界处分割
        if end_pos < len(text):
            # 向前查找句子结束标记
            search_start = end_pos - 100  # 往回搜索100个字符
            if search_start < position:
                search_start = position

            search_text = text[search_start:end_pos + 100]

            # 查找最后一个句子结束标记
            sentence_ends = []
            for i, char in enumerate(search_text):
                if char in '.!?。！？':
                    actual_pos = search_start + i + 1
                    if actual_pos > position + min_chunk_size:
                        sentence_ends.append(actual_pos)

            if sentence_ends:
                end_pos = sentence_ends[-1]

        # 提取块文本
        chunk_text = text[position:end_pos].strip()

        if chunk_text:
            chunks.append({
                'text': chunk_text,
                'start': position,
                'end': end_pos
            })

        # 移动位置，考虑重叠
        position = end_pos
        if overlap > 0 and position < len(text):
            position = max(position - overlap, position)

    print(f"分块完成，生成 {len(chunks)} 个块")
    return chunks

def rechunk_document(document_id: int = 102):
    """重新切片文档"""

    db = Session()

    try:
        # 1. 获取文档内容
        print("1. 获取文档内容...")
        result = db.execute(text("""
            SELECT id, content, title, knowledge_base_id
            FROM knowledge_documents
            WHERE id = :doc_id
        """), {"doc_id": document_id})
        doc = result.fetchone()

        if not doc:
            print(f"未找到文档 ID {document_id}")
            return False

        content = doc.content
        print(f"   文档标题: {doc.title}")
        print(f"   内容长度: {len(content)} 字符")

        # 2. 删除旧切片
        print("\n2. 删除旧切片...")
        result = db.execute(text("""
            DELETE FROM document_chunks
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        deleted_count = result.rowcount
        print(f"   删除了 {deleted_count} 个旧切片")

        # 3. 删除旧实体
        print("\n3. 删除旧实体...")
        result = db.execute(text("""
            DELETE FROM chunk_entities
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        deleted_entities = result.rowcount
        print(f"   删除了 {deleted_entities} 个旧实体")

        # 4. 重新切片
        print("\n4. 重新切片...")
        chunks = simple_chunking(content, max_chunk_size=1500, min_chunk_size=300, overlap=100)
        print(f"   生成了 {len(chunks)} 个新切片")

        # 5. 保存新切片
        print("\n5. 保存新切片...")
        total_chars = 0
        now = datetime.now().isoformat()

        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data['text']
            start_pos = chunk_data['start']
            end_pos = chunk_data['end']

            # 准备元数据
            metadata = json.dumps({
                'char_count': len(chunk_text),
                'word_count': len(chunk_text.split()),
                'paragraph_count': chunk_text.count('\n\n') + 1
            })

            result = db.execute(text("""
                INSERT INTO document_chunks
                (document_id, chunk_index, chunk_text, start_pos, end_pos,
                 total_chunks, is_vectorized, created_at, chunk_metadata)
                VALUES (:doc_id, :index, :text, :start_pos, :end_pos,
                        :total_chunks, 0, :created_at, :metadata)
            """), {
                "doc_id": document_id,
                "index": i,
                "text": chunk_text,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "total_chunks": len(chunks),
                "created_at": now,
                "metadata": metadata
            })
            total_chars += len(chunk_text)

        # 6. 更新文档信息（只更新存在的字段）
        print("\n6. 更新文档信息...")
        db.execute(text("""
            UPDATE knowledge_documents
            SET updated_at = :updated_at
            WHERE id = :doc_id
        """), {
            "updated_at": now,
            "doc_id": document_id
        })

        db.commit()

        # 7. 显示统计
        print("\n" + "=" * 60)
        print("重新切片完成！")
        print("=" * 60)
        print(f"新切片数量: {len(chunks)}")
        if chunks:
            sizes = [len(c['text']) for c in chunks]
            print(f"平均切片大小: {sum(sizes) // len(sizes)} 字符")
            print(f"最小切片: {min(sizes)} 字符")
            print(f"最大切片: {max(sizes)} 字符")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = rechunk_document(102)
    if success:
        print("\n✓ 重新切片成功！")
    else:
        print("\n✗ 重新切片失败！")
