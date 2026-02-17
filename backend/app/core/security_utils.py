"""安全工具模块"""
import re
import html
from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, status
from app.core.logging_config import logger


class SecurityValidator:
    """安全验证器"""
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|WHERE|OR|AND)\b)",
        r"(\-\-|\#|\/\*|\*\/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"])",
        r"(\b(OR|AND)\s+\w+\s*LIKE\s*['\"].*['\"])",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?<\/script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?<\/iframe>",
        r"<object[^>]*>.*?<\/object>",
        r"<embed[^>]*>.*?<\/embed>",
        r"eval\s*\(",
        r"expression\s*\(",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.[\/\\]",
        r"%2e%2e[\/\\]",
        r"%252e%252e[\/\\]",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\|\|",
        r"&&",
        r"`[^`]*`",
    ]
    
    @classmethod
    def validate_sql_injection(cls, input_string: str) -> bool:
        """
        检测SQL注入
        
        Args:
            input_string: 输入字符串
        
        Returns:
            是否包含SQL注入
        """
        if not input_string:
            return False
        
        input_upper = input_string.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def validate_xss(cls, input_string: str) -> bool:
        """
        检测XSS攻击
        
        Args:
            input_string: 输入字符串
        
        Returns:
            是否包含XSS攻击
        """
        if not input_string:
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    @classmethod
    def validate_path_traversal(cls, input_string: str) -> bool:
        """
        检测路径遍历攻击
        
        Args:
            input_string: 输入字符串
        
        Returns:
            是否包含路径遍历攻击
        """
        if not input_string:
            return False
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def validate_command_injection(cls, input_string: str) -> bool:
        """
        检测命令注入攻击
        
        Args:
            input_string: 输入字符串
        
        Returns:
            是否包含命令注入攻击
        """
        if not input_string:
            return False
        
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, input_string):
                return True
        
        return False
    
    @classmethod
    def sanitize_input(cls, input_string: str) -> str:
        """
        清理输入字符串
        
        Args:
            input_string: 输入字符串
        
        Returns:
            清理后的字符串
        """
        if not input_string:
            return input_string
        
        sanitized = html.escape(input_string)
        sanitized = re.sub(r"<[^>]*>", "", sanitized)
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"on\w+\s*=", "", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
        
        Returns:
            是否为有效邮箱
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url: URL地址
        
        Returns:
            是否为有效URL
        """
        if not url:
            return False
        
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone: 手机号
        
        Returns:
            是否为有效手机号
        """
        if not phone:
            return False
        
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))


class RequestValidator:
    """请求验证器"""
    
    def __init__(self):
        self.security_validator = SecurityValidator()
    
    def validate_request_body(self, body: Dict[str, Any]) -> None:
        """
        验证请求体
        
        Args:
            body: 请求体字典
        
        Raises:
            HTTPException: 验证失败时抛出
        """
        if not isinstance(body, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求体格式错误"
            )
        
        self._validate_dict_values(body)
    
    def _validate_dict_values(self, data: Dict[str, Any]) -> None:
        """递归验证字典中的所有值"""
        for key, value in data.items():
            if isinstance(value, str):
                self._validate_string_value(key, value)
            elif isinstance(value, dict):
                self._validate_dict_values(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        self._validate_string_value(key, item)
                    elif isinstance(item, dict):
                        self._validate_dict_values(item)
    
    def _validate_string_value(self, key: str, value: str) -> None:
        """验证字符串值"""
        if self.security_validator.validate_sql_injection(value):
            logger.warning(f"检测到SQL注入尝试 - 字段: {key}, 值: {value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入包含非法字符"
            )
        
        if self.security_validator.validate_xss(value):
            logger.warning(f"检测到XSS攻击尝试 - 字段: {key}, 值: {value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入包含非法字符"
            )
        
        if self.security_validator.validate_path_traversal(value):
            logger.warning(f"检测到路径遍历攻击尝试 - 字段: {key}, 值: {value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入包含非法字符"
            )
        
        if self.security_validator.validate_command_injection(value):
            logger.warning(f"检测到命令注入攻击尝试 - 字段: {key}, 值: {value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入包含非法字符"
            )
    
    def validate_query_params(self, params: Dict[str, Any]) -> None:
        """
        验证查询参数
        
        Args:
            params: 查询参数字典
        
        Raises:
            HTTPException: 验证失败时抛出
        """
        if not isinstance(params, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="查询参数格式错误"
            )
        
        self._validate_dict_values(params)
    
    def validate_headers(self, headers: Dict[str, str]) -> None:
        """
        验证请求头
        
        Args:
            headers: 请求头字典
        
        Raises:
            HTTPException: 验证失败时抛出
        """
        if not isinstance(headers, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求头格式错误"
            )
        
        user_agent = headers.get("user-agent", "")
        if self.security_validator.validate_xss(user_agent):
            logger.warning(f"检测到可疑User-Agent: {user_agent}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求头包含非法字符"
            )


class ContentSecurityPolicy:
    """内容安全策略"""
    
    @staticmethod
    def get_csp_headers() -> Dict[str, str]:
        """
        获取CSP响应头
        
        Returns:
            CSP响应头字典
        """
        return {
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "media-src 'self' https:; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self):
        self.validator = RequestValidator()
        self.csp = ContentSecurityPolicy()
    
    async def __call__(self, request: Request, call_next):
        """
        中间件处理函数
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
        
        Returns:
            响应对象
        """
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    import json
                    try:
                        body_dict = json.loads(body.decode())
                        self.validator.validate_request_body(body_dict)
                    except json.JSONDecodeError:
                        pass
            
            query_params = dict(request.query_params)
            if query_params:
                self.validator.validate_query_params(query_params)
            
            headers = dict(request.headers)
            self.validator.validate_headers(headers)
            
            response = await call_next(request)
            
            for header_name, header_value in self.csp.get_csp_headers().items():
                response.headers[header_name] = header_value
            
            return response
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"安全中间件错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器内部错误"
            )


def get_security_middleware() -> SecurityMiddleware:
    """获取安全中间件实例"""
    return SecurityMiddleware()


def get_security_validator() -> SecurityValidator:
    """获取安全验证器实例"""
    return SecurityValidator()
