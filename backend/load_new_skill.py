#!/usr/bin/env python
"""
加载新技能到系统中
"""
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.core.database import get_db
from app.services.skill_service import SkillService
from app.services.skill_loader import SkillLoader

def main():
    """加载新技能"""
    print("加载新技能...")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建技能加载器实例
        skill_loader = SkillLoader()
        
        # 测试直接加载技能文件
        skill_file = os.path.join(current_dir, "app", "skills", "skills", "data-analysis", "SKILL.md")
        print(f"尝试加载技能文件: {skill_file}")
        
        if os.path.exists(skill_file):
            skill_info = skill_loader.parse_skill_file(skill_file)
            if skill_info:
                print("成功解析技能文件:")
                print(f"  名称: {skill_info['metadata']['name']}")
                print(f"  描述: {skill_info['metadata']['description']}")
                
                # 创建技能服务实例
                skill_service = SkillService(db)
                
                # 直接加载单个技能文件
                skill = skill_service.load_skill_from_file(skill_file)
                if skill:
                    print("成功加载技能到数据库:")
                    print(f"  ID: {skill.id}")
                    print(f"  状态: {skill.status}")
                    print(f"  版本: {skill.version}")
                else:
                    print("加载技能到数据库失败")
            else:
                print("解析技能文件失败")
        else:
            print(f"技能文件不存在: {skill_file}")
            
            # 检查目录结构
            skills_dir = os.path.join(current_dir, "app", "skills", "skills")
            print(f"技能目录: {skills_dir}")
            if os.path.exists(skills_dir):
                print("技能目录内容:")
                for item in os.listdir(skills_dir):
                    print(f"  - {item}")
            else:
                print("技能目录不存在")
            
    except Exception as e:
        print(f"加载技能时出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库会话
        db.close()


if __name__ == "__main__":
    main()
