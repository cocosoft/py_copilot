#!/usr/bin/env python3
"""
添加常用 MCP 服务器和客户端配置
"""

import sqlite3
import json
import os

def seed_mcp_configs():
    db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 清空现有配置
    cursor.execute('DELETE FROM mcp_server_configs')
    cursor.execute('DELETE FROM mcp_client_configs')

    # 常用 MCP 服务端配置
    servers = [
        {
            'name': '本地 MCP 服务端',
            'description': '本地运行的 MCP 服务端，用于测试和开发',
            'transport': 'sse',
            'host': '127.0.0.1',
            'port': 8008,
            'enabled': 1,
            'auth_type': 'none',
            'auth_config': None,
            'exposed_modules': json.dumps(['tools', 'skills', 'knowledge', 'memory'])
        },
        {
            'name': '本地 Stdio 服务端',
            'description': '通过标准输入输出通信的 MCP 服务端',
            'transport': 'stdio',
            'host': '127.0.0.1',
            'port': 8009,
            'enabled': 0,
            'auth_type': 'none',
            'auth_config': None,
            'exposed_modules': json.dumps(['tools'])
        }
    ]

    # 常用 MCP 客户端配置
    clients = [
        {
            'name': 'GitHub MCP 服务',
            'description': '连接 GitHub MCP 服务，提供代码搜索、仓库管理等功能',
            'transport': 'sse',
            'connection_url': 'http://localhost:3001/sse',
            'command': None,
            'enabled': 1,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'token'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': '文件系统 MCP 服务',
            'description': '本地文件系统 MCP 服务，提供文件读写、目录浏览等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-filesystem /home/user/documents',
            'enabled': 1,
            'auto_connect': 1,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'SQLite MCP 服务',
            'description': 'SQLite 数据库 MCP 服务，提供数据库查询和管理功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-sqlite /path/to/database.db',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Brave 搜索 MCP 服务',
            'description': 'Brave 搜索引擎 MCP 服务，提供网络搜索功能',
            'transport': 'sse',
            'connection_url': 'http://localhost:3002/sse',
            'command': None,
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'api_key'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'PostgreSQL MCP 服务',
            'description': 'PostgreSQL 数据库 MCP 服务',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-postgres postgresql://localhost/mydb',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        }
    ]

    # 插入服务端配置
    for server in servers:
        cursor.execute('''
        INSERT INTO mcp_server_configs 
        (user_id, name, description, transport, host, port, enabled, auth_type, auth_config, exposed_modules)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,  # user_id
            server['name'],
            server['description'],
            server['transport'],
            server['host'],
            server['port'],
            server['enabled'],
            server['auth_type'],
            server['auth_config'],
            server['exposed_modules']
        ))

    # 插入客户端配置
    for client in clients:
        cursor.execute('''
        INSERT INTO mcp_client_configs 
        (user_id, name, description, transport, connection_url, command, enabled, auto_connect, 
         auth_config, tool_whitelist, tool_blacklist, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,  # user_id
            client['name'],
            client['description'],
            client['transport'],
            client['connection_url'],
            client['command'],
            client['enabled'],
            client['auto_connect'],
            client['auth_config'],
            client['tool_whitelist'],
            client['tool_blacklist'],
            client['status']
        ))

    conn.commit()
    conn.close()
    print(f'已添加 {len(servers)} 个服务端配置')
    print(f'已添加 {len(clients)} 个客户端配置')
    print('\n常用 MCP 服务配置添加完成！')

if __name__ == '__main__':
    seed_mcp_configs()
