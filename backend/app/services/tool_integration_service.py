"""工具集成服务 - 外部工具调用和管理"""
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from pydantic import BaseModel, Field
import logging
import json
import inspect
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具分类枚举"""
    DATA_PROCESSING = "data_processing"
    CHART_GENERATION = "chart_generation"
    DEVELOPMENT = "development"
    TEXT_PROCESSING = "text_processing"
    AI_ENHANCEMENT = "ai_enhancement"
    UTILITY = "utility"


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必需")
    default: Optional[Any] = Field(None, description="默认值")


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str = Field(..., description="工具名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="工具描述")
    category: ToolCategory = Field(..., description="工具分类")
    parameters: List[ToolParameter] = Field([], description="参数列表")
    function: Callable = Field(..., description="工具函数")
    icon: str = Field("🔧", description="工具图标")
    usage_count: int = Field(0, description="使用次数")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ToolExecutionResult(BaseModel):
    """工具执行结果"""
    success: bool = Field(..., description="执行是否成功")
    result: Optional[Any] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间（秒）")
    tool_name: str = Field(..., description="工具名称")


class ToolIntegrationService:
    """工具集成服务"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._registered_categories: Dict[str, List[str]] = {}
        self._initialize_builtin_tools()
    
    def _initialize_builtin_tools(self):
        """初始化内置工具"""
        # 文本处理工具
        self.register_tool(
            name="text_summarizer",
            display_name="文本摘要",
            description="自动提取长篇文本的关键信息",
            category=ToolCategory.TEXT_PROCESSING,
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="需要摘要的文本",
                    required=True
                ),
                ToolParameter(
                    name="max_length",
                    type="integer",
                    description="摘要最大长度",
                    required=False,
                    default=200
                )
            ],
            function=self._text_summarizer
        )
        
        # 代码格式化工具
        self.register_tool(
            name="code_formatter",
            display_name="代码格式化",
            description="自动格式化多种编程语言的代码",
            category=ToolCategory.DEVELOPMENT,
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="需要格式化的代码",
                    required=True
                ),
                ToolParameter(
                    name="language",
                    type="string",
                    description="编程语言",
                    required=True
                )
            ],
            function=self._code_formatter
        )
        
        # 数据分析工具
        self.register_tool(
            name="data_analyzer",
            display_name="数据分析",
            description="快速分析CSV和Excel数据，生成统计结果",
            category=ToolCategory.DATA_PROCESSING,
            parameters=[
                ToolParameter(
                    name="data",
                    type="string",
                    description="CSV格式的数据",
                    required=True
                ),
                ToolParameter(
                    name="analysis_type",
                    type="string",
                    description="分析类型（statistics, correlation, etc）",
                    required=False,
                    default="statistics"
                )
            ],
            function=self._data_analyzer
        )
        
        # JSON解析器工具
        self.register_tool(
            name="json_parser",
            display_name="JSON解析器",
            description="验证和格式化JSON数据，支持语法高亮",
            category=ToolCategory.UTILITY,
            parameters=[
                ToolParameter(
                    name="json_string",
                    type="string",
                    description="JSON字符串",
                    required=True
                ),
                ToolParameter(
                    name="format",
                    type="boolean",
                    description="是否格式化输出",
                    required=False,
                    default=True
                )
            ],
            function=self._json_parser
        )
        
        # 内容生成工具
        self.register_tool(
            name="content_generator",
            display_name="内容生成",
            description="根据关键词和指令生成各种类型的内容",
            category=ToolCategory.AI_ENHANCEMENT,
            parameters=[
                ToolParameter(
                    name="keywords",
                    type="string",
                    description="关键词",
                    required=True
                ),
                ToolParameter(
                    name="content_type",
                    type="string",
                    description="内容类型（article, story, poem, etc）",
                    required=False,
                    default="article"
                ),
                ToolParameter(
                    name="length",
                    type="integer",
                    description="内容长度（字数）",
                    required=False,
                    default=500
                )
            ],
            function=self._content_generator
        )

        # 时间日期工具
        self.register_tool(
            name="datetime_tool",
            display_name="时间日期工具",
            description="获取当前时间、日期计算、时区转换等功能",
            category=ToolCategory.UTILITY,
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型",
                    required=True,
                    enum=["now", "format", "parse", "add", "diff", "timezone_convert"]
                ),
                ToolParameter(
                    name="datetime_str",
                    type="string",
                    description="日期时间字符串（用于parse、format等操作）",
                    required=False
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    description="日期时间格式",
                    required=False,
                    default="%Y-%m-%d %H:%M:%S"
                ),
                ToolParameter(
                    name="timezone",
                    type="string",
                    description="时区",
                    required=False,
                    default="UTC"
                )
            ],
            function=self._datetime_tool,
            icon="📅"
        )
    
    def register_tool(self, name: str, display_name: str, description: str, 
                     category: ToolCategory, parameters: List[ToolParameter], 
                     function: Callable, icon: str = "🔧") -> bool:
        """注册新工具"""
        try:
            if name in self._tools:
                logger.warning(f"工具 '{name}' 已存在，将更新")
            
            tool = ToolDefinition(
                name=name,
                display_name=display_name,
                description=description,
                category=category,
                parameters=parameters,
                function=function,
                icon=icon
            )
            
            self._tools[name] = tool
            
            # 更新分类索引
            category_name = category.value
            if category_name not in self._registered_categories:
                self._registered_categories[category_name] = []
            
            if name not in self._registered_categories[category_name]:
                self._registered_categories[category_name].append(name)
            
            logger.info(f"工具 '{name}' 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"注册工具 '{name}' 失败: {str(e)}")
            return False
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行工具"""
        start_time = datetime.now()
        
        try:
            if tool_name not in self._tools:
                return ToolExecutionResult(
                    success=False,
                    error_message=f"工具 '{tool_name}' 未找到",
                    execution_time=0.0,
                    tool_name=tool_name
                )
            
            tool = self._tools[tool_name]
            
            # 验证参数
            validation_result = self._validate_parameters(tool, parameters)
            if not validation_result["valid"]:
                return ToolExecutionResult(
                    success=False,
                    error_message=validation_result["error"],
                    execution_time=0.0,
                    tool_name=tool_name
                )
            
            # 执行工具函数
            result = tool.function(**parameters)
            
            # 更新使用次数
            tool.usage_count += 1
            tool.updated_at = datetime.now()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=tool_name
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"执行工具 '{tool_name}' 失败: {str(e)}")
            
            return ToolExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                tool_name=tool_name
            )
    
    def _validate_parameters(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证工具参数"""
        required_params = {p.name for p in tool.parameters if p.required}
        provided_params = set(parameters.keys())
        
        # 检查必需参数
        missing_params = required_params - provided_params
        if missing_params:
            return {
                "valid": False,
                "error": f"缺少必需参数: {', '.join(missing_params)}"
            }
        
        # 检查未知参数
        valid_params = {p.name for p in tool.parameters}
        unknown_params = provided_params - valid_params
        if unknown_params:
            logger.warning(f"工具 '{tool.name}' 接收到未知参数: {', '.join(unknown_params)}")
        
        return {"valid": True}
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(tool_name)
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """列出工具"""
        if category:
            if category not in self._registered_categories:
                return []
            return [self._tools[name] for name in self._registered_categories[category] 
                    if name in self._tools]
        
        return list(self._tools.values())
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._registered_categories.keys())
    
    # ===== 内置工具实现 =====
    
    def _text_summarizer(self, text: str, max_length: int = 200) -> str:
        """文本摘要工具"""
        # 简化的文本摘要实现
        if len(text) <= max_length:
            return text
        
        # 简单的句子分割和摘要
        sentences = text.split('。')
        summary_parts = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) <= max_length:
                summary_parts.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        summary = '。'.join(summary_parts) + '。'
        
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'
        
        return summary
    
    def _code_formatter(self, code: str, language: str) -> str:
        """代码格式化工具"""
        # 简化的代码格式化
        if language.lower() in ['python', 'py']:
            # Python 代码基本格式化
            lines = code.split('\n')
            formatted_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped:
                    formatted_lines.append(stripped)
            
            return '\n'.join(formatted_lines)
        
        elif language.lower() in ['javascript', 'js']:
            # JavaScript 基本格式化
            return code.replace(';', ';\n').replace('{', '{\n').replace('}', '\n}')
        
        else:
            # 通用格式化
            return code.replace(';', ';\n').replace('{', '{\n').replace('}', '\n}')
    
    def _data_analyzer(self, data: str, analysis_type: str = "statistics") -> Dict[str, Any]:
        """数据分析工具"""
        # 简化的数据分析
        lines = data.strip().split('\n')
        
        if analysis_type == "statistics":
            # 基本统计信息
            result = {
                "row_count": len(lines),
                "analysis_type": "statistics",
                "summary": f"数据包含 {len(lines)} 行"
            }
            
            if lines:
                # 简单的列统计
                columns = lines[0].split(',')
                result["column_count"] = len(columns)
                result["columns"] = columns
            
            return result
        
        else:
            return {
                "error": f"不支持的分析类型: {analysis_type}",
                "supported_types": ["statistics"]
            }
    
    def _json_parser(self, json_string: str, format: bool = True) -> Dict[str, Any]:
        """JSON解析器工具"""
        try:
            data = json.loads(json_string)
            
            if format:
                # 返回格式化的JSON字符串
                return {
                    "valid": True,
                    "formatted": json.dumps(data, indent=2, ensure_ascii=False)
                }
            else:
                return {"valid": True, "data": data}
                
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"JSON解析错误: {str(e)}"
            }
    
    def _content_generator(self, keywords: str, content_type: str = "article", 
                          length: int = 500) -> str:
        """内容生成工具"""
        # 简化的内容生成
        if content_type == "article":
            return f"关于'{keywords}'的文章（{length}字）: 这是一个示例文章内容。"
        elif content_type == "story":
            return f"关于'{keywords}'的故事（{length}字）: 这是一个示例故事内容。"
        elif content_type == "poem":
            return f"关于'{keywords}'的诗歌（{length}字）: 这是一个示例诗歌内容。"
        else:
            return f"关于'{keywords}'的{content_type}内容（{length}字）: 这是一个示例内容。"

    def _datetime_tool(self, action: str, datetime_str: str = None, format: str = "%Y-%m-%d %H:%M:%S",
                      timezone: str = "UTC") -> Dict[str, Any]:
        """时间日期工具"""
        from datetime import datetime, timedelta
        import time

        result = {"action": action, "timezone": timezone}

        if action == "now":
            now = datetime.now()
            result["datetime"] = now.strftime(format)
            result["timestamp"] = int(time.time())
            result["date"] = now.strftime("%Y-%m-%d")
            result["time"] = now.strftime("%H:%M:%S")

        elif action == "format":
            if datetime_str:
                try:
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    result["formatted"] = dt.strftime(format)
                except:
                    result["error"] = "无法解析日期时间字符串"
            else:
                result["error"] = "缺少 datetime_str 参数"

        elif action == "parse":
            if datetime_str:
                try:
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    result["year"] = dt.year
                    result["month"] = dt.month
                    result["day"] = dt.day
                    result["hour"] = dt.hour
                    result["minute"] = dt.minute
                    result["second"] = dt.second
                    result["weekday"] = dt.weekday()
                except:
                    result["error"] = "无法解析日期时间字符串"
            else:
                result["error"] = "缺少 datetime_str 参数"

        elif action == "diff":
            result["message"] = "日期差计算功能需要两个日期参数"

        elif action == "timezone_convert":
            result["message"] = f"时区转换: {timezone}"
            result["note"] = "时区转换功能需要额外的时区库支持"

        else:
            result["error"] = f"不支持的操作: {action}"

        return result