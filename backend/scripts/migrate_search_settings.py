"""将搜索设置迁移到工具配置"""

import sys
import os
import json

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
import sqlalchemy as sa


def migrate_search_settings():
    """将搜索设置迁移到网络搜索工具配置"""
    db = SessionLocal()
    
    try:
        # 获取搜索设置（取第一个全局设置）
        result = db.execute(sa.text(
            "SELECT default_search_engine, safe_search FROM search_settings WHERE user_id IS NULL LIMIT 1"
        )).fetchone()
        
        if not result:
            print("未找到全局搜索设置，跳过迁移")
            return
        
        default_engine, safe_search = result
        
        # 查找是否已存在网络搜索工具
        existing = db.execute(sa.text(
            "SELECT id FROM tools WHERE name = 'web_search'"
        )).fetchone()
        
        config = json.dumps({
            'default_engine': default_engine or 'google',
            'safe_search': bool(safe_search) if safe_search is not None else True
        })
        
        if existing:
            # 更新现有工具
            tool_id = existing[0]
            db.execute(sa.text("""
                UPDATE tools 
                SET config = :config, status = 'active', is_active = 1
                WHERE id = :id
            """), {'config': config, 'id': tool_id})
            print(f"更新网络搜索工具 (ID: {tool_id})")
        else:
            # 创建新工具
            result = db.execute(sa.text("""
                INSERT INTO tools (
                    name, display_name, description, category, tool_type,
                    source, is_official, is_builtin, status, is_active,
                    author, version, icon, tags, config
                ) VALUES (
                    'web_search', '网络搜索', '执行网络搜索，获取实时信息',
                    'search', 'official', 'official', 1, 1, 'active', 1,
                    'System', '1.0.0', '🔍', '["search", "web", "official"]', :config
                )
            """), {'config': config})
            print("创建网络搜索工具")
        
        db.commit()
        print(f"✅ 搜索设置已迁移到网络搜索工具")
        print(f"   默认搜索引擎: {default_engine or 'google'}")
        print(f"   安全搜索: {'开启' if safe_search else '关闭'}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始迁移搜索设置到工具配置...")
    migrate_search_settings()
