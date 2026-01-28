"""
多用户并发场景测试用例
测试在多用户同时使用系统时的稳定性和性能
"""

import asyncio
import time
import pytest
import random
from datetime import datetime
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from app.api.main import app
from app.services.collaboration_service import CollaborationService
from app.services.websocket_router import WebSocketRouter


class ConcurrentUserSimulator:
    """并发用户模拟器"""
    
    def __init__(self, client: TestClient, user_count: int = 10):
        self.client = client
        self.user_count = user_count
        self.users = []
        self.results = []
        
    async def simulate_user_actions(self, user_id: str, session_id: str, room_id: str) -> Dict[str, Any]:
        """模拟单个用户的操作序列"""
        
        start_time = time.time()
        actions = []
        
        try:
            # 1. 用户登录
            login_start = time.time()
            response = self.client.post("/api/auth/login", json={
                "username": f"test_user_{user_id}",
                "password": "password123"
            })
            login_time = time.time() - login_start
            
            if response.status_code != 200:
                # 如果用户不存在，先注册
                register_response = self.client.post("/api/auth/register", json={
                    "username": f"test_user_{user_id}",
                    "password": "password123",
                    "email": f"test_{user_id}@example.com"
                })
                
                if register_response.status_code == 200:
                    # 重新登录
                    response = self.client.post("/api/auth/login", json={
                        "username": f"test_user_{user_id}",
                        "password": "password123"
                    })
            
            actions.append({
                "action": "login",
                "duration": login_time,
                "success": response.status_code == 200
            })
            
            if response.status_code != 200:
                return {
                    "user_id": user_id,
                    "success": False,
                    "error": f"Login failed: {response.text}",
                    "actions": actions
                }
            
            # 获取认证令牌
            token = response.json().get("access_token")
            
            # 2. 创建或加入协作房间
            room_start = time.time()
            room_response = self.client.post(
                f"/api/collaboration/rooms/{room_id}/join",
                headers={"Authorization": f"Bearer {token}"}
            )
            room_time = time.time() - room_start
            
            actions.append({
                "action": "join_room",
                "duration": room_time,
                "success": room_response.status_code == 200
            })
            
            # 3. 模拟画布操作
            canvas_actions = await self.simulate_canvas_actions(token, room_id)
            actions.extend(canvas_actions)
            
            # 4. 模拟数据操作
            data_actions = await self.simulate_data_actions(token)
            actions.extend(data_actions)
            
            # 5. 模拟图表操作
            chart_actions = await self.simulate_chart_actions(token)
            actions.extend(chart_actions)
            
            total_time = time.time() - start_time
            
            return {
                "user_id": user_id,
                "success": True,
                "total_time": total_time,
                "actions": actions,
                "action_count": len(actions)
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "success": False,
                "error": str(e),
                "actions": actions
            }
    
    async def simulate_canvas_actions(self, token: str, room_id: str) -> List[Dict[str, Any]]:
        """模拟画布操作"""
        
        actions = []
        
        # 模拟添加节点
        for i in range(random.randint(3, 8)):
            action_start = time.time()
            
            response = self.client.post(
                "/api/canvas/nodes",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "room_id": room_id,
                    "type": "process",
                    "position": {"x": random.randint(0, 1000), "y": random.randint(0, 600)},
                    "properties": {
                        "label": f"节点_{i}",
                        "color": random.choice(["blue", "green", "red", "yellow"])
                    }
                }
            )
            
            action_time = time.time() - action_start
            
            actions.append({
                "action": f"add_node_{i}",
                "duration": action_time,
                "success": response.status_code == 200
            })
            
            # 随机延迟
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # 模拟移动节点
        for i in range(random.randint(2, 5)):
            action_start = time.time()
            
            response = self.client.put(
                f"/api/canvas/nodes/{i}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "room_id": room_id,
                    "position": {"x": random.randint(0, 1000), "y": random.randint(0, 600)}
                }
            )
            
            action_time = time.time() - action_start
            
            actions.append({
                "action": f"move_node_{i}",
                "duration": action_time,
                "success": response.status_code == 200
            })
            
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        return actions
    
    async def simulate_data_actions(self, token: str) -> List[Dict[str, Any]]:
        """模拟数据操作"""
        
        actions = []
        
        # 模拟数据查询
        for i in range(random.randint(2, 4)):
            action_start = time.time()
            
            response = self.client.get(
                "/api/data/sources",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            action_time = time.time() - action_start
            
            actions.append({
                "action": f"query_data_{i}",
                "duration": action_time,
                "success": response.status_code == 200
            })
            
            await asyncio.sleep(random.uniform(0.05, 0.2))
        
        return actions
    
    async def simulate_chart_actions(self, token: str) -> List[Dict[str, Any]]:
        """模拟图表操作"""
        
        actions = []
        
        # 模拟创建图表
        chart_types = ["bar", "line", "pie", "scatter", "area"]
        
        for i in range(random.randint(1, 3)):
            action_start = time.time()
            
            response = self.client.post(
                "/api/charts",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "type": random.choice(chart_types),
                    "title": f"测试图表_{i}",
                    "data_source": "test_data",
                    "config": {
                        "width": 600,
                        "height": 400,
                        "colors": ["#3498db", "#2ecc71", "#e74c3c"]
                    }
                }
            )
            
            action_time = time.time() - action_start
            
            actions.append({
                "action": f"create_chart_{i}",
                "duration": action_time,
                "success": response.status_code == 200
            })
            
            await asyncio.sleep(random.uniform(0.2, 0.5))
        
        return actions
    
    async def run_concurrent_test(self) -> Dict[str, Any]:
        """运行并发测试"""
        
        start_time = time.time()
        room_id = f"test_room_{int(time.time())}"
        
        # 创建测试任务
        tasks = []
        for i in range(self.user_count):
            user_id = str(i + 1)
            session_id = f"session_{user_id}"
            task = self.simulate_user_actions(user_id, session_id, room_id)
            tasks.append(task)
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # 处理结果
        successful_users = 0
        total_actions = 0
        successful_actions = 0
        
        for result in results:
            if isinstance(result, Exception):
                continue
            
            if result.get("success"):
                successful_users += 1
                total_actions += result.get("action_count", 0)
                
                # 计算成功操作数
                for action in result.get("actions", []):
                    if action.get("success"):
                        successful_actions += 1
        
        return {
            "test_type": "concurrent_users",
            "user_count": self.user_count,
            "successful_users": successful_users,
            "success_rate": successful_users / self.user_count if self.user_count > 0 else 0,
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "action_success_rate": successful_actions / total_actions if total_actions > 0 else 0,
            "total_time": total_time,
            "throughput": total_actions / total_time if total_time > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "detailed_results": results
        }


class WebSocketConcurrencyTest:
    """WebSocket并发测试"""
    
    def __init__(self, websocket_url: str, user_count: int = 5):
        self.websocket_url = websocket_url
        self.user_count = user_count
        
    async def test_websocket_connections(self) -> Dict[str, Any]:
        """测试WebSocket并发连接"""
        
        # 这个测试需要实际的WebSocket连接，这里提供测试框架
        # 在实际环境中，可以使用websockets库进行测试
        
        return {
            "test_type": "websocket_concurrency",
            "user_count": self.user_count,
            "status": "requires_websocket_library",
            "recommendation": "Use websockets library for real WebSocket testing"
        }


@pytest.mark.asyncio
class TestConcurrentScenarios:
    """并发场景测试类"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.mark.parametrize("user_count", [5, 10, 20])
    async def test_concurrent_user_operations(self, client, user_count):
        """测试并发用户操作"""
        
        simulator = ConcurrentUserSimulator(client, user_count)
        result = await simulator.run_concurrent_test()
        
        # 验证测试结果
        assert result["success_rate"] >= 0.8, f"Success rate too low: {result['success_rate']}"
        assert result["action_success_rate"] >= 0.9, f"Action success rate too low: {result['action_success_rate']}"
        assert result["total_time"] < 60, f"Test took too long: {result['total_time']}s"
        
        # 输出性能指标
        print(f"\n=== 并发用户测试结果 (用户数: {user_count}) ===")
        print(f"用户成功率: {result['success_rate']:.2%}")
        print(f"操作成功率: {result['action_success_rate']:.2%}")
        print(f"总耗时: {result['total_time']:.2f}s")
        print(f"吞吐量: {result['throughput']:.2f} 操作/秒")
    
    async def test_collaboration_service_concurrency(self):
        """测试协作服务的并发处理能力"""
        
        collaboration_service = CollaborationService()
        room_id = "test_concurrency_room"
        
        # 模拟多个用户同时加入房间
        user_count = 10
        join_times = []
        
        async def simulate_user_join(user_id: str):
            start_time = time.time()
            
            # 模拟用户加入房间
            await collaboration_service.join_room(room_id, user_id, f"session_{user_id}")
            
            join_time = time.time() - start_time
            join_times.append(join_time)
            
            # 模拟用户发送消息
            for i in range(5):
                await collaboration_service.broadcast_message(
                    room_id,
                    {
                        "type": "canvas_update",
                        "user_id": user_id,
                        "data": {"action": f"move_node_{i}"}
                    }
                )
                await asyncio.sleep(0.1)
        
        # 并发执行
        tasks = [simulate_user_join(str(i)) for i in range(user_count)]
        await asyncio.gather(*tasks)
        
        # 验证性能
        avg_join_time = sum(join_times) / len(join_times)
        assert avg_join_time < 0.5, f"Average join time too high: {avg_join_time}s"
        
        print(f"\n=== 协作服务并发测试结果 ===")
        print(f"平均加入时间: {avg_join_time:.3f}s")
        print(f"最大加入时间: {max(join_times):.3f}s")
        print(f"最小加入时间: {min(join_times):.3f}s")
    
    async def test_database_concurrency(self, client):
        """测试数据库并发访问"""
        
        # 模拟多个用户同时进行数据库操作
        user_count = 8
        operation_times = []
        
        async def simulate_database_operation(user_id: str):
            start_time = time.time()
            
            # 模拟数据库操作
            for i in range(3):
                response = client.get(
                    "/api/data/sources",
                    headers={"Authorization": f"Bearer test_token_{user_id}"}
                )
                
                # 模拟写入操作
                if i == 1:
                    response = client.post(
                        "/api/data/sources",
                        headers={"Authorization": f"Bearer test_token_{user_id}"},
                        json={
                            "name": f"test_source_{user_id}_{i}",
                            "type": "api",
                            "config": {"url": "https://api.example.com/data"}
                        }
                    )
            
            operation_time = time.time() - start_time
            operation_times.append(operation_time)
        
        # 并发执行
        tasks = [simulate_database_operation(str(i)) for i in range(user_count)]
        await asyncio.gather(*tasks)
        
        # 验证性能
        avg_operation_time = sum(operation_times) / len(operation_times)
        assert avg_operation_time < 2.0, f"Average operation time too high: {avg_operation_time}s"
        
        print(f"\n=== 数据库并发测试结果 ===")
        print(f"平均操作时间: {avg_operation_time:.3f}s")
        print(f"最大操作时间: {max(operation_times):.3f}s")
        print(f"最小操作时间: {min(operation_times):.3f}s")


def run_performance_benchmark():
    """运行性能基准测试"""
    
    client = TestClient(app)
    
    async def run_benchmarks():
        """运行所有基准测试"""
        
        print("=== 开始多用户场景性能基准测试 ===\n")
        
        # 测试不同用户规模
        user_counts = [5, 10, 20, 30]
        
        benchmark_results = []
        
        for user_count in user_counts:
            print(f"正在测试 {user_count} 个并发用户...")
            
            simulator = ConcurrentUserSimulator(client, user_count)
            result = await simulator.run_concurrent_test()
            
            benchmark_results.append({
                "user_count": user_count,
                **result
            })
            
            # 添加延迟，避免服务器过载
            await asyncio.sleep(2)
        
        # 输出基准测试报告
        print("\n=== 性能基准测试报告 ===")
        print("用户数\t成功率\t操作成功率\t总耗时\t吞吐量")
        print("-" * 60)
        
        for result in benchmark_results:
            print(f"{result['user_count']}\t"
                  f"{result['success_rate']:.2%}\t"
                  f"{result['action_success_rate']:.2%}\t\t"
                  f"{result['total_time']:.1f}s\t"
                  f"{result['throughput']:.1f} ops/s")
        
        return benchmark_results
    
    # 运行基准测试
    return asyncio.run(run_benchmarks())


if __name__ == "__main__":
    """直接运行性能基准测试"""
    results = run_performance_benchmark()
    
    # 保存测试结果
    import json
    with open("performance_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n测试结果已保存到 performance_benchmark_results.json")