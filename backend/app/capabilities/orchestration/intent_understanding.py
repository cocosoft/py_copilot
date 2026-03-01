"""
意图理解模块

本模块提供用户意图识别和参数提取功能
"""

import logging
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.capabilities.center.unified_center import UnifiedCapabilityCenter
from app.capabilities.types import CapabilityType

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型"""
    SINGLE = "single"           # 单能力调用
    SEQUENTIAL = "sequential"   # 顺序执行多个能力
    PARALLEL = "parallel"       # 并行执行多个能力
    CONDITIONAL = "conditional" # 条件执行
    LOOP = "loop"              # 循环执行
    COMPOSITE = "composite"    # 组合任务
    QUERY = "query"            # 信息查询
    CLARIFICATION = "clarification"  # 需要澄清
    UNKNOWN = "unknown"        # 未知意图


@dataclass
class IntentResult:
    """
    意图理解结果

    Attributes:
        intent_type: 意图类型
        primary_intent: 主要意图描述
        confidence: 置信度 (0-1)
        capabilities: 识别的能力列表
        parameters: 提取的参数
        context_needed: 是否需要上下文
        clarification_needed: 是否需要澄清
        suggested_questions: 建议的澄清问题
    """
    intent_type: IntentType
    primary_intent: str
    confidence: float
    capabilities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    context_needed: bool = False
    clarification_needed: bool = False
    suggested_questions: List[str] = field(default_factory=list)


@dataclass
class Entity:
    """
    实体信息

    Attributes:
        type: 实体类型
        value: 实体值
        start: 起始位置
        end: 结束位置
        confidence: 置信度
    """
    type: str
    value: str
    start: int
    end: int
    confidence: float


class IntentUnderstanding:
    """
    意图理解器

    负责分析用户输入，识别意图，提取参数。
    支持基于规则、关键词和上下文的意图识别。

    Attributes:
        _center: 统一能力中心
        _intent_patterns: 意图模式
        _entity_extractors: 实体提取器
        _context: 上下文信息
    """

    # 默认意图模式
    DEFAULT_PATTERNS = {
        IntentType.QUERY: [
            r"查询|查找|搜索|是什么|怎么样|如何|怎么",
            r"show me|find|search|what is|how to",
        ],
        IntentType.SEQUENTIAL: [
            r"先.*然后|首先.*接着|第一步.*第二步",
            r"first.*then|after.*do",
        ],
        IntentType.PARALLEL: [
            r"同时|一起|一并|顺便",
            r"at the same time|together|also",
        ],
        IntentType.CONDITIONAL: [
            r"如果.*就|假如.*那么",
            r"if.*then|when.*do",
        ],
        IntentType.LOOP: [
            r"重复|循环|每隔|每次",
            r"repeat|loop|every|each",
        ],
    }

    def __init__(self, center: UnifiedCapabilityCenter):
        """
        初始化意图理解器

        Args:
            center: 统一能力中心
        """
        self._center = center
        self._intent_patterns: Dict[IntentType, List[str]] = self.DEFAULT_PATTERNS.copy()
        self._entity_extractors: Dict[str, Callable[[str], List[Entity]]] = {}
        self._context: Dict[str, Any] = {}

        # 注册默认实体提取器
        self._register_default_extractors()

        logger.info("意图理解器已创建")

    def _register_default_extractors(self):
        """注册默认实体提取器"""
        # 日期提取器
        self._entity_extractors["date"] = self._extract_date
        # 时间提取器
        self._entity_extractors["time"] = self._extract_time
        # 数字提取器
        self._entity_extractors["number"] = self._extract_number
        # 邮箱提取器
        self._entity_extractors["email"] = self._extract_email

    def _extract_date(self, text: str) -> List[Entity]:
        """提取日期实体"""
        entities = []
        # 简单日期模式匹配
        patterns = [
            (r"(\d{4}年\d{1,2}月\d{1,2}日)", "date_cn"),
            (r"(\d{4}-\d{2}-\d{2})", "date_iso"),
            (r"(今天|明天|后天|昨天)", "date_relative"),
        ]

        for pattern, date_type in patterns:
            for match in re.finditer(pattern, text):
                entities.append(Entity(
                    type=date_type,
                    value=match.group(1),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9
                ))

        return entities

    def _extract_time(self, text: str) -> List[Entity]:
        """提取时间实体"""
        entities = []
        patterns = [
            (r"(\d{1,2}:\d{2})", "time"),
            (r"(\d{1,2}点\d{1,2}分)", "time_cn"),
        ]

        for pattern, time_type in patterns:
            for match in re.finditer(pattern, text):
                entities.append(Entity(
                    type=time_type,
                    value=match.group(1),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9
                ))

        return entities

    def _extract_number(self, text: str) -> List[Entity]:
        """提取数字实体"""
        entities = []
        pattern = r"(\d+(?:\.\d+)?)"

        for match in re.finditer(pattern, text):
            entities.append(Entity(
                type="number",
                value=match.group(1),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))

        return entities

    def _extract_email(self, text: str) -> List[Entity]:
        """提取邮箱实体"""
        entities = []
        pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"

        for match in re.finditer(pattern, text):
            entities.append(Entity(
                type="email",
                value=match.group(1),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))

        return entities

    async def understand(self,
                        user_input: str,
                        conversation_context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        理解用户意图

        Args:
            user_input: 用户输入
            conversation_context: 对话上下文

        Returns:
            IntentResult: 意图理解结果
        """
        logger.info(f"开始理解意图: {user_input[:50]}...")

        # 1. 识别意图类型
        intent_type = self._detect_intent_type(user_input)

        # 2. 提取实体
        entities = self._extract_entities(user_input)

        # 3. 匹配能力
        matched_capabilities = await self._match_capabilities(user_input, entities)

        # 4. 提取参数
        parameters = self._extract_parameters(user_input, entities, matched_capabilities)

        # 5. 计算置信度
        confidence = self._calculate_confidence(
            intent_type, matched_capabilities, entities, user_input
        )

        # 6. 判断是否需要澄清
        clarification_needed, suggested_questions = self._check_clarification_needed(
            intent_type, matched_capabilities, parameters, confidence
        )

        result = IntentResult(
            intent_type=intent_type,
            primary_intent=self._generate_intent_description(intent_type, matched_capabilities),
            confidence=confidence,
            capabilities=[cap.name for cap in matched_capabilities],
            parameters=parameters,
            context_needed=len(matched_capabilities) > 1 or intent_type in [
                IntentType.SEQUENTIAL, IntentType.PARALLEL, IntentType.CONDITIONAL
            ],
            clarification_needed=clarification_needed,
            suggested_questions=suggested_questions
        )

        logger.info(f"意图理解完成: type={intent_type.value}, confidence={confidence:.2f}")

        return result

    def _detect_intent_type(self, user_input: str) -> IntentType:
        """
        检测意图类型

        Args:
            user_input: 用户输入

        Returns:
            IntentType: 意图类型
        """
        user_input_lower = user_input.lower()

        # 检查每种意图类型的模式
        scores = {}
        for intent_type, patterns in self._intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    score += 1
            if score > 0:
                scores[intent_type] = score

        if scores:
            # 返回得分最高的意图类型
            return max(scores.items(), key=lambda x: x[1])[0]

        # 默认返回单能力调用
        return IntentType.SINGLE

    def _extract_entities(self, user_input: str) -> List[Entity]:
        """
        提取所有实体

        Args:
            user_input: 用户输入

        Returns:
            List[Entity]: 实体列表
        """
        all_entities = []

        for extractor_name, extractor_func in self._entity_extractors.items():
            try:
                entities = extractor_func(user_input)
                all_entities.extend(entities)
            except Exception as e:
                logger.warning(f"实体提取失败 [{extractor_name}]: {e}")

        # 按位置排序
        all_entities.sort(key=lambda e: e.start)

        return all_entities

    async def _match_capabilities(self,
                                  user_input: str,
                                  entities: List[Entity]) -> List[Any]:
        """
        匹配能力

        Args:
            user_input: 用户输入
            entities: 实体列表

        Returns:
            List[Any]: 匹配的能力列表
        """
        matched = []

        # 从能力中心搜索
        from app.capabilities.center.discovery_service import DiscoveryService
        discovery = DiscoveryService(self._center)

        # 搜索前几个关键词
        keywords = self._extract_keywords(user_input)

        for keyword in keywords[:3]:  # 限制搜索数量
            try:
                results = discovery.search(keyword, limit=5)
                for result in results:
                    if result.capability not in matched:
                        matched.append(result.capability)
            except Exception as e:
                logger.warning(f"能力匹配失败: {e}")

        return matched[:5]  # 最多返回5个

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（去除停用词）
        stop_words = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]

        return keywords

    def _extract_parameters(self,
                           user_input: str,
                           entities: List[Entity],
                           capabilities: List[Any]) -> Dict[str, Any]:
        """
        提取参数

        Args:
            user_input: 用户输入
            entities: 实体列表
            capabilities: 匹配的能力列表

        Returns:
            Dict[str, Any]: 参数字典
        """
        parameters = {}

        # 从实体中提取参数
        for entity in entities:
            param_name = self._map_entity_to_parameter(entity.type)
            if param_name:
                parameters[param_name] = entity.value

        # 尝试从能力schema中提取更多参数
        for cap in capabilities:
            if hasattr(cap, 'metadata') and cap.metadata.input_schema:
                schema = cap.metadata.input_schema
                if 'properties' in schema:
                    for prop_name in schema['properties'].keys():
                        if prop_name not in parameters:
                            # 尝试从文本中提取
                            value = self._extract_parameter_value(user_input, prop_name)
                            if value:
                                parameters[prop_name] = value

        return parameters

    def _map_entity_to_parameter(self, entity_type: str) -> Optional[str]:
        """映射实体类型到参数名"""
        mapping = {
            "date_cn": "date",
            "date_iso": "date",
            "date_relative": "date",
            "time": "time",
            "time_cn": "time",
            "number": "count",
            "email": "email",
        }
        return mapping.get(entity_type)

    def _extract_parameter_value(self, text: str, param_name: str) -> Optional[str]:
        """从文本中提取参数值"""
        # 简单的参数值提取模式
        patterns = [
            rf"{param_name}[是为]?([\u4e00-\u9fa5a-zA-Z0-9]+)",
            rf"{param_name}[:=]\s*([\u4e00-\u9fa5a-zA-Z0-9]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _calculate_confidence(self,
                             intent_type: IntentType,
                             capabilities: List[Any],
                             entities: List[Entity],
                             user_input: str) -> float:
        """
        计算置信度

        Args:
            intent_type: 意图类型
            capabilities: 匹配的能力
            entities: 实体
            user_input: 用户输入

        Returns:
            float: 置信度 (0-1)
        """
        confidence = 0.5  # 基础置信度

        # 根据匹配的能力数量调整
        if capabilities:
            confidence += min(len(capabilities) * 0.1, 0.3)

        # 根据提取的实体数量调整
        if entities:
            confidence += min(len(entities) * 0.05, 0.2)

        # 根据输入长度调整（太短可能信息不足）
        if len(user_input) < 5:
            confidence -= 0.2
        elif len(user_input) > 20:
            confidence += 0.1

        # 限制在0-1范围内
        return max(0.0, min(1.0, confidence))

    def _check_clarification_needed(self,
                                    intent_type: IntentType,
                                    capabilities: List[Any],
                                    parameters: Dict[str, Any],
                                    confidence: float) -> tuple:
        """
        检查是否需要澄清

        Returns:
            tuple: (是否需要澄清, 建议问题列表)
        """
        if confidence < 0.4:
            return True, ["我不太确定您的意思，能否详细描述一下？"]

        if not capabilities:
            return True, ["我没有找到适合处理这个请求的能力，能否换一种说法？"]

        suggested_questions = []

        # 检查必需参数
        for cap in capabilities:
            if hasattr(cap, 'metadata') and cap.metadata.input_schema:
                schema = cap.metadata.input_schema
                required = schema.get('required', [])
                for req_param in required:
                    if req_param not in parameters:
                        suggested_questions.append(f"请提供{req_param}的值")

        return len(suggested_questions) > 0, suggested_questions[:3]

    def _generate_intent_description(self,
                                    intent_type: IntentType,
                                    capabilities: List[Any]) -> str:
        """生成意图描述"""
        cap_names = [getattr(c, 'name', str(c)) for c in capabilities[:2]]

        descriptions = {
            IntentType.SINGLE: f"执行{'/'.join(cap_names)}" if cap_names else "执行单个任务",
            IntentType.SEQUENTIAL: f"顺序执行{'、'.join(cap_names)}" if cap_names else "顺序执行多个任务",
            IntentType.PARALLEL: f"并行执行{'、'.join(cap_names)}" if cap_names else "并行执行多个任务",
            IntentType.CONDITIONAL: "条件执行任务",
            IntentType.LOOP: "循环执行任务",
            IntentType.QUERY: "查询信息",
            IntentType.CLARIFICATION: "需要澄清",
            IntentType.UNKNOWN: "未知意图",
        }

        return descriptions.get(intent_type, "执行任务")

    def add_intent_pattern(self, intent_type: IntentType, pattern: str):
        """
        添加意图模式

        Args:
            intent_type: 意图类型
            pattern: 正则表达式模式
        """
        if intent_type not in self._intent_patterns:
            self._intent_patterns[intent_type] = []
        self._intent_patterns[intent_type].append(pattern)

    def add_entity_extractor(self, name: str, extractor: Callable[[str], List[Entity]]):
        """
        添加实体提取器

        Args:
            name: 提取器名称
            extractor: 提取函数
        """
        self._entity_extractors[name] = extractor
