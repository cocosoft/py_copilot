#!/usr/bin/env python3
"""
模型分类图标分配脚本
为每个模型分类搜索并分配最合适的Font Awesome图标
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.model_category import ModelCategory

# 模型分类与Font Awesome图标的映射字典
# 基于分类名称和描述，为每个分类分配最合适的图标
CATEGORY_ICON_MAPPING = {
    # 任务类型相关分类
    "task_type": "fa-tasks",
    "completion": "fa-keyboard",
    "chat": "fa-comments",
    "embedding": "fa-layer-group",
    "code": "fa-code",
    "image": "fa-image",
    "audio": "fa-music",
    "multimodal": "fa-object-group",
    
    # 模型规模相关分类
    "size": "fa-chart-bar",
    "small": "fa-cube",
    "medium": "fa-cubes",
    "large": "fa-cube",
    "xlarge": "fa-cubes",
    
    # 架构相关分类
    "architecture": "fa-microchip",
    "transformer": "fa-cogs",
    "cnn": "fa-project-diagram",
    "rnn": "fa-network-wired",
    "llama": "fa-robot",
    "gpt": "fa-brain",
    
    # 应用领域相关分类
    "domain": "fa-globe",
    "general": "fa-star",
    "coding": "fa-laptop-code",
    "education": "fa-graduation-cap",
    "business": "fa-briefcase",
    "creative": "fa-palette",
    "research": "fa-flask",
    
    # 其他分类
    "supplier": "fa-building",
    "capability": "fa-bolt",
    "performance": "fa-tachometer-alt",
    "quality": "fa-award",
}

def get_icon_for_category(category_name, display_name, description):
    """根据分类信息获取最合适的图标"""
    
    # 首先尝试直接匹配分类名称
    if category_name in CATEGORY_ICON_MAPPING:
        return CATEGORY_ICON_MAPPING[category_name]
    
    # 根据显示名称和描述进行智能匹配
    category_info = f"{category_name} {display_name} {description or ''}".lower()
    
    # 智能匹配逻辑
    if any(word in category_info for word in ['任务', 'task', '工作']):
        return "fa-tasks"
    elif any(word in category_info for word in ['对话', '聊天', 'chat']):
        return "fa-comments"
    elif any(word in category_info for word in ['代码', '编程', 'code']):
        return "fa-code"
    elif any(word in category_info for word in ['图像', '图片', 'image']):
        return "fa-image"
    elif any(word in category_info for word in ['音频', '声音', 'audio']):
        return "fa-music"
    elif any(word in category_info for word in ['多模态', 'multimodal']):
        return "fa-object-group"
    elif any(word in category_info for word in ['规模', '大小', 'size']):
        return "fa-chart-bar"
    elif any(word in category_info for word in ['架构', '结构', 'architecture']):
        return "fa-microchip"
    elif any(word in category_info for word in ['transformer']):
        return "fa-cogs"
    elif any(word in category_info for word in ['cnn', '卷积']):
        return "fa-project-diagram"
    elif any(word in category_info for word in ['rnn', '循环']):
        return "fa-network-wired"
    elif any(word in category_info for word in ['llama']):
        return "fa-robot"
    elif any(word in category_info for word in ['gpt']):
        return "fa-brain"
    elif any(word in category_info for word in ['通用', 'general']):
        return "fa-star"
    elif any(word in category_info for word in ['教育', '学习', 'education']):
        return "fa-graduation-cap"
    elif any(word in category_info for word in ['商业', '业务', 'business']):
        return "fa-briefcase"
    elif any(word in category_info for word in ['创意', '创作', 'creative']):
        return "fa-palette"
    elif any(word in category_info for word in ['科研', '研究', 'research']):
        return "fa-flask"
    elif any(word in category_info for word in ['供应商', 'supplier']):
        return "fa-building"
    elif any(word in category_info for word in ['能力', 'capability']):
        return "fa-bolt"
    elif any(word in category_info for word in ['性能', 'performance']):
        return "fa-tachometer-alt"
    elif any(word in category_info for word in ['质量', 'quality']):
        return "fa-award"
    
    # 默认图标
    return "fa-tag"

def assign_icons_to_categories():
    """为所有模型分类分配图标"""
    db = SessionLocal()
    try:
        # 获取所有模型分类
        categories = db.query(ModelCategory).all()
        
        if not categories:
            print("未找到任何模型分类")
            return
        
        print(f"找到 {len(categories)} 个模型分类，开始分配图标...")
        
        updated_count = 0
        for category in categories:
            # 获取适合的图标
            icon_class = get_icon_for_category(
                category.name, 
                category.display_name, 
                category.description
            )
            
            # 构建SVG格式的logo数据
            # 这里我们使用Font Awesome的类名，前端可以直接使用
            logo_data = f"<i class='fas {icon_class}'></i>"
            
            # 更新分类的logo字段
            category.logo = logo_data
            
            print(f"分类 '{category.display_name}' ({category.name}) -> 图标: {icon_class}")
            updated_count += 1
        
        # 提交更改到数据库
        db.commit()
        print(f"\n成功为 {updated_count} 个分类分配了图标")
        
    except Exception as e:
        db.rollback()
        print(f"分配图标时发生错误: {e}")
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("开始为模型分类分配Font Awesome图标...")
    
    try:
        assign_icons_to_categories()
        print("\n图标分配完成！")
        
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()