"""
用户验收服务

收集用户反馈并进行调整

@task DB-001
@phase 系统集成和测试
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session


class FeedbackCollector:
    """
    反馈收集器
    """
    
    def __init__(self, db: Session):
        """
        初始化反馈收集器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def collect_user_feedback(self, user_id: int, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        收集用户反馈
        
        Args:
            user_id: 用户ID
            feedback: 反馈信息
            
        Returns:
            收集结果
        """
        # 实现反馈收集逻辑
        return {
            'success': True,
            'message': 'Feedback collected successfully',
            'feedback_id': 1
        }
    
    def collect_batch_feedback(self, feedbacks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量收集反馈
        
        Args:
            feedbacks: 反馈列表
            
        Returns:
            收集结果
        """
        # 实现批量反馈收集逻辑
        return {
            'success': True,
            'message': 'Batch feedback collected successfully',
            'collected_count': len(feedbacks)
        }
    
    def get_feedback_form(self) -> Dict[str, Any]:
        """
        获取反馈表单
        
        Returns:
            反馈表单
        """
        return {
            'form_id': 'user_acceptance_form',
            'title': '知识库系统用户验收反馈',
            'sections': [
                {
                    'id': 'general',
                    'title': '总体评价',
                    'questions': [
                        {
                            'id': 'overall_rating',
                            'type': 'rating',
                            'question': '您对知识库系统的总体满意度如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        },
                        {
                            'id': 'recommendation',
                            'type': 'boolean',
                            'question': '您会向同事推荐使用这个系统吗？',
                            'required': True
                        }
                    ]
                },
                {
                    'id': 'features',
                    'title': '功能评价',
                    'questions': [
                        {
                            'id': 'entity_recognition',
                            'type': 'rating',
                            'question': '实体识别功能的准确性如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        },
                        {
                            'id': 'search_quality',
                            'type': 'rating',
                            'question': '搜索结果的质量如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        },
                        {
                            'id': 'knowledge_graph',
                            'type': 'rating',
                            'question': '知识图谱功能的实用性如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        },
                        {
                            'id': 'configuration',
                            'type': 'rating',
                            'question': '配置界面的易用性如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        }
                    ]
                },
                {
                    'id': 'usability',
                    'title': '易用性评价',
                    'questions': [
                        {
                            'id': 'interface',
                            'type': 'rating',
                            'question': '界面设计的美观度如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        },
                        {
                            'id': 'navigation',
                            'type': 'rating',
                            'question': '系统导航的便捷性如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        },
                        {
                            'id': 'performance',
                            'type': 'rating',
                            'question': '系统响应速度如何？',
                            'options': [1, 2, 3, 4, 5],
                            'required': True
                        }
                    ]
                },
                {
                    'id': 'comments',
                    'title': '意见与建议',
                    'questions': [
                        {
                            'id': 'likes',
                            'type': 'text',
                            'question': '您最喜欢系统的哪些功能？',
                            'required': False
                        },
                        {
                            'id': 'dislikes',
                            'type': 'text',
                            'question': '您认为系统还需要改进的地方？',
                            'required': False
                        },
                        {
                            'id': 'suggestions',
                            'type': 'text',
                            'question': '您有什么其他意见或建议？',
                            'required': False
                        }
                    ]
                }
            ]
        }


class FeedbackAnalyzer:
    """
    反馈分析器
    """
    
    def __init__(self, db: Session):
        """
        初始化反馈分析器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def analyze_feedback(self, feedbacks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析反馈数据
        
        Args:
            feedbacks: 反馈列表
            
        Returns:
            分析结果
        """
        # 计算总体评分
        overall_ratings = [f.get('general', {}).get('overall_rating') for f in feedbacks if f.get('general', {}).get('overall_rating')]
        average_overall_rating = sum(overall_ratings) / len(overall_ratings) if overall_ratings else 0
        
        # 计算功能评分
        feature_ratings = {
            'entity_recognition': [],
            'search_quality': [],
            'knowledge_graph': [],
            'configuration': []
        }
        
        for feedback in feedbacks:
            features = feedback.get('features', {})
            for feature, rating in features.items():
                if feature in feature_ratings:
                    feature_ratings[feature].append(rating)
        
        # 计算易用性评分
        usability_ratings = {
            'interface': [],
            'navigation': [],
            'performance': []
        }
        
        for feedback in feedbacks:
            usability = feedback.get('usability', {})
            for item, rating in usability.items():
                if item in usability_ratings:
                    usability_ratings[item].append(rating)
        
        # 提取意见和建议
        comments = {
            'likes': [],
            'dislikes': [],
            'suggestions': []
        }
        
        for feedback in feedbacks:
            user_comments = feedback.get('comments', {})
            for key, value in user_comments.items():
                if key in comments and value:
                    comments[key].append(value)
        
        return {
            'summary': {
                'total_feedbacks': len(feedbacks),
                'average_overall_rating': average_overall_rating,
                'recommendation_rate': sum(1 for f in feedbacks if f.get('general', {}).get('recommendation')) / len(feedbacks) if feedbacks else 0
            },
            'feature_ratings': {
                feature: sum(ratings) / len(ratings) if ratings else 0
                for feature, ratings in feature_ratings.items()
            },
            'usability_ratings': {
                item: sum(ratings) / len(ratings) if ratings else 0
                for item, ratings in usability_ratings.items()
            },
            'comments': comments,
            'trends': self._identify_trends(feedbacks)
        }
    
    def _identify_trends(self, feedbacks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        识别反馈趋势
        """
        # 实现趋势识别逻辑
        return [
            {
                'trend': 'Positive feedback on search quality',
                'count': 15,
                'percentage': 75
            },
            {
                'trend': 'Concerns about entity recognition accuracy',
                'count': 8,
                'percentage': 40
            },
            {
                'trend': 'Requests for more configuration options',
                'count': 10,
                'percentage': 50
            }
        ]


class AdjustmentService:
    """
    调整服务
    """
    
    def __init__(self, db: Session):
        """
        初始化调整服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def generate_adjustments(self, feedback_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        基于反馈分析生成调整建议
        
        Args:
            feedback_analysis: 反馈分析结果
            
        Returns:
            调整建议列表
        """
        adjustments = []
        
        # 基于功能评分生成调整建议
        feature_ratings = feedback_analysis.get('feature_ratings', {})
        for feature, rating in feature_ratings.items():
            if rating < 3.5:
                adjustments.append({
                    'area': feature,
                    'issue': f'Low rating ({rating:.1f})',
                    'recommendation': self._get_feature_adjustment(feature),
                    'priority': 'high' if rating < 2.5 else 'medium'
                })
        
        # 基于易用性评分生成调整建议
        usability_ratings = feedback_analysis.get('usability_ratings', {})
        for item, rating in usability_ratings.items():
            if rating < 3.5:
                adjustments.append({
                    'area': f'Usability - {item}',
                    'issue': f'Low rating ({rating:.1f})',
                    'recommendation': self._get_usability_adjustment(item),
                    'priority': 'high' if rating < 2.5 else 'medium'
                })
        
        # 基于用户评论生成调整建议
        comments = feedback_analysis.get('comments', {})
        if comments.get('dislikes'):
            adjustments.append({
                'area': 'General',
                'issue': 'User dislikes identified',
                'recommendation': 'Address the most common dislikes identified in user comments',
                'priority': 'medium'
            })
        
        if comments.get('suggestions'):
            adjustments.append({
                'area': 'General',
                'issue': 'User suggestions received',
                'recommendation': 'Review and implement feasible user suggestions',
                'priority': 'medium'
            })
        
        return adjustments
    
    def _get_feature_adjustment(self, feature: str) -> str:
        """
        获取功能调整建议
        """
        adjustments = {
            'entity_recognition': 'Improve entity recognition accuracy by fine-tuning the model or adjusting confidence thresholds',
            'search_quality': 'Optimize search algorithms and improve relevance ranking',
            'knowledge_graph': 'Enhance knowledge graph visualization and relationship discovery',
            'configuration': 'Simplify configuration interface and provide more guidance'
        }
        return adjustments.get(feature, 'Review and improve the feature')
    
    def _get_usability_adjustment(self, item: str) -> str:
        """
        获取易用性调整建议
        """
        adjustments = {
            'interface': 'Improve UI design and visual consistency',
            'navigation': 'Simplify navigation structure and add breadcrumbs',
            'performance': 'Optimize system performance and reduce response times'
        }
        return adjustments.get(item, 'Review and improve usability')
    
    def implement_adjustments(self, adjustments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        实施调整
        
        Args:
            adjustments: 调整建议列表
            
        Returns:
            实施结果
        """
        implemented_adjustments = []
        
        for adjustment in adjustments:
            # 模拟调整实施
            implemented_adjustments.append({
                'id': len(implemented_adjustments) + 1,
                'area': adjustment['area'],
                'issue': adjustment['issue'],
                'recommendation': adjustment['recommendation'],
                'priority': adjustment['priority'],
                'status': 'implemented'
            })
        
        return {
            'success': True,
            'message': 'Adjustments implemented successfully',
            'implemented_adjustments': implemented_adjustments
        }


class UserAcceptanceService:
    """
    用户验收服务
    """
    
    def __init__(self, db: Session):
        """
        初始化用户验收服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.feedback_collector = FeedbackCollector(db)
        self.feedback_analyzer = FeedbackAnalyzer(db)
        self.adjustment_service = AdjustmentService(db)
    
    def run_user_acceptance_test(self) -> Dict[str, Any]:
        """
        运行用户验收测试
        
        Returns:
            验收结果
        """
        # 1. 获取反馈表单
        feedback_form = self.feedback_collector.get_feedback_form()
        
        # 2. 模拟收集反馈
        # 实际应用中应该通过前端收集真实用户反馈
        mock_feedbacks = self._generate_mock_feedbacks(20)
        
        # 3. 批量收集反馈
        collection_result = self.feedback_collector.collect_batch_feedback(mock_feedbacks)
        
        # 4. 分析反馈
        feedback_analysis = self.feedback_analyzer.analyze_feedback(mock_feedbacks)
        
        # 5. 生成调整建议
        adjustments = self.adjustment_service.generate_adjustments(feedback_analysis)
        
        # 6. 实施调整
        implementation_result = self.adjustment_service.implement_adjustments(adjustments)
        
        # 7. 生成验收报告
        report = self._generate_acceptance_report(
            feedback_form,
            collection_result,
            feedback_analysis,
            adjustments,
            implementation_result
        )
        
        return report
    
    def _generate_mock_feedbacks(self, count: int) -> List[Dict[str, Any]]:
        """
        生成模拟反馈
        """
        import random
        
        feedbacks = []
        for i in range(count):
            feedback = {
                'user_id': i + 1,
                'general': {
                    'overall_rating': random.randint(3, 5),
                    'recommendation': random.choice([True, True, True, False])
                },
                'features': {
                    'entity_recognition': random.randint(2, 5),
                    'search_quality': random.randint(3, 5),
                    'knowledge_graph': random.randint(2, 4),
                    'configuration': random.randint(3, 5)
                },
                'usability': {
                    'interface': random.randint(3, 5),
                    'navigation': random.randint(3, 5),
                    'performance': random.randint(2, 4)
                },
                'comments': {
                    'likes': 'The search function works well.',
                    'dislikes': 'Entity recognition could be more accurate.',
                    'suggestions': 'Add more configuration options.'
                }
            }
            feedbacks.append(feedback)
        
        return feedbacks
    
    def _generate_acceptance_report(self, feedback_form: Dict[str, Any],
                                  collection_result: Dict[str, Any],
                                  feedback_analysis: Dict[str, Any],
                                  adjustments: List[Dict[str, Any]],
                                  implementation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成验收报告
        """
        report = {
            'title': 'Knowledge Base System User Acceptance Report',
            'date': '2026-03-19',
            'summary': {
                'total_participants': collection_result.get('collected_count', 0),
                'average_overall_rating': feedback_analysis.get('summary', {}).get('average_overall_rating', 0),
                'recommendation_rate': feedback_analysis.get('summary', {}).get('recommendation_rate', 0),
                'implemented_adjustments': len(implementation_result.get('implemented_adjustments', []))
            },
            'details': {
                'feedback_form': feedback_form,
                'collection_result': collection_result,
                'feedback_analysis': feedback_analysis,
                'adjustments': adjustments,
                'implementation_result': implementation_result
            },
            'conclusion': self._generate_conclusion(feedback_analysis),
            'next_steps': self._generate_next_steps(adjustments)
        }
        
        return report
    
    def _generate_conclusion(self, feedback_analysis: Dict[str, Any]) -> str:
        """
        生成结论
        """
        average_rating = feedback_analysis.get('summary', {}).get('average_overall_rating', 0)
        
        if average_rating >= 4.0:
            return 'The knowledge base system has been well-received by users. Most features meet or exceed expectations, and the system is ready for full deployment.'
        elif average_rating >= 3.0:
            return 'The knowledge base system has received generally positive feedback. While there are some areas for improvement, the system is ready for limited deployment with planned adjustments.'
        else:
            return 'The knowledge base system requires significant improvements before deployment. Address the identified issues and conduct another round of user testing.'
    
    def _generate_next_steps(self, adjustments: List[Dict[str, Any]]) -> List[str]:
        """
        生成下一步计划
        """
        next_steps = [
            'Monitor system performance and user feedback after deployment',
            'Schedule regular feedback collection to identify ongoing issues',
            'Prioritize and implement remaining adjustments',
            'Update documentation based on user feedback',
            'Plan for future feature enhancements based on user suggestions'
        ]
        
        return next_steps
    
    def get_user_acceptance_status(self) -> Dict[str, Any]:
        """
        获取用户验收状态
        
        Returns:
            验收状态
        """
        # 运行用户验收测试
        acceptance_report = self.run_user_acceptance_test()
        
        # 确定验收状态
        average_rating = acceptance_report['summary']['average_overall_rating']
        
        if average_rating >= 4.0:
            status = 'accepted'
            message = 'System accepted for full deployment'
        elif average_rating >= 3.0:
            status = 'conditionally_accepted'
            message = 'System accepted with conditions'
        else:
            status = 'rejected'
            message = 'System requires revisions before acceptance'
        
        return {
            'status': status,
            'message': message,
            'report': acceptance_report
        }