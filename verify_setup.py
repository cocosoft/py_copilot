#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Py Copilot 安装验证脚本

此脚本用于验证项目的基本安装和配置是否正确。
使用前请确保已经按照 README.md 中的说明完成了基本设置。
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    print("检查 Python 版本...")
    version = sys.version_info
    if version < (3, 10):
        print(f"警告: 当前 Python 版本为 {version.major}.{version.minor}，项目推荐使用 Python 3.10 或更高版本")
    else:
        print(f"✓ Python 版本检查通过: {version.major}.{version.minor}.{version.micro}")

def check_env_files():
    """检查环境配置文件"""
    print("\n检查环境配置文件...")
    backend_dir = Path("backend")
    
    # 检查 .env.example 文件
    env_example = backend_dir / ".env.example"
    if env_example.exists():
        print(f"✓ 找到环境变量示例文件: {env_example}")
    else:
        print(f"✗ 未找到环境变量示例文件: {env_example}")
    
    # 检查 .env 文件（应该由用户创建）
    env_file = backend_dir / ".env"
    if env_file.exists():
        print(f"✓ 找到环境变量文件: {env_file}")
        # 检查必需的环境变量是否存在（不检查值，只检查是否有占位符）
        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "HUGGINGFACE_API_KEY"
        ]
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for var in required_vars:
            if var in content:
                # 检查是否有值（不只是注释）
                lines = content.split('\n')
                found = False
                for line in lines:
                    if not line.strip().startswith('#') and var in line and '=' in line:
                        value = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if value and not value.startswith('your-') and not value == "":
                            print(f"  - ✓ {var}: 已配置")
                        else:
                            print(f"  - ⚠ {var}: 可能需要更新默认值")
                        found = True
                        break
                if not found:
                    print(f"  - ✗ {var}: 未找到或被注释")
    else:
        print(f"✗ 未找到环境变量文件: {env_file}")
        print("  请根据 .env.example 创建 .env 文件并配置相应的值")

def check_dependencies():
    """检查依赖安装"""
    print("\n检查依赖...")
    
    # 检查后端依赖文件
    backend_req = Path("backend") / "requirements.txt"
    if backend_req.exists():
        print(f"✓ 找到后端依赖文件: {backend_req}")
        # 检查是否已安装部分关键依赖
        try:
            import fastapi
            import sqlalchemy
            import uvicorn
            print("  - ✓ 关键后端依赖已安装")
        except ImportError:
            print("  - ✗ 关键后端依赖未安装，请运行 'pip install -r backend/requirements.txt'")
    else:
        print(f"✗ 未找到后端依赖文件: {backend_req}")
    
    # 检查前端依赖文件
    frontend_pkg = Path("frontend") / "package.json"
    if frontend_pkg.exists():
        print(f"✓ 找到前端依赖文件: {frontend_pkg}")
        # 简单检查 node_modules 目录是否存在
        node_modules = Path("frontend") / "node_modules"
        if node_modules.exists():
            print("  - ✓ 前端依赖可能已安装")
        else:
            print("  - ✗ 前端依赖未安装，请运行 'cd frontend && npm install'")
    else:
        print(f"✗ 未找到前端依赖文件: {frontend_pkg}")

def check_gitignore():
    """检查 .gitignore 文件"""
    print("\n检查版本控制配置...")
    gitignore = Path(".gitignore")
    if gitignore.exists():
        print(f"✓ 找到 .gitignore 文件: {gitignore}")
        # 检查是否包含关键的忽略项
        with open(gitignore, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_ignores = [
            ".venv", "venv", ".env", "__pycache__", 
            "node_modules", "*.db", "*.sqlite3"
        ]
        
        missing = []
        for item in required_ignores:
            if item not in content:
                missing.append(item)
        
        if missing:
            print(f"  - ⚠ 以下关键项可能应添加到 .gitignore: {', '.join(missing)}")
        else:
            print("  - ✓ 关键忽略项检查通过")
    else:
        print(f"✗ 未找到 .gitignore 文件: {gitignore}")
        print("  建议创建 .gitignore 文件，避免提交不必要的文件")

def display_next_steps():
    """显示下一步操作建议"""
    print("\n=== 后续步骤建议 ===")
    print("1. 确保已正确配置 .env 文件中的所有环境变量")
    print("2. 运行数据库迁移: cd backend && alembic upgrade head")
    print("3. 启动后端服务: cd backend && python main.py")
    print("4. 在另一个终端启动前端服务: cd frontend && npm run dev")
    print("5. 访问 http://localhost:5173 查看应用")
    print("\n更多详细信息，请参考 README.md 和 CONTRIBUTING.md")

def main():
    """主函数"""
    print("=" * 50)
    print("欢迎使用 Py Copilot 安装验证脚本")
    print("=" * 50)
    
    check_python_version()
    check_env_files()
    check_dependencies()
    check_gitignore()
    
    print("\n" + "=" * 50)
    print("验证完成")
    print("=" * 50)
    
    display_next_steps()

if __name__ == "__main__":
    main()