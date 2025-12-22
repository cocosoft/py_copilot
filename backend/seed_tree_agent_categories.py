"""树形结构智能体分类种子数据"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.agent_category import AgentCategory


def seed_tree_categories():
    """导入树形结构的智能体分类数据"""
    db = SessionLocal()
    
    try:
        # 定义树形结构的智能体分类数据
        # 第一级：主要分类
        tree_categories = [
            # 1. 对话交流类（根分类）
            {
                "name": "对话交流助手",
                "logo": "💬",
                "is_system": True,
                "children": [
                    {
                        "name": "日常聊天助手",
                        "logo": "🗨️",
                        "is_system": True
                    },
                    {
                        "name": "情感陪伴助手",
                        "logo": "❤️",
                        "is_system": True
                    }
                ]
            },
            
            # 2. 信息查询类（根分类）
            {
                "name": "信息查询助手",
                "logo": "🔍",
                "is_system": True,
                "children": [
                    {
                        "name": "知识百科助手",
                        "logo": "📚",
                        "is_system": True
                    },
                    {
                        "name": "实时信息助手",
                        "logo": "📰",
                        "is_system": True
                    }
                ]
            },
            
            # 3. 任务处理类（根分类）
            {
                "name": "任务处理助手",
                "logo": "✅",
                "is_system": True,
                "children": [
                    {
                        "name": "文件管理助手",
                        "logo": "📁",
                        "is_system": True
                    },
                    {
                        "name": "系统操作助手",
                        "logo": "⚙️",
                        "is_system": True
                    }
                ]
            },
            
            # 4. 创作辅助类（根分类）
            {
                "name": "创作辅助助手",
                "logo": "✍️",
                "is_system": True,
                "children": [
                    {
                        "name": "写作助手",
                        "logo": "📝",
                        "is_system": True
                    },
                    {
                        "name": "创意生成助手",
                        "logo": "💡",
                        "is_system": True
                    }
                ]
            },
            
            # 5. 学习辅导类（根分类）
            {
                "name": "学习辅导助手",
                "logo": "🎓",
                "is_system": True,
                "children": [
                    {
                        "name": "学习助手",
                        "logo": "📖",
                        "is_system": True
                    },
                    {
                        "name": "解题助手",
                        "logo": "🧮",
                        "is_system": True
                    }
                ]
            },
            
            # 6. 娱乐休闲类（根分类）
            {
                "name": "娱乐休闲助手",
                "logo": "🎮",
                "is_system": True,
                "children": [
                    {
                        "name": "游戏娱乐助手",
                        "logo": "🎯",
                        "is_system": True
                    },
                    {
                        "name": "休闲娱乐助手",
                        "logo": "🎭",
                        "is_system": True
                    }
                ]
            },
            
            # 7. 专业工具类（根分类）
            {
                "name": "专业工具助手",
                "logo": "🔧",
                "is_system": True,
                "children": [
                    {
                        "name": "编程助手",
                        "logo": "💻",
                        "is_system": True
                    },
                    {
                        "name": "数据分析助手",
                        "logo": "📊",
                        "is_system": True
                    }
                ]
            }
        ]
        
        print("开始导入树形结构的智能体分类数据...")
        
        # 导入数据
        for root_category_data in tree_categories:
            # 创建根分类
            children_data = root_category_data.pop("children", [])
            
            root_category = AgentCategory(**root_category_data)
            db.add(root_category)
            db.flush()  # 获取根分类的ID
            
            print(f"✅ 创建根分类: {root_category.name}")
            
            # 创建子分类
            for child_data in children_data:
                child_data["parent_id"] = root_category.id
                child_category = AgentCategory(**child_data)
                db.add(child_category)
                print(f"  └─ 创建子分类: {child_category.name}")
        
        db.commit()
        print(f"✅ 成功导入 {len(tree_categories)} 个根分类和 {sum(len(cat.get('children', [])) for cat in tree_categories)} 个子分类")
        
        # 验证数据
        root_count = db.query(AgentCategory).filter(AgentCategory.parent_id.is_(None)).count()
        total_count = db.query(AgentCategory).count()
        
        print(f"📊 数据统计:")
        print(f"   - 根分类数量: {root_count}")
        print(f"   - 总分类数量: {total_count}")
        print(f"   - 子分类数量: {total_count - root_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 导入数据时出错: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_tree_categories()