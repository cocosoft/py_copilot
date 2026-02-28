"""
MCP客户端工具迁移脚本

将现有的MCP客户端配置迁移到能力中心工具表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def migrate_mcp_tools():
    """
    迁移MCP客户端工具到能力中心
    """
    print("=" * 60)
    print("开始迁移MCP客户端工具到能力中心")
    print("=" * 60)

    # 创建数据库连接
    engine = create_engine(settings.database_url)

    try:
        with engine.connect() as conn:
            # 检查mcp_client_configs表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='mcp_client_configs'"
            ))
            if not result.fetchone():
                print("\nMCP客户端配置表不存在，跳过迁移")
                return True

            # 获取所有MCP客户端配置
            result = conn.execute(text("SELECT id, name FROM mcp_client_configs"))
            mcp_configs = result.fetchall()
            print(f"\n找到 {len(mcp_configs)} 个MCP客户端配置")

            # 检查mcp_tool_mappings表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='mcp_tool_mappings'"
            ))
            if not result.fetchone():
                print("MCP工具映射表不存在，跳过迁移")
                return True

            migrated_count = 0
            skipped_count = 0

            for config in mcp_configs:
                config_id = config[0]
                config_name = config[1]
                print(f"\n处理MCP客户端: {config_name} (ID: {config_id})")

                # 获取该客户端的工具映射
                result = conn.execute(text(
                    """SELECT id, local_name, original_name, description, 
                              input_schema, enabled 
                       FROM mcp_tool_mappings 
                       WHERE client_config_id = :config_id"""
                ), {"config_id": config_id})
                tool_mappings = result.fetchall()

                print(f"  - 找到 {len(tool_mappings)} 个工具映射")

                for mapping in tool_mappings:
                    mapping_id = mapping[0]
                    local_name = mapping[1]
                    original_name = mapping[2]
                    description = mapping[3]
                    input_schema = mapping[4]
                    enabled = mapping[5]

                    # 检查是否已存在同名工具
                    result = conn.execute(text(
                        "SELECT id FROM tools WHERE name = :name"
                    ), {"name": local_name})
                    if result.fetchone():
                        print(f"  - 跳过已存在的工具: {local_name}")
                        skipped_count += 1
                        continue

                    # 创建新的工具记录
                    display_name = local_name.replace('_', ' ').title()
                    desc = description or f"MCP工具: {original_name}"

                    conn.execute(text(
                        """INSERT INTO tools 
                           (name, display_name, description, category, version, icon,
                            source, is_official, is_builtin, tool_type,
                            mcp_client_config_id, mcp_tool_name, status, is_active,
                            allow_disable, allow_edit, parameters_schema)
                           VALUES 
                           (:name, :display_name, :description, 'mcp', '1.0.0', '🔌',
                            'mcp', 0, 0, 'mcp',
                            :mcp_client_config_id, :mcp_tool_name, 
                            :status, :is_active,
                            1, 1, :parameters_schema)"""
                    ), {
                        "name": local_name,
                        "display_name": display_name,
                        "description": desc,
                        "mcp_client_config_id": config_id,
                        "mcp_tool_name": original_name,
                        "status": 'active' if enabled else 'disabled',
                        "is_active": enabled,
                        "parameters_schema": input_schema or '{}'
                    })

                    migrated_count += 1
                    print(f"  - 迁移工具: {local_name} -> {original_name}")

            # 提交事务
            conn.commit()

        print("\n" + "=" * 60)
        print("迁移完成!")
        print(f"  - 迁移工具数: {migrated_count}")
        print(f"  - 跳过工具数: {skipped_count}")
        print(f"  - MCP客户端数: {len(mcp_configs)}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_mcp_tools()
    sys.exit(0 if success else 1)
