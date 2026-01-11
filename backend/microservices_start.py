"""微服务启动脚本"""
import uvicorn
import asyncio
import multiprocessing
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class MicroserviceManager:
    """微服务管理器"""
    
    def __init__(self):
        self.services = {
            "gateway": {
                "app": "app.api.microservices.gateway:gateway_app",
                "host": "localhost",
                "port": 8000,
                "workers": 1
            },
            "chat": {
                "app": "app.api.microservices.chat_service:chat_app",
                "host": "localhost",
                "port": 8001,
                "workers": 2
            },
            "search": {
                "app": "app.api.microservices.search_service:search_app",
                "host": "localhost",
                "port": 8002,
                "workers": 1
            },
            "file": {
                "app": "app.api.microservices.file_service:file_app",
                "host": "localhost",
                "port": 8003,
                "workers": 1
            },
            "voice": {
                "app": "app.api.microservices.voice_service:voice_app",
                "host": "localhost",
                "port": 8004,
                "workers": 1
            },
            "monitoring": {
                "app": "app.api.microservices.monitoring_service:monitoring_app",
                "host": "localhost",
                "port": 8005,
                "workers": 1
            },
            "enhanced_chat": {
                "app": "app.api.microservices.enhanced_chat_service:enhanced_chat_app",
                "host": "localhost",
                "port": 8006,
                "workers": 2
            }
        }
        
        self.processes = {}
    
    def start_service(self, service_name: str):
        """启动单个微服务"""
        if service_name not in self.services:
            print(f"错误: 未知的服务 '{service_name}'")
            return
        
        service_config = self.services[service_name]
        
        # 配置uvicorn
        config = uvicorn.Config(
            app=service_config["app"],
            host=service_config["host"],
            port=service_config["port"],
            workers=service_config["workers"],
            reload=False,  # 生产环境关闭热重载
            log_level="info"
        )
        
        # 创建服务器实例
        server = uvicorn.Server(config)
        
        # 启动服务
        print(f"启动服务: {service_name} ({service_config['host']}:{service_config['port']})")
        
        try:
            server.run()
        except Exception as e:
            print(f"服务 {service_name} 启动失败: {e}")
    
    def start_all_services(self):
        """启动所有微服务"""
        print("开始启动所有微服务...")
        
        # 使用多进程启动所有服务
        for service_name in self.services:
            process = multiprocessing.Process(
                target=self.start_service,
                args=(service_name,)
            )
            process.start()
            self.processes[service_name] = process
            
            # 短暂延迟，避免端口冲突
            import time
            time.sleep(1)
        
        print("所有微服务已启动")
        
        # 等待所有进程
        for process in self.processes.values():
            process.join()
    
    def stop_all_services(self):
        """停止所有微服务"""
        print("停止所有微服务...")
        
        for service_name, process in self.processes.items():
            if process.is_alive():
                process.terminate()
                print(f"已停止服务: {service_name}")
        
        self.processes.clear()
        print("所有微服务已停止")
    
    def status(self):
        """查看服务状态"""
        print("微服务状态:")
        
        for service_name, process in self.processes.items():
            status = "运行中" if process.is_alive() else "已停止"
            service_config = self.services[service_name]
            print(f"  {service_name}: {status} ({service_config['host']}:{service_config['port']})")


def main():
    """主函数"""
    manager = MicroserviceManager()
    
    if len(sys.argv) < 2:
        print("用法: python microservices_start.py [start|stop|status|start_service]")
        print("  start - 启动所有微服务")
        print("  stop - 停止所有微服务")
        print("  status - 查看服务状态")
        print("  start_service <service_name> - 启动单个服务")
        return
    
    command = sys.argv[1]
    
    if command == "start":
        manager.start_all_services()
    elif command == "stop":
        manager.stop_all_services()
    elif command == "status":
        manager.status()
    elif command == "start_service" and len(sys.argv) > 2:
        service_name = sys.argv[2]
        manager.start_service(service_name)
    else:
        print("未知命令")


if __name__ == "__main__":
    main()