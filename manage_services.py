#!/usr/bin/env python3
import subprocess
import time
import sys
import os
from pathlib import Path

class ProcessManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        
    def check_port(self, port):
        """检查端口是否被占用"""
        try:
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    return True
            return False
        except Exception as e:
            print(f"检查端口 {port} 时出错: {e}")
            return False
    
    def kill_processes_on_port(self, port):
        """终止占用指定端口的所有进程"""
        try:
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                check=True
            )
            
            pids = set()
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            pids.add(int(pid))
                        except ValueError:
                            continue
            
            if pids:
                print(f"发现 {len(pids)} 个进程占用端口 {port}，正在终止...")
                for pid in pids:
                    try:
                        subprocess.run(
                            ['taskkill', '/F', '/PID', str(pid)],
                            capture_output=True,
                            check=True
                        )
                        print(f"  ✓ 已终止进程 PID: {pid}")
                    except Exception as e:
                        print(f"  ✗ 终止进程 {pid} 失败: {e}")
                time.sleep(1)
            else:
                print(f"端口 {port} 没有被占用")
                
        except Exception as e:
            print(f"终止端口 {port} 进程时出错: {e}")
    
    def start_chroma(self):
        """启动 ChromaDB 服务"""
        print("\n=== 启动 ChromaDB 服务 ===")
        
        # 清理端口
        self.kill_processes_on_port(8008)
        
        # 启动服务
        try:
            os.chdir(self.backend_dir)
            cmd = ['python', 'chroma_server.py']
            
            print("启动命令:", ' '.join(cmd))
            print("ChromaDB 服务正在启动...")
            
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # 等待服务启动
            for i in range(10):
                time.sleep(1)
                if self.check_port(8008):
                    print("✓ ChromaDB 服务启动成功！")
                    print("  地址: http://localhost:8008")
                    return True
                print(f"  等待服务启动... ({i+1}/10)")
            
            print("✗ ChromaDB 服务启动超时")
            return False
            
        except Exception as e:
            print(f"✗ 启动 ChromaDB 服务失败: {e}")
            return False
    
    def start_backend(self):
        """启动后端服务"""
        print("\n=== 启动后端服务 ===")
        
        # 清理端口
        self.kill_processes_on_port(8007)
        
        # 启动服务
        try:
            os.chdir(self.backend_dir)
            cmd = [
                'python', '-m', 'uvicorn',
                'app.api.main:app',
                '--host', '0.0.0.0',
                '--port', '8007',
                '--reload'
            ]
            
            print("启动命令:", ' '.join(cmd))
            print("后端服务正在启动...")
            
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # 等待服务启动
            for i in range(10):
                time.sleep(1)
                if self.check_port(8007):
                    print("✓ 后端服务启动成功！")
                    print("  地址: http://localhost:8007")
                    return True
                print(f"  等待服务启动... ({i+1}/10)")
            
            print("✗ 后端服务启动超时")
            return False
            
        except Exception as e:
            print(f"✗ 启动后端服务失败: {e}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        print("\n=== 启动前端服务 ===")
        
        # 清理端口
        self.kill_processes_on_port(5173)
        
        # 启动服务
        try:
            os.chdir(self.frontend_dir)
            cmd = ['npm', 'run', 'dev']
            
            print("启动命令:", ' '.join(cmd))
            print("前端服务正在启动...")
            
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # 等待服务启动
            for i in range(10):
                time.sleep(1)
                if self.check_port(5173):
                    print("✓ 前端服务启动成功！")
                    print("  地址: http://localhost:5173")
                    return True
                print(f"  等待服务启动... ({i+1}/10)")
            
            print("✗ 前端服务启动超时")
            return False
            
        except Exception as e:
            print(f"✗ 启动前端服务失败: {e}")
            return False
    
    def stop_all(self):
        """停止所有服务"""
        print("\n=== 停止所有服务 ===")
        
        print("停止 ChromaDB 服务...")
        self.kill_processes_on_port(8008)
        
        print("停止后端服务...")
        self.kill_processes_on_port(8007)
        
        print("停止前端服务...")
        self.kill_processes_on_port(5173)
        
        print("✓ 所有服务已停止")
    
    def restart_all(self):
        """重启所有服务"""
        print("\n=== 重启所有服务 ===")
        self.stop_all()
        time.sleep(2)
        self.start_backend()
        self.start_frontend()
    
    def status(self):
        """检查服务状态"""
        print("\n=== 服务状态 ===")
        
        chroma_running = self.check_port(8008)
        backend_running = self.check_port(8007)
        frontend_running = self.check_port(5173)
        
        print(f"ChromaDB 服务 (8008): {'✓ 运行中' if chroma_running else '✗ 未运行'}")
        print(f"后端服务 (8007): {'✓ 运行中' if backend_running else '✗ 未运行'}")
        print(f"前端服务 (5173): {'✓ 运行中' if frontend_running else '✗ 未运行'}")
        
        return {
            'chroma': chroma_running,
            'backend': backend_running,
            'frontend': frontend_running
        }

def main():
    manager = ProcessManager()
    
    if len(sys.argv) < 2:
        print("用法: python manage_services.py [命令]")
        print("\n可用命令:")
        print("  start    - 启动所有服务")
        print("  stop     - 停止所有服务")
        print("  restart  - 重启所有服务")
        print("  status   - 检查服务状态")
        print("  chroma   - 仅启动 ChromaDB")
        print("  backend  - 仅启动后端")
        print("  frontend - 仅启动前端")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        manager.start_chroma()
        time.sleep(2)
        manager.start_backend()
        manager.start_frontend()
    elif command == 'stop':
        manager.stop_all()
    elif command == 'restart':
        manager.restart_all()
    elif command == 'status':
        manager.status()
    elif command == 'chroma':
        manager.start_chroma()
    elif command == 'backend':
        manager.start_backend()
    elif command == 'frontend':
        manager.start_frontend()
    else:
        print(f"未知命令: {command}")
        print("运行 'python manage_services.py' 查看可用命令")

if __name__ == '__main__':
    main()
