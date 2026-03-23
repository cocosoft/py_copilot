"""
使用 force 参数强制重新处理文档
"""

import requests
import time

API_URL = "http://localhost:8009/api/v1"


def reprocess_document(doc_id: int):
    """强制重新处理文档"""

    print("=" * 70)
    print("强制重新处理文档")
    print("=" * 70)

    # 1. 先检查当前状态
    print(f"\n[1] 检查文档 {doc_id} 当前状态...")
    resp = requests.get(f"{API_URL}/knowledge/documents/{doc_id}", timeout=10)
    if resp.status_code != 200:
        print(f"✗ 获取文档失败: {resp.status_code}")
        return

    doc = resp.json()
    print(f"  标题: {doc.get('title')}")
    print(f"  当前状态: {doc.get('document_metadata', {}).get('processing_status', 'unknown')}")

    # 2. 触发强制重新处理
    print(f"\n[2] 触发强制重新处理...")
    resp = requests.post(
        f"{API_URL}/knowledge/documents/{doc_id}/process?force=true",
        timeout=10
    )
    print(f"  响应: {resp.status_code} - {resp.text[:300]}")

    result = resp.json()
    if result.get('status') == 'queued':
        print(f"  ✓ 文档已进入处理队列")
    elif result.get('status') == 'completed':
        print(f"  ! 文档未被重新处理")
        return 0
    else:
        print(f"  ! 未知状态: {result.get('status')}")
        return -1

    # 3. 等待处理完成
    print(f"\n[3] 等待处理完成...")
    for i in range(120):  # 最多等待10分钟
        time.sleep(5)

        try:
            resp = requests.get(f"{API_URL}/knowledge/documents/{doc_id}", timeout=10)
            if resp.status_code == 200:
                doc = resp.json()
                status = doc.get('document_metadata', {}).get('processing_status', 'unknown')

                if i % 6 == 0:  # 每30秒输出一次
                    print(f"  状态: {status}")

                if status == 'completed':
                    print(f"\n  ✓ 处理完成!")
                    print(f"  向量化率: {doc.get('document_metadata', {}).get('vectorization_rate', 0):.2%}")

                    # 检查分块
                    try:
                        chunks_resp = requests.get(
                            f"{API_URL}/knowledge/documents/{doc_id}/chunks",
                            timeout=30
                        )
                        if chunks_resp.status_code == 200:
                            chunks = chunks_resp.json()
                            print(f"  分块数量: {len(chunks)}")
                            return len(chunks)
                    except Exception as e:
                        print(f"  获取分块失败: {e}")
                    return 0

                if status == 'failed':
                    print(f"\n  ✗ 处理失败")
                    return -1
        except Exception as e:
            print(f"  检查状态失败: {e}")

    print(f"\n  ⚠️ 等待超时")
    return -2


if __name__ == "__main__":
    chunk_count = reprocess_document(102)

    print("\n" + "=" * 70)
    if chunk_count > 0:
        print(f"✅ 成功！文档已重新处理，共有 {chunk_count} 个分块")
        print("现在可以进行实体识别测试了！")
    elif chunk_count == 0:
        print("⚠️ 处理完成，但没有分块")
    else:
        print("✗ 处理失败或超时")
    print("=" * 70)
