"""轻量级监控系统启动脚本（基于Python）"""
import subprocess
import sys
import os
import time
from pathlib import Path
import socket

def check_port_available(port: int) -> bool:
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def start_monitoring_service():
    """启动监控服务"""
    # 检查端口8005是否可用
    if not check_port_available(8005):
        print("✗ 监控服务端口8005已被占用")
        return None
    
    try:
        # 启动监控服务
        cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.app.api.microservices.monitoring_service:monitoring_app",
            "--host", "localhost",
            "--port", "8005",
            "--workers", "1"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        time.sleep(3)
        
        # 检查服务是否成功启动
        if process.poll() is None:
            print("✓ 监控服务启动成功 (端口: 8005)")
            return process
        else:
            print("✗ 监控服务启动失败")
            return None
            
    except Exception as e:
        print(f"✗ 监控服务启动失败: {e}")
        return None

def start_all_microservices():
    """启动所有微服务（包含监控）"""
    try:
        cmd = [sys.executable, "backend/microservices_start.py"]
        
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✓ 所有微服务启动中...")
        return process
        
    except Exception as e:
        print(f"✗ 微服务启动失败: {e}")
        return None

def test_monitoring_endpoints():
    """测试监控端点"""
    import requests
    import time
    
    base_url = "http://localhost:8005"
    endpoints = [
        "/health",
        "/api/monitoring/metrics/summary",
        "/api/monitoring/system/info"
    ]
    
    print("\n测试监控端点...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✓ {endpoint}: 正常")
            else:
                print(f"✗ {endpoint}: 失败 (状态码: {response.status_code})")
        except Exception as e:
            print(f"✗ {endpoint}: 错误 ({e})")
    
    print("\n监控系统测试完成")

def main():
    """主函数"""
    print("=" * 50)
    print("Py Copilot 轻量级监控系统启动")
    print("=" * 50)
    
    processes = []
    
    # 1. 启动监控服务
    print("\n1. 启动监控服务...")
    monitoring_process = start_monitoring_service()
    if monitoring_process:
        processes.append(("监控服务", monitoring_process))
    
    # 2. 启动所有微服务
    print("\n2. 启动所有微服务...")
    microservices_process = start_all_microservices()
    if microservices_process:
        processes.append(("微服务", microservices_process))
    
    # 3. 等待服务启动
    print("\n3. 等待服务启动...")
    time.sleep(5)
    
    # 4. 测试监控端点
    test_monitoring_endpoints()
    
    # 5. 显示状态信息
    print("\n4. 系统状态:")
    print("-" * 30)
    
    for name, process in processes:
        if process.poll() is None:
            print(f"✓ {name}: 运行中")
        else:
            print(f"✗ {name}: 已停止")
    
    print("\n5. 访问地址:")
    print("-" * 30)
    print("监控服务:   http://localhost:8005")
    print("API网关:    http://localhost:8000")
    print("聊天服务:   http://localhost:8001")
    print("搜索服务:   http://localhost:8002")
    print("文件服务:   http://localhost:8003")
    print("语音服务:   http://localhost:8004")
    
    print("\n6. 监控API:")
    print("-" * 30)
    print("健康检查: http://localhost:8005/health")
    print("性能指标: http://localhost:8005/api/monitoring/metrics/summary")
    print("系统信息: http://localhost:8005/api/monitoring/system/info")
    print("活跃告警: http://localhost:8005/api/monitoring/alerts")
    
    print("\n7. 使用说明:")
    print("-" * 30)
    print("• 监控服务将自动收集所有微服务的性能指标")
    print("• 性能监控中间件会记录每个API请求的响应时间和错误率")
    print("• 系统会监控CPU、内存、磁盘等资源使用情况")
    print("• 监控数据存储在内存中，重启后数据会重置")
    
    print("\n8. 停止系统:")
    print("-" * 30)
    print("按 Ctrl+C 停止所有服务")
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止所有服务...")
        for name, process in processes:
            if process.poll() is None:
                process.terminate()
                print(f"✓ {name}: 已停止")
    
    print("\n监控系统已停止")

if __name__ == "__main__":
    main()