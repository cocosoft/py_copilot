"""
添加话题标题生成参数模板迁移脚本
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.parameter_template import ParameterTemplate, ModelParameter

def add_topic_title_parameter_template():
    """添加话题标题生成参数模板"""
    db: Session = SessionLocal()
    
    try:
        existing = db.query(ParameterTemplate).filter(
            ParameterTemplate.name == 'topic_title_generation'
        ).first()
        
        if existing:
            print("参数模板已存在")
            return
        
        template = ParameterTemplate(
            name='topic_title_generation',
            description='话题标题生成专用参数模板',
            is_default=False,
            is_active=True
        )
        
        db.add(template)
        db.flush()
        
        parameters_data = [
            {
                "parameter_name": "temperature",
                "parameter_value": "0.3",
                "parameter_type": "float",
                "description": "低温度值，确保标题生成的一致性和准确性",
                "is_default": True
            },
            {
                "parameter_name": "max_tokens",
                "parameter_value": "50",
                "parameter_type": "integer",
                "description": "限制生成标题的最大长度",
                "is_default": True
            },
            {
                "parameter_name": "top_p",
                "parameter_value": "0.9",
                "parameter_type": "float",
                "description": "核采样参数，控制生成多样性",
                "is_default": True
            },
            {
                "parameter_name": "frequency_penalty",
                "parameter_value": "0.5",
                "parameter_type": "float",
                "description": "频率惩罚，避免重复词汇",
                "is_default": True
            }
        ]
        
        for param_data in parameters_data:
            parameter = ModelParameter(
                template_id=template.id,
                **param_data
            )
            db.add(parameter)
            print(f"添加参数: {param_data['parameter_name']}")
        
        db.commit()
        print("\n话题标题生成参数模板添加完成！")
        
    except Exception as e:
        db.rollback()
        print(f"添加参数模板失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_topic_title_parameter_template()
