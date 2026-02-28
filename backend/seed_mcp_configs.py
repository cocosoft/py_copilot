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

    # 常用 MCP 客户端配置 - 包含主流市场上常用的MCP服务
    clients = [
        {
            'name': 'GitHub MCP 服务',
            'description': '连接 GitHub MCP 服务，提供代码搜索、仓库管理、Issue管理、Pull Request操作等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-github',
            'enabled': 1,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'token', 'env_var': 'GITHUB_PERSONAL_ACCESS_TOKEN'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': '文件系统 MCP 服务',
            'description': '本地文件系统 MCP 服务，提供文件读写、目录浏览、文件搜索等功能',
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
            'description': 'SQLite 数据库 MCP 服务，提供数据库查询、表管理、数据操作等功能',
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
            'name': 'PostgreSQL MCP 服务',
            'description': 'PostgreSQL 数据库 MCP 服务，提供数据库查询、表管理、数据操作等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-postgres postgresql://localhost/mydb',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Brave 搜索 MCP 服务',
            'description': 'Brave 搜索引擎 MCP 服务，提供网络搜索、图片搜索、新闻搜索等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-brave-search',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'api_key', 'env_var': 'BRAVE_API_KEY'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Fetch MCP 服务',
            'description': '网页获取 MCP 服务，提供网页内容抓取、HTML解析、内容提取等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-fetch',
            'enabled': 1,
            'auto_connect': 1,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Puppeteer MCP 服务',
            'description': '浏览器自动化 MCP 服务，提供网页截图、PDF生成、自动化测试等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-puppeteer',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Slack MCP 服务',
            'description': 'Slack 集成 MCP 服务，提供消息发送、频道管理、用户查询等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-slack',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'token', 'env_var': 'SLACK_BOT_TOKEN'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Google Maps MCP 服务',
            'description': 'Google Maps MCP 服务，提供地理编码、路线规划、地点搜索等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-google-maps',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'api_key', 'env_var': 'GOOGLE_MAPS_API_KEY'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Memory MCP 服务',
            'description': '知识图谱记忆 MCP 服务，提供长期记忆存储、知识检索、关联分析等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-memory',
            'enabled': 1,
            'auto_connect': 1,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Sentry MCP 服务',
            'description': 'Sentry 错误监控 MCP 服务，提供错误追踪、问题管理、项目监控等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-sentry',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'token', 'env_var': 'SENTRY_AUTH_TOKEN'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Redis MCP 服务',
            'description': 'Redis 缓存 MCP 服务，提供键值操作、数据结构操作、缓存管理等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-redis',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'connection_string', 'env_var': 'REDIS_URL'}),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'AWS S3 MCP 服务',
            'description': 'AWS S3 对象存储 MCP 服务，提供文件上传下载、存储桶管理、对象操作等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-aws-s3',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({
                'type': 'aws_credentials',
                'env_vars': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
            }),
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Git MCP 服务',
            'description': 'Git 版本控制 MCP 服务，提供仓库操作、提交管理、分支操作等功能',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-git',
            'enabled': 1,
            'auto_connect': 1,
            'auth_config': None,
            'tool_whitelist': None,
            'tool_blacklist': None,
            'status': 'disconnected'
        },
        {
            'name': 'Command MCP 服务',
            'description': '命令行 MCP 服务，提供系统命令执行、脚本运行、进程管理等功能（谨慎使用）',
            'transport': 'stdio',
            'connection_url': None,
            'command': 'npx -y @modelcontextprotocol/server-command',
            'enabled': 0,
            'auto_connect': 0,
            'auth_config': json.dumps({'type': 'whitelist', 'allowed_commands': ['ls', 'cat', 'echo', 'pwd']}),
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
