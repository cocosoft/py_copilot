"""
日期时间工具

提供日期时间获取、格式化、计算、时区转换等功能
"""

from typing import Dict, Any, List
import time
import logging
from datetime import datetime, timedelta
import calendar

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class DateTimeTool(BaseTool):
    """
    日期时间工具
    
    提供日期时间获取、格式化、计算、时区转换等功能
    """
    
    def __init__(self):
        """初始化日期时间工具"""
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="datetime",
            display_name="日期时间",
            description="提供日期时间获取、格式化、计算、时区转换等功能",
            category=ToolCategory.UTILITY.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="📅",
            tags=["日期", "时间", "计算"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            List[ToolParameter]: 参数定义列表
        """
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=[
                    "now", "format", "parse",
                    "add", "diff",
                    "timezone_convert",
                    "get_weekday", "get_calendar"
                ]
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
            ),
            ToolParameter(
                name="amount",
                type="integer",
                description="数量（用于add操作）",
                required=False
            ),
            ToolParameter(
                name="unit",
                type="string",
                description="单位（用于add操作）",
                required=False,
                enum=["seconds", "minutes", "hours", "days", "weeks", "months", "years"]
            ),
            ToolParameter(
                name="year",
                type="integer",
                description="年份（用于get_calendar操作）",
                required=False
            ),
            ToolParameter(
                name="month",
                type="integer",
                description="月份（用于get_calendar操作）",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行日期时间操作
        
        Args:
            **kwargs: 操作参数
                - action: 操作类型（必需）
                - 其他参数根据action不同而不同
        
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            # 验证参数
            validation_result = self.validate_parameters(**kwargs)
            if not validation_result.is_valid:
                errors = [e.message for e in validation_result.errors]
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"参数验证失败: {'; '.join(errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time=time.time() - start_time
                )
            
            action = kwargs.get("action")
            
            logger.info(f"执行日期时间操作: action={action}")
            
            # 根据操作类型执行不同逻辑
            if action == "now":
                result = self._handle_now(kwargs)
            elif action == "format":
                result = self._handle_format(kwargs)
            elif action == "parse":
                result = self._handle_parse(kwargs)
            elif action == "add":
                result = self._handle_add(kwargs)
            elif action == "diff":
                result = self._handle_diff(kwargs)
            elif action == "timezone_convert":
                result = self._handle_timezone_convert(kwargs)
            elif action == "get_weekday":
                result = self._handle_get_weekday(kwargs)
            elif action == "get_calendar":
                result = self._handle_get_calendar(kwargs)
            else:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"不支持的操作类型: {action}",
                    error_code="INVALID_ACTION",
                    execution_time=time.time() - start_time
                )
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=result,
                execution_time=time.time() - start_time,
                metadata={"action": action}
            )
            
        except Exception as e:
            logger.error(f"日期时间操作失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"操作失败: {str(e)}",
                error_code="DATETIME_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _handle_now(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取当前时间"""
        timezone = kwargs.get("timezone", "UTC")
        format_str = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
        
        now = datetime.now()
        
        return {
            "datetime": now.strftime(format_str),
            "timestamp": int(now.timestamp()),
            "iso": now.isoformat(),
            "timezone": timezone,
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.weekday(),
            "weekday_name": calendar.day_name[now.weekday()]
        }
    
    def _handle_format(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """格式化日期时间"""
        datetime_str = kwargs.get("datetime_str")
        format_str = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
        input_format = kwargs.get("input_format", "%Y-%m-%d %H:%M:%S")
        
        if not datetime_str:
            raise ValueError("需要提供datetime_str参数")
        
        # 解析输入日期时间
        try:
            dt = datetime.strptime(datetime_str, input_format)
        except ValueError:
            # 尝试自动解析
            dt = self._parse_datetime_auto(datetime_str)
        
        return {
            "original": datetime_str,
            "formatted": dt.strftime(format_str),
            "format": format_str,
            "iso": dt.isoformat(),
            "timestamp": int(dt.timestamp())
        }
    
    def _handle_parse(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """解析日期时间字符串"""
        datetime_str = kwargs.get("datetime_str")
        format_str = kwargs.get("format")
        
        if not datetime_str:
            raise ValueError("需要提供datetime_str参数")
        
        if format_str:
            dt = datetime.strptime(datetime_str, format_str)
        else:
            dt = self._parse_datetime_auto(datetime_str)
        
        return {
            "original": datetime_str,
            "parsed": {
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second,
                "weekday": dt.weekday(),
                "weekday_name": calendar.day_name[dt.weekday()]
            },
            "iso": dt.isoformat(),
            "timestamp": int(dt.timestamp())
        }
    
    def _handle_add(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """添加时间"""
        datetime_str = kwargs.get("datetime_str")
        amount = kwargs.get("amount", 0)
        unit = kwargs.get("unit", "days")
        format_str = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
        
        if not datetime_str:
            dt = datetime.now()
        else:
            dt = self._parse_datetime_auto(datetime_str)
        
        # 计算新时间
        if unit == "seconds":
            new_dt = dt + timedelta(seconds=amount)
        elif unit == "minutes":
            new_dt = dt + timedelta(minutes=amount)
        elif unit == "hours":
            new_dt = dt + timedelta(hours=amount)
        elif unit == "days":
            new_dt = dt + timedelta(days=amount)
        elif unit == "weeks":
            new_dt = dt + timedelta(weeks=amount)
        elif unit == "months":
            # 手动计算月份
            month = dt.month + amount
            year = dt.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            new_dt = dt.replace(year=year, month=month)
        elif unit == "years":
            new_dt = dt.replace(year=dt.year + amount)
        else:
            new_dt = dt
        
        return {
            "original": dt.strftime(format_str),
            "result": new_dt.strftime(format_str),
            "added": f"{amount} {unit}",
            "timestamp": int(new_dt.timestamp())
        }
    
    def _handle_diff(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """计算时间差"""
        datetime_str1 = kwargs.get("datetime_str")
        datetime_str2 = kwargs.get("datetime_str2")
        
        if not datetime_str1 or not datetime_str2:
            raise ValueError("需要提供两个日期时间参数")
        
        dt1 = self._parse_datetime_auto(datetime_str1)
        dt2 = self._parse_datetime_auto(datetime_str2)
        
        diff = dt2 - dt1
        
        total_seconds = diff.total_seconds()
        total_days = diff.days
        
        return {
            "datetime1": datetime_str1,
            "datetime2": datetime_str2,
            "difference": {
                "days": total_days,
                "hours": total_seconds / 3600,
                "minutes": total_seconds / 60,
                "seconds": total_seconds
            },
            "human_readable": self._format_timedelta(diff)
        }
    
    def _handle_timezone_convert(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """时区转换"""
        datetime_str = kwargs.get("datetime_str")
        from_tz = kwargs.get("timezone", "UTC")
        to_tz = kwargs.get("to_timezone", "UTC")
        
        if not datetime_str:
            raise ValueError("需要提供datetime_str参数")
        
        # 注意：这里简化处理，实际应该使用pytz等库
        dt = self._parse_datetime_auto(datetime_str)
        
        return {
            "original": datetime_str,
            "from_timezone": from_tz,
            "to_timezone": to_tz,
            "converted": dt.isoformat(),
            "note": "时区转换需要安装pytz库以支持完整的时区功能"
        }
    
    def _handle_get_weekday(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取星期几"""
        datetime_str = kwargs.get("datetime_str")
        
        if datetime_str:
            dt = self._parse_datetime_auto(datetime_str)
        else:
            dt = datetime.now()
        
        return {
            "date": dt.strftime("%Y-%m-%d"),
            "weekday": dt.weekday(),
            "weekday_name": calendar.day_name[dt.weekday()],
            "is_weekend": dt.weekday() >= 5
        }
    
    def _handle_get_calendar(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取日历"""
        year = kwargs.get("year", datetime.now().year)
        month = kwargs.get("month", datetime.now().month)
        
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)
        
        return {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "weekdays": list(calendar.day_name),
            "calendar": month_days,
            "days_in_month": calendar.monthrange(year, month)[1]
        }
    
    def _parse_datetime_auto(self, datetime_str: str) -> datetime:
        """自动解析日期时间字符串"""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y%m%d%H%M%S",
            "%Y%m%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"无法解析日期时间字符串: {datetime_str}")
    
    def _format_timedelta(self, td: timedelta) -> str:
        """格式化时间差为人类可读格式"""
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")
        
        return "".join(parts)
