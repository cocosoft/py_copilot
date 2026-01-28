"""
性能基准测试工具
用于测试系统在不同负载下的性能表现
"""

import asyncio
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from fastapi.testclient import TestClient
from app.api.main import app


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.results = []
    
    async def benchmark_api_endpoint(self, 
                                   endpoint: str, 
                                   method: str = "GET",
                                   payload: Dict = None,
                                   concurrent_requests: int = 10,
                                   total_requests: int = 100) -> Dict[str, Any]:
        """基准测试API端点"""
        
        print(f"正在测试端点: {endpoint} ({method})")
        print(f"并发请求数: {concurrent_requests}, 总请求数: {total_requests}")
        
        response_times = []
        success_count = 0
        error_count = 0
        
        async def make_request(request_id: int):
            """发送单个请求"""
            nonlocal success_count, error_count
            
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = self.client.get(endpoint)
                elif method == "POST":
                    response = self.client.post(endpoint, json=payload)
                elif method == "PUT":
                    response = self.client.put(endpoint, json=payload)
                elif method == "DELETE":
                    response = self.client.delete(endpoint)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if 200 <= response.status_code < 300:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"请求 {request_id} 失败: {response.status_code}")
                    
            except Exception as e:
                error_count += 1
                print(f"请求 {request_id} 异常: {str(e)}")
        
        # 创建请求任务
        tasks = []
        for i in range(total_requests):
            task = make_request(i)
            tasks.append(task)
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        # 执行请求
        start_time = time.time()
        await asyncio.gather(*[bounded_task(task) for task in tasks])
        total_time = time.time() - start_time
        
        # 计算统计信息
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = min_response_time = max_response_time = 0
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "concurrent_requests": concurrent_requests,
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / total_requests if total_requests > 0 else 0,
            "total_time": total_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    async def benchmark_database_operations(self, 
                                          operation_count: int = 1000,
                                          batch_size: int = 100) -> Dict[str, Any]:
        """基准测试数据库操作"""
        
        print(f"正在测试数据库操作: {operation_count} 次操作，批次大小: {batch_size}")
        
        operation_times = []
        
        async def perform_database_operation(operation_id: int):
            """执行单个数据库操作"""
            
            start_time = time.time()
            
            # 模拟数据库操作
            try:
                # 查询操作
                response = self.client.get("/api/data/sources")
                
                # 写入操作（每10次操作执行一次写入）
                if operation_id % 10 == 0:
                    response = self.client.post(
                        "/api/data/sources",
                        json={
                            "name": f"benchmark_source_{operation_id}",
                            "type": "api",
                            "config": {"url": "https://api.example.com/data"}
                        }
                    )
                
                operation_time = time.time() - start_time
                operation_times.append(operation_time)
                
            except Exception as e:
                print(f"数据库操作 {operation_id} 失败: {str(e)}")
        
        # 执行操作
        tasks = []
        for i in range(operation_count):
            task = perform_database_operation(i)
            tasks.append(task)
        
        # 分批执行
        start_time = time.time()
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch)
            await asyncio.sleep(0.1)  # 批次间延迟
        
        total_time = time.time() - start_time
        
        # 计算统计信息
        if operation_times:
            avg_operation_time = statistics.mean(operation_times)
            p95_operation_time = statistics.quantiles(operation_times, n=20)[18]
            operations_per_second = len(operation_times) / total_time
        else:
            avg_operation_time = p95_operation_time = operations_per_second = 0
        
        result = {
            "test_type": "database_operations",
            "operation_count": operation_count,
            "batch_size": batch_size,
            "total_time": total_time,
            "operations_per_second": operations_per_second,
            "avg_operation_time": avg_operation_time,
            "p95_operation_time": p95_operation_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    async def benchmark_memory_usage(self, 
                                   object_count: int = 10000,
                                   object_size: int = 1024) -> Dict[str, Any]:
        """基准测试内存使用"""
        
        import psutil
        import os
        
        print(f"正在测试内存使用: {object_count} 个对象，每个大小: {object_size} 字节")
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建测试对象
        test_objects = []
        creation_times = []
        
        for i in range(object_count):
            start_time = time.time()
            
            # 创建测试对象
            obj = {
                "id": i,
                "data": "x" * object_size,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "type": "benchmark",
                    "size": object_size
                }
            }
            test_objects.append(obj)
            
            creation_time = time.time() - start_time
            creation_times.append(creation_time)
        
        # 获取创建后内存使用
        after_creation_memory = process.memory_info().rss
        memory_increase = after_creation_memory - initial_memory
        
        # 模拟对象操作
        operation_times = []
        
        for obj in test_objects[:1000]:  # 只测试前1000个对象
            start_time = time.time()
            
            # 模拟对象操作
            obj["processed"] = True
            obj["hash"] = hash(str(obj))
            
            operation_time = time.time() - start_time
            operation_times.append(operation_time)
        
        # 清理对象
        del test_objects
        
        # 获取清理后内存使用
        after_cleanup_memory = process.memory_info().rss
        
        result = {
            "test_type": "memory_usage",
            "object_count": object_count,
            "object_size": object_size,
            "initial_memory": initial_memory,
            "after_creation_memory": after_creation_memory,
            "memory_increase": memory_increase,
            "memory_increase_per_object": memory_increase / object_count if object_count > 0 else 0,
            "after_cleanup_memory": after_cleanup_memory,
            "avg_creation_time": statistics.mean(creation_times) if creation_times else 0,
            "avg_operation_time": statistics.mean(operation_times) if operation_times else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    async def benchmark_cpu_intensive_operations(self, 
                                               operation_count: int = 1000) -> Dict[str, Any]:
        """基准测试CPU密集型操作"""
        
        print(f"正在测试CPU密集型操作: {operation_count} 次操作")
        
        def fibonacci(n: int) -> int:
            """计算斐波那契数列（CPU密集型操作）"""
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
        
        operation_times = []
        
        async def perform_cpu_operation(operation_id: int):
            """执行CPU密集型操作"""
            
            start_time = time.time()
            
            # 执行CPU密集型计算
            result = fibonacci(20)  # 计算第20个斐波那契数
            
            operation_time = time.time() - start_time
            operation_times.append(operation_time)
        
        # 执行操作
        tasks = [perform_cpu_operation(i) for i in range(operation_count)]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 计算统计信息
        if operation_times:
            avg_operation_time = statistics.mean(operation_times)
            operations_per_second = operation_count / total_time
        else:
            avg_operation_time = operations_per_second = 0
        
        result = {
            "test_type": "cpu_intensive_operations",
            "operation_count": operation_count,
            "total_time": total_time,
            "operations_per_second": operations_per_second,
            "avg_operation_time": avg_operation_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能测试报告"""
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "test_categories": set(r.get("test_type", "api") for r in self.results),
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.results,
            "recommendations": []
        }
        
        # 分析结果并生成建议
        for result in self.results:
            test_type = result.get("test_type", "api")
            
            if test_type == "api":
                if result.get("avg_response_time", 0) > 1.0:
                    report["recommendations"].append(
                        f"API端点 {result['endpoint']} 响应时间较慢: {result['avg_response_time']:.3f}s"
                    )
                
                if result.get("success_rate", 0) < 0.95:
                    report["recommendations"].append(
                        f"API端点 {result['endpoint']} 成功率较低: {result['success_rate']:.2%}"
                    )
            
            elif test_type == "database_operations":
                if result.get("avg_operation_time", 0) > 0.5:
                    report["recommendations"].append(
                        f"数据库操作平均时间较长: {result['avg_operation_time']:.3f}s"
                    )
            
            elif test_type == "memory_usage":
                memory_per_object = result.get("memory_increase_per_object", 0)
                if memory_per_object > 2048:  # 2KB per object
                    report["recommendations"].append(
                        f"单个对象内存占用较大: {memory_per_object:.0f} 字节"
                    )
        
        return report
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行全面的性能基准测试"""
        
        print("=== 开始全面性能基准测试 ===\n")
        
        # 测试API端点
        api_endpoints = [
            ("/api/data/sources", "GET"),
            ("/api/collaboration/rooms", "GET"),
            ("/api/auth/status", "GET"),
            ("/api/skills", "GET")
        ]
        
        for endpoint, method in api_endpoints:
            await self.benchmark_api_endpoint(
                endpoint=endpoint,
                method=method,
                concurrent_requests=10,
                total_requests=100
            )
        
        # 测试数据库操作
        await self.benchmark_database_operations(
            operation_count=500,
            batch_size=50
        )
        
        # 测试内存使用
        await self.benchmark_memory_usage(
            object_count=5000,
            object_size=512
        )
        
        # 测试CPU密集型操作
        await self.benchmark_cpu_intensive_operations(
            operation_count=100
        )
        
        # 生成报告
        report = self.generate_performance_report()
        
        print("\n=== 性能基准测试完成 ===")
        print(f"总共执行了 {len(self.results)} 个测试")
        print(f"测试类型: {', '.join(report['summary']['test_categories'])}")
        
        if report["recommendations"]:
            print("\n优化建议:")
            for recommendation in report["recommendations"]:
                print(f"- {recommendation}")
        
        return report


def run_benchmark():
    """运行性能基准测试"""
    
    client = TestClient(app)
    benchmark = PerformanceBenchmark(client)
    
    # 运行基准测试
    report = asyncio.run(benchmark.run_comprehensive_benchmark())
    
    # 保存报告
    with open("performance_benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n详细报告已保存到 performance_benchmark_report.json")
    
    return report


class LoadTestScenario:
    """负载测试场景"""
    
    def __init__(self, name: str, client: TestClient):
        self.name = name
        self.client = client
        self.scenarios = {}
    
    def add_scenario(self, name: str, scenario_func: Callable):
        """添加测试场景"""
        self.scenarios[name] = scenario_func
    
    async def run_scenario(self, scenario_name: str, user_count: int = 10) -> Dict[str, Any]:
        """运行特定场景"""
        
        if scenario_name not in self.scenarios:
            raise ValueError(f"未知的场景: {scenario_name}")
        
        print(f"正在运行场景: {scenario_name} (用户数: {user_count})")
        
        scenario_func = self.scenarios[scenario_name]
        
        # 模拟多个用户同时执行场景
        tasks = []
        results = []
        
        for i in range(user_count):
            task = scenario_func(f"user_{i}")
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = user_count - success_count
        
        return {
            "scenario": scenario_name,
            "user_count": user_count,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / user_count,
            "total_time": total_time,
            "throughput": user_count / total_time if total_time > 0 else 0
        }
    
    async def run_all_scenarios(self, user_counts: List[int] = None) -> Dict[str, Any]:
        """运行所有场景"""
        
        if user_counts is None:
            user_counts = [5, 10, 20, 30]
        
        all_results = {}
        
        for scenario_name in self.scenarios:
            scenario_results = []
            
            for user_count in user_counts:
                result = await self.run_scenario(scenario_name, user_count)
                scenario_results.append(result)
                
                # 场景间延迟
                await asyncio.sleep(1)
            
            all_results[scenario_name] = scenario_results
        
        return all_results


if __name__ == "__main__":
    """直接运行性能基准测试"""
    
    print("Py Copilot 性能基准测试")
    print("=" * 50)
    
    report = run_benchmark()
    
    # 输出关键指标
    print("\n关键性能指标:")
    for result in report["detailed_results"]:
        test_type = result.get("test_type", "api")
        
        if test_type == "api":
            print(f"{result['endpoint']}:")
            print(f"  平均响应时间: {result['avg_response_time']:.3f}s")
            print(f"  吞吐量: {result['requests_per_second']:.1f} 请求/秒")
            print(f"  成功率: {result['success_rate']:.2%}")
        
        elif test_type == "database_operations":
            print(f"数据库操作:")
            print(f"  平均操作时间: {result['avg_operation_time']:.3f}s")
            print(f"  吞吐量: {result['operations_per_second']:.1f} 操作/秒")
    
    print("\n测试完成！")