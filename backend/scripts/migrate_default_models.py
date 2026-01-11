"""基于能力数据重新初始化默认模型配置的迁移脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal, engine
from app.models.default_model import DefaultModel
from app.models.supplier_db import ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.services.capability_model_filter import CapabilityBasedModelFilter


def migrate_default_models():
    """基于能力数据重新初始化默认模型配置"""
    db = SessionLocal()
    
    try:
        print("=== 开始迁移默认模型配置 ===")
        
        # 1. 清理现有的默认模型配置（保留历史数据，只清理无效配置）
        print("1. 清理无效的默认模型配置...")
        
        # 删除模型不存在的默认配置
        invalid_defaults = db.query(DefaultModel).filter(
            ~DefaultModel.model_id.in_(db.query(ModelDB.id))
        ).all()
        
        if invalid_defaults:
            print(f"  删除 {len(invalid_defaults)} 个无效的默认模型配置")
            for invalid in invalid_defaults:
                db.delete(invalid)
        
        # 2. 基于能力筛选器获取适合的模型
        print("2. 基于能力筛选合适的模型...")
        filter_service = CapabilityBasedModelFilter(db)
        
        # 获取chat场景的推荐模型
        chat_models = filter_service.get_models_with_capability_scores("chat")
        if chat_models:
            best_chat_model = chat_models[0]["model"]
            print(f"  Chat场景推荐模型: {best_chat_model.model_name} (匹配度: {chat_models[0]['match_percentage']}%)")
        else:
            # 如果没有符合条件的模型，选择第一个活跃模型
            best_chat_model = db.query(ModelDB).filter(ModelDB.is_active == True).first()
            print(f"  Chat场景使用默认模型: {best_chat_model.model_name if best_chat_model else '无可用模型'}")
        
        # 获取translate场景的推荐模型
        translate_models = filter_service.get_models_with_capability_scores("translate")
        if translate_models:
            best_translate_model = translate_models[0]["model"]
            print(f"  Translate场景推荐模型: {best_translate_model.model_name} (匹配度: {translate_models[0]['match_percentage']}%)")
        else:
            # 如果没有符合条件的模型，选择第一个活跃模型
            best_translate_model = db.query(ModelDB).filter(ModelDB.is_active == True).first()
            print(f"  Translate场景使用默认模型: {best_translate_model.model_name if best_translate_model else '无可用模型'}")
        
        # 3. 设置全局默认模型
        print("3. 设置全局默认模型...")
        
        # 检查是否已存在全局默认模型
        existing_global = db.query(DefaultModel).filter(
            DefaultModel.scope == 'global',
            DefaultModel.scene.is_(None)
        ).first()
        
        if existing_global:
            # 更新现有的全局默认模型
            existing_global.model_id = best_chat_model.id if best_chat_model else None
            existing_global.is_active = True
            print(f"  更新全局默认模型: {best_chat_model.model_name if best_chat_model else '无'}")
        else:
            # 创建新的全局默认模型配置
            if best_chat_model:
                global_default = DefaultModel(
                    scope='global',
                    scene=None,
                    model_id=best_chat_model.id,
                    priority=1,
                    is_active=True
                )
                db.add(global_default)
                print(f"  创建全局默认模型: {best_chat_model.model_name}")
        
        # 4. 设置chat场景默认模型
        print("4. 设置chat场景默认模型...")
        
        existing_chat = db.query(DefaultModel).filter(
            DefaultModel.scope == 'scene',
            DefaultModel.scene == 'chat'
        ).first()
        
        if existing_chat:
            # 更新现有的chat场景默认模型
            existing_chat.model_id = best_chat_model.id if best_chat_model else None
            existing_chat.is_active = True
            print(f"  更新chat场景默认模型: {best_chat_model.model_name if best_chat_model else '无'}")
        else:
            # 创建新的chat场景默认模型配置
            if best_chat_model:
                chat_default = DefaultModel(
                    scope='scene',
                    scene='chat',
                    model_id=best_chat_model.id,
                    priority=1,
                    is_active=True
                )
                db.add(chat_default)
                print(f"  创建chat场景默认模型: {best_chat_model.model_name}")
        
        # 5. 设置translate场景默认模型
        print("5. 设置translate场景默认模型...")
        
        existing_translate = db.query(DefaultModel).filter(
            DefaultModel.scope == 'scene',
            DefaultModel.scene == 'translate'
        ).first()
        
        if existing_translate:
            # 更新现有的translate场景默认模型
            existing_translate.model_id = best_translate_model.id if best_translate_model else None
            existing_translate.is_active = True
            print(f"  更新translate场景默认模型: {best_translate_model.model_name if best_translate_model else '无'}")
        else:
            # 创建新的translate场景默认模型配置
            if best_translate_model:
                translate_default = DefaultModel(
                    scope='scene',
                    scene='translate',
                    model_id=best_translate_model.id,
                    priority=1,
                    is_active=True
                )
                db.add(translate_default)
                print(f"  创建translate场景默认模型: {best_translate_model.model_name}")
        
        # 6. 提交事务
        db.commit()
        print("6. 提交事务完成")
        
        # 7. 验证迁移结果
        print("7. 验证迁移结果...")
        
        default_models = db.query(DefaultModel).all()
        print(f"  当前默认模型配置数量: {len(default_models)}")
        
        for dm in default_models:
            model = db.query(ModelDB).filter(ModelDB.id == dm.model_id).first()
            model_name = model.model_name if model else "未知模型"
            print(f"    - {dm.scope} {dm.scene or '全局'}: {model_name}")
        
        print("=== 迁移完成 ===")
        
    except Exception as e:
        print(f"迁移过程中发生错误: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    migrate_default_models()