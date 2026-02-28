"""调试能力中心API"""
import os
os.chdir('e:/PY/CODES/py copilot IV/backend')

from app.core.database import SessionLocal
from app.models.skill import Skill
from app.models.tool import Tool

print("=== 检查技能表 ===")
db = SessionLocal()
try:
    skills = db.query(Skill).all()
    print(f"找到 {len(skills)} 个技能")

    for skill in skills[:3]:
        print(f"\n技能: {skill.name}")
        print(f"  id: {skill.id}")
        print(f"  tags: {skill.tags} (type: {type(skill.tags)})")
        print(f"  tags raw: {repr(skill.tags)}")
        
    print("\n=== 检查工具表 ===")
    tools = db.query(Tool).all()
    print(f"找到 {len(tools)} 个工具")

    for tool in tools[:3]:
        print(f"\n工具: {tool.name}")
        print(f"  id: {tool.id}")
        print(f"  tags: {tool.tags} (type: {type(tool.tags)})")
        print(f"  tags raw: {repr(tool.tags)}")
finally:
    db.close()

print("\n完成")
