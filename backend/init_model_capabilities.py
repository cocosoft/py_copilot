#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型能力初始化脚本
用于初始化模型能力数据，包括标准AI能力
"""

import json
from app.core.database import SessionLocal
from app.models.model_capability import ModelCapability


def init_model_capabilities():
    """初始化模型能力数据"""
    # 数据库会话
    db = SessionLocal()
    
    try:
        print("开始初始化模型能力数据...")
        
        # 检查是否已存在能力数据
        existing_capabilities = db.query(ModelCapability).count()
        if existing_capabilities > 0:
            print(f"数据库中已存在 {existing_capabilities} 个能力，跳过初始化。")
            return
        
        # 定义初始能力数据
        capabilities_data = [
            # NLP领域能力
            {
                "name": "text_generation",
                "display_name": "文本生成",
                "description": "生成自然语言文本，包括对话、文章、代码等",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "text_summarization",
                "display_name": "文本摘要",
                "description": "将长文本压缩为简洁的摘要",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "text_classification",
                "display_name": "文本分类",
                "description": "将文本分类到预定义的类别中",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "sentiment_analysis",
                "display_name": "情感分析",
                "description": "分析文本的情感倾向（正面、负面、中性）",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text", "numeric"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "translation",
                "display_name": "翻译",
                "description": "将文本从一种语言翻译到另一种语言",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "question_answering",
                "display_name": "问答",
                "description": "回答基于给定文本的问题",
                "capability_type": "standard",
                "input_types": json.dumps(["text", "text"]),
                "output_types": json.dumps(["text"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "code_generation",
                "display_name": "代码生成",
                "description": "根据自然语言描述生成代码",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text"]),
                "domain": "nlp",
                "is_active": True
            },
            {
                "name": "text_embedding",
                "display_name": "文本嵌入",
                "description": "将文本转换为向量表示",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["vector"]),
                "domain": "nlp",
                "is_active": True
            },
            
            # 计算机视觉领域能力
            {
                "name": "image_generation",
                "display_name": "图像生成",
                "description": "根据文本描述生成图像",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["image"]),
                "domain": "cv",
                "is_active": True
            },
            {
                "name": "image_classification",
                "display_name": "图像分类",
                "description": "将图像分类到预定义的类别中",
                "capability_type": "standard",
                "input_types": json.dumps(["image"]),
                "output_types": json.dumps(["text"]),
                "domain": "cv",
                "is_active": True
            },
            {
                "name": "object_detection",
                "display_name": "目标检测",
                "description": "识别图像中的对象及其位置",
                "capability_type": "standard",
                "input_types": json.dumps(["image"]),
                "output_types": json.dumps(["text", "bounding_box"]),
                "domain": "cv",
                "is_active": True
            },
            {
                "name": "image_segmentation",
                "display_name": "图像分割",
                "description": "将图像分割为不同的区域或对象",
                "capability_type": "standard",
                "input_types": json.dumps(["image"]),
                "output_types": json.dumps(["mask"]),
                "domain": "cv",
                "is_active": True
            },
            {
                "name": "image_captioning",
                "display_name": "图像描述",
                "description": "为图像生成自然语言描述",
                "capability_type": "standard",
                "input_types": json.dumps(["image"]),
                "output_types": json.dumps(["text"]),
                "domain": "cv",
                "is_active": True
            },
            
            # 音频领域能力
            {
                "name": "speech_recognition",
                "display_name": "语音识别",
                "description": "将语音转换为文本",
                "capability_type": "standard",
                "input_types": json.dumps(["audio"]),
                "output_types": json.dumps(["text"]),
                "domain": "audio",
                "is_active": True
            },
            {
                "name": "text_to_speech",
                "display_name": "文本转语音",
                "description": "将文本转换为语音",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["audio"]),
                "domain": "audio",
                "is_active": True
            },
            {
                "name": "audio_classification",
                "display_name": "音频分类",
                "description": "将音频分类到预定义的类别中",
                "capability_type": "standard",
                "input_types": json.dumps(["audio"]),
                "output_types": json.dumps(["text"]),
                "domain": "audio",
                "is_active": True
            },
            
            # 多模态领域能力
            {
                "name": "multimodal_understanding",
                "display_name": "多模态理解",
                "description": "理解包含文本、图像、音频等多种模态的内容",
                "capability_type": "standard",
                "input_types": json.dumps(["text", "image", "audio"]),
                "output_types": json.dumps(["text"]),
                "domain": "multimodal",
                "is_active": True
            },
            {
                "name": "multimodal_generation",
                "display_name": "多模态生成",
                "description": "生成包含多种模态的内容",
                "capability_type": "standard",
                "input_types": json.dumps(["text"]),
                "output_types": json.dumps(["text", "image", "audio"]),
                "domain": "multimodal",
                "is_active": True
            }
        ]
        
        # 创建能力数据
        created_capabilities = []
        for capability_data in capabilities_data:
            capability = ModelCapability(**capability_data)
            db.add(capability)
            created_capabilities.append(capability)
            print(f"创建能力: {capability.display_name} ({capability.name})")
        
        # 提交事务
        db.commit()
        print(f"\n✅ 模型能力初始化完成！")
        print(f"   创建了 {len(created_capabilities)} 个模型能力")
        
    except Exception as e:
        print(f"\n❌ 初始化模型能力时出错: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_model_capabilities()
