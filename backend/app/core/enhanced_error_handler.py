"""增强的错误处理模块

提供更细粒度的错误分类和日志记录
"""
import logging
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ErrorCategory(Enum):
    """错误分类枚举"""
    AUTHENTICATION = "authentication"  # 认证错误
    AUTHORIZATION = "authorization"    # 授权错误
    VALIDATION = "validation"          # 验证错误
    DATABASE = "database"              # 数据库错误
    NETWORK = "network"                # 网络错误
    SERVICE = "service"                # 服务错误
    RESOURCE = "resource"              # 资源错误
    CONFIGURATION = "configuration"      # 配置错误
    EXTERNAL = "external"              # 外部服务错误
    SYSTEM = "system"                  # 系统错误
    BUSINESS = "business"                # 业务逻辑错误
    WEBSOCKET = "websocket"            # WebSocket错误
    FILE = "file"                      # 文件处理错误
    VOICE = "voice"                    # 语音处理错误
    IMAGE = "image"                    # 图像处理错误
    MEMORY = "memory"                  # 记忆服务错误
    KNOWLEDGE = "knowledge"            # 知识库错误
    SEARCH = "search"                  # 搜索错误


class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"          # 低：不影响主要功能
    MEDIUM = "medium"    # 中：影响部分功能
    HIGH = "high"        # 高：影响主要功能
    CRITICAL = "critical"  # 严重：系统不可用


class EnhancedError(Exception):
    """增强的错误基类"""
    
    def __init__(
        self,
        code: str,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[str] = None,
        field: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        初始化增强错误
        
        Args:
            code: 错误码
            message: 错误消息
            category: 错误分类
            severity: 错误严重程度
            details: 错误详情
            field: 错误字段
            context: 错误上下文
        """
        self.code = code
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details
        self.field = field
        self.context = context or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "field": self.field,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }
    
    def get_log_level(self) -> int:
        """获取日志级别"""
        severity_to_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_to_level.get(self.severity, logging.ERROR)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: logging.Logger):
        """
        初始化错误处理器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.error_stats: Dict[str, Dict[str, Any]] = {}
    
    def handle_error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理错误
        
        Args:
            error: 异常对象
            request_id: 请求ID
            user_id: 用户ID
            path: 请求路径
            method: 请求方法
            
        Returns:
            错误响应字典
        """
        # 如果是增强错误，直接使用
        if isinstance(error, EnhancedError):
            enhanced_error = error
        else:
            # 将普通异常转换为增强错误
            enhanced_error = self._convert_to_enhanced_error(error)
        
        # 更新错误统计
        self._update_error_stats(enhanced_error)
        
        # 记录错误日志
        self._log_error(enhanced_error, request_id, user_id, path, method)
        
        # 构建错误响应
        error_response = {
            "success": False,
            "error": enhanced_error.to_dict()
        }
        
        # 添加请求上下文
        if request_id or user_id or path or method:
            error_response["error"]["context"].update({
                "request_id": request_id,
                "user_id": user_id,
                "path": path,
                "method": method
            })
        
        return error_response
    
    def _convert_to_enhanced_error(self, error: Exception) -> EnhancedError:
        """
        将普通异常转换为增强错误
        
        Args:
            error: 异常对象
            
        Returns:
            增强错误对象
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 根据异常类型确定错误分类
        category_mapping = {
            "ValueError": ErrorCategory.VALIDATION,
            "TypeError": ErrorCategory.VALIDATION,
            "KeyError": ErrorCategory.VALIDATION,
            "AttributeError": ErrorCategory.SYSTEM,
            "ImportError": ErrorCategory.CONFIGURATION,
            "ConnectionError": ErrorCategory.NETWORK,
            "TimeoutError": ErrorCategory.NETWORK,
            "FileNotFoundError": ErrorCategory.RESOURCE,
            "PermissionError": ErrorCategory.AUTHORIZATION,
            "DatabaseError": ErrorCategory.DATABASE,
            "HTTPException": ErrorCategory.SERVICE,
            "ValidationError": ErrorCategory.VALIDATION,
            "UnicodeDecodeError": ErrorCategory.VALIDATION,
            "JSONDecodeError": ErrorCategory.VALIDATION
        }
        
        category = category_mapping.get(error_type, ErrorCategory.SYSTEM)
        
        # 根据异常类型确定严重程度
        severity_mapping = {
            "ValueError": ErrorSeverity.MEDIUM,
            "TypeError": ErrorSeverity.MEDIUM,
            "KeyError": ErrorSeverity.MEDIUM,
            "AttributeError": ErrorSeverity.HIGH,
            "ImportError": ErrorSeverity.HIGH,
            "ConnectionError": ErrorSeverity.HIGH,
            "TimeoutError": ErrorSeverity.MEDIUM,
            "FileNotFoundError": ErrorSeverity.MEDIUM,
            "PermissionError": ErrorSeverity.HIGH,
            "DatabaseError": ErrorSeverity.HIGH,
            "HTTPException": ErrorSeverity.MEDIUM,
            "ValidationError": ErrorSeverity.LOW
        }
        
        severity = severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
        
        # 生成错误码
        error_code = self._generate_error_code(category, error_type)
        
        return EnhancedError(
            code=error_code,
            message=error_message,
            category=category,
            severity=severity,
            details=f"{error_type}: {error_message}"
        )
    
    def _generate_error_code(self, category: ErrorCategory, error_type: str) -> str:
        """
        生成错误码
        
        Args:
            category: 错误分类
            error_type: 错误类型
            
        Returns:
            错误码
        """
        category_prefix = {
            ErrorCategory.AUTHENTICATION: "AUTH",
            ErrorCategory.AUTHORIZATION: "PERM",
            ErrorCategory.VALIDATION: "VAL",
            ErrorCategory.DATABASE: "DB",
            ErrorCategory.NETWORK: "NET",
            ErrorCategory.SERVICE: "SVC",
            ErrorCategory.RESOURCE: "RES",
            ErrorCategory.CONFIGURATION: "CFG",
            ErrorCategory.EXTERNAL: "EXT",
            ErrorCategory.SYSTEM: "SYS",
            ErrorCategory.BUSINESS: "BIZ",
            ErrorCategory.WEBSOCKET: "WS",
            ErrorCategory.FILE: "FILE",
            ErrorCategory.VOICE: "VOICE",
            ErrorCategory.IMAGE: "IMG",
            ErrorCategory.MEMORY: "MEM",
            ErrorCategory.KNOWLEDGE: "KNOW",
            ErrorCategory.SEARCH: "SEARCH"
        }
        
        prefix = category_prefix.get(category, "ERR")
        error_type_short = error_type[:8].upper() if error_type else "UNKNOWN"
        return f"{prefix}_{error_type_short}"
    
    def _log_error(
        self,
        error: EnhancedError,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None
    ):
        """
        记录错误日志
        
        Args:
            error: 增强错误对象
            request_id: 请求ID
            user_id: 用户ID
            path: 请求路径
            method: 请求方法
        """
        log_level = error.get_log_level()
        
        log_data = {
            "error_code": error.code,
            "error_category": error.category.value,
            "error_severity": error.severity.value,
            "error_message": error.message,
            "error_details": error.details,
            "error_field": error.field,
            "timestamp": error.timestamp.isoformat()
        }
        
        if request_id:
            log_data["request_id"] = request_id
        if user_id:
            log_data["user_id"] = user_id
        if path:
            log_data["path"] = path
        if method:
            log_data["method"] = method
        
        if error.context:
            log_data["context"] = error.context
        
        # 根据严重程度选择日志级别
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"[{error.code}] {error.message}", extra={"extra_fields": log_data})
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"[{error.code}] {error.message}", extra={"extra_fields": log_data})
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"[{error.code}] {error.message}", extra={"extra_fields": log_data})
        else:
            self.logger.info(f"[{error.code}] {error.message}", extra={"extra_fields": log_data})
    
    def _update_error_stats(self, error: EnhancedError):
        """
        更新错误统计
        
        Args:
            error: 增强错误对象
        """
        error_key = error.code
        
        if error_key not in self.error_stats:
            self.error_stats[error_key] = {
                "code": error.code,
                "category": error.category.value,
                "count": 0,
                "first_occurrence": error.timestamp,
                "last_occurrence": error.timestamp,
                "severity": error.severity.value
            }
        
        stats = self.error_stats[error_key]
        stats["count"] += 1
        stats["last_occurrence"] = error.timestamp
    
    def get_error_stats(self) -> List[Dict[str, Any]]:
        """
        获取错误统计
        
        Returns:
            错误统计列表
        """
        return sorted(
            self.error_stats.values(),
            key=lambda x: x["count"],
            reverse=True
        )
    
    def clear_error_stats(self):
        """清除错误统计"""
        self.error_stats.clear()


# 创建全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler(logger: Optional[logging.Logger] = None) -> ErrorHandler:
    """
    获取错误处理器实例
    
    Args:
        logger: 日志记录器
        
    Returns:
        错误处理器实例
    """
    global _error_handler
    if _error_handler is None:
        if logger is None:
            logger = logging.getLogger(__name__)
        _error_handler = ErrorHandler(logger)
    return _error_handler


# 便捷的错误创建函数
def create_error(
    code: str,
    message: str,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    **kwargs
) -> EnhancedError:
    """
    创建增强错误
    
    Args:
        code: 错误码
        message: 错误消息
        category: 错误分类
        severity: 错误严重程度
        **kwargs: 其他参数
        
    Returns:
        增强错误对象
    """
    return EnhancedError(
        code=code,
        message=message,
        category=category,
        severity=severity,
        **kwargs
    )


# 预定义的便捷错误创建函数
def create_validation_error(message: str, field: Optional[str] = None, **kwargs) -> EnhancedError:
    """创建验证错误"""
    return create_error(
        code="VALIDATION_ERROR",
        message=message,
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        field=field,
        **kwargs
    )


def create_database_error(message: str, **kwargs) -> EnhancedError:
    """创建数据库错误"""
    return create_error(
        code="DATABASE_ERROR",
        message=message,
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        **kwargs
    )


def create_network_error(message: str, **kwargs) -> EnhancedError:
    """创建网络错误"""
    return create_error(
        code="NETWORK_ERROR",
        message=message,
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_service_error(message: str, **kwargs) -> EnhancedError:
    """创建服务错误"""
    return create_error(
        code="SERVICE_ERROR",
        message=message,
        category=ErrorCategory.SERVICE,
        severity=ErrorSeverity.HIGH,
        **kwargs
    )


def create_resource_error(message: str, **kwargs) -> EnhancedError:
    """创建资源错误"""
    return create_error(
        code="RESOURCE_ERROR",
        message=message,
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_external_error(message: str, **kwargs) -> EnhancedError:
    """创建外部服务错误"""
    return create_error(
        code="EXTERNAL_ERROR",
        message=message,
        category=ErrorCategory.EXTERNAL,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_file_error(message: str, **kwargs) -> EnhancedError:
    """创建文件处理错误"""
    return create_error(
        code="FILE_ERROR",
        message=message,
        category=ErrorCategory.FILE,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_voice_error(message: str, **kwargs) -> EnhancedError:
    """创建语音处理错误"""
    return create_error(
        code="VOICE_ERROR",
        message=message,
        category=ErrorCategory.VOICE,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_image_error(message: str, **kwargs) -> EnhancedError:
    """创建图像处理错误"""
    return create_error(
        code="IMAGE_ERROR",
        message=message,
        category=ErrorCategory.IMAGE,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_memory_error(message: str, **kwargs) -> EnhancedError:
    """创建记忆服务错误"""
    return create_error(
        code="MEMORY_ERROR",
        message=message,
        category=ErrorCategory.MEMORY,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_knowledge_error(message: str, **kwargs) -> EnhancedError:
    """创建知识库错误"""
    return create_error(
        code="KNOWLEDGE_ERROR",
        message=message,
        category=ErrorCategory.KNOWLEDGE,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_search_error(message: str, **kwargs) -> EnhancedError:
    """创建搜索错误"""
    return create_error(
        code="SEARCH_ERROR",
        message=message,
        category=ErrorCategory.SEARCH,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )


def create_websocket_error(message: str, **kwargs) -> EnhancedError:
    """创建WebSocket错误"""
    return create_error(
        code="WEBSOCKET_ERROR",
        message=message,
        category=ErrorCategory.WEBSOCKET,
        severity=ErrorSeverity.MEDIUM,
        **kwargs
    )
