#!/usr/bin/env python3
"""
微服务启动脚本

使用方法:
    python run_microservice.py <service_name>

可用的微服务名称:
    - gateway: API网关服务
    - auth: 认证服务
    - chat: 聊天服务
    - knowledge: 知识服务
    - workflow: 工作流服务
    - capability: 能力管理服务
    - parameter: 参数管理服务
    - monitoring: 监控服务
    - all: 启动所有微服务
"""
import sys
import os
import subprocess
import multiprocessing
from typing import List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.logging_config import logger
from app.core.microservices_entry import MICROSERVICES

def run_microservice(service_name: str) -> None:
    """
    运行单个微服务
    
    Args:
        service_name: 微服务名称
    """
    try:
        logger.info(f"启动微服务: {service_name}")
        
        # 根据服务名称选择启动方式
        if service_name == "gateway":
            # 启动API网关
            from app.api.microservices.gateway import gateway_app
            import uvicorn
            
            # 获取网关配置
            from app.core.microservices_config import microservices_settings
            
            uvicorn.run(
                "app.api.microservices.gateway:gateway_app",
                host=microservices_settings.GATEWAY_HOST,
                port=microservices_settings.GATEWAY_PORT,
                reload=True,
                log_level="info"
            )
        elif service_name == "all":
            # 启动所有微服务
            run_all_microservices()
        else:
            # 启动其他微服务
            import uvicorn
            from app.core.microservices_entry import create_microservice_app
            
            # 创建微服务应用
            microservice_app = create_microservice_app(service_name)
            if microservice_app:
                # 获取服务配置
                from app.core.microservices_config import microservices_settings
                config_class = getattr(microservices_settings, f"{service_name.upper()}_SETTINGS", None)
                
                if config_class:
                    host = getattr(config_class, "HOST", "localhost")
                    port = getattr(config_class, "PORT", 8000)
                    workers = getattr(config_class, "WORKERS", 1)
                else:
                    # 默认配置
                    host = "localhost"
                    port = 8000 + list(MICROSERVICES.keys()).index(service_name) + 1
                    workers = 1
                
                uvicorn.run(
                    microservice_app.app,
                    host=host,
                    port=port,
                    reload=True,
                    log_level="info",
                    workers=workers
                )
            else:
                logger.error(f"无法创建微服务应用: {service_name}")
                sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info(f"停止微服务: {service_name}")
    except Exception as e:
        logger.error(f"启动微服务失败: {service_name}, 错误: {str(e)}")
        sys.exit(1)

def run_all_microservices() -> None:
    """
    启动所有微服务
    """
    logger.info("启动所有微服务")
    
    processes: List[multiprocessing.Process] = []
    
    try:
        # 启动每个微服务
        for service_name in MICROSERVICES.keys():
            process = multiprocessing.Process(
                target=run_microservice,
                args=(service_name,)
            )
            processes.append(process)
            process.start()
            logger.info(f"已启动微服务进程: {service_name} (PID: {process.pid})")
        
        # 等待所有进程完成
        for process in processes:
            process.join()
            
    except KeyboardInterrupt:
        logger.info("停止所有微服务")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
    except Exception as e:
        logger.error(f"启动所有微服务失败: {str(e)}")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
        sys.exit(1)

def main() -> None:
    """
    主函数
    """
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法: python run_microservice.py <service_name>")
        print("\n可用的微服务名称:")
        print("    - gateway: API网关服务")
        print("    - auth: 认证服务")
        print("    - chat: 聊天服务")
        print("    - knowledge: 知识服务")
        print("    - workflow: 工作流服务")
        print("    - capability: 能力管理服务")
        print("    - parameter: 参数管理服务")
        print("    - monitoring: 监控服务")
        print("    - all: 启动所有微服务")
        sys.exit(1)
    
    service_name = sys.argv[1].lower()
    
    # 检查服务名称是否有效
    valid_services = list(MICROSERVICES.keys()) + ["gateway", "all"]
    if service_name not in valid_services:
        print(f"无效的微服务名称: {service_name}")
        print("\n可用的微服务名称:")
        for service in valid_services:
            print(f"    - {service}")
        sys.exit(1)
    
    # 运行微服务
    run_microservice(service_name)

if __name__ == "__main__":
    main()
