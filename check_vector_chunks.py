"""
检查向量片段数据
"""
import requests
import json

def check_vector_chunks():
    # 1. 获取文档列表
    print('=== 获取文档列表 ===')
    response = requests.get('http://localhost:5173/api/v1/knowledge/documents?skip=0&limit=5')
    if response.status_code == 200:
        docs = response.json().get('documents', [])
        print(f'找到 {len(docs)} 个文档')
        for doc in docs[:3]:
            print(f"  文档ID: {doc['id']}, 标题: {doc['title']}, 已向量化: {doc['is_vectorized']}")
            
        # 2. 检查第一个已向量化文档的向量片段
        vectorized_docs = [d for d in docs if d['is_vectorized']]
        if vectorized_docs:
            doc_id = vectorized_docs[0]['id']
            print(f"\n=== 检查文档 {doc_id} 的向量片段 ===")
            chunks_response = requests.get(f'http://localhost:5173/api/v1/knowledge/documents/{doc_id}/chunks')
            if chunks_response.status_code == 200:
                chunks = chunks_response.json()
                print(f'找到 {len(chunks)} 个向量片段')
                if chunks:
                    print(f"  第一个片段ID: {chunks[0].get('id', 'N/A')}")
                    print(f"  内容预览: {chunks[0].get('content', '')[:100]}...")
            else:
                print(f'获取向量片段失败: {chunks_response.status_code}')
                print(chunks_response.text)
        else:
            print('\n没有找到已向量化文档')
    else:
        print(f'获取文档列表失败: {response.status_code}')

if __name__ == "__main__":
    check_vector_chunks()
