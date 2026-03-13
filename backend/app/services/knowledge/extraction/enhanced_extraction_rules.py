#!/usr/bin/env python3
"""
增强实体提取规则库

提供更丰富的实体提取规则，支持更多实体类型和提取模式
"""

import re
from typing import Dict, List, Any, Optional, Pattern
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractionRule:
    """提取规则定义"""
    name: str
    entity_type: str
    pattern: Pattern
    priority: int = 1
    confidence: float = 0.9
    description: str = ""
    examples: List[str] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


class EnhancedExtractionRules:
    """
    增强实体提取规则库
    
    提供丰富的预定义提取规则，支持：
    - 人物实体（姓名、职位、联系方式）
    - 组织实体（公司、机构、部门）
    - 地点实体（地址、地标、区域）
    - 时间实体（日期、时间、时段）
    - 数值实体（金额、百分比、数量）
    - 产品实体（产品名、型号、规格）
    - 事件实体（会议、活动、项目）
    - 技术实体（技术术语、协议、标准）
    """

    def __init__(self):
        self.rules: Dict[str, List[ExtractionRule]] = {}
        self._init_rules()

    def _init_rules(self):
        """初始化所有提取规则"""
        self._init_person_rules()
        self._init_organization_rules()
        self._init_location_rules()
        self._init_time_rules()
        self._init_number_rules()
        self._init_product_rules()
        self._init_event_rules()
        self._init_technology_rules()

    def _init_person_rules(self):
        """初始化人物实体规则"""
        rules = [
            # 中文姓名（2-4个字）
            ExtractionRule(
                name="chinese_name",
                entity_type="PERSON",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,4}(?:先生|女士|博士|教授|经理|主任|书记)?'),
                priority=1,
                confidence=0.85,
                description="中文姓名",
                examples=["张三", "张三丰", "张三先生", "李四博士"]
            ),
            # 英文姓名
            ExtractionRule(
                name="english_name",
                entity_type="PERSON",
                pattern=re.compile(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'),
                priority=1,
                confidence=0.8,
                description="英文姓名",
                examples=["John Smith", "Mary Johnson"]
            ),
            # 职位头衔
            ExtractionRule(
                name="job_title",
                entity_type="JOB_TITLE",
                pattern=re.compile(r'(?:总经理|总监|经理|主管|工程师|分析师|顾问|助理|专员|秘书)(?:\s*[\u4e00-\u9fa5]{2,4})?'),
                priority=2,
                confidence=0.75,
                description="职位头衔",
                examples=["总经理", "技术总监", "产品经理"]
            ),
            # 联系方式 - 手机号
            ExtractionRule(
                name="mobile_phone",
                entity_type="CONTACT",
                pattern=re.compile(r'1[3-9]\d{9}'),
                priority=1,
                confidence=0.95,
                description="手机号码",
                examples=["13800138000", "15912345678"]
            ),
            # 联系方式 - 邮箱
            ExtractionRule(
                name="email",
                entity_type="CONTACT",
                pattern=re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
                priority=1,
                confidence=0.95,
                description="电子邮箱",
                examples=["example@email.com", "user@company.cn"]
            ),
            # 联系方式 - 电话
            ExtractionRule(
                name="telephone",
                entity_type="CONTACT",
                pattern=re.compile(r'(?:0\d{2,3}-?)?[1-9]\d{6,7}'),
                priority=2,
                confidence=0.85,
                description="固定电话",
                examples=["010-12345678", "021-87654321"]
            ),
        ]
        self.rules["PERSON"] = rules

    def _init_organization_rules(self):
        """初始化组织实体规则"""
        rules = [
            # 公司名称
            ExtractionRule(
                name="company_name",
                entity_type="ORGANIZATION",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:集团|公司|企业|厂|店|行|社|所|院|校|中心)(?:有限|股份|责任)?(?:公司)?'),
                priority=1,
                confidence=0.9,
                description="公司名称",
                examples=["阿里巴巴集团", "腾讯公司", "华为技术有限公司"]
            ),
            # 政府机构
            ExtractionRule(
                name="government_agency",
                entity_type="GOVERNMENT",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:政府|部门|局|厅|委|办|部|院|所)(?:\s*[\u4e00-\u9fa5]{2,8})?'),
                priority=1,
                confidence=0.9,
                description="政府机构",
                examples=["国务院", "工信部", "北京市政府"]
            ),
            # 金融机构
            ExtractionRule(
                name="financial_institution",
                entity_type="FINANCIAL",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:银行|证券|保险|基金|信托|投资)(?:公司)?'),
                priority=1,
                confidence=0.9,
                description="金融机构",
                examples=["中国工商银行", "中信证券", "平安保险"]
            ),
            # 学校/教育机构
            ExtractionRule(
                name="educational_institution",
                entity_type="EDUCATION",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:大学|学院|学校|研究所)(?:\s*[\u4e00-\u9fa5]{2,8})?'),
                priority=1,
                confidence=0.9,
                description="教育机构",
                examples=["清华大学", "北京大学", "中科院"]
            ),
            # 部门/团队
            ExtractionRule(
                name="department",
                entity_type="DEPARTMENT",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:部|处|科|室|组|团队|中心)(?:\s*[\u4e00-\u9fa5]{2,6})?'),
                priority=2,
                confidence=0.75,
                description="部门/团队",
                examples=["技术部", "人力资源部", "研发中心"]
            ),
        ]
        self.rules["ORGANIZATION"] = rules

    def _init_location_rules(self):
        """初始化地点实体规则"""
        rules = [
            # 省/直辖市
            ExtractionRule(
                name="province",
                entity_type="LOCATION",
                pattern=re.compile(r'(?:北京|上海|天津|重庆|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾|内蒙古|广西|西藏|宁夏|新疆)(?:省|市|自治区)?'),
                priority=1,
                confidence=0.95,
                description="省/直辖市",
                examples=["北京市", "广东省", "内蒙古自治区"]
            ),
            # 城市
            ExtractionRule(
                name="city",
                entity_type="LOCATION",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:市|州|盟|地区)'),
                priority=2,
                confidence=0.85,
                description="城市",
                examples=["深圳市", "杭州市", "苏州市"]
            ),
            # 详细地址
            ExtractionRule(
                name="detailed_address",
                entity_type="ADDRESS",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:省|市|区|县|镇|乡|街|路|号|楼|室|层)(?:[\u4e00-\u9fa50-9\-]+)?'),
                priority=2,
                confidence=0.8,
                description="详细地址",
                examples=["北京市海淀区中关村大街1号", "上海市浦东新区陆家嘴环路1000号"]
            ),
            # 地标建筑
            ExtractionRule(
                name="landmark",
                entity_type="LANDMARK",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:大厦|中心|广场|公园|博物馆|图书馆|体育馆|机场|车站|码头)'),
                priority=2,
                confidence=0.85,
                description="地标建筑",
                examples=["国贸大厦", "天安门广场", "首都国际机场"]
            ),
            # 国家/地区
            ExtractionRule(
                name="country",
                entity_type="COUNTRY",
                pattern=re.compile(r'(?:中国|美国|日本|韩国|英国|法国|德国|俄罗斯|印度|巴西|澳大利亚|加拿大|新加坡|泰国|马来西亚|越南|印度尼西亚|菲律宾)(?:共和国)?'),
                priority=1,
                confidence=0.95,
                description="国家/地区",
                examples=["中国", "美利坚合众国", "日本国"]
            ),
        ]
        self.rules["LOCATION"] = rules

    def _init_time_rules(self):
        """初始化时间实体规则"""
        rules = [
            # 日期（YYYY-MM-DD格式）
            ExtractionRule(
                name="date_iso",
                entity_type="DATE",
                pattern=re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?'),
                priority=1,
                confidence=0.95,
                description="ISO格式日期",
                examples=["2024-01-15", "2024年3月8日"]
            ),
            # 时间（HH:MM格式）
            ExtractionRule(
                name="time",
                entity_type="TIME",
                pattern=re.compile(r'\d{1,2}:\d{2}(?::\d{2})?'),
                priority=1,
                confidence=0.95,
                description="时间",
                examples=["14:30", "09:00:00"]
            ),
            # 日期时间组合
            ExtractionRule(
                name="datetime",
                entity_type="DATETIME",
                pattern=re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?\s+\d{1,2}:\d{2}'),
                priority=1,
                confidence=0.95,
                description="日期时间",
                examples=["2024-01-15 14:30", "2024年3月8日 上午9点"]
            ),
            # 时间段
            ExtractionRule(
                name="time_period",
                entity_type="TIME_PERIOD",
                pattern=re.compile(r'(?:上午|下午|晚上|凌晨|早晨|傍晚|午夜|清晨)(?:\d{1,2}[点时])?'),
                priority=2,
                confidence=0.8,
                description="时间段",
                examples=["上午", "下午3点", "晚上"]
            ),
            # 相对时间
            ExtractionRule(
                name="relative_time",
                entity_type="RELATIVE_TIME",
                pattern=re.compile(r'(?:今天|昨天|明天|前天|后天|本周|上周|下周|本月|上月|下月|今年|去年|明年)(?:的?\s*[\u4e00-\u9fa5]{0,4})?'),
                priority=2,
                confidence=0.85,
                description="相对时间",
                examples=["今天", "昨天", "下周三", "上个月"]
            ),
        ]
        self.rules["TIME"] = rules

    def _init_number_rules(self):
        """初始化数值实体规则"""
        rules = [
            # 金额（人民币）
            ExtractionRule(
                name="money_rmb",
                entity_type="MONEY",
                pattern=re.compile(r'(?:人民币|RMB|￥|¥)?\s*(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{1,2})?\s*(?:元|万元|亿元)'),
                priority=1,
                confidence=0.9,
                description="人民币金额",
                examples=["100万元", "￥50,000元", "1.5亿元"]
            ),
            # 金额（美元）
            ExtractionRule(
                name="money_usd",
                entity_type="MONEY",
                pattern=re.compile(r'(?:USD|\$)?\s*(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{1,2})?\s*(?:美元|万美金|亿美金)?'),
                priority=1,
                confidence=0.9,
                description="美元金额",
                examples=["$100,000", "50万美元", "1.5亿美金"]
            ),
            # 百分比
            ExtractionRule(
                name="percentage",
                entity_type="PERCENTAGE",
                pattern=re.compile(r'(?:\d{1,3}(?:\.\d{1,2})?)\s*%'),
                priority=1,
                confidence=0.95,
                description="百分比",
                examples=["50%", "99.9%", "12.5%"]
            ),
            # 数量
            ExtractionRule(
                name="quantity",
                entity_type="QUANTITY",
                pattern=re.compile(r'(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?\s*(?:个|件|台|套|辆|吨|千克|克|米|千米|平方米|立方米|升|毫升)'),
                priority=2,
                confidence=0.85,
                description="数量",
                examples=["100个", "50.5吨", "1000平方米"]
            ),
            # 编号
            ExtractionRule(
                name="code",
                entity_type="CODE",
                pattern=re.compile(r'(?:No\.|编号|号码|代码)?[.:\s]*[A-Z0-9\-]{3,}'),
                priority=2,
                confidence=0.8,
                description="编号代码",
                examples=["No.12345", "编号ABC-123", "代码XYZ-2024-001"]
            ),
        ]
        self.rules["NUMBER"] = rules

    def _init_product_rules(self):
        """初始化产品实体规则"""
        rules = [
            # 产品名称
            ExtractionRule(
                name="product_name",
                entity_type="PRODUCT",
                pattern=re.compile(r'[\u4e00-\u9fa5A-Za-z0-9]{2,}(?:产品|设备|系统|软件|硬件|服务|解决方案)'),
                priority=2,
                confidence=0.8,
                description="产品名称",
                examples=["智能客服系统", "数据分析平台", "云存储服务"]
            ),
            # 产品型号
            ExtractionRule(
                name="product_model",
                entity_type="PRODUCT_MODEL",
                pattern=re.compile(r'[A-Z]{1,4}[-]?\d{3,}[A-Z0-9\-]*'),
                priority=1,
                confidence=0.9,
                description="产品型号",
                examples=["iPhone15", "ThinkPad-X1", "RTX-4090"]
            ),
            # 软件版本
            ExtractionRule(
                name="software_version",
                entity_type="VERSION",
                pattern=re.compile(r'v?\d+\.\d+(?:\.\d+)*(?:[-.]?(?:alpha|beta|rc|release|stable|patch))?'),
                priority=1,
                confidence=0.95,
                description="软件版本",
                examples=["v1.0.0", "2.5.3-beta", "Windows 11"]
            ),
            # 商标/品牌
            ExtractionRule(
                name="brand",
                entity_type="BRAND",
                pattern=re.compile(r'(?:苹果|华为|小米|三星|索尼|微软|谷歌|亚马逊|阿里巴巴|腾讯|百度|字节跳动|美团|滴滴|京东|网易|新浪|搜狐|携程|比亚迪|特斯拉|宝马|奔驰|奥迪|丰田|本田|福特|通用)(?:公司)?'),
                priority=1,
                confidence=0.9,
                description="知名品牌",
                examples=["苹果", "华为", "阿里巴巴"]
            ),
        ]
        self.rules["PRODUCT"] = rules

    def _init_event_rules(self):
        """初始化事件实体规则"""
        rules = [
            # 会议
            ExtractionRule(
                name="meeting",
                entity_type="EVENT",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:会议|大会|峰会|论坛|研讨会|座谈会|发布会)'),
                priority=1,
                confidence=0.85,
                description="会议活动",
                examples=["年度总结会议", "产品发布会", "技术峰会"]
            ),
            # 项目
            ExtractionRule(
                name="project",
                entity_type="PROJECT",
                pattern=re.compile(r'[\u4e00-\u9fa5A-Z]{2,}(?:项目|工程|计划|方案|行动)'),
                priority=2,
                confidence=0.8,
                description="项目计划",
                examples=["数字化转型项目", "新基建工程", "五年计划"]
            ),
            # 活动
            ExtractionRule(
                name="activity",
                entity_type="ACTIVITY",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:活动|比赛|竞赛|展览|展示|演出|庆典|节日)'),
                priority=2,
                confidence=0.8,
                description="活动事件",
                examples=["春节联欢晚会", "双十一购物节", "科技展览"]
            ),
            # 合同/协议
            ExtractionRule(
                name="contract",
                entity_type="CONTRACT",
                pattern=re.compile(r'[\u4e00-\u9fa5]{2,}(?:合同|协议|合约|协定|备忘录|意向书)'),
                priority=2,
                confidence=0.85,
                description="合同协议",
                examples=["战略合作协议", "劳动合同", "保密协议"]
            ),
        ]
        self.rules["EVENT"] = rules

    def _init_technology_rules(self):
        """初始化技术实体规则"""
        rules = [
            # 编程语言
            ExtractionRule(
                name="programming_language",
                entity_type="TECHNOLOGY",
                pattern=re.compile(r'(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|R|MATLAB|SQL|HTML|CSS|Shell|Bash|PowerShell)(?:\s*\d+\.\d+)?'),
                priority=1,
                confidence=0.95,
                description="编程语言",
                examples=["Python", "Java", "JavaScript", "C++"]
            ),
            # 技术框架
            ExtractionRule(
                name="framework",
                entity_type="TECHNOLOGY",
                pattern=re.compile(r'(?:React|Vue|Angular|Django|Flask|Spring|TensorFlow|PyTorch|Kubernetes|Docker|Hadoop|Spark|Kafka|Elasticsearch|Redis|MongoDB|MySQL|PostgreSQL|Oracle|AWS|Azure|GCP)(?:\s*\d+)?'),
                priority=1,
                confidence=0.9,
                description="技术框架/平台",
                examples=["React", "Spring Boot", "TensorFlow", "Kubernetes"]
            ),
            # 技术标准
            ExtractionRule(
                name="standard",
                entity_type="STANDARD",
                pattern=re.compile(r'(?:ISO|GB|IEEE|RFC|W3C|ITU|ANSI|DIN|JIS|EN)\s*[-]?\s*\d+[\-/]?\d*'),
                priority=1,
                confidence=0.95,
                description="技术标准",
                examples=["ISO 9001", "GB/T 19001", "IEEE 802.11"]
            ),
            # 专利
            ExtractionRule(
                name="patent",
                entity_type="PATENT",
                pattern=re.compile(r'(?:专利|Patent)[号]?[\s:：]?[A-Z0-9\-\.]+'),
                priority=2,
                confidence=0.85,
                description="专利号",
                examples=["专利号: ZL202410123456.7", "Patent US12345678"]
            ),
        ]
        self.rules["TECHNOLOGY"] = rules

    def get_rules(self, entity_type: Optional[str] = None) -> List[ExtractionRule]:
        """
        获取提取规则

        Args:
            entity_type: 实体类型，为None则返回所有规则

        Returns:
            规则列表
        """
        if entity_type:
            return self.rules.get(entity_type, [])
        
        all_rules = []
        for rules in self.rules.values():
            all_rules.extend(rules)
        return sorted(all_rules, key=lambda r: r.priority)

    def extract(self, text: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        使用规则提取实体

        Args:
            text: 输入文本
            entity_types: 指定实体类型列表

        Returns:
            提取的实体列表
        """
        entities = []
        
        # 获取要应用的规则
        if entity_types:
            rules = []
            for et in entity_types:
                rules.extend(self.rules.get(et, []))
        else:
            rules = self.get_rules()

        # 应用规则提取
        for rule in rules:
            for match in rule.pattern.finditer(text):
                entity = {
                    'text': match.group(),
                    'type': rule.entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': rule.confidence,
                    'rule': rule.name,
                    'priority': rule.priority,
                }
                entities.append(entity)

        # 去重（按位置）
        entities = self._deduplicate(entities)
        
        return entities

    def _deduplicate(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重实体（保留优先级高的）"""
        # 按位置排序
        entities.sort(key=lambda e: (e['start'], -e['priority']))
        
        result = []
        last_end = -1
        
        for entity in entities:
            if entity['start'] >= last_end:
                result.append(entity)
                last_end = entity['end']
        
        return result

    def add_custom_rule(self, rule: ExtractionRule):
        """添加自定义规则"""
        entity_type = rule.entity_type
        if entity_type not in self.rules:
            self.rules[entity_type] = []
        self.rules[entity_type].append(rule)
        logger.info(f"添加自定义规则: {rule.name} ({entity_type})")

    def get_rule_stats(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        stats = {
            'total_rules': 0,
            'by_type': {},
            'by_priority': {1: 0, 2: 0, 3: 0}
        }
        
        for entity_type, rules in self.rules.items():
            count = len(rules)
            stats['total_rules'] += count
            stats['by_type'][entity_type] = count
            
            for rule in rules:
                stats['by_priority'][rule.priority] = stats['by_priority'].get(rule.priority, 0) + 1
        
        return stats


# 创建全局规则实例
enhanced_rules = EnhancedExtractionRules()


# 便捷函数
def extract_entities(text: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """使用增强规则提取实体"""
    return enhanced_rules.extract(text, entity_types)


def get_rule_statistics() -> Dict[str, Any]:
    """获取规则统计"""
    return enhanced_rules.get_rule_stats()


if __name__ == '__main__':
    # 测试规则库
    rules = EnhancedExtractionRules()
    
    # 打印统计
    stats = rules.get_rule_stats()
    print("规则统计:")
    print(f"  总规则数: {stats['total_rules']}")
    print(f"  按类型: {stats['by_type']}")
    
    # 测试提取
    test_text = """
    张三先生是阿里巴巴集团的高级工程师，工作地点在杭州市西湖区。
    联系电话：13800138000，邮箱：zhangsan@alibaba.com
    他参与了数字化转型项目，预算为500万元。
    项目启动时间是2024年1月15日，使用了Python和React技术栈。
    """
    
    print("\n测试文本提取:")
    entities = rules.extract(test_text)
    for entity in entities:
        print(f"  {entity['text']} -> {entity['type']} (置信度: {entity['confidence']})")
