#!/usr/bin/env python3
"""
模型分类图标映射配置文件
定义模型分类与Font Awesome图标的对应关系
便于维护和扩展
"""

# 模型分类与Font Awesome图标的映射字典
# 基于分类名称和描述，为每个分类分配最合适的图标
CATEGORY_ICON_MAPPING = {
    # ========== 任务类型相关分类 ==========
    "task_type": "fa-tasks",
    "completion": "fa-keyboard",
    "chat": "fa-comments",
    "embedding": "fa-layer-group",
    "code": "fa-code",
    "image": "fa-image",
    "audio": "fa-music",
    "multimodal": "fa-object-group",
    "llm": "fa-comment-dots",  # 大语言模型
    
    # ========== 模型规模相关分类 ==========
    "size": "fa-chart-bar",
    "small": "fa-cube",
    "medium": "fa-cubes",
    "large": "fa-cube",
    "xlarge": "fa-cubes",
    
    # ========== 架构相关分类 ==========
    "architecture": "fa-microchip",
    "tech_type": "fa-microchip",
    "transformer": "fa-cogs",
    "cnn": "fa-project-diagram",
    "rnn": "fa-network-wired",
    "llama": "fa-robot",
    "gpt": "fa-brain",
    
    # ========== 应用领域相关分类 ==========
    "domain": "fa-globe",
    "application": "fa-globe",
    "general": "fa-star",
    "coding": "fa-laptop-code",
    "education": "fa-graduation-cap",
    "business": "fa-briefcase",
    "creative": "fa-palette",
    "research": "fa-flask",
    
    # ========== 其他分类 ==========
    "supplier": "fa-building",
    "capability": "fa-bolt",
    "performance": "fa-tachometer-alt",
    "quality": "fa-award",
}

# 智能匹配关键词字典
KEYWORD_ICON_MAPPING = {
    # 任务相关关键词
    "任务": "fa-tasks",
    "task": "fa-tasks",
    "工作": "fa-tasks",
    
    # 对话相关关键词
    "对话": "fa-comments",
    "聊天": "fa-comments",
    "chat": "fa-comments",
    
    # 代码相关关键词
    "代码": "fa-code",
    "编程": "fa-laptop-code",
    "code": "fa-code",
    
    # 图像相关关键词
    "图像": "fa-image",
    "图片": "fa-image",
    "image": "fa-image",
    
    # 音频相关关键词
    "音频": "fa-music",
    "声音": "fa-music",
    "audio": "fa-music",
    
    # 多模态相关关键词
    "多模态": "fa-object-group",
    "multimodal": "fa-object-group",
    
    # 规模相关关键词
    "规模": "fa-chart-bar",
    "大小": "fa-chart-bar",
    "size": "fa-chart-bar",
    
    # 架构相关关键词
    "架构": "fa-microchip",
    "结构": "fa-microchip",
    "architecture": "fa-microchip",
    
    # 技术相关关键词
    "技术": "fa-microchip",
    "tech": "fa-microchip",
    
    # 通用相关关键词
    "通用": "fa-star",
    "general": "fa-star",
    
    # 教育相关关键词
    "教育": "fa-graduation-cap",
    "学习": "fa-graduation-cap",
    "education": "fa-graduation-cap",
    
    # 商业相关关键词
    "商业": "fa-briefcase",
    "业务": "fa-briefcase",
    "business": "fa-briefcase",
    
    # 创意相关关键词
    "创意": "fa-palette",
    "创作": "fa-palette",
    "creative": "fa-palette",
    
    # 科研相关关键词
    "科研": "fa-flask",
    "研究": "fa-flask",
    "research": "fa-flask",
    
    # 供应商相关关键词
    "供应商": "fa-building",
    "supplier": "fa-building",
    
    # 能力相关关键词
    "能力": "fa-bolt",
    "capability": "fa-bolt",
    
    # 性能相关关键词
    "性能": "fa-tachometer-alt",
    "performance": "fa-tachometer-alt",
    
    # 质量相关关键词
    "质量": "fa-award",
    "quality": "fa-award",
}

def get_icon_for_category(category_name, display_name, description):
    """
    根据分类信息获取最合适的图标
    
    Args:
        category_name: 分类名称（英文）
        display_name: 显示名称（中文）
        description: 分类描述
    
    Returns:
        str: Font Awesome图标类名
    """
    
    # 首先尝试直接匹配分类名称
    if category_name in CATEGORY_ICON_MAPPING:
        return CATEGORY_ICON_MAPPING[category_name]
    
    # 根据显示名称和描述进行智能匹配
    category_info = f"{category_name} {display_name} {description or ''}".lower()
    
    # 遍历关键词映射，找到匹配的关键词
    for keyword, icon in KEYWORD_ICON_MAPPING.items():
        if keyword.lower() in category_info:
            return icon
    
    # 默认图标
    return "fa-tag"

def get_all_icons():
    """获取所有可用的图标映射"""
    return {
        "direct_mapping": CATEGORY_ICON_MAPPING,
        "keyword_mapping": KEYWORD_ICON_MAPPING
    }

if __name__ == "__main__":
    # 测试函数
    test_categories = [
        ("task_type", "任务类型", "不同类型的任务"),
        ("unknown", "未知分类", "这是一个测试分类"),
        ("test", "测试分类", "包含教育关键词的教育分类"),
    ]
    
    print("图标映射测试:")
    for name, display, desc in test_categories:
        icon = get_icon_for_category(name, display, desc)
        print(f"{name} -> {icon}")