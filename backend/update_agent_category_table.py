"""更新智能体分类表结构脚本"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.models.agent_category import AgentCategory


def update_table_structure():
    """更新智能体分类表结构"""
    
    try:
        # 直接删除旧表并创建新表（不备份数据，因为我们要重新导入树形结构数据）
        print("正在删除旧表...")
        Base.metadata.drop_all(bind=engine, tables=[AgentCategory.__table__])
        
        print("正在创建新表...")
        Base.metadata.create_all(bind=engine, tables=[AgentCategory.__table__])
        
        print("✅ 智能体分类表结构已更新")
        print("✅ 添加了 parent_id 字段支持树形结构")
        print("✅ 移除了 name 字段的唯一性约束")
        
    except Exception as e:
        print(f"❌ 更新表结构时出错: {e}")
        raise


def main():
    """主函数"""
    print("开始更新智能体分类表结构...")
    update_table_structure()
    print("表结构更新完成！")


if __name__ == "__main__":
    main()