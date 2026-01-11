"""监控系统启动脚本"""
import subprocess
import sys
import os
import time
from pathlib import Path

def check_port_available(port: int) -> bool:
    """检查端口是否可用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def start_prometheus():
    """启动Prometheus"""
    prometheus_dir = Path(__file__).parent / "prometheus"
    prometheus_config = prometheus_dir / "prometheus.yml"
    
    if not prometheus_config.exists():
        print("✗ Prometheus配置文件不存在")
        return None
    
    # 检查端口9090是否可用
    if not check_port_available(9090):
        print("✗ Prometheus端口9090已被占用")
        return None
    
    try:
        # 启动Prometheus
        cmd = [
            "prometheus",
            f"--config.file={prometheus_config}",
            f"--web.listen-address=:9090",
            f"--storage.tsdb.path={prometheus_dir / 'data'}"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=prometheus_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✓ Prometheus启动成功 (端口: 9090)")
        return process
        
    except Exception as e:
        print(f"✗ Prometheus启动失败: {e}")
        return None

def start_grafana():
    """启动Grafana"""
    grafana_dir = Path(__file__).parent / "grafana"
    
    # 检查端口3000是否可用
    if not check_port_available(3000):
        print("✗ Grafana端口3000已被占用")
        return None
    
    try:
        # 启动Grafana（这里假设Grafana已安装）
        cmd = [
            "grafana-server",
            "--homepath=/usr/share/grafana",  # 根据实际安装路径调整
            "--config=/etc/grafana/grafana.ini"  # 根据实际配置路径调整
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✓ Grafana启动成功 (端口: 3000)")
        return process
        
    except Exception as e:
        print(f"✗ Grafana启动失败: {e}")
        print("提示: 请确保Grafana已正确安装")
        return None

def start_node_exporter():
    """启动Node Exporter"""
    # 检查端口9100是否可用
    if not check_port_available(9100):
        print("✗ Node Exporter端口9100已被占用")
        return None
    
    try:
        # 启动Node Exporter
        cmd = ["node_exporter"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✓ Node Exporter启动成功 (端口: 9100)")
        return process
        
    except Exception as e:
        print(f"✗ Node Exporter启动失败: {e}")
        print("提示: 请确保Node Exporter已正确安装")
        return None

def start_redis_exporter():
    """启动Redis Exporter"""
    # 检查端口9121是否可用
    if not check_port_available(9121):
        print("✗ Redis Exporter端口9121已被占用")
        return None
    
    try:
        # 启动Redis Exporter
        cmd = ["redis_exporter"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✓ Redis Exporter启动成功 (端口: 9121)")
        return process
        
    except Exception as e:
        print(f"✗ Redis Exporter启动失败: {e}")
        print("提示: 请确保Redis Exporter已正确安装")
        return None

def main():
    """主函数"""
    print("=" * 50)
    print("Py Copilot 监控系统启动")
    print("=" * 50)
    
    processes = []
    
    # 启动监控组件
    print("\n1. 启动监控组件...")
    
    # 启动Node Exporter（系统指标）
    node_process = start_node_exporter()
    if node_process:
        processes.append(("Node Exporter", node_process))
    
    # 启动Redis Exporter（Redis指标）
    redis_process = start_redis_exporter()
    if redis_process:
        processes.append(("Redis Exporter", redis_process))
    
    # 启动Prometheus（指标收集）
    prometheus_process = start_prometheus()
    if prometheus_process:
        processes.append(("Prometheus", prometheus_process))
    
    # 启动Grafana（可视化）
    grafana_process = start_grafana()
    if grafana_process:
        processes.append(("Grafana", grafana_process))
    
    print("\n2. 监控系统状态:")
    print("-" * 30)
    
    for name, process in processes:
        if process.poll() is None:
            print(f"✓ {name}: 运行中")
        else:
            print(f"✗ {name}: 已停止")
    
    print("\n3. 访问地址:")
    print("-" * 30)
    print("Prometheus: http://localhost:9090")
    print("Grafana:    http://localhost:3000")
    print("Node Exporter: http://localhost:9100")
    print("Redis Exporter: http://localhost:9121")
    print("监控服务:   http://localhost:8005")
    
    print("\n4. 监控服务API:")
    print("-" * 30)
    print("健康检查: http://localhost:8005/health")
    print("性能指标: http://localhost:8005/api/monitoring/metrics/summary")
    print("系统信息: http://localhost:8005/api/monitoring/system/info")
    print("活跃告警: http://localhost:8005/api/monitoring/alerts")
    
    print("\n5. 使用说明:")
    print("-" * 30)
    print("• 监控服务将自动收集所有微服务的性能指标")
    print("• 性能监控中间件会记录每个API请求的响应时间和错误率")
    print("• 系统会监控CPU、内存、磁盘等资源使用情况")
    print("• 当指标超过阈值时会自动触发告警")
    
    try:
        # 等待所有进程
        print("\n监控系统正在运行... (按Ctrl+C停止)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止监控系统...")
        
        # 停止所有进程
        for name, process in processes:
            if process.poll() is None:
                process.terminate()
                print(f"✓ 停止 {name}")
        
        # 等待进程结束
        for name, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"✗ 强制停止 {name}")
        
        print("监控系统已停止")

if __name__ == "__main__":
    main()