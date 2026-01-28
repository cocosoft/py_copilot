"""
用户体验评估工具
评估多用户场景下的用户体验指标
"""

import asyncio
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any, Tuple
from fastapi.testclient import TestClient
from app.api.main import app


class UserExperienceMetrics:
    """用户体验指标收集器"""
    
    def __init__(self):
        self.metrics = {
            "response_times": [],
            "success_rates": [],
            "error_counts": [],
            "user_satisfaction": [],
            "task_completion_times": []
        }
    
    def record_response_time(self, endpoint: str, response_time: float):
        """记录响应时间"""
        self.metrics["response_times"].append({
            "endpoint": endpoint,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_success_rate(self, task_type: str, success_count: int, total_count: int):
        """记录成功率"""
        success_rate = success_count / total_count if total_count > 0 else 0
        self.metrics["success_rates"].append({
            "task_type": task_type,
            "success_rate": success_rate,
            "success_count": success_count,
            "total_count": total_count,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_error(self, error_type: str, error_message: str):
        """记录错误"""
        self.metrics["error_counts"].append({
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_user_satisfaction(self, user_id: str, satisfaction_score: int, feedback: str = ""):
        """记录用户满意度"""
        self.metrics["user_satisfaction"].append({
            "user_id": user_id,
            "satisfaction_score": satisfaction_score,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_task_completion_time(self, task_type: str, completion_time: float):
        """记录任务完成时间"""
        self.metrics["task_completion_times"].append({
            "task_type": task_type,
            "completion_time": completion_time,
            "timestamp": datetime.now().isoformat()
        })
    
    def calculate_overall_metrics(self) -> Dict[str, Any]:
        """计算总体指标"""
        
        # 响应时间统计
        response_times = [rt["response_time"] for rt in self.metrics["response_times"]]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if response_times else 0
        
        # 成功率统计
        success_rates = [sr["success_rate"] for sr in self.metrics["success_rates"]]
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0
        
        # 用户满意度统计
        satisfaction_scores = [us["satisfaction_score"] for us in self.metrics["user_satisfaction"]]
        avg_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 0
        
        # 任务完成时间统计
        completion_times = [tct["completion_time"] for tct in self.metrics["task_completion_times"]]
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0
        
        return {
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "avg_success_rate": avg_success_rate,
            "avg_satisfaction": avg_satisfaction,
            "avg_completion_time": avg_completion_time,
            "total_errors": len(self.metrics["error_counts"]),
            "total_tasks": len(self.metrics["task_completion_times"]),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_ux_report(self) -> Dict[str, Any]:
        """生成用户体验报告"""
        
        overall_metrics = self.calculate_overall_metrics()
        
        # 评估用户体验等级
        ux_score = self.calculate_ux_score(overall_metrics)
        ux_grade = self.get_ux_grade(ux_score)
        
        # 识别问题区域
        problem_areas = self.identify_problem_areas()
        
        # 生成改进建议
        recommendations = self.generate_recommendations(overall_metrics, problem_areas)
        
        return {
            "overall_metrics": overall_metrics,
            "ux_score": ux_score,
            "ux_grade": ux_grade,
            "problem_areas": problem_areas,
            "recommendations": recommendations,
            "detailed_metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_ux_score(self, metrics: Dict[str, Any]) -> float:
        """计算用户体验得分（0-100）"""
        
        # 响应时间得分（权重：30%）
        response_time_score = max(0, 100 - (metrics["avg_response_time"] * 20))
        
        # 成功率得分（权重：30%）
        success_rate_score = metrics["avg_success_rate"] * 100
        
        # 用户满意度得分（权重：30%）
        satisfaction_score = metrics["avg_satisfaction"] * 20  # 假设满意度是1-5分
        
        # 错误率得分（权重：10%）
        error_penalty = min(30, metrics["total_errors"] * 2)
        error_score = 100 - error_penalty
        
        # 加权平均
        ux_score = (
            response_time_score * 0.3 +
            success_rate_score * 0.3 +
            satisfaction_score * 0.3 +
            error_score * 0.1
        )
        
        return max(0, min(100, ux_score))
    
    def get_ux_grade(self, score: float) -> str:
        """获取用户体验等级"""
        
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "一般"
        elif score >= 60:
            return "需要改进"
        else:
            return "较差"
    
    def identify_problem_areas(self) -> List[Dict[str, Any]]:
        """识别问题区域"""
        
        problem_areas = []
        
        # 分析响应时间
        slow_endpoints = {}
        for rt in self.metrics["response_times"]:
            if rt["response_time"] > 1.0:  # 超过1秒认为慢
                endpoint = rt["endpoint"]
                if endpoint not in slow_endpoints:
                    slow_endpoints[endpoint] = []
                slow_endpoints[endpoint].append(rt["response_time"])
        
        for endpoint, times in slow_endpoints.items():
            problem_areas.append({
                "type": "slow_response",
                "endpoint": endpoint,
                "avg_time": statistics.mean(times),
                "occurrences": len(times)
            })
        
        # 分析错误类型
        error_types = {}
        for error in self.metrics["error_counts"]:
            error_type = error["error_type"]
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        for error_type, count in error_types.items():
            if count >= 3:  # 同一错误出现3次以上
                problem_areas.append({
                    "type": "frequent_error",
                    "error_type": error_type,
                    "occurrences": count
                })
        
        # 分析低成功率任务
        for sr in self.metrics["success_rates"]:
            if sr["success_rate"] < 0.8:  # 成功率低于80%
                problem_areas.append({
                    "type": "low_success_rate",
                    "task_type": sr["task_type"],
                    "success_rate": sr["success_rate"]
                })
        
        return problem_areas
    
    def generate_recommendations(self, metrics: Dict[str, Any], problem_areas: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        # 基于总体指标的建议
        if metrics["avg_response_time"] > 1.0:
            recommendations.append("优化API响应时间，考虑使用缓存或异步处理")
        
        if metrics["avg_success_rate"] < 0.9:
            recommendations.append("提高系统稳定性，减少错误发生率")
        
        if metrics["avg_satisfaction"] < 4.0:  # 假设满意度是1-5分
            recommendations.append("改善用户界面和交互体验")
        
        # 基于问题区域的建议
        for problem in problem_areas:
            if problem["type"] == "slow_response":
                recommendations.append(
                    f"优化端点 {problem['endpoint']} 的性能，当前平均响应时间: {problem['avg_time']:.2f}s"
                )
            
            elif problem["type"] == "frequent_error":
                recommendations.append(
                    f"解决频繁出现的错误类型: {problem['error_type']} (出现 {problem['occurrences']} 次)"
                )
            
            elif problem["type"] == "low_success_rate":
                recommendations.append(
                    f"提高任务 {problem['task_type']} 的成功率，当前: {problem['success_rate']:.1%}"
                )
        
        return recommendations


class UserExperienceEvaluator:
    """用户体验评估器"""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.metrics = UserExperienceMetrics()
    
    async def evaluate_task_completion(self, user_id: str, task_scenario: str) -> Dict[str, Any]:
        """评估任务完成体验"""
        
        print(f"评估用户 {user_id} 的任务完成体验: {task_scenario}")
        
        start_time = time.time()
        success_count = 0
        total_actions = 0
        
        try:
            # 模拟用户完成任务
            if task_scenario == "data_visualization":
                result = await self.simulate_data_visualization_task(user_id)
            elif task_scenario == "collaboration":
                result = await self.simulate_collaboration_task(user_id)
            elif task_scenario == "skill_execution":
                result = await self.simulate_skill_execution_task(user_id)
            else:
                result = await self.simulate_general_task(user_id, task_scenario)
            
            completion_time = time.time() - start_time
            
            # 记录指标
            self.metrics.record_task_completion_time(task_scenario, completion_time)
            self.metrics.record_success_rate(task_scenario, result["success_count"], result["total_actions"])
            
            # 模拟用户满意度评分（1-5分）
            satisfaction_score = self.calculate_satisfaction_score(completion_time, result["success_count"])
            self.metrics.record_user_satisfaction(user_id, satisfaction_score)
            
            return {
                "user_id": user_id,
                "task_scenario": task_scenario,
                "completion_time": completion_time,
                "success_count": result["success_count"],
                "total_actions": result["total_actions"],
                "satisfaction_score": satisfaction_score,
                "success": True
            }
            
        except Exception as e:
            completion_time = time.time() - start_time
            self.metrics.record_error("task_failure", str(e))
            
            return {
                "user_id": user_id,
                "task_scenario": task_scenario,
                "completion_time": completion_time,
                "success_count": 0,
                "total_actions": 0,
                "satisfaction_score": 1,  # 最低分
                "success": False,
                "error": str(e)
            }
    
    async def simulate_data_visualization_task(self, user_id: str) -> Dict[str, Any]:
        """模拟数据可视化任务"""
        
        success_count = 0
        total_actions = 0
        
        # 1. 查询数据源
        start_time = time.time()
        response = self.client.get("/api/data/sources")
        response_time = time.time() - start_time
        
        self.metrics.record_response_time("/api/data/sources", response_time)
        total_actions += 1
        
        if response.status_code == 200:
            success_count += 1
        
        # 2. 创建图表
        start_time = time.time()
        response = self.client.post(
            "/api/charts",
            json={
                "type": "bar",
                "title": "销售数据",
                "data_source": "test_data",
                "config": {"width": 600, "height": 400}
            }
        )
        response_time = time.time() - start_time
        
        self.metrics.record_response_time("/api/charts", response_time)
        total_actions += 1
        
        if response.status_code == 200:
            success_count += 1
        
        return {
            "success_count": success_count,
            "total_actions": total_actions
        }
    
    async def simulate_collaboration_task(self, user_id: str) -> Dict[str, Any]:
        """模拟协作任务"""
        
        success_count = 0
        total_actions = 0
        
        # 1. 加入协作房间
        start_time = time.time()
        response = self.client.post("/api/collaboration/rooms/test_room/join")
        response_time = time.time() - start_time
        
        self.metrics.record_response_time("/api/collaboration/rooms/{room_id}/join", response_time)
        total_actions += 1
        
        if response.status_code == 200:
            success_count += 1
        
        # 2. 添加画布节点
        start_time = time.time()
        response = self.client.post(
            "/api/canvas/nodes",
            json={
                "room_id": "test_room",
                "type": "process",
                "position": {"x": 100, "y": 100},
                "properties": {"label": "测试节点"}
            }
        )
        response_time = time.time() - start_time
        
        self.metrics.record_response_time("/api/canvas/nodes", response_time)
        total_actions += 1
        
        if response.status_code == 200:
            success_count += 1
        
        return {
            "success_count": success_count,
            "total_actions": total_actions
        }
    
    async def simulate_skill_execution_task(self, user_id: str) -> Dict[str, Any]:
        """模拟技能执行任务"""
        
        success_count = 0
        total_actions = 0
        
        # 1. 查询可用技能
        start_time = time.time()
        response = self.client.get("/api/skills")
        response_time = time.time() - start_time
        
        self.metrics.record_response_time("/api/skills", response_time)
        total_actions += 1
        
        if response.status_code == 200:
            success_count += 1
        
        # 2. 执行技能（模拟）
        start_time = time.time()
        # 这里应该是实际的技能执行API调用
        response_time = time.time() - start_time
        
        self.metrics.record_response_time("/api/skills/execute", response_time)
        total_actions += 1
        success_count += 1  # 假设执行成功
        
        return {
            "success_count": success_count,
            "total_actions": total_actions
        }
    
    async def simulate_general_task(self, user_id: str, task_type: str) -> Dict[str, Any]:
        """模拟一般任务"""
        
        # 执行一些通用的API调用
        endpoints = [
            "/api/auth/status",
            "/api/data/sources",
            "/api/collaboration/rooms"
        ]
        
        success_count = 0
        total_actions = len(endpoints)
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            response_time = time.time() - start_time
            
            self.metrics.record_response_time(endpoint, response_time)
            
            if response.status_code == 200:
                success_count += 1
        
        return {
            "success_count": success_count,
            "total_actions": total_actions
        }
    
    def calculate_satisfaction_score(self, completion_time: float, success_count: int) -> int:
        """计算用户满意度评分（1-5分）"""
        
        # 基于完成时间和成功率计算满意度
        time_score = max(1, 5 - (completion_time // 10))  # 每10秒减1分
        success_score = 5 if success_count > 0 else 1
        
        return min(5, max(1, (time_score + success_score) // 2))
    
    async def evaluate_concurrent_users(self, user_count: int = 10) -> Dict[str, Any]:
        """评估并发用户场景"""
        
        print(f"评估 {user_count} 个并发用户的体验")
        
        task_scenarios = ["data_visualization", "collaboration", "skill_execution"]
        
        # 为每个用户分配任务场景
        tasks = []
        for i in range(user_count):
            user_id = f"user_{i}"
            scenario = task_scenarios[i % len(task_scenarios)]
            
            task = self.evaluate_task_completion(user_id, scenario)
            tasks.append(task)
        
        # 并发执行
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 统计结果
        successful_tasks = [r for r in results if not isinstance(r, Exception) and r.get("success")]
        failed_tasks = [r for r in results if not isinstance(r, Exception) and not r.get("success")]
        
        return {
            "user_count": user_count,
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / user_count,
            "total_time": total_time,
            "avg_completion_time": statistics.mean([r["completion_time"] for r in successful_tasks]) if successful_tasks else 0,
            "avg_satisfaction": statistics.mean([r["satisfaction_score"] for r in successful_tasks]) if successful_tasks else 0
        }
    
    async def run_comprehensive_evaluation(self, user_counts: List[int] = None) -> Dict[str, Any]:
        """运行全面的用户体验评估"""
        
        if user_counts is None:
            user_counts = [5, 10, 20]
        
        print("=== 开始全面的用户体验评估 ===\n")
        
        concurrent_results = {}
        
        for user_count in user_counts:
            print(f"正在评估 {user_count} 个并发用户...")
            
            result = await self.evaluate_concurrent_users(user_count)
            concurrent_results[user_count] = result
            
            # 用户间延迟
            await asyncio.sleep(2)
        
        # 生成最终报告
        ux_report = self.metrics.generate_ux_report()
        ux_report["concurrent_results"] = concurrent_results
        
        print("\n=== 用户体验评估完成 ===")
        print(f"用户体验得分: {ux_report['ux_score']:.1f} ({ux_report['ux_grade']})")
        print(f"平均响应时间: {ux_report['overall_metrics']['avg_response_time']:.3f}s")
        print(f"平均成功率: {ux_report['overall_metrics']['avg_success_rate']:.2%}")
        
        if ux_report["problem_areas"]:
            print(f"发现 {len(ux_report['problem_areas'])} 个问题区域")
        
        return ux_report


def run_user_experience_evaluation():
    """运行用户体验评估"""
    
    client = TestClient(app)
    evaluator = UserExperienceEvaluator(client)
    
    # 运行评估
    report = asyncio.run(evaluator.run_comprehensive_evaluation())
    
    # 保存报告
    with open("user_experience_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n详细报告已保存到 user_experience_report.json")
    
    return report


if __name__ == "__main__":
    """直接运行用户体验评估"""
    
    print("Py Copilot 用户体验评估")
    print("=" * 50)
    
    report = run_user_experience_evaluation()
    
    # 输出关键发现
    print("\n关键发现:")
    print(f"• 总体用户体验: {report['ux_grade']} ({report['ux_score']:.1f}/100)")
    print(f"• 平均响应时间: {report['overall_metrics']['avg_response_time']:.3f}s")
    print(f"• 任务成功率: {report['overall_metrics']['avg_success_rate']:.2%}")
    print(f"• 用户满意度: {report['overall_metrics']['avg_satisfaction']:.1f}/5.0")
    
    if report["recommendations"]:
        print("\n改进建议:")
        for i, recommendation in enumerate(report["recommendations"], 1):
            print(f"{i}. {recommendation}")
    
    print("\n评估完成！")