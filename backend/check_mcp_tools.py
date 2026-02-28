#!/usr/bin/env python3
"""检查MCP工具是否正确插入"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings
from sqlalchemy import create_engine, text

def check_mcp_tools():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, name, display_name, tool_type, category, status FROM tools WHERE tool_type='mcp'"
        ))
        rows = result.fetchall()
        print(f'找到 {len(rows)} 个MCP工具:')
        for r in rows:
            print(f'  ID:{r[0]}, 名称:{r[1]}, 显示名:{r[2]}, 类型:{r[3]}, 分类:{r[4]}, 状态:{r[5]}')

if __name__ == '__main__':
    check_mcp_tools()
