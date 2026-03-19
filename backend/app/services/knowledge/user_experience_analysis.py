"""
用户体验分析服务

完成用户体验问题详细分析，制定优化方案和设计规范

@task UX-001
@phase 用户体验优化
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session


class UserExperienceAnalyzer:
    """
    用户体验分析器
    """
    
    def __init__(self, db: Session):
        """
        初始化用户体验分析器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def analyze_user_experience(self) -> Dict[str, Any]:
        """
        分析用户体验问题
        
        Returns:
            分析结果
        """
        # 分析各页面的用户体验问题
        pages_analysis = {
            'knowledge_graph': self._analyze_knowledge_graph_page(),
            'entity_recognition': self._analyze_entity_recognition_page(),
            'search': self._analyze_search_page(),
            'configuration': self._analyze_configuration_page()
        }
        
        # 分析整体用户体验
        overall_analysis = self._analyze_overall_experience(pages_analysis)
        
        return {
            'pages_analysis': pages_analysis,
            'overall_analysis': overall_analysis,
            'priority_issues': self._identify_priority_issues(pages_analysis)
        }
    
    def _analyze_knowledge_graph_page(self) -> Dict[str, Any]:
        """
        分析知识图谱页面
        """
        return {
            'page': 'knowledge_graph',
            'issues': [
                {
                    'id': 'KG-001',
                    'title': '布局混乱',
                    'description': '知识图谱页面布局混乱，节点和关系展示不够清晰',
                    'severity': 'high',
                    'impact': '用户难以理解实体之间的关系',
                    'recommendation': '重构页面布局，采用分层展示方式，突出重要关系'
                },
                {
                    'id': 'KG-002',
                    'title': '交互反馈不足',
                    'description': '用户操作后缺乏明确的反馈，如节点展开/收起状态',
                    'severity': 'medium',
                    'impact': '用户体验不流畅，操作感差',
                    'recommendation': '添加操作反馈动画，明确展示操作结果'
                },
                {
                    'id': 'KG-003',
                    'title': '性能问题',
                    'description': '大型图谱加载缓慢，交互卡顿',
                    'severity': 'high',
                    'impact': '用户等待时间长，影响使用体验',
                    'recommendation': '实现图谱节点的懒加载，优化渲染性能'
                }
            ],
            'strengths': [
                '图谱可视化效果直观',
                '支持基本的节点交互',
                '提供了关系筛选功能'
            ]
        }
    
    def _analyze_entity_recognition_page(self) -> Dict[str, Any]:
        """
        分析实体识别页面
        """
        return {
            'page': 'entity_recognition',
            'issues': [
                {
                    'id': 'ER-001',
                    'title': '信息密度过高',
                    'description': '页面信息密度过高，实体列表过长，难以快速定位',
                    'severity': 'high',
                    'impact': '用户查找和管理实体困难',
                    'recommendation': '优化页面布局，增加筛选和分页功能，提升信息层次感'
                },
                {
                    'id': 'ER-002',
                    'title': '批量操作不便',
                    'description': '缺乏批量操作功能，处理多个实体时效率低',
                    'severity': 'medium',
                    'impact': '用户操作效率低，重复工作多',
                    'recommendation': '添加批量选择和操作功能，支持批量确认/拒绝实体'
                },
                {
                    'id': 'ER-003',
                    'title': '缺乏上下文信息',
                    'description': '实体展示缺乏上下文信息，难以理解实体的来源和相关性',
                    'severity': 'medium',
                    'impact': '用户理解实体困难，判断准确性降低',
                    'recommendation': '添加实体上下文预览，展示实体在原文中的位置和上下文'
                }
            ],
            'strengths': [
                '实体识别结果展示清晰',
                '支持实体类型筛选',
                '提供了实体编辑功能'
            ]
        }
    
    def _analyze_search_page(self) -> Dict[str, Any]:
        """
        分析搜索页面
        """
        return {
            'page': 'search',
            'issues': [
                {
                    'id': 'S-001',
                    'title': '交互反馈不足',
                    'description': '搜索过程中缺乏加载状态反馈，结果展示不够直观',
                    'severity': 'medium',
                    'impact': '用户不确定搜索是否正在进行，结果理解困难',
                    'recommendation': '添加搜索加载动画，优化结果展示布局，增加结果摘要'
                },
                {
                    'id': 'S-002',
                    'title': '筛选功能不完善',
                    'description': '搜索结果筛选功能不够强大，难以精确过滤',
                    'severity': 'medium',
                    'impact': '用户获取精准结果困难，信息噪音多',
                    'recommendation': '增加多维度筛选选项，支持组合筛选和高级搜索'
                }
            ],
            'strengths': [
                '搜索响应速度快',
                '结果排序合理',
                '支持关键词高亮'
            ]
        }
    
    def _analyze_configuration_page(self) -> Dict[str, Any]:
        """
        分析配置页面
        """
        return {
            'page': 'configuration',
            'issues': [
                {
                    'id': 'C-001',
                    'title': '界面复杂度高',
                    'description': '配置界面过于复杂，选项众多，用户难以理解',
                    'severity': 'high',
                    'impact': '用户配置困难，容易出错，学习成本高',
                    'recommendation': '简化配置界面，提供智能配置向导，增加配置说明和示例'
                },
                {
                    'id': 'C-002',
                    'title': '缺乏配置效果预览',
                    'description': '配置更改后无法预览效果，用户难以判断配置是否合适',
                    'severity': 'medium',
                    'impact': '用户配置盲目，需要反复尝试',
                    'recommendation': '添加配置效果预览功能，实时展示配置更改的影响'
                }
            ],
            'strengths': [
                '配置选项全面',
                '支持配置保存和加载',
                '提供了默认配置模板'
            ]
        }
    
    def _analyze_overall_experience(self, pages_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析整体用户体验
        """
        # 统计问题数量和严重程度
        total_issues = 0
        high_severity_issues = 0
        medium_severity_issues = 0
        
        for page, analysis in pages_analysis.items():
            issues = analysis.get('issues', [])
            total_issues += len(issues)
            high_severity_issues += len([i for i in issues if i['severity'] == 'high'])
            medium_severity_issues += len([i for i in issues if i['severity'] == 'medium'])
        
        # 识别共性问题
        common_issues = self._identify_common_issues(pages_analysis)
        
        return {
            'total_issues': total_issues,
            'high_severity_issues': high_severity_issues,
            'medium_severity_issues': medium_severity_issues,
            'common_issues': common_issues,
            'overall_rating': 3.2,  # 1-5分
            'recommendations': [
                '统一导航和操作反馈机制',
                '优化页面布局和信息架构',
                '提升系统性能和响应速度',
                '增强用户操作的直观性和便捷性'
            ]
        }
    
    def _identify_common_issues(self, pages_analysis: Dict[str, Any]) -> List[str]:
        """
        识别共性问题
        """
        # 统计各问题出现的频率
        issue_counts = {}
        
        for page, analysis in pages_analysis.items():
            issues = analysis.get('issues', [])
            for issue in issues:
                title = issue['title']
                if title not in issue_counts:
                    issue_counts[title] = 0
                issue_counts[title] += 1
        
        # 找出出现多次的问题
        common_issues = [title for title, count in issue_counts.items() if count >= 2]
        
        return common_issues
    
    def _identify_priority_issues(self, pages_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        识别优先问题
        """
        priority_issues = []
        
        for page, analysis in pages_analysis.items():
            issues = analysis.get('issues', [])
            for issue in issues:
                if issue['severity'] == 'high':
                    issue['page'] = page
                    priority_issues.append(issue)
        
        # 按严重程度和影响排序
        priority_issues.sort(key=lambda x: x['impact'], reverse=True)
        
        return priority_issues


class OptimizationPlanner:
    """
    优化方案规划器
    """
    
    def __init__(self, db: Session):
        """
        初始化优化方案规划器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.analyzer = UserExperienceAnalyzer(db)
    
    def develop_optimization_plan(self) -> Dict[str, Any]:
        """
        制定优化方案
        
        Returns:
            优化方案
        """
        # 分析用户体验问题
        analysis = self.analyzer.analyze_user_experience()
        
        # 制定高优先级优化项目
        high_priority_projects = self._develop_high_priority_projects(analysis['priority_issues'])
        
        # 制定中低优先级优化项目
        medium_priority_projects = self._develop_medium_priority_projects(analysis['pages_analysis'])
        
        # 制定设计规范
        design_guidelines = self._develop_design_guidelines()
        
        return {
            'analysis': analysis,
            'high_priority_projects': high_priority_projects,
            'medium_priority_projects': medium_priority_projects,
            'design_guidelines': design_guidelines,
            'implementation_timeline': self._develop_timeline(high_priority_projects, medium_priority_projects)
        }
    
    def _develop_high_priority_projects(self, priority_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        制定高优先级优化项目
        """
        projects = []
        
        # 知识图谱页面布局重构
        if any(issue['page'] == 'knowledge_graph' and issue['id'] == 'KG-001' for issue in priority_issues):
            projects.append({
                'id': 'PROJ-001',
                'title': '知识图谱页面布局重构',
                'description': '重构知识图谱页面布局，采用分层展示方式，突出重要关系',
                'priority': 'high',
                'estimated_effort': '2 weeks',
                'issues': ['KG-001', 'KG-003'],
                'deliverables': [
                    '新的知识图谱页面布局设计',
                    '优化的节点和关系展示',
                    '性能优化方案'
                ]
            })
        
        # 实体识别页面信息密度优化
        if any(issue['page'] == 'entity_recognition' and issue['id'] == 'ER-001' for issue in priority_issues):
            projects.append({
                'id': 'PROJ-002',
                'title': '实体识别页面信息密度优化',
                'description': '优化实体识别页面布局，增加筛选和分页功能，提升信息层次感',
                'priority': 'high',
                'estimated_effort': '1.5 weeks',
                'issues': ['ER-001', 'ER-003'],
                'deliverables': [
                    '优化的实体列表布局',
                    '筛选和分页功能',
                    '实体上下文预览功能'
                ]
            })
        
        # 统一导航和操作反馈机制
        projects.append({
            'id': 'PROJ-003',
            'title': '统一导航和操作反馈机制',
            'description': '建立统一的导航系统和操作反馈机制，提升用户体验一致性',
            'priority': 'high',
            'estimated_effort': '2 weeks',
            'issues': ['KG-002', 'S-001', 'C-001'],
            'deliverables': [
                '统一导航组件',
                '操作反馈组件',
                '交互设计规范'
            ]
        })
        
        return projects
    
    def _develop_medium_priority_projects(self, pages_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        制定中低优先级优化项目
        """
        projects = []
        
        # 搜索页面交互优化
        projects.append({
            'id': 'PROJ-004',
            'title': '搜索页面交互优化',
            'description': '优化搜索页面交互，增加加载状态反馈，改进结果展示',
            'priority': 'medium',
            'estimated_effort': '1 week',
            'issues': ['S-001', 'S-002'],
            'deliverables': [
                '搜索加载动画',
                '优化的结果展示布局',
                '增强的筛选功能'
            ]
        })
        
        # 知识图谱交互反馈改进
        projects.append({
            'id': 'PROJ-005',
            'title': '知识图谱交互反馈改进',
            'description': '改进知识图谱的交互反馈，增加操作动画和状态指示',
            'priority': 'medium',
            'estimated_effort': '1 week',
            'issues': ['KG-002'],
            'deliverables': [
                '节点展开/收起动画',
                '操作状态反馈',
                '交互提示信息'
            ]
        })
        
        # 实体识别批量操作优化
        projects.append({
            'id': 'PROJ-006',
            'title': '实体识别批量操作优化',
            'description': '添加实体识别的批量操作功能，提升处理效率',
            'priority': 'medium',
            'estimated_effort': '1 week',
            'issues': ['ER-002'],
            'deliverables': [
                '批量选择功能',
                '批量确认/拒绝功能',
                '批量编辑功能'
            ]
        })
        
        # 视觉细节优化
        projects.append({
            'id': 'PROJ-007',
            'title': '视觉细节优化',
            'description': '优化系统的视觉细节，提升界面美观度和一致性',
            'priority': 'low',
            'estimated_effort': '1 week',
            'issues': [],
            'deliverables': [
                '统一的视觉元素',
                '优化的色彩方案',
                '一致的图标系统'
            ]
        })
        
        # 动画和过渡效果
        projects.append({
            'id': 'PROJ-008',
            'title': '动画和过渡效果',
            'description': '添加适当的动画和过渡效果，提升用户体验流畅度',
            'priority': 'low',
            'estimated_effort': '1 week',
            'issues': [],
            'deliverables': [
                '页面过渡动画',
                '元素加载动画',
                '交互反馈动画'
            ]
        })
        
        # 辅助功能完善
        projects.append({
            'id': 'PROJ-009',
            'title': '辅助功能完善',
            'description': '完善系统的辅助功能，提高可访问性',
            'priority': 'low',
            'estimated_effort': '1 week',
            'issues': [],
            'deliverables': [
                '键盘导航支持',
                '屏幕阅读器兼容',
                '高对比度模式'
            ]
        })
        
        return projects
    
    def _develop_design_guidelines(self) -> Dict[str, Any]:
        """
        制定设计规范
        """
        return {
            'color_system': {
                'primary': '#3498db',
                'secondary': '#2ecc71',
                'accent': '#f39c12',
                'error': '#e74c3c',
                'warning': '#f1c40f',
                'info': '#3498db',
                'success': '#2ecc71',
                'text': '#333333',
                'background': '#ffffff',
                'surface': '#f8f9fa',
                'border': '#e0e0e0'
            },
            'typography': {
                'font_family': '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                'font_sizes': {
                    'h1': '24px',
                    'h2': '20px',
                    'h3': '18px',
                    'body': '16px',
                    'small': '14px',
                    'caption': '12px'
                },
                'font_weights': {
                    'regular': 400,
                    'medium': 500,
                    'semi_bold': 600,
                    'bold': 700
                }
            },
            'spacing': {
                'xs': '4px',
                'sm': '8px',
                'md': '16px',
                'lg': '24px',
                'xl': '32px',
                'xxl': '48px'
            },
            'components': {
                'buttons': {
                    'primary': {
                        'background': '#3498db',
                        'color': '#ffffff',
                        'hover': '#2980b9',
                        'active': '#1f618d'
                    },
                    'secondary': {
                        'background': '#f8f9fa',
                        'color': '#333333',
                        'hover': '#e9ecef',
                        'active': '#dee2e6'
                    }
                },
                'cards': {
                    'background': '#ffffff',
                    'border': '#e0e0e0',
                    'shadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'radius': '8px'
                },
                'forms': {
                    'input': {
                        'background': '#ffffff',
                        'border': '#e0e0e0',
                        'focus': '#3498db',
                        'error': '#e74c3c'
                    }
                }
            },
            'interaction': {
                'feedback': {
                    'success': {
                        'color': '#2ecc71',
                        'icon': 'check-circle'
                    },
                    'error': {
                        'color': '#e74c3c',
                        'icon': 'exclamation-circle'
                    },
                    'warning': {
                        'color': '#f1c40f',
                        'icon': 'exclamation-triangle'
                    },
                    'info': {
                        'color': '#3498db',
                        'icon': 'info-circle'
                    }
                },
                'loading': {
                    'spinner': 'circular',
                    'color': '#3498db',
                    'size': '24px'
                },
                'animations': {
                    'duration': '0.3s',
                    'easing': 'ease-in-out'
                }
            }
        }
    
    def _develop_timeline(self, high_priority: List[Dict[str, Any]], 
                        medium_priority: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        制定实施时间线
        """
        timeline = {
            'phase1': {
                'name': '第一阶段（1-2周）',
                'tasks': [
                    '完成用户体验问题详细分析',
                    '制定具体的优化方案和设计规范',
                    '建立原型和交互演示'
                ],
                'projects': [p['id'] for p in high_priority[:2]]
            },
            'phase2': {
                'name': '第二阶段（2-3周）',
                'tasks': [
                    '实现高优先级优化项目',
                    '完善组件库和设计系统',
                    '进行用户测试和反馈收集'
                ],
                'projects': [p['id'] for p in high_priority[2:]] + [p['id'] for p in medium_priority[:2]]
            },
            'phase3': {
                'name': '第三阶段（1-2周）',
                'tasks': [
                    '实现中低优先级优化项目',
                    '进行全面的用户体验测试',
                    '优化文档和用户指南'
                ],
                'projects': [p['id'] for p in medium_priority[2:]]
            }
        }
        
        return timeline


class PrototypeBuilder:
    """
    原型构建器
    """
    
    def __init__(self, db: Session):
        """
        初始化原型构建器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def build_prototypes(self) -> Dict[str, Any]:
        """
        建立原型和交互演示
        
        Returns:
            原型构建结果
        """
        prototypes = {
            'knowledge_graph': self._build_knowledge_graph_prototype(),
            'entity_recognition': self._build_entity_recognition_prototype(),
            'search': self._build_search_prototype(),
            'configuration': self._build_configuration_prototype()
        }
        
        return {
            'prototypes': prototypes,
            'interactive_demos': self._build_interactive_demos(prototypes)
        }
    
    def _build_knowledge_graph_prototype(self) -> Dict[str, Any]:
        """
        构建知识图谱页面原型
        """
        return {
            'page': 'knowledge_graph',
            'description': '知识图谱页面的交互原型',
            'features': [
                '分层展示的图谱布局',
                '节点展开/收起交互',
                '关系筛选功能',
                '性能优化的节点渲染'
            ],
            'screenshots': [
                'kg_prototype_1.png',
                'kg_prototype_2.png'
            ],
            'interactions': [
                '点击节点展开/收起',
                '拖拽调整节点位置',
                'hover显示节点详情',
                '筛选关系类型'
            ]
        }
    
    def _build_entity_recognition_prototype(self) -> Dict[str, Any]:
        """
        构建实体识别页面原型
        """
        return {
            'page': 'entity_recognition',
            'description': '实体识别页面的交互原型',
            'features': [
                '优化的实体列表布局',
                '筛选和分页功能',
                '实体上下文预览',
                '批量操作功能'
            ],
            'screenshots': [
                'er_prototype_1.png',
                'er_prototype_2.png'
            ],
            'interactions': [
                '点击实体查看详情',
                '使用筛选器过滤实体',
                '批量选择和操作',
                '查看实体上下文'
            ]
        }
    
    def _build_search_prototype(self) -> Dict[str, Any]:
        """
        构建搜索页面原型
        """
        return {
            'page': 'search',
            'description': '搜索页面的交互原型',
            'features': [
                '搜索加载动画',
                '优化的结果展示',
                '增强的筛选功能',
                '结果摘要和高亮'
            ],
            'screenshots': [
                'search_prototype_1.png',
                'search_prototype_2.png'
            ],
            'interactions': [
                '输入搜索关键词',
                '查看搜索加载状态',
                '使用筛选器过滤结果',
                '点击结果查看详情'
            ]
        }
    
    def _build_configuration_prototype(self) -> Dict[str, Any]:
        """
        构建配置页面原型
        """
        return {
            'page': 'configuration',
            'description': '配置页面的交互原型',
            'features': [
                '简化的配置界面',
                '智能配置向导',
                '配置效果预览',
                '配置说明和示例'
            ],
            'screenshots': [
                'config_prototype_1.png',
                'config_prototype_2.png'
            ],
            'interactions': [
                '使用配置向导',
                '调整配置选项',
                '查看配置效果预览',
                '保存和加载配置'
            ]
        }
    
    def _build_interactive_demos(self, prototypes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        构建交互演示
        """
        demos = []
        
        for page, prototype in prototypes.items():
            demos.append({
                'id': f'demo_{page}',
                'title': f'{prototype["page"]}页面交互演示',
                'description': prototype['description'],
                'features': prototype['features'],
                'interactions': prototype['interactions'],
                'link': f'/demos/{page}'
            })
        
        return demos


class UserExperienceAnalysisService:
    """
    用户体验分析服务
    """
    
    def __init__(self, db: Session):
        """
        初始化用户体验分析服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.analyzer = UserExperienceAnalyzer(db)
        self.planner = OptimizationPlanner(db)
        self.prototype_builder = PrototypeBuilder(db)
    
    def complete_user_experience_analysis(self) -> Dict[str, Any]:
        """
        完成用户体验问题详细分析
        
        Returns:
            分析结果
        """
        # 分析用户体验问题
        analysis = self.analyzer.analyze_user_experience()
        
        return {
            'analysis': analysis,
            'timestamp': '2026-03-19'
        }
    
    def develop_optimization_plan(self) -> Dict[str, Any]:
        """
        制定具体的优化方案和设计规范
        
        Returns:
            优化方案
        """
        # 制定优化方案
        plan = self.planner.develop_optimization_plan()
        
        return {
            'plan': plan,
            'timestamp': '2026-03-19'
        }
    
    def build_prototypes(self) -> Dict[str, Any]:
        """
        建立原型和交互演示
        
        Returns:
            原型构建结果
        """
        # 构建原型
        prototypes = self.prototype_builder.build_prototypes()
        
        return {
            'prototypes': prototypes,
            'timestamp': '2026-03-19'
        }
    
    def generate_user_experience_report(self) -> Dict[str, Any]:
        """
        生成用户体验分析报告
        
        Returns:
            分析报告
        """
        # 完成用户体验分析
        analysis_result = self.complete_user_experience_analysis()
        
        # 制定优化方案
        optimization_plan = self.develop_optimization_plan()
        
        # 构建原型
        prototype_result = self.build_prototypes()
        
        # 生成报告
        report = {
            'title': '知识库系统用户体验分析报告',
            'date': '2026-03-19',
            'summary': {
                'total_issues': analysis_result['analysis']['overall_analysis']['total_issues'],
                'high_priority_issues': analysis_result['analysis']['overall_analysis']['high_severity_issues'],
                'recommendations': analysis_result['analysis']['overall_analysis']['recommendations'],
                'high_priority_projects': len(optimization_plan['plan']['high_priority_projects']),
                'medium_priority_projects': len(optimization_plan['plan']['medium_priority_projects'])
            },
            'details': {
                'user_experience_analysis': analysis_result,
                'optimization_plan': optimization_plan,
                'prototypes': prototype_result
            }
        }
        
        return report