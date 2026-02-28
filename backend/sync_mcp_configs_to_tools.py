#!/usr/bin/env python3
"""
将MCP客户端配置同步到工具表

这个脚本将mcp_client_configs表中的配置同步到tools表，
使得这些MCP服务能够在能力中心中显示和管理。
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def sync_mcp_configs_to_tools():
    """
    同步MCP客户端配置到工具表
    """
    print("=" * 60)
    print("开始同步MCP客户端配置到工具表")
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
                print("\nMCP客户端配置表不存在，跳过同步")
                return True

            # 获取所有MCP客户端配置
            result = conn.execute(text(
                "SELECT id, name, description, transport, command, connection_url, enabled, status "
                "FROM mcp_client_configs"
            ))
            mcp_configs = result.fetchall()
            print(f"\n找到 {len(mcp_configs)} 个MCP客户端配置")

            synced_count = 0
            skipped_count = 0
            error_count = 0

            for config in mcp_configs:
                config_id = config[0]
                config_name = config[1]
                description = config[2] or f"MCP服务: {config_name}"
                transport = config[3]
                command = config[4]
                connection_url = config[5]
                enabled = config[6]
                status = config[7]

                # 生成工具名称（使用小写和下划线）
                tool_name = f"mcp_{config_name.lower().replace(' ', '_').replace('-', '_')}"
                # 移除多余的连续下划线
                tool_name = '_'.join(filter(None, tool_name.split('_')))

                print(f"\n处理MCP客户端: {config_name} (ID: {config_id})")
                print(f"  - 工具名称: {tool_name}")

                try:
                    # 检查是否已存在同名工具
                    result = conn.execute(text(
                        "SELECT id FROM tools WHERE name = :name OR (mcp_client_config_id = :config_id)"
                    ), {"name": tool_name, "config_id": config_id})
                    existing = result.fetchone()

                    if existing:
                        print(f"  - 更新已存在的工具: {tool_name}")
                        # 更新现有工具
                        conn.execute(text(
                            """UPDATE tools SET
                                display_name = :display_name,
                                description = :description,
                                is_active = :is_active,
                                status = :status,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id"""
                        ), {
                            "id": existing[0],
                            "display_name": config_name,
                            "description": description,
                            "is_active": enabled,
                            "status": 'active' if enabled else 'disabled'
                        })
                        skipped_count += 1
                    else:
                        print(f"  - 创建新工具: {tool_name}")
                        # 创建新的工具记录
                        conn.execute(text(
                            """INSERT INTO tools
                                (name, display_name, description, category, version, icon,
                                 source, is_official, is_builtin, tool_type,
                                 mcp_client_config_id, status, is_active,
                                 allow_disable, allow_edit, created_at, updated_at)
                                VALUES
                                (:name, :display_name, :description, 'mcp', '1.0.0', '🔌',
                                 'mcp', 0, 0, 'mcp',
                                 :mcp_client_config_id, :status, :is_active,
                                 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
                        ), {
                            "name": tool_name,
                            "display_name": config_name,
                            "description": description,
                            "mcp_client_config_id": config_id,
                            "status": 'active' if enabled else 'disabled',
                            "is_active": enabled
                        })
                        synced_count += 1

                except Exception as e:
                    print(f"  - 错误: {str(e)}")
                    error_count += 1

            # 提交事务
            conn.commit()

        print("\n" + "=" * 60)
        print("同步完成!")
        print(f"  - 新同步工具数: {synced_count}")
        print(f"  - 更新工具数: {skipped_count}")
        print(f"  - 错误数: {error_count}")
        print(f"  - MCP客户端总数: {len(mcp_configs)}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = sync_mcp_configs_to_tools()
    sys.exit(0 if success else 1)
