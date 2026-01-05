"""全面的API性能测试 - 包含默认模型管理和监控API"""
from locust import HttpUser, task, between, tag, events
import json
import random
import time
import os
from datetime import datetime


class DefaultModelManagementUser(HttpUser):
    """默认模型管理API性能测试用户类"""
    wait_time = between(1, 3)  # 每个用户操作间隔1-3秒
    
    def on_start(self):
        """测试开始前的准备工作"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 模拟用户登录（这里使用模拟数据）
        self.user_data = {
            "username": "test_user",
            "password": "test_password"
        }
    
    @tag("default_model_api")
    @task(3)
    def get_default_models(self):
        """测试获取默认模型列表"""
        response = self.client.get(
            "/api/v1/default-models",
            headers=self.headers,
            name="获取默认模型列表"
        )
        if response.status_code == 200:
            data = response.json()
            if 'default_models' in data:
                self.default_models = data['default_models']
    
    @tag("default_model_api")
    @task(2)
    def get_current_global_default(self):
        """测试获取当前全局默认模型"""
        response = self.client.get(
            "/api/v1/default-models/current/global",
            headers=self.headers,
            name="获取全局默认模型"
        )
        if response.status_code == 200:
            data = response.json()
            if 'default_model' in data:
                self.current_global_default = data['default_model']
    
    @tag("default_model_api")
    @task(2)
    def set_global_default_model(self):
        """测试设置全局默认模型"""
        if hasattr(self, 'default_models') and self.default_models:
            model_id = random.choice([m['id'] for m in self.default_models if m['id'] != 1])
        else:
            model_id = 2  # 使用备用模型ID
        
        data = {
            "model_id": model_id,
            "priority": 1,
            "fallback_model_id": 1
        }
        
        response = self.client.post(
            "/api/v1/default-models/global",
            headers=self.headers,
            json=data,
            name="设置全局默认模型"
        )
        
        if response.status_code == 200:
            print(f"成功设置全局默认模型: {model_id}")
    
    @tag("default_model_api")
    @task(1)
    def get_user_default_models(self):
        """测试获取用户默认模型"""
        response = self.client.get(
            "/api/v1/default-models/user",
            headers=self.headers,
            name="获取用户默认模型"
        )


class MonitoringApiUser(HttpUser):
    """监控API性能测试用户类"""
    wait_time = between(2, 5)  # 监控API操作间隔稍长
    
    def on_start(self):
        """测试开始前的准备工作"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @tag("monitoring_api")
    @task(4)
    def get_metric_data(self):
        """测试获取指标数据"""
        metric_name = random.choice(["response_time", "cpu_usage", "memory_usage", "error_rate"])
        duration = random.choice([3600, 7200, 86400])  # 1小时、2小时、24小时
        
        response = self.client.get(
            f"/api/monitoring/metrics/{metric_name}?duration={duration}",
            headers=self.headers,
            name="获取指标数据"
        )
    
    @tag("monitoring_api")
    @task(3)
    def get_active_alerts(self):
        """测试获取活跃告警"""
        response = self.client.get(
            "/api/monitoring/alerts/active",
            headers=self.headers,
            name="获取活跃告警"
        )
    
    @tag("monitoring_api")
    @task(2)
    def get_alert_history(self):
        """测试获取告警历史"""
        duration = random.choice([3600, 86400, 604800])  # 1小时、24小时、7天
        level = random.choice([None, "warning", "error", "critical"])
        alert_type = random.choice([None, "performance", "error_rate"])
        
        params = f"duration={duration}"
        if level:
            params += f"&level={level}"
        if alert_type:
            params += f"&type={alert_type}"
        
        response = self.client.get(
            f"/api/monitoring/alerts/history?{params}",
            headers=self.headers,
            name="获取告警历史"
        )
    
    @tag("monitoring_api")
    @task(1)
    def get_statistics(self):
        """测试获取统计信息"""
        response = self.client.get(
            "/api/monitoring/statistics",
            headers=self.headers,
            name="获取监控统计"
        )
    
    @tag("monitoring_api")
    @task(1)
    def record_metric(self):
        """测试记录指标"""
        metric_data = {
            "metric_name": f"test_metric_{int(time.time())}",
            "value": random.uniform(10, 1000),
            "tags": {
                "environment": "test",
                "service": "api",
                "endpoint": "/test"
            }
        }
        
        response = self.client.post(
            "/api/monitoring/metrics/record",
            headers=self.headers,
            json=metric_data,
            name="记录测试指标"
        )


class ModelManagementUser(HttpUser):
    """模型管理API性能测试用户类（扩展版）"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """测试开始前的准备工作"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @tag("model_management")
    @task(2)
    def get_suppliers_extended(self):
        """测试获取供应商列表（扩展版）"""
        response = self.client.get(
            "/api/v1/model-management/suppliers/all",
            headers=self.headers,
            name="获取供应商列表"
        )
        if response.status_code == 200:
            suppliers = response.json()
            if suppliers:
                self.suppliers = suppliers
    
    @tag("model_management")
    @task(3)
    def get_models_extended(self):
        """测试获取模型列表（扩展版）"""
        if hasattr(self, 'suppliers') and self.suppliers:
            supplier_id = random.choice(self.suppliers)['id']
        else:
            supplier_id = random.choice([1, 2, 3])  # 使用预设ID
        
        response = self.client.get(
            f"/api/v1/model-management/suppliers/{supplier_id}/models",
            headers=self.headers,
            name="获取模型列表"
        )
    
    @tag("model_management")
    @task(2)
    def get_model_details(self):
        """测试获取模型详细信息"""
        supplier_id = random.choice([1, 2, 3])
        model_id = random.choice([1, 2, 3, 4, 5])
        
        response = self.client.get(
            f"/api/v1/model-management/suppliers/{supplier_id}/models/{model_id}",
            headers=self.headers,
            name="获取模型详情"
        )
    
    @tag("model_management")
    @task(1)
    def search_models(self):
        """测试搜索模型"""
        search_queries = ["gpt", "claude", "llama", "bert", "transformer"]
        query = random.choice(search_queries)
        
        response = self.client.get(
            f"/api/v1/model-management/search?query={query}",
            headers=self.headers,
            name="搜索模型"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的钩子函数"""
    print(f"\n🚀 开始性能测试: {datetime.now()}")
    print(f"📊 测试配置:")
    print(f"   - 主机: {environment.host}")
    print(f"   - 用户数: {environment.num_users}")
    print(f"   - 启动速率: {environment.spawn_rate}")
    print(f"   - 运行时间: {environment.runner.target_time}s")
    
    # 创建测试结果目录
    os.makedirs("performance_results", exist_ok=True)


@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """测试结束时的钩子函数"""
    print(f"\n🏁 性能测试结束: {datetime.now()}")
    
    # 导出测试统计信息
    stats = environment.stats
    
    with open("performance_results/test_summary.txt", "w", encoding="utf-8") as f:
        f.write("性能测试结果汇总\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"测试时间: {datetime.now()}\n")
        f.write(f"测试主机: {environment.host}\n\n")
        
        f.write("总体统计:\n")
        f.write(f"  总请求数: {stats.total.num_requests}\n")
        f.write(f"  失败请求数: {stats.total.num_failures}\n")
        f.write(f"  平均响应时间: {stats.total.avg_response_time:.2f}ms\n")
        f.write(f"  最小响应时间: {stats.total.min_response_time:.2f}ms\n")
        f.write(f"  最大响应时间: {stats.total.max_response_time:.2f}ms\n")
        f.write(f"  95%响应时间: {stats.total.get_response_time_percentile(0.95):.2f}ms\n")
        f.write(f"  99%响应时间: {stats.total.get_response_time_percentile(0.99):.2f}ms\n")
        f.write(f"  请求成功率: {(1 - stats.total.num_failures/stats.total.num_requests)*100:.2f}%\n\n")
        
        f.write("详细统计（按API端点）:\n")
        for name, stat in stats.entries.items():
            f.write(f"  {name}:\n")
            f.write(f"    请求数: {stat.num_requests}\n")
            f.write(f"    失败数: {stat.num_failures}\n")
            f.write(f"    平均响应时间: {stat.avg_response_time:.2f}ms\n")
            f.write(f"    95%响应时间: {stat.get_response_time_percentile(0.95):.2f}ms\n")
            f.write(f"    请求成功率: {(1 - stat.num_failures/stat.num_requests)*100:.2f}%\n\n")
    
    print("📄 测试结果已保存到 performance_results/test_summary.txt")


if __name__ == "__main__":
    import subprocess
    
    print("""
    性能测试选项:
    1. 默认模型管理API测试
    2. 监控API测试  
    3. 模型管理API测试
    4. 全面测试（所有API）
    """)
    
    choice = input("请选择测试类型 (1-4): ").strip()
    
    if choice == "1":
        # 只测试默认模型管理API
        host = "http://localhost:8001"
        tags = "default_model_api"
    elif choice == "2":
        # 只测试监控API
        host = "http://localhost:8001"
        tags = "monitoring_api"
    elif choice == "3":
        # 只测试模型管理API
        host = "http://localhost:8001"
        tags = "model_management"
    else:
        # 全面测试
        host = "http://localhost:8001"
        tags = None
    
    cmd = [
        "locust",
        "-f", os.path.basename(__file__),
        "--host", host,
        "--headless",
        "-u", "10",  # 并发用户数
        "-r", "2",   # 启动速率
        "-t", "300s" # 运行时间
    ]
    
    if tags:
        cmd.extend(["--tag", tags])
    
    print(f"\n启动命令: {' '.join(cmd)}")
    subprocess.run(cmd)