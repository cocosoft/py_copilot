#!/usr/bin/env python3
"""
模型验证脚本
验证所有模型是否正确下载和加载
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def verify_spacy_model():
    """验证spaCy模型"""
    print("\n[1/4] 验证spaCy中文模型...")
    try:
        import spacy
        nlp = spacy.load("zh_core_web_sm")
        
        # 测试实体识别
        doc = nlp("苹果公司位于美国加州。")
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        print(f"  ✓ spaCy模型加载成功")
        print(f"  ✓ 测试实体识别: {entities}")
        return True
    except Exception as e:
        print(f"  ✗ spaCy模型加载失败: {e}")
        return False


def verify_embedding_model():
    """验证Embedding模型"""
    print("\n[2/4] 验证Embedding模型(BAAI/bge-large-zh-v1.5)...")
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        
        model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
        
        # 测试编码
        test_text = "这是一个测试句子。"
        embedding = model.encode(test_text)
        
        device = "CUDA" if torch.cuda.is_available() else "CPU"
        print(f"  ✓ Embedding模型加载成功")
        print(f"  ✓ 设备: {device}")
        print(f"  ✓ 向量维度: {len(embedding)}")
        return True
    except Exception as e:
        print(f"  ✗ Embedding模型加载失败: {e}")
        return False


def verify_rerank_model():
    """验证重排序模型"""
    print("\n[3/4] 验证重排序模型(BAAI/bge-reranker-large)...")
    try:
        from sentence_transformers import CrossEncoder
        import torch
        
        model = CrossEncoder('BAAI/bge-reranker-large')
        
        # 测试重排序
        query = "测试查询"
        documents = ["相关文档内容", "不相关的内容"]
        scores = model.predict([[query, doc] for doc in documents])
        
        device = "CUDA" if torch.cuda.is_available() else "CPU"
        print(f"  ✓ 重排序模型加载成功")
        print(f"  ✓ 设备: {device}")
        print(f"  ✓ 测试评分: {scores}")
        return True
    except Exception as e:
        print(f"  ✗ 重排序模型加载失败: {e}")
        return False


def verify_services():
    """验证服务集成"""
    print("\n[4/4] 验证服务集成...")
    try:
        from app.services.knowledge.chroma_service import ChromaService
        from app.services.knowledge.rerank_service import RerankService
        from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
        
        # 初始化服务
        chroma_service = ChromaService()
        rerank_service = RerankService()
        text_processor = AdvancedTextProcessor()
        
        # 获取模型信息
        rerank_info = rerank_service.get_model_info()
        entity_info = text_processor.get_entity_extraction_info()
        
        print(f"  ✓ ChromaService初始化成功")
        print(f"  ✓ RerankService初始化成功: {rerank_info}")
        print(f"  ✓ AdvancedTextProcessor初始化成功: {entity_info}")
        return True
    except Exception as e:
        print(f"  ✗ 服务集成验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*60)
    print("模型验证脚本")
    print("="*60)
    
    results = []
    
    # 验证各个模型
    results.append(("spaCy中文模型", verify_spacy_model()))
    results.append(("Embedding模型", verify_embedding_model()))
    results.append(("重排序模型", verify_rerank_model()))
    results.append(("服务集成", verify_services()))
    
    # 打印总结
    print("\n" + "="*60)
    print("验证结果总结")
    print("="*60)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✓ 所有模型验证通过！系统已准备就绪。")
        return 0
    else:
        print("\n✗ 部分模型验证失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
