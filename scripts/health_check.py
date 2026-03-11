#!/usr/bin/env python3
"""
环境健康检查脚本 - OP-001

检查向量化管理模块各组件的健康状态

使用方法:
    python health_check.py [选项]

示例:
    python health_check.py --all
    python health_check.py --service postgres,redis
    python health_check.py --verbose
"""

import sys
import argparse
import logging
import socket
import requests
import psycopg2
import redis
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """健康状态"""
    service: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: float
    message: str
    details: Optional[Dict] = None


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.results: List[HealthStatus] = []
    
    def check_postgres(self, host: str, port: int, 
                       database: str, user: str, password: str) -> HealthStatus:
        """检查PostgreSQL健康状态"""
        import time
        start = time.time()
        
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            connections = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start) * 1000
            
            return HealthStatus(
                service="PostgreSQL",
                status="healthy",
                response_time_ms=response_time,
                message=f"运行正常",
                details={
                    "version": version.split()[1],
                    "active_connections": connections
                }
            )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="PostgreSQL",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_redis(self, host: str, port: int, 
                    password: Optional[str] = None) -> HealthStatus:
        """检查Redis健康状态"""
        import time
        start = time.time()
        
        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            info = client.info()
            
            response_time = (time.time() - start) * 1000
            
            return HealthStatus(
                service="Redis",
                status="healthy",
                response_time_ms=response_time,
                message="运行正常",
                details={
                    "version": info.get('redis_version'),
                    "used_memory_human": info.get('used_memory_human'),
                    "connected_clients": info.get('connected_clients')
                }
            )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="Redis",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_milvus(self, host: str, port: int) -> HealthStatus:
        """检查Milvus健康状态"""
        import time
        start = time.time()
        
        try:
            from pymilvus import connections, utility
            
            connections.connect(
                alias="health_check",
                host=host,
                port=port
            )
            
            # 检查服务器版本
            version = utility.get_server_version()
            
            connections.disconnect("health_check")
            
            response_time = (time.time() - start) * 1000
            
            return HealthStatus(
                service="Milvus",
                status="healthy",
                response_time_ms=response_time,
                message="运行正常",
                details={"version": version}
            )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="Milvus",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_api(self, url: str) -> HealthStatus:
        """检查API服务健康状态"""
        import time
        start = time.time()
        
        try:
            response = requests.get(
                f"{url}/health",
                timeout=5
            )
            
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return HealthStatus(
                    service="API",
                    status="healthy",
                    response_time_ms=response_time,
                    message="运行正常",
                    details=response.json() if response.content else {}
                )
            else:
                return HealthStatus(
                    service="API",
                    status="unhealthy",
                    response_time_ms=response_time,
                    message=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="API",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_prometheus(self, url: str) -> HealthStatus:
        """检查Prometheus健康状态"""
        import time
        start = time.time()
        
        try:
            response = requests.get(
                f"{url}/-/healthy",
                timeout=5
            )
            
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return HealthStatus(
                    service="Prometheus",
                    status="healthy",
                    response_time_ms=response_time,
                    message="运行正常"
                )
            else:
                return HealthStatus(
                    service="Prometheus",
                    status="unhealthy",
                    response_time_ms=response_time,
                    message=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="Prometheus",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_grafana(self, url: str, user: str, password: str) -> HealthStatus:
        """检查Grafana健康状态"""
        import time
        start = time.time()
        
        try:
            response = requests.get(
                f"{url}/api/health",
                auth=(user, password),
                timeout=5
            )
            
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return HealthStatus(
                    service="Grafana",
                    status="healthy",
                    response_time_ms=response_time,
                    message="运行正常",
                    details={"version": data.get('version')}
                )
            else:
                return HealthStatus(
                    service="Grafana",
                    status="unhealthy",
                    response_time_ms=response_time,
                    message=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="Grafana",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_elasticsearch(self, url: str) -> HealthStatus:
        """检查Elasticsearch健康状态"""
        import time
        start = time.time()
        
        try:
            response = requests.get(
                f"{url}/_cluster/health",
                timeout=5
            )
            
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                status = "healthy" if data.get('status') in ['green', 'yellow'] else "unhealthy"
                
                return HealthStatus(
                    service="Elasticsearch",
                    status=status,
                    response_time_ms=response_time,
                    message=f"集群状态: {data.get('status')}",
                    details={
                        "cluster_name": data.get('cluster_name'),
                        "number_of_nodes": data.get('number_of_nodes')
                    }
                )
            else:
                return HealthStatus(
                    service="Elasticsearch",
                    status="unhealthy",
                    response_time_ms=response_time,
                    message=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service="Elasticsearch",
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def check_port(self, host: str, port: int, service_name: str) -> HealthStatus:
        """检查端口是否开放"""
        import time
        start = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            response_time = (time.time() - start) * 1000
            
            if result == 0:
                return HealthStatus(
                    service=service_name,
                    status="healthy",
                    response_time_ms=response_time,
                    message=f"端口 {port} 开放"
                )
            else:
                return HealthStatus(
                    service=service_name,
                    status="unhealthy",
                    response_time_ms=response_time,
                    message=f"端口 {port} 未开放"
                )
        
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return HealthStatus(
                service=service_name,
                status="unhealthy",
                response_time_ms=response_time,
                message=str(e)
            )
    
    def run_all_checks(self) -> List[HealthStatus]:
        """运行所有健康检查"""
        logger.info("开始健康检查...")
        
        # PostgreSQL 主库
        self.results.append(self.check_postgres(
            self.config.get('postgres_host', 'localhost'),
            int(self.config.get('postgres_port', '5432')),
            self.config.get('postgres_db', 'vectorization'),
            self.config.get('postgres_user', 'postgres'),
            self.config.get('postgres_password', 'postgres')
        ))
        
        # PostgreSQL 从库
        self.results.append(self.check_postgres(
            self.config.get('postgres_replica_host', 'localhost'),
            int(self.config.get('postgres_replica_port', '5433')),
            self.config.get('postgres_db', 'vectorization'),
            self.config.get('postgres_user', 'postgres'),
            self.config.get('postgres_password', 'postgres')
        ))
        
        # Redis
        self.results.append(self.check_redis(
            self.config.get('redis_host', 'localhost'),
            int(self.config.get('redis_port', '6379')),
            self.config.get('redis_password')
        ))
        
        # Milvus
        self.results.append(self.check_milvus(
            self.config.get('milvus_host', 'localhost'),
            int(self.config.get('milvus_port', '19530'))
        ))
        
        # API
        self.results.append(self.check_api(
            self.config.get('api_url', 'http://localhost:8000')
        ))
        
        # Prometheus
        self.results.append(self.check_prometheus(
            self.config.get('prometheus_url', 'http://localhost:9090')
        ))
        
        # Grafana
        self.results.append(self.check_grafana(
            self.config.get('grafana_url', 'http://localhost:3000'),
            self.config.get('grafana_user', 'admin'),
            self.config.get('grafana_password', 'admin')
        ))
        
        # Elasticsearch
        self.results.append(self.check_elasticsearch(
            self.config.get('elasticsearch_url', 'http://localhost:9200')
        ))
        
        logger.info("健康检查完成")
        return self.results
    
    def print_report(self, verbose: bool = False):
        """打印健康检查报告"""
        print("\n" + "=" * 70)
        print("  健康检查报告")
        print("=" * 70)
        print(f"{'服务':<20} {'状态':<10} {'响应时间':<12} {'消息'}")
        print("-" * 70)
        
        healthy_count = 0
        unhealthy_count = 0
        
        for result in self.results:
            status_icon = "✓" if result.status == "healthy" else "✗"
            status_text = f"{status_icon} {result.status}"
            
            print(f"{result.service:<20} {status_text:<10} "
                  f"{result.response_time_ms:>6.1f}ms     {result.message}")
            
            if verbose and result.details:
                for key, value in result.details.items():
                    print(f"  └─ {key}: {value}")
            
            if result.status == "healthy":
                healthy_count += 1
            else:
                unhealthy_count += 1
        
        print("-" * 70)
        print(f"总计: {len(self.results)} 个服务 | "
              f"✓ 健康: {healthy_count} | "
              f"✗ 异常: {unhealthy_count}")
        print("=" * 70)
        
        return unhealthy_count == 0


def main():
    parser = argparse.ArgumentParser(
        description='向量化管理模块健康检查工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查所有服务
  %(prog)s --all

  # 检查指定服务
  %(prog)s --service postgres,redis,api

  # 详细输出
  %(prog)s --all --verbose

  # 使用自定义配置
  %(prog)s --all --config config.json
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='检查所有服务')
    parser.add_argument('--service', type=str,
                       help='指定要检查的服务，逗号分隔')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    parser.add_argument('--config', type=str,
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 默认配置
    config = {
        'postgres_host': 'localhost',
        'postgres_port': '5432',
        'postgres_db': 'vectorization',
        'postgres_user': 'postgres',
        'postgres_password': 'postgres',
        'postgres_replica_host': 'localhost',
        'postgres_replica_port': '5433',
        'redis_host': 'localhost',
        'redis_port': '6379',
        'redis_password': None,
        'milvus_host': 'localhost',
        'milvus_port': '19530',
        'api_url': 'http://localhost:8000',
        'prometheus_url': 'http://localhost:9090',
        'grafana_url': 'http://localhost:3000',
        'grafana_user': 'admin',
        'grafana_password': 'admin',
        'elasticsearch_url': 'http://localhost:9200',
    }
    
    # 加载配置文件
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config.update(json.load(f))
    
    # 创建健康检查器
    checker = HealthChecker(config)
    
    if args.all:
        checker.run_all_checks()
        all_healthy = checker.print_report(verbose=args.verbose)
        sys.exit(0 if all_healthy else 1)
    
    elif args.service:
        services = args.service.split(',')
        logger.info(f"检查服务: {', '.join(services)}")
        # TODO: 实现指定服务的检查
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
