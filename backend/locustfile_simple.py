#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版性能测试 - 测试基本API端点性能
"""

from locust import HttpUser, task, between, events
import json
import random
import time

class SimpleApiUser(HttpUser):
    """简单API性能测试用户类"""
    wait_time = between(1, 2)  # 每个用户操作间隔1-2秒
    
    def on_start(self):
        """测试开始前的准备工作"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @task(3)
    def health_check(self):
        """测试健康检查端点"""
        response = self.client.get(
            "/health",
            headers=self.headers,
            name="健康检查"
        )
    
    @task(2)
    def docs_access(self):
        """测试API文档访问"""
        response = self.client.get(
            "/docs",
            headers=self.headers,
            name="API文档"
        )
    
    @task(1)
    def openapi_docs(self):
        """测试OpenAPI文档"""
        response = self.client.get(
            "/openapi.json",
            headers=self.headers,
            name="OpenAPI文档"
        )

class BasicModelApiUser(HttpUser):
    """基本模型API性能测试用户类"""
    wait_time = between(2, 3)  # 每个用户操作间隔2-3秒
    
    def on_start(self):
        """测试开始前的准备工作"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @task(1)
    def get_root_info(self):
        """测试根路径信息"""
        response = self.client.get(
            "/",
            headers=self.headers,
            name="根路径信息"
        )

# 全局变量存储测试结果
test_results = {
    "start_time": None,
    "end_time": None,
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "avg_response_time": 0,
    "min_response_time": float('inf'),
    "max_response_time": 0,
    "request_times": []
}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始事件监听器"""
    test_results["start_time"] = time.time()
    print("\n" + "="*60)
    print("🚀 开始基本API性能测试")
    print("="*60)
    print(f"主机地址: {environment.host}")
    print(f"并发用户数: {environment.runner.target_user_count}")
    print(f"生成速率: {environment.runner.spawn_rate} 用户/秒")
    print(f"测试运行时间: {environment.runner.run_time}")
    print("="*60)

@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """测试结束事件监听器"""
    test_results["end_time"] = time.time()
    total_duration = test_results["end_time"] - test_results["start_time"]
    
    print("\n" + "="*60)
    print("📊 基本API性能测试结果汇总")
    print("="*60)
    print(f"总运行时间: {total_duration:.2f} 秒")
    print(f"总请求数: {test_results['total_requests']}")
    print(f"成功请求数: {test_results['successful_requests']}")
    print(f"失败请求数: {test_results['failed_requests']}")
    
    if test_results['successful_requests'] > 0:
        success_rate = (test_results['successful_requests'] / test_results['total_requests']) * 100
        print(f"成功率: {success_rate:.2f}%")
        print(f"平均响应时间: {test_results['avg_response_time']:.2f} ms")
        print(f"最小响应时间: {test_results['min_response_time']:.2f} ms")
        print(f"最大响应时间: {test_results['max_response_time']:.2f} ms")
        
        # 计算百分位数
        if test_results['request_times']:
            sorted_times = sorted(test_results['request_times'])
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            print(f"50% 百分位数: {p50:.2f} ms")
            print(f"95% 百分位数: {p95:.2f} ms")
            print(f"99% 百分位数: {p99:.2f} ms")
    
    print("="*60)
    
    # 保存结果到文件
    with open('performance_test_results_simple.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    print("📁 详细测试结果已保存到: performance_test_results_simple.json")

@events.request.add_listener
def on_request(environment, request, response, **kwargs):
    """请求完成事件监听器"""
    test_results["total_requests"] += 1
    
    if response.status_code < 400:
        test_results["successful_requests"] += 1
    else:
        test_results["failed_requests"] += 1
    
    # 记录响应时间
    response_time = response.elapsed.total_seconds() * 1000  # 转换为毫秒
    test_results["request_times"].append(response_time)
    
    # 更新统计信息
    test_results["avg_response_time"] = (
        (test_results["avg_response_time"] * (test_results["total_requests"] - 1) + response_time) / 
        test_results["total_requests"]
    )
    
    test_results["min_response_time"] = min(test_results["min_response_time"], response_time)
    test_results["max_response_time"] = max(test_results["max_response_time"], response_time)

if __name__ == "__main__":
    print("基本API性能测试文件已创建")
    print("使用方法:")
    print("1. 启动服务器: python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000")
    print("2. 运行测试: python locustfile_simple.py --headless --users 10 --spawn-rate 2 --run-time 30s --host http://localhost:8000")