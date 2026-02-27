#!/usr/bin/env python3
"""
创建 MCP 相关数据库表
"""

import sqlite3
import os

def create_mcp_tables():
    db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除旧表（如果存在）
    cursor.execute('DROP TABLE IF EXISTS mcp_tools')
    cursor.execute('DROP TABLE IF EXISTS mcp_tool_mappings')
    cursor.execute('DROP TABLE IF EXISTS mcp_client_configs')
    cursor.execute('DROP TABLE IF EXISTS mcp_server_configs')

    # 创建 MCP 服务端配置表
    cursor.execute('''
    CREATE TABLE mcp_server_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        transport VARCHAR(50) DEFAULT 'sse',
        host VARCHAR(255) DEFAULT '127.0.0.1',
        port INTEGER DEFAULT 8008,
        enabled BOOLEAN DEFAULT 1,
        auth_type VARCHAR(50) DEFAULT 'none',
        auth_config TEXT,
        exposed_modules TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建 MCP 客户端配置表
    cursor.execute('''
    CREATE TABLE mcp_client_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        transport VARCHAR(50) DEFAULT 'sse',
        connection_url VARCHAR(500),
        command VARCHAR(500),
        enabled BOOLEAN DEFAULT 1,
        auto_connect BOOLEAN DEFAULT 1,
        auth_config TEXT,
        tool_whitelist TEXT,
        tool_blacklist TEXT,
        last_connected_at TIMESTAMP,
        status VARCHAR(50) DEFAULT 'disconnected',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建 MCP 工具映射表
    cursor.execute('''
    CREATE TABLE mcp_tool_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_config_id INTEGER NOT NULL,
        original_name VARCHAR(255) NOT NULL,
        local_name VARCHAR(255) NOT NULL,
        description TEXT,
        input_schema TEXT,
        enabled BOOLEAN DEFAULT 1,
        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_config_id) REFERENCES mcp_client_configs(id) ON DELETE CASCADE
    )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX idx_mcp_server_configs_user_id ON mcp_server_configs(user_id)')
    cursor.execute('CREATE INDEX idx_mcp_server_configs_enabled ON mcp_server_configs(enabled)')
    cursor.execute('CREATE INDEX idx_mcp_client_configs_user_id ON mcp_client_configs(user_id)')
    cursor.execute('CREATE INDEX idx_mcp_client_configs_enabled ON mcp_client_configs(enabled)')
    cursor.execute('CREATE INDEX idx_mcp_client_configs_status ON mcp_client_configs(status)')
    cursor.execute('CREATE INDEX idx_mcp_tool_mappings_client_id ON mcp_tool_mappings(client_config_id)')
    cursor.execute('CREATE INDEX idx_mcp_tool_mappings_enabled ON mcp_tool_mappings(enabled)')

    # 更新 alembic_version 表
    cursor.execute('DELETE FROM alembic_version')
    cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('003_add_mcp_support')")

    conn.commit()
    conn.close()
    print('MCP 表创建成功')

if __name__ == '__main__':
    create_mcp_tables()
