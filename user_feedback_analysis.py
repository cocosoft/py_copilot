#!/usr/bin/env python3
"""
用户反馈收集和分析工具
基于实际使用场景收集和分析用户反馈
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('user_feedback_analysis')

class UserFeedbackAnalyzer:
    """用户反馈分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.feedback_data = []
        self.analysis_results = {}
    
    def collect_test_feedback(self) -> List[Dict[str, Any]]:
        """收集测试反馈数据"""
        feedback = []
        
        # 基于用户验收测试结果
        test_results = self._load_test_results()
        
        # 从测试结果中提取反馈
        if test_results:
            for test in test_results.get('results', []):
                if not test.get('success'):
                    feedback.append({
                        "feedback_id": f"test_{test.get('test_id')}",
                        "type": "bug",
                        "severity": "medium",
                        "category": "system_test",
                        "title": f"{test.get('test_name')}测试失败",
                        "description": f"{test.get('test_name')}测试未能通过，可能存在功能问题",
                        "status": "open",
                        "priority": "medium",
                        "created_at": datetime.now().isoformat(),
                        "source": "automated_test"
                    })
        
        # 基于系统状态分析
        system_feedback = self._analyze_system_state()
        feedback.extend(system_feedback)
        
        # 基于用户体验分析
        ux_feedback = self._analyze_user_experience()
        feedback.extend(ux_feedback)
        
        self.feedback_data = feedback
        return feedback
    
    def _load_test_results(self) -> Dict[str, Any]:
        """加载测试结果"""
        # 查找最新的测试报告
        test_reports = [f for f in os.listdir('.') if f.startswith('user_acceptance_report_') and f.endswith('.json')]
        if not test_reports:
            logger.warning("未找到测试报告文件")
            return {}
        
        # 按时间排序，取最新的
        test_reports.sort(reverse=True)
        latest_report = test_reports[0]
        
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载测试报告失败: {e}")
            return {}
    
    def _analyze_system_state(self) -> List[Dict[str, Any]]:
        """分析系统状态"""
        feedback = []
        
        # 检查服务状态
        services = [
            {"name": "backend", "url": "http://localhost:8000/api/health", "status": "unknown"},
            {"name": "frontend", "url": "http://localhost:3000", "status": "unknown"},
            {"name": "chromadb", "url": "http://localhost:8008", "status": "unknown"}
        ]
        
        try:
            import requests
            for service in services:
                try:
                    response = requests.get(service['url'], timeout=5)
                    if response.status_code == 200:
                        service['status'] = "healthy"
                    else:
                        service['status'] = "unhealthy"
                except Exception:
                    service['status'] = "down"
        except ImportError:
            logger.warning("未安装requests库，跳过服务状态检查")
        
        # 基于服务状态生成反馈
        for service in services:
            if service['status'] != "healthy":
                feedback.append({
                    "feedback_id": f"service_{service['name']}",
                    "type": "system",
                    "severity": "high" if service['status'] == "down" else "medium",
                    "category": "service_status",
                    "title": f"{service['name']}服务状态异常",
                    "description": f"{service['name']}服务当前状态为: {service['status']}，可能影响系统正常运行",
                    "status": "open",
                    "priority": "high" if service['status'] == "down" else "medium",
                    "created_at": datetime.now().isoformat(),
                    "source": "system_analysis"
                })
        
        return feedback
    
    def _analyze_user_experience(self) -> List[Dict[str, Any]]:
        """分析用户体验"""
        feedback = []
        
        # 分析导航结构
        try:
            with open('e:\\PY\\CODES\\py copilot IV\\frontend\\src\\layouts\\KnowledgeLayout\\index.jsx', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'TABS' in content:
                    # 检查导航顺序是否正确
                    expected_order = [
                        'documents', 'vectorization', 'entity-recognition', 
                        'entity-relationships', 'knowledge-graph', 'reranking', 
                        'search', 'settings'
                    ]
                    # 简单检查导航项是否存在
                    for item in expected_order:
                        if item not in content:
                            feedback.append({
                                "feedback_id": f"nav_{item}",
                                "type": "ux",
                                "severity": "low",
                                "category": "navigation",
                                "title": f"导航项缺失: {item}",
                                "description": f"知识库导航中缺少{item}项，可能影响用户体验",
                                "status": "open",
                                "priority": "low",
                                "created_at": datetime.now().isoformat(),
                                "source": "ux_analysis"
                            })
        except Exception as e:
            logger.error(f"分析导航结构失败: {e}")
        
        # 分析功能完整性
        features = [
            "文档管理", "向量化", "实体识别", "实体关系", 
            "知识图谱", "重排序", "高级搜索", "设置"
        ]
        
        for feature in features:
            # 这里可以根据实际情况检查功能是否完整
            # 暂时基于文件名存在性进行简单检查
            feature_files = {
                "文档管理": "DocumentManagement",
                "向量化": "Vectorization",
                "实体识别": "EntityRecognition",
                "实体关系": "EntityRelationships",
                "知识图谱": "KnowledgeGraph",
                "重排序": "Reranking",
                "高级搜索": "Search",
                "设置": "Settings"
            }
            
            if feature in feature_files:
                feature_dir = f"e:\\PY\\CODES\\py copilot IV\\frontend\\src\\pages\\knowledge\\{feature_files[feature]}"
                if not os.path.exists(feature_dir):
                    feedback.append({
                        "feedback_id": f"feature_{feature}",
                        "type": "feature",
                        "severity": "medium",
                        "category": "feature_completeness",
                        "title": f"功能模块缺失: {feature}",
                        "description": f"{feature}功能模块可能未实现，影响系统完整性",
                        "status": "open",
                        "priority": "medium",
                        "created_at": datetime.now().isoformat(),
                        "source": "feature_analysis"
                    })
        
        return feedback
    
    def analyze_feedback(self) -> Dict[str, Any]:
        """分析反馈数据"""
        if not self.feedback_data:
            self.collect_test_feedback()
        
        # 按类型分组
        by_type = {}
        by_severity = {}
        by_category = {}
        
        for feedback in self.feedback_data:
            # 按类型分组
            feedback_type = feedback.get('type')
            if feedback_type not in by_type:
                by_type[feedback_type] = []
            by_type[feedback_type].append(feedback)
            
            # 按严重程度分组
            severity = feedback.get('severity')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(feedback)
            
            # 按类别分组
            category = feedback.get('category')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(feedback)
        
        # 生成分析结果
        self.analysis_results = {
            "summary": {
                "total_feedback": len(self.feedback_data),
                "by_type": {k: len(v) for k, v in by_type.items()},
                "by_severity": {k: len(v) for k, v in by_severity.items()},
                "by_category": {k: len(v) for k, v in by_category.items()}
            },
            "detailed_analysis": {
                "by_type": by_type,
                "by_severity": by_severity,
                "by_category": by_category
            },
            "recommendations": self._generate_recommendations()
        }
        
        return self.analysis_results
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成改进建议"""
        recommendations = []
        
        # 基于反馈生成建议
        for feedback in self.feedback_data:
            if feedback.get('type') == "bug":
                recommendations.append({
                    "id": f"rec_{feedback.get('feedback_id')}",
                    "title": f"修复{feedback.get('title')}",
                    "description": feedback.get('description'),
                    "priority": feedback.get('priority'),
                    "estimated_effort": "low" if feedback.get('severity') == "low" else "medium",
                    "status": "recommended",
                    "related_feedback": feedback.get('feedback_id')
                })
            elif feedback.get('type') == "feature":
                recommendations.append({
                    "id": f"rec_{feedback.get('feedback_id')}",
                    "title": f"实现{feedback.get('title')}",
                    "description": feedback.get('description'),
                    "priority": feedback.get('priority'),
                    "estimated_effort": "medium",
                    "status": "recommended",
                    "related_feedback": feedback.get('feedback_id')
                })
            elif feedback.get('type') == "ux":
                recommendations.append({
                    "id": f"rec_{feedback.get('feedback_id')}",
                    "title": f"优化{feedback.get('title')}",
                    "description": feedback.get('description'),
                    "priority": feedback.get('priority'),
                    "estimated_effort": "low",
                    "status": "recommended",
                    "related_feedback": feedback.get('feedback_id')
                })
        
        # 添加系统级建议
        recommendations.extend([
            {
                "id": "rec_system_monitoring",
                "title": "建立系统监控机制",
                "description": "实现服务状态监控，及时发现和处理服务异常",
                "priority": "high",
                "estimated_effort": "medium",
                "status": "recommended",
                "related_feedback": "system_analysis"
            },
            {
                "id": "rec_user_testing",
                "title": "开展用户测试",
                "description": "组织真实用户测试，收集实际使用场景的反馈",
                "priority": "medium",
                "estimated_effort": "high",
                "status": "recommended",
                "related_feedback": "ux_analysis"
            },
            {
                "id": "rec_documentation",
                "title": "完善系统文档",
                "description": "编写详细的系统文档，包括功能说明、API文档和使用指南",
                "priority": "medium",
                "estimated_effort": "medium",
                "status": "recommended",
                "related_feedback": "system_analysis"
            }
        ])
        
        return recommendations
    
    def generate_report(self) -> Dict[str, Any]:
        """生成反馈分析报告"""
        if not self.analysis_results:
            self.analyze_feedback()
        
        report = {
            "report_date": datetime.now().isoformat(),
            "feedback_data": self.feedback_data,
            "analysis": self.analysis_results
        }
        
        # 保存报告
        report_filename = f"user_feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"用户反馈分析报告已保存至: {report_filename}")
        return report

def main():
    """主函数"""
    # 初始化分析器
    analyzer = UserFeedbackAnalyzer()
    
    # 收集反馈
    feedback = analyzer.collect_test_feedback()
    logger.info(f"收集到 {len(feedback)} 条用户反馈")
    
    # 分析反馈
    analysis = analyzer.analyze_feedback()
    
    # 生成报告
    report = analyzer.generate_report()
    
    # 打印摘要
    print("\n用户反馈分析摘要:")
    print(f"分析时间: {report['report_date']}")
    print(f"总反馈数: {report['analysis']['summary']['total_feedback']}")
    print(f"按类型分布: {report['analysis']['summary']['by_type']}")
    print(f"按严重程度分布: {report['analysis']['summary']['by_severity']}")
    print(f"按类别分布: {report['analysis']['summary']['by_category']}")
    
    print("\n推荐改进项:")
    for rec in report['analysis']['recommendations'][:5]:  # 只显示前5个
        print(f"- {rec['title']} (优先级: {rec['priority']})")
    
    if len(report['analysis']['recommendations']) > 5:
        print(f"... 还有 {len(report['analysis']['recommendations']) - 5} 个推荐项")
    
    print("\n详细报告已保存至 JSON 文件")

if __name__ == "__main__":
    main()
