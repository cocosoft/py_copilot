"""
添加话题标题相关能力迁移脚本
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.model_capability import ModelCapability

def add_topic_title_capabilities():
    """添加话题标题相关能力"""
    db: Session = SessionLocal()
    
    try:
        capabilities_data = [
            {
                "name": "text_summarization",
                "display_name": "文本总结",
                "description": "能够将长文本总结为简洁的摘要",
                "capability_dimension": "generation",
                "capability_type": "standard",
                "domain": "nlp",
                "base_strength": 3,
                "max_strength": 5,
                "input_types": ["text"],
                "output_types": ["text"],
                "is_active": True,
                "is_system": True
            },
            {
                "name": "intent_recognition",
                "display_name": "意图识别",
                "description": "能够识别对话的核心意图和主题",
                "capability_dimension": "understanding",
                "capability_type": "standard",
                "domain": "nlp",
                "base_strength": 3,
                "max_strength": 5,
                "input_types": ["text"],
                "output_types": ["text"],
                "is_active": True,
                "is_system": True
            },
            {
                "name": "keyword_extraction",
                "display_name": "关键词提取",
                "description": "能够从文本中提取关键信息",
                "capability_dimension": "understanding",
                "capability_type": "standard",
                "domain": "nlp",
                "base_strength": 3,
                "max_strength": 5,
                "input_types": ["text"],
                "output_types": ["text"],
                "is_active": True,
                "is_system": True
            },
            {
                "name": "concise_expression",
                "display_name": "简洁表达",
                "description": "能够用简洁准确的语言表达核心内容",
                "capability_dimension": "generation",
                "capability_type": "standard",
                "domain": "nlp",
                "base_strength": 3,
                "max_strength": 5,
                "input_types": ["text"],
                "output_types": ["text"],
                "is_active": True,
                "is_system": True
            }
        ]
        
        for capability_data in capabilities_data:
            existing = db.query(ModelCapability).filter(
                ModelCapability.name == capability_data["name"]
            ).first()
            
            if not existing:
                capability = ModelCapability(**capability_data)
                db.add(capability)
                db.flush()
                print(f"添加能力: {capability_data['display_name']} (ID: {capability.id})")
            else:
                print(f"能力已存在: {capability_data['display_name']} (ID: {existing.id})")
        
        db.commit()
        print("\n话题标题相关能力添加完成！")
        
    except Exception as e:
        db.rollback()
        print(f"添加能力失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_topic_title_capabilities()
