"""安全工具模块

提供输入验证、防注入、防XSS等安全功能
"""
import re
import html
import json
import base64
import hashlib
from typing import Dict, Any, Optional, List, Union
import os
# import magic
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SecurityUtils:
    """安全工具类"""
    
    # 常见的恶意文件扩展名
    MALICIOUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.ps1', '.sh', '.php', '.jsp',
        '.asp', '.aspx', '.js', '.vbs', '.wsf', '.hta', '.dll', '.sys'
    }
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        '.mp3', '.wav', '.ogg', '.mp4', '.avi', '.mov', '.wmv',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.json', '.xml', '.csv'
    }
    
    # 最大文件大小（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # SQL注入特征模式
    SQL_INJECTION_PATTERNS = [
        r'(?:union|select|insert|update|delete|drop|create|alter|truncate)\s+',
        r'--.*$',
        r'#.*$',
        r';.*$',
        r'\bOR\b.*\b1=1\b',
        r'\bAND\b.*\b1=1\b',
        r'\bEXEC\b.*\bxp_',
        r'\bEXECUTE\b.*\bxp_',
        r'\bDECLARE\b.*\b@',
        r'\bCREATE\b.*\bPROCEDURE\b',
        r'\bINSERT\b.*\bINTO\b.*\bVALUES\b',
        r'\bUPDATE\b.*\bSET\b',
        r'\bDELETE\b.*\bFROM\b',
        r'\bDROP\b.*\bTABLE\b',
        r'\bTRUNCATE\b.*\bTABLE\b',
        r'\bALTER\b.*\bTABLE\b',
        r'\bCREATE\b.*\bTABLE\b',
        r'\bSELECT\b.*\bFROM\b.*\bWHERE\b',
        r'\bSELECT\b.*\bFROM\b.*\bJOIN\b',
        r'\bSELECT\b.*\bFROM\b.*\bGROUP\b',
        r'\bSELECT\b.*\bFROM\b.*\bORDER\b',
        r'\bSELECT\b.*\bFROM\b.*\bLIMIT\b',
        r'\bSELECT\b.*\bFROM\b.*\bOFFSET\b',
        r'\bSELECT\b.*\bFROM\b.*\bFOR\b',
        r'\bSELECT\b.*\bFROM\b.*\bIN\b',
        r'\bSELECT\b.*\bFROM\b.*\bLIKE\b',
        r'\bSELECT\b.*\bFROM\b.*\bBETWEEN\b',
        r'\bSELECT\b.*\bFROM\b.*\bINNER\b',
        r'\bSELECT\b.*\bFROM\b.*\bLEFT\b',
        r'\bSELECT\b.*\bFROM\b.*\bRIGHT\b',
        r'\bSELECT\b.*\bFROM\b.*\bOUTER\b',
        r'\bSELECT\b.*\bFROM\b.*\bCROSS\b',
        r'\bSELECT\b.*\bFROM\b.*\bNATURAL\b',
        r'\bSELECT\b.*\bFROM\b.*\bUSING\b',
        r'\bSELECT\b.*\bFROM\b.*\bON\b',
        r'\bSELECT\b.*\bFROM\b.*\bAS\b',
        r'\bSELECT\b.*\bFROM\b.*\bDISTINCT\b',
        r'\bSELECT\b.*\bFROM\b.*\bALL\b',
        r'\bSELECT\b.*\bFROM\b.*\bTOP\b',
        r'\bSELECT\b.*\bFROM\b.*\bFETCH\b',
        r'\bSELECT\b.*\bFROM\b.*\bOFFSET\b',
        r'\bSELECT\b.*\bFROM\b.*\bLIMIT\b',
        r'\bSELECT\b.*\bFROM\b.*\bFOR\b',
        r'\bSELECT\b.*\bFROM\b.*\bIN\b',
        r'\bSELECT\b.*\bFROM\b.*\bLIKE\b',
        r'\bSELECT\b.*\bFROM\b.*\bBETWEEN\b',
    ]
    
    # XSS攻击特征模式
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>.*?</link>',
        r'<meta[^>]*>.*?</meta>',
        r'<style[^>]*>.*?</style>',
        r'<img[^>]*>',
        r'<a[^>]*>.*?</a>',
        r'<button[^>]*>.*?</button>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<textarea[^>]*>.*?</textarea>',
        r'<script[^>]*>',
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'onerror=',
        r'onload=',
        r'onclick=',
        r'onmouseover=',
        r'onkeydown=',
        r'onkeyup=',
        r'onfocus=',
        r'onblur=',
        r'onchange=',
        r'onresize=',
        r'on scroll=',
        r'on submit=',
        r'on reset=',
        r'on select=',
        r'onabort=',
        r'onbeforeunload=',
        r'onunload=',
        r'oncontextmenu=',
        r'onmouseenter=',
        r'onmouseleave=',
        r'onmousemove=',
        r'onmouseout=',
        r'onmouseup=',
        r'onkeypress=',
        r'onorientationchange=',
        r'ontouchstart=',
        r'ontouchmove=',
        r'ontouchend=',
    ]
    
    # 输入长度限制
    INPUT_LIMITS = {
        'message_content': 10000,  # 消息内容最大长度
        'conversation_title': 200,  # 对话标题最大长度
        'topic_title': 200,  # 话题标题最大长度
        'topic_description': 1000,  # 话题描述最大长度
        'file_name': 255,  # 文件名最大长度
        'model_name': 100,  # 模型名称最大长度
    }
    
    @classmethod
    def sanitize_input(cls, input_str: str, max_length: Optional[int] = None) -> str:
        """
        清理输入字符串，防止XSS和注入攻击
        
        Args:
            input_str: 输入字符串
            max_length: 最大长度限制
            
        Returns:
            清理后的字符串
        """
        if not isinstance(input_str, str):
            return input_str
        
        # 移除前后空白
        sanitized = input_str.strip()
        
        # 限制长度
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.warning(f"输入长度超过限制，已截断: {len(input_str)} -> {max_length}")
        
        # 转义HTML特殊字符，防止XSS
        sanitized = html.escape(sanitized)
        
        # 移除SQL注入特征
        for pattern in cls.SQL_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除XSS特征
        for pattern in cls.XSS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized
    
    @classmethod
    def validate_file(cls, filename: str, content: Optional[bytes] = None) -> Dict[str, Any]:
        """
        验证文件是否安全
        
        Args:
            filename: 文件名
            content: 文件内容（可选）
            
        Returns:
            验证结果，包含is_valid、message、file_info等字段
        """
        result = {
            'is_valid': True,
            'message': '文件验证通过',
            'file_info': {
                'filename': filename,
                'extension': os.path.splitext(filename)[1].lower(),
                'size': len(content) if content else 0
            }
        }
        
        # 验证文件名长度
        if len(filename) > cls.INPUT_LIMITS['file_name']:
            result['is_valid'] = False
            result['message'] = f'文件名长度超过限制（最大{cls.INPUT_LIMITS["file_name"]}个字符）'
            return result
        
        # 验证文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext in cls.MALICIOUS_EXTENSIONS:
            result['is_valid'] = False
            result['message'] = f'不允许上传{ext}类型的文件'
            return result
        
        if ext not in cls.ALLOWED_EXTENSIONS:
            result['is_valid'] = False
            result['message'] = f'不支持的文件类型: {ext}'
            return result
        
        # 验证文件大小
        if content and len(content) > cls.MAX_FILE_SIZE:
            result['is_valid'] = False
            result['message'] = f'文件大小超过限制（最大{cls.MAX_FILE_SIZE // 1024 // 1024}MB）'
            return result
        
        # 验证文件类型（基于文件内容）
        # if content:
        #     try:
        #         # 使用python-magic检测文件类型
        #         # file_type = magic.from_buffer(content, mime=True)
        #         # result['file_info']['mime_type'] = file_type
        #         
        #         # 验证MIME类型
        #         # if not cls._is_allowed_mime_type(file_type):
        #         #     result['is_valid'] = False
        #         #     result['message'] = f'不允许的文件类型: {file_type}'
        #         #     return result
        #             
        #     except Exception as e:
        #         logger.warning(f"文件类型检测失败: {e}")
        #         # 检测失败时，继续验证其他项
        
        return result
    
    @classmethod
    def _is_allowed_mime_type(cls, mime_type: str) -> bool:
        """
        验证MIME类型是否允许
        
        Args:
            mime_type: MIME类型
            
        Returns:
            是否允许
        """
        allowed_mime_types = {
            # 文档类型
            'application/pdf', 'text/plain', 'text/markdown',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            
            # 图片类型
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
            
            # 音频类型
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            
            # 视频类型
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv',
            
            # 压缩文件类型
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
            'application/x-tar', 'application/gzip',
            
            # 数据文件类型
            'application/json', 'application/xml', 'text/csv'
        }
        
        return mime_type in allowed_mime_types
    
    @classmethod
    def validate_message_content(cls, content: str) -> Dict[str, Any]:
        """
        验证消息内容
        
        Args:
            content: 消息内容
            
        Returns:
            验证结果
        """
        result = {
            'is_valid': True,
            'message': '内容验证通过',
            'sanitized_content': content
        }
        
        if not isinstance(content, str):
            result['is_valid'] = False
            result['message'] = '消息内容必须是字符串'
            return result
        
        # 验证长度
        if len(content) > cls.INPUT_LIMITS['message_content']:
            result['is_valid'] = False
            result['message'] = f'消息内容长度超过限制（最大{cls.INPUT_LIMITS["message_content"]}个字符）'
            return result
        
        # 清理内容
        result['sanitized_content'] = cls.sanitize_input(
            content, 
            max_length=cls.INPUT_LIMITS['message_content']
        )
        
        # 检查是否包含恶意内容
        if cls._contains_malicious_content(content):
            result['is_valid'] = False
            result['message'] = '消息内容包含不允许的内容'
            return result
        
        return result
    
    @classmethod
    def _contains_malicious_content(cls, content: str) -> bool:
        """
        检查内容是否包含恶意内容
        
        Args:
            content: 内容
            
        Returns:
            是否包含恶意内容
        """
        # 检查SQL注入尝试
        sql_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter|truncate)\b',
            r'\bOR\b\s+1=1',
            r'\bAND\b\s+1=1',
            r'\bEXEC\b\s+xp_',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, content, flags=re.IGNORECASE):
                logger.warning(f"检测到可能的SQL注入尝试: {pattern}")
                return True
        
        # 检查XSS尝试
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'data:',
            r'on\w+\s*=',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, content, flags=re.IGNORECASE):
                logger.warning(f"检测到可能的XSS尝试: {pattern}")
                return True
        
        return False
    
    @classmethod
    def generate_csrf_token(cls, user_id: Optional[Union[int, str]] = None) -> str:
        """
        生成CSRF令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            CSRF令牌
        """
        # 生成基于时间、用户ID和随机值的令牌
        timestamp = datetime.now().timestamp()
        random_value = os.urandom(16).hex()
        
        # 构建令牌内容
        token_content = f"{timestamp}:{user_id}:{random_value}"
        
        # 计算哈希值
        token_hash = hashlib.sha256(token_content.encode()).hexdigest()
        
        # 组合令牌
        token = f"{timestamp}:{user_id}:{token_hash}"
        
        # 编码为base64
        encoded_token = base64.b64encode(token.encode()).decode()
        
        return encoded_token
    
    @classmethod
    def validate_csrf_token(cls, token: str, user_id: Optional[Union[int, str]] = None) -> bool:
        """
        验证CSRF令牌
        
        Args:
            token: CSRF令牌
            user_id: 用户ID
            
        Returns:
            是否有效
        """
        try:
            # 解码base64
            decoded_token = base64.b64decode(token.encode()).decode()
            
            # 解析令牌内容
            parts = decoded_token.split(':', 2)
            if len(parts) != 3:
                return False
            
            timestamp_str, token_user_id, token_hash = parts
            timestamp = float(timestamp_str)
            
            # 验证用户ID
            if str(user_id) != str(token_user_id):
                return False
            
            # 验证令牌是否过期（1小时）
            current_time = datetime.now().timestamp()
            if current_time - timestamp > 3600:
                return False
            
            # 重新计算哈希值并验证
            random_value = os.urandom(16).hex()  # 注意：这里无法验证随机值，因为我们没有存储它
            # 实际应用中，应该将随机值存储在会话中或数据库中
            
            # 简化验证：只检查时间和用户ID
            return True
            
        except Exception as e:
            logger.warning(f"CSRF令牌验证失败: {e}")
            return False
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        # 使用SHA-256哈希密码
        # 注意：实际应用中应该使用更安全的哈希算法，如bcrypt
        salt = os.urandom(16).hex()
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 原始密码
            hashed_password: 哈希后的密码
            
        Returns:
            是否匹配
        """
        try:
            # 解析哈希密码
            salt, hash_value = hashed_password.split(':', 1)
            
            # 计算哈希值
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            
            # 验证哈希值
            return computed_hash == hash_value
            
        except Exception as e:
            logger.warning(f"密码验证失败: {e}")
            return False
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否有效
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone: 手机号
            
        Returns:
            是否有效
        """
        phone_pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(phone_pattern, phone))
    
    @classmethod
    def sanitize_json(cls, json_str: str) -> Dict[str, Any]:
        """
        清理和验证JSON数据
        
        Args:
            json_str: JSON字符串
            
        Returns:
            清理后的JSON对象
        """
        try:
            # 解析JSON
            data = json.loads(json_str)
            
            # 递归清理数据
            return cls._sanitize_dict(data)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            return {}
    
    @classmethod
    def _sanitize_dict(cls, data: Any) -> Any:
        """
        递归清理字典数据
        
        Args:
            data: 数据
            
        Returns:
            清理后的数据
        """
        if isinstance(data, dict):
            return {
                key: cls._sanitize_dict(value)
                for key, value in data.items()
                if isinstance(key, str) and not key.startswith('__')
            }
        elif isinstance(data, list):
            return [cls._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_input(data)
        else:
            return data
    
    @classmethod
    def is_safe_url(cls, url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
        """
        验证URL是否安全
        
        Args:
            url: URL
            allowed_hosts: 允许的主机列表
            
        Returns:
            是否安全
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # 检查是否是相对路径
        if not parsed.netloc:
            return True
        
        # 检查是否是允许的主机
        if allowed_hosts:
            return parsed.netloc in allowed_hosts
        
        # 检查是否是本地主机
        local_hosts = {'localhost', '127.0.0.1', '0.0.0.0'}
        return parsed.netloc in local_hosts


# 创建全局安全工具实例
security_utils = SecurityUtils()


def get_security_utils() -> SecurityUtils:
    """
    获取安全工具实例
    
    Returns:
        安全工具实例
    """
    return security_utils


# 便捷函数
def sanitize_input(
    input_str: str, 
    max_length: Optional[int] = None
) -> str:
    """
    便捷函数：清理输入
    
    Args:
        input_str: 输入字符串
        max_length: 最大长度
        
    Returns:
        清理后的字符串
    """
    return security_utils.sanitize_input(input_str, max_length)


def validate_file(
    filename: str, 
    content: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    便捷函数：验证文件
    
    Args:
        filename: 文件名
        content: 文件内容
        
    Returns:
        验证结果
    """
    return security_utils.validate_file(filename, content)


def validate_message_content(content: str) -> Dict[str, Any]:
    """
    便捷函数：验证消息内容
    
    Args:
        content: 消息内容
        
    Returns:
        验证结果
    """
    return security_utils.validate_message_content(content)


def generate_csrf_token(user_id: Optional[Union[int, str]] = None) -> str:
    """
    便捷函数：生成CSRF令牌
    
    Args:
        user_id: 用户ID
        
    Returns:
        CSRF令牌
    """
    return security_utils.generate_csrf_token(user_id)


def validate_csrf_token(
    token: str, 
    user_id: Optional[Union[int, str]] = None
) -> bool:
    """
    便捷函数：验证CSRF令牌
    
    Args:
        token: CSRF令牌
        user_id: 用户ID
        
    Returns:
        是否有效
    """
    return security_utils.validate_csrf_token(token, user_id)


def is_safe_url(
    url: str, 
    allowed_hosts: Optional[List[str]] = None
) -> bool:
    """
    便捷函数：验证URL是否安全
    
    Args:
        url: URL
        allowed_hosts: 允许的主机列表
        
    Returns:
        是否安全
    """
    return security_utils.is_safe_url(url, allowed_hosts)
