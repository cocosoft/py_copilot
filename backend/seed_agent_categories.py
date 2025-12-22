"""智能体分类种子数据导入脚本"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.agent_category import AgentCategory
from app.schemas.agent_category import AgentCategoryCreate


def seed_agent_categories():
    """导入智能体分类种子数据"""
    
    # 定义智能体分类数据
    agent_categories = [
        # 1. 对话交流类
        {
            "name": "对话交流助手",
            "logo": "💬",
            "is_system": True,
            "description": "处理日常对话、闲聊和情感交流"
        },
        {
            "name": "专业问答专家", 
            "logo": "🎓",
            "is_system": True,
            "description": "回答技术、学术等专业问题"
        },
        {
            "name": "情感陪伴伙伴",
            "logo": "❤️",
            "is_system": True,
            "description": "提供情感支持和心理陪伴"
        },
        
        # 2. 任务执行类
        {
            "name": "文件管理助手",
            "logo": "📁",
            "is_system": True,
            "description": "文档处理、文件管理和操作"
        },
        {
            "name": "系统控制专家",
            "logo": "⚙️",
            "is_system": True,
            "description": "系统设置、应用启动和管理"
        },
        {
            "name": "自动化脚本助手",
            "logo": "🤖",
            "is_system": True,
            "description": "批量任务处理和自动化脚本"
        },
        
        # 3. 信息处理类
        {
            "name": "文档分析专家",
            "logo": "📊",
            "is_system": True,
            "description": "文档总结、关键信息提取和分析"
        },
        {
            "name": "数据查询助手",
            "logo": "🔍",
            "is_system": True,
            "description": "信息检索、数据查询和分析"
        },
        {
            "name": "内容创作助手",
            "logo": "✍️",
            "is_system": True,
            "description": "写作、代码生成和创意内容创作"
        },
        
        # 4. 学习辅助类
        {
            "name": "知识解答导师",
            "logo": "📚",
            "is_system": True,
            "description": "学习问题解答和知识辅导"
        },
        {
            "name": "编程辅导教练",
            "logo": "💻",
            "is_system": True,
            "description": "编程学习指导和代码辅导"
        },
        {
            "name": "语言学习伙伴",
            "logo": "🌍",
            "is_system": True,
            "description": "外语学习和语言交流辅助"
        },
        
        # 5. 娱乐休闲类
        {
            "name": "游戏娱乐伙伴",
            "logo": "🎮",
            "is_system": True,
            "description": "互动游戏和娱乐活动"
        },
        {
            "name": "创意娱乐助手",
            "logo": "🎭",
            "is_system": True,
            "description": "故事创作、角色扮演和创意娱乐"
        },
        {
            "name": "媒体推荐专家",
            "logo": "🎵",
            "is_system": True,
            "description": "音乐、视频等媒体内容推荐"
        }
    ]
    
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_count = db.query(AgentCategory).count()
        if existing_count > 0:
            print(f"数据库中已有 {existing_count} 个智能体分类，跳过种子数据导入")
            return
        
        # 导入种子数据
        for category_data in agent_categories:
            # 检查是否已存在同名分类
            existing_category = db.query(AgentCategory).filter(
                AgentCategory.name == category_data["name"]
            ).first()
            
            if not existing_category:
                # 创建新的分类
                category = AgentCategory(
                    name=category_data["name"],
                    logo=category_data["logo"],
                    is_system=category_data["is_system"]
                )
                db.add(category)
                print(f"✅ 创建智能体分类: {category_data['name']} ({category_data['logo']})")
            else:
                print(f"⚠️  智能体分类已存在: {category_data['name']}")
        
        db.commit()
        print(f"🎉 成功导入 {len(agent_categories)} 个智能体分类种子数据")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 导入种子数据时出错: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("开始导入智能体分类种子数据...")
    seed_agent_categories()
    print("种子数据导入完成！")


if __name__ == "__main__":
    main()