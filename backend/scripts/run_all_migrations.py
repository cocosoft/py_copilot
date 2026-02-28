"""
执行所有数据迁移脚本

统一执行能力中心相关的所有数据迁移
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrate_mcp_tools import migrate_mcp_tools
from migrate_search_settings import migrate_search_settings
from migrate_agent_skills import migrate_agent_skills, verify_agent_capabilities


def run_all_migrations():
    """
    执行所有迁移脚本
    """
    print("\n" + "=" * 70)
    print(" 能力中心数据迁移工具 ")
    print("=" * 70)
    print("\n此脚本将执行以下迁移:")
    print("  1. MCP客户端工具迁移")
    print("  2. 搜索设置迁移")
    print("  3. 智能体技能字段迁移")
    print("\n" + "=" * 70)

    # 确认执行
    confirm = input("\n确认执行所有迁移? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("\n已取消迁移")
        return False

    results = []

    # 1. MCP客户端工具迁移
    print("\n" + "=" * 70)
    print(" [1/3] MCP客户端工具迁移 ")
    print("=" * 70)
    try:
        result = migrate_mcp_tools()
        results.append(("MCP客户端工具迁移", result))
    except Exception as e:
        print(f"\nMCP客户端工具迁移失败: {str(e)}")
        results.append(("MCP客户端工具迁移", False))

    # 2. 搜索设置迁移
    print("\n" + "=" * 70)
    print(" [2/3] 搜索设置迁移 ")
    print("=" * 70)
    try:
        result = migrate_search_settings()
        results.append(("搜索设置迁移", result))
    except Exception as e:
        print(f"\n搜索设置迁移失败: {str(e)}")
        results.append(("搜索设置迁移", False))

    # 3. 智能体技能字段迁移
    print("\n" + "=" * 70)
    print(" [3/3] 智能体技能字段迁移 ")
    print("=" * 70)
    try:
        result = migrate_agent_skills()
        results.append(("智能体技能字段迁移", result))
    except Exception as e:
        print(f"\n智能体技能字段迁移失败: {str(e)}")
        results.append(("智能体技能字段迁移", False))

    # 验证
    print("\n" + "=" * 70)
    print(" 验证迁移结果 ")
    print("=" * 70)
    try:
        verify_agent_capabilities()
    except Exception as e:
        print(f"\n验证失败: {str(e)}")

    # 汇总结果
    print("\n" + "=" * 70)
    print(" 迁移结果汇总 ")
    print("=" * 70)

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {status} - {name}")

    print("\n" + "=" * 70)
    print(f" 总计: {success_count}/{total_count} 个迁移成功")
    print("=" * 70)

    return success_count == total_count


if __name__ == "__main__":
    success = run_all_migrations()
    sys.exit(0 if success else 1)
