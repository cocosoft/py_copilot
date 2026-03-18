"""
实体识别问题诊断脚本

用于诊断实体识别结果为0的问题
检查项：
1. 文档是否存在
2. 文档内容是否为空
3. 文档是否已处理（向量化）
4. 模型配置是否正确
5. LLM 服务是否可用
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument, KnowledgeBase
from app.services.default_model_cache_service import DefaultModelCacheService
from app.services.llm_service import LLMService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def diagnose_entity_extraction(knowledge_base_name: str = None, document_title: str = None):
    """
    诊断实体提取问题
    
    Args:
        knowledge_base_name: 知识库名称（可选）
        document_title: 文档标题（可选）
    """
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("实体识别问题诊断")
        print("=" * 60)
        
        # 1. 检查知识库
        print("\n【1】检查知识库...")
        knowledge_bases = db.query(KnowledgeBase).all()
        print(f"    找到 {len(knowledge_bases)} 个知识库")
        
        target_kb = None
        for kb in knowledge_bases:
            if knowledge_base_name and knowledge_base_name in kb.name:
                target_kb = kb
                print(f"    ✓ 找到目标知识库: {kb.name} (ID: {kb.id})")
            else:
                print(f"    - {kb.name} (ID: {kb.id})")
        
        if knowledge_base_name and not target_kb:
            print(f"    ✗ 未找到名称包含 '{knowledge_base_name}' 的知识库")
            return
        
        # 2. 检查文档
        print("\n【2】检查文档...")
        query = db.query(KnowledgeDocument)
        if target_kb:
            query = query.filter(KnowledgeDocument.knowledge_base_id == target_kb.id)
        
        documents = query.all()
        print(f"    找到 {len(documents)} 个文档")
        
        target_doc = None
        for doc in documents:
            content_length = len(doc.content) if doc.content else 0
            is_vectorized = "✓ 已处理" if doc.is_vectorized else "✗ 未处理"
            
            if document_title and document_title in doc.title:
                target_doc = doc
                print(f"    ✓ 找到目标文档: {doc.title}")
                print(f"      - ID: {doc.id}")
                print(f"      - 内容长度: {content_length} 字符")
                print(f"      - 处理状态: {is_vectorized}")
            else:
                print(f"    - {doc.title} (内容: {content_length}字符, {is_vectorized})")
        
        if document_title and not target_doc:
            print(f"    ✗ 未找到标题包含 '{document_title}' 的文档")
            return
        
        # 3. 详细检查目标文档
        if target_doc:
            print("\n【3】详细检查目标文档...")
            print(f"    文档ID: {target_doc.id}")
            print(f"    文档标题: {target_doc.title}")
            print(f"    文件类型: {target_doc.file_type}")
            print(f"    知识库ID: {target_doc.knowledge_base_id}")
            print(f"    是否向量化: {target_doc.is_vectorized}")
            
            if target_doc.content:
                print(f"    内容长度: {len(target_doc.content)} 字符")
                print(f"    内容预览(前200字符): {target_doc.content[:200]}...")
            else:
                print("    ✗ 文档内容为空！这是实体识别结果为0的主要原因")
                return
            
            if not target_doc.is_vectorized:
                print("    ✗ 文档未处理（未向量化）！请先在文档管理页面处理文档")
                return
        
        # 4. 检查模型配置
        print("\n【4】检查模型配置...")
        try:
            all_models = DefaultModelCacheService.get_cached_all_models()
            print(f"    可用模型数量: {len(all_models) if all_models else 0}")
            if all_models:
                for model in all_models[:5]:
                    print(f"    - {model.get('model_name', 'N/A')} (ID: {model.get('id')}, model_id: {model.get('model_id')})")
                if len(all_models) > 5:
                    print(f"    ... 还有 {len(all_models) - 5} 个模型")
        except Exception as e:
            print(f"    ✗ 获取模型列表失败: {e}")
        
        # 检查知识库场景的默认模型
        if target_kb:
            scenes = [
                f"knowledge_kb_{target_kb.id}_extraction",
                f"knowledge_kb_{target_kb.id}",
                "knowledge_extraction",
                "knowledge"
            ]
            print(f"\n    检查知识库场景默认模型:")
            for scene in scenes:
                try:
                    model = DefaultModelCacheService.get_scene_default_model(scene)
                    if model:
                        print(f"    ✓ {scene}: {model.get('model_name', 'N/A')}")
                    else:
                        print(f"    - {scene}: 未配置")
                except Exception as e:
                    print(f"    ✗ {scene}: 获取失败 - {e}")
        
        # 5. 测试 LLM 服务
        print("\n【5】测试 LLM 服务...")
        try:
            llm_service = LLMService()
            
            test_prompt = "请回复'测试成功'"
            messages = [{"role": "user", "content": test_prompt}]
            
            print("    发送测试请求...")
            response = llm_service.chat_completion(
                messages=messages,
                model_name=None,
                max_tokens=50,
                temperature=0.1,
                db=db
            )
            
            if response.get('success'):
                generated_text = response.get('generated_text', '')
                print(f"    ✓ LLM 服务正常")
                print(f"    响应: {generated_text[:100]}...")
            else:
                print(f"    ✗ LLM 调用失败: {response.get('error', '未知错误')}")
        except Exception as e:
            print(f"    ✗ LLM 服务异常: {e}")
        
        # 6. 总结诊断结果
        print("\n" + "=" * 60)
        print("诊断总结")
        print("=" * 60)
        
        issues = []
        if target_doc:
            if not target_doc.content:
                issues.append("文档内容为空")
            if not target_doc.is_vectorized:
                issues.append("文档未处理（未向量化）")
        else:
            issues.append("未找到目标文档")
        
        if issues:
            print("发现以下问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n建议解决方案:")
            if "文档内容为空" in issues:
                print("  - 重新上传文档，确保文档包含文本内容")
                print("  - 检查文档解析是否成功")
            if "文档未处理" in issues:
                print("  - 在文档管理页面点击'处理'按钮处理文档")
            if "未找到目标文档" in issues:
                print("  - 确认文档已上传到正确的知识库")
        else:
            print("✓ 未发现明显问题，实体识别应该可以正常工作")
            print("  如果仍然无法提取实体，请检查:")
            print("  1. 后端日志中是否有 LLM 调用错误")
            print("  2. LLM 返回的 JSON 是否格式正确")
            print("  3. 模型是否支持中文实体识别")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="诊断实体识别问题")
    parser.add_argument("--kb", type=str, help="知识库名称（支持模糊匹配）")
    parser.add_argument("--doc", type=str, help="文档标题（支持模糊匹配）")
    
    args = parser.parse_args()
    
    diagnose_entity_extraction(
        knowledge_base_name=args.kb,
        document_title=args.doc
    )
