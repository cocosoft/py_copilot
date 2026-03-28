#!/usr/bin/env python3
"""
启动后端服务的辅助脚本
"""

import subprocess
import sys
import os

def start_backend():
    """
    启动后端服务
    """
    # 切换到 backend 目录
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    
    print(f"正在启动后端服务...")
    print(f"工作目录: {backend_dir}")
    
    try:
        # 启动后端服务
        result = subprocess.run(
            [sys.executable, 'main.py'],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\n返回码: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("后端服务启动超时（这是正常的，服务可能已在后台运行）")
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == '__main__':
    start_backend()
