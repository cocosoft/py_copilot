#!/usr/bin/env python3
"""
知识图谱LLM化改造验证脚本

验证所有组件是否正常工作：
1. 模型配置验证
2. LLM实体提取器验证
3. LLM文本处理器验证
4. 集成测试验证
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.knowledge.llm_extractor import LLMEntityExtractor, LLMEntityDisambiguator
from app.services.knowledge.llm_text_processor import LLMTextProcessor
from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor


async def verify_model_configuration():
    """验证模型配置"""
    print("\n" + "="*60)
    print("验证1: 模型配置")
    print("="*60)
    
    db = SessionLocal()
    try:
        extractor = LLMEntityExtractor(db)
        model_id = extractor._get_model_for_extraction()
        
        if model_id:
            print(f"✅ 模型配置正常")
            print(f"   使用的模型ID: {model_id}")
            
            # 查询模型详情
            from app.models.supplier_db import ModelDB, SupplierDB
            model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
            if model:
                supplier = db.query(SupplierDB).filter(SupplierDB.id == model.supplier_id).first()
                print(f"   模型名称: {model.model_name}")
                print(f"   供应商: {supplier.name if supplier else '未知'}")
            return True
        else:
            print("⚠️ 未配置场景模型，将使用LLM服务默认模型")
            return True
    except Exception as e:
        print(f"❌ 模型配置验证失败: {e}")
        return False
    finally:
        db.close()


async def verify_llm_extractor():
    """验证LLM实体提取器"""
    print("\n" + "="*60)
    print("验证2: LLM实体提取器")
    print("="*60)
    
    db = SessionLocal()
    try:
        extractor = LLMEntityExtractor(db)
        
        test_text = "张三在阿里巴巴工作，他是人工智能专家。"
        print(f"\n测试文本: {test_text}")
        
        entities, relationships = await extractor.extract_entities_and_relationships(test_text)
        
        print(f"✅ LLM实体提取器工作正常")
        print(f"   提取到 {len(entities)} 个实体")
        print(f"   提取到 {len(relationships)} 个关系")
        
        if entities:
            print("\n   实体示例:")
            for entity in entities[:3]:
                print(f"     - {entity.get('text')} ({entity.get('type')})")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM实体提取器验证失败: {e}")
        return False
    finally:
        db.close()


async def verify_llm_text_processor():
    """验证LLM文本处理器"""
    print("\n" + "="*60)
    print("验证3: LLM文本处理器")
    print("="*60)
    
    db = SessionLocal()
    try:
        processor = LLMTextProcessor(db)
        
        # 测试语义分块
        test_text = "自然语言处理是人工智能的重要分支。它研究如何实现人与计算机之间的有效通信。深度学习在NLP领域取得了突破性进展。"
        print(f"\n测试文本分块...")
        
        chunks = await processor.semantic_chunking(test_text, max_chunk_size=100, min_chunk_size=50)
        print(f"✅ 语义分块工作正常")
        print(f"   分块数量: {len(chunks)}")
        
        # 测试关键词提取
        print("\n测试关键词提取...")
        keywords = await processor.extract_keywords(test_text, top_n=5)
        print(f"✅ 关键词提取工作正常")
        print(f"   关键词数量: {len(keywords)}")
        if keywords:
            print("   关键词示例:")
            for kw in keywords[:3]:
                print(f"     - {kw.get('word')}: {kw.get('weight', 0):.4f}")
        
        # 测试相似度计算
        print("\n测试相似度计算...")
        text1 = "人工智能是计算机科学的一个分支。"
        text2 = "AI是计算机科学的重要领域。"
        similarity = await processor.calculate_similarity(text1, text2)
        print(f"✅ 相似度计算工作正常")
        print(f"   相似度: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM文本处理器验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def verify_advanced_processor():
    """验证高级文本处理器"""
    print("\n" + "="*60)
    print("验证4: 高级文本处理器集成")
    print("="*60)
    
    db = SessionLocal()
    try:
        processor = AdvancedTextProcessor(db)
        
        # 测试实体提取
        test_text = "李四在北京大学学习计算机科学，他的导师是王教授。"
        print(f"\n测试文本: {test_text}")
        
        entities, relationships = await processor.extract_entities_relationships(test_text)
        print(f"✅ 实体提取集成正常")
        print(f"   实体数量: {len(entities)}")
        print(f"   关系数量: {len(relationships)}")
        
        # 测试分块
        long_text = "这是第一段内容。" * 20 + "这是第二段内容。" * 20
        chunks = await processor.semantic_chunking(long_text, max_chunk_size=200, min_chunk_size=100)
        print(f"✅ 语义分块集成正常")
        print(f"   分块数量: {len(chunks)}")
        
        # 测试信息获取
        info = processor.get_entity_extraction_info()
        print(f"✅ 信息获取正常")
        print(f"   LLM提取器可用: {info.get('llm_extractor_available')}")
        print(f"   LLM消歧器可用: {info.get('llm_disambiguator_available')}")
        print(f"   LLM文本处理器可用: {info.get('llm_text_processor_available')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 高级文本处理器验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """主验证函数"""
    print("\n" + "="*60)
    print("知识图谱LLM化改造验证")
    print("="*60)
    print("\n开始验证所有组件...")
    
    results = []
    
    # 验证1: 模型配置
    results.append(("模型配置", await verify_model_configuration()))
    
    # 验证2: LLM实体提取器
    results.append(("LLM实体提取器", await verify_llm_extractor()))
    
    # 验证3: LLM文本处理器
    results.append(("LLM文本处理器", await verify_llm_text_processor()))
    
    # 验证4: 高级文本处理器集成
    results.append(("高级文本处理器集成", await verify_advanced_processor()))
    
    # 打印结果汇总
    print("\n" + "="*60)
    print("验证结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 项验证通过")
    
    if passed_count == total_count:
        print("\n🎉 所有验证通过！知识图谱LLM化改造成功。")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} 项验证失败，请检查配置。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
