#!/usr/bin/env python3
"""
技能数据库与目录同步脚本
自动同步数据库中的技能记录与技能目录中的实际文件
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

def sync_skills():
    """同步技能数据库和目录"""
    
    # 数据库路径
    db_path = os.path.join('backend', 'py_copilot.db')
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    # 技能目录路径
    skills_dir = Path('backend/app/skills/skills')
    
    if not skills_dir.exists():
        print(f"错误: 技能目录不存在: {skills_dir}")
        return False
    
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取数据库中的技能列表
    cursor.execute('SELECT id, name, display_name, source, status FROM skills;')
    db_skills = {row[1]: row for row in cursor.fetchall()}
    
    # 获取目录中的技能列表
    dir_skills = {}
    for item in skills_dir.iterdir():
        if item.is_dir():
            skill_json = item / 'skill.json'
            if skill_json.exists():
                try:
                    with open(skill_json, 'r', encoding='utf-8') as f:
                        skill_data = json.load(f)
                    dir_skills[item.name] = skill_data
                except Exception as e:
                    print(f"警告: 无法读取 {skill_json}: {e}")
    
    print(f"数据库中的技能: {len(db_skills)} 个")
    print(f"目录中的技能: {len(dir_skills)} 个")
    
    # 找出需要删除的数据库记录（目录中不存在的技能）
    to_delete = set(db_skills.keys()) - set(dir_skills.keys())
    if to_delete:
        print(f"\n需要删除的数据库记录 ({len(to_delete)} 个):")
        for skill_name in to_delete:
            print(f"  - {skill_name}")
            cursor.execute('DELETE FROM skills WHERE name = ?', (skill_name,))
    
    # 找出需要添加到数据库的技能（数据库中不存在的技能）
    to_add = set(dir_skills.keys()) - set(db_skills.keys())
    if to_add:
        print(f"\n需要添加到数据库的技能 ({len(to_add)} 个):")
        for skill_name in to_add:
            skill_data = dir_skills[skill_name]
            print(f"  - {skill_name}")
            
            # 构建插入语句
            insert_sql = """
            INSERT INTO skills (
                name, display_name, description, version, license, tags,
                source, status, is_system, author, requirements, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 准备数据
            name = skill_name
            display_name = skill_data.get('name', skill_name)
            description = skill_data.get('description', '')
            version = skill_data.get('version', '1.0.0')
            license = skill_data.get('license', 'MIT')
            tags = json.dumps(skill_data.get('tags', []))
            source = 'local'
            status = 'disabled'  # 默认禁用，需要手动启用
            is_system = False
            author = skill_data.get('author', 'Unknown')
            requirements = json.dumps(skill_data.get('dependencies', {}))
            created_at = datetime.now().isoformat()
            
            cursor.execute(insert_sql, (
                name, display_name, description, version, license, tags,
                source, status, is_system, author, requirements, created_at
            ))
    
    # 提交更改
    conn.commit()
    
    # 验证同步结果
    cursor.execute('SELECT COUNT(*) FROM skills;')
    final_count = cursor.fetchone()[0]
    
    print(f"\n同步完成!")
    print(f"最终技能数量: {final_count}")
    print(f"删除记录: {len(to_delete)}")
    print(f"新增记录: {len(to_add)}")
    
    conn.close()
    return True

def check_sync_result():
    """检查同步结果"""
    db_path = os.path.join('backend', 'py_copilot.db')
    skills_dir = Path('backend/app/skills/skills')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取数据库技能
    cursor.execute('SELECT name FROM skills;')
    db_skills = {row[0] for row in cursor.fetchall()}
    
    # 获取目录技能
    dir_skills = {item.name for item in skills_dir.iterdir() if item.is_dir()}
    
    # 检查一致性
    db_only = db_skills - dir_skills
    dir_only = dir_skills - db_skills
    
    print("\n=== 同步结果检查 ===")
    print(f"数据库技能数量: {len(db_skills)}")
    print(f"目录技能数量: {len(dir_skills)}")
    
    if not db_only and not dir_only:
        print("✓ 同步成功! 数据库和目录完全一致")
    else:
        if db_only:
            print(f"⚠️ 数据库中有但目录中缺失: {len(db_only)} 个")
            for skill in db_only:
                print(f"  - {skill}")
        if dir_only:
            print(f"⚠️ 目录中有但数据库中缺失: {len(dir_only)} 个")
            for skill in dir_only:
                print(f"  - {skill}")
    
    conn.close()

if __name__ == "__main__":
    print("开始同步技能数据库和目录...")
    
    if sync_skills():
        check_sync_result()
    else:
        print("同步失败!")