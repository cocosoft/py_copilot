from app.core.database import get_db
from app.models.default_model import DefaultModel

# 获取数据库会话
db = next(get_db())

try:
    # 检查现有的默认模型配置
    print('Existing default models:')
    default_models = db.query(DefaultModel).all()
    for model in default_models:
        print(f'ID: {model.id}, Scope: {model.scope}, Scene: {model.scene}, Model ID: {model.model_id}, Priority: {model.priority}, Is Active: {model.is_active}')
    
    # 检查是否已存在全局默认模型
    existing_default = db.query(DefaultModel).filter(
        DefaultModel.scope == 'global'
    ).first()
    
    # deepseek-r1:1.5b模型的ID是46
    model_id = 46
    
    if not existing_default:
        # 添加全局默认模型
        new_default = DefaultModel(
            scope='global',
            model_id=model_id,
            priority=1,  # 优先级最高
            is_active=True
        )
        db.add(new_default)
        db.commit()
        print('\nAdded new global default model: deepseek-r1:1.5b (ID: 46)')
    else:
        # 更新现有的全局默认模型
        existing_default.model_id = model_id
        existing_default.priority = 1
        existing_default.is_active = True
        db.commit()
        print('\nUpdated global default model: deepseek-r1:1.5b (ID: 46)')
    
    # 验证更新后的默认模型
    print('\nUpdated default models:')
    updated_defaults = db.query(DefaultModel).all()
    for model in updated_defaults:
        print(f'ID: {model.id}, Scope: {model.scope}, Scene: {model.scene}, Model ID: {model.model_id}, Priority: {model.priority}, Is Active: {model.is_active}')
        
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
