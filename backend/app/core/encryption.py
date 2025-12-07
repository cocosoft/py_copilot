"""加密工具模块，用于安全存储API密钥等敏感信息"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from app.core.config import settings


class EncryptionTool:
    """加密工具类，提供加密和解密方法"""
    
    def __init__(self):
        """初始化加密工具，使用环境变量中的密钥或生成默认密钥"""
        # 尝试从环境变量获取密钥
        secret_key = settings.encryption_key
        
        if secret_key:
            # 如果提供了密钥，确保它是有效的Fernet密钥格式
            if len(secret_key) == 44:  # Fernet密钥是44个字符的base64字符串
                self.key = secret_key.encode('utf-8')
            else:
                # 如果密钥格式不正确，使用它的哈希作为基础
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'fixed-salt-change-in-production',  # 生产环境应该使用随机盐
                    iterations=100000,
                )
                self.key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        else:
            # 否则生成一个随机密钥（注意：生产环境应使用固定密钥）
            self.key = Fernet.generate_key()
            
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """加密字符串数据
        
        Args:
            data: 要加密的字符串
            
        Returns:
            加密后的字符串
        """
        if not data:
            return data
            
        encrypted_data = self.cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted_data.decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密字符串数据
        
        Args:
            encrypted_data: 要解密的字符串
            
        Returns:
            解密后的字符串
        """
        if not encrypted_data:
            return encrypted_data
            
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_data.decode('utf-8')


# 创建全局加密工具实例
encryption_tool = EncryptionTool()


# 便捷函数
def encrypt_string(data: str) -> str:
    """加密字符串的便捷函数"""
    return encryption_tool.encrypt(data)


def decrypt_string(encrypted_data: str) -> str:
    """解密字符串的便捷函数
    
    Args:
        encrypted_data: 要解密的字符串，如果不是有效的Fernet令牌，则直接返回
        
    Returns:
        解密后的字符串或原始字符串（如果不是加密数据）
    """
    if not encrypted_data:
        return encrypted_data
    
    # 检查是否为有效的Fernet令牌（通常以gAAAAAB开头）
    if not encrypted_data.startswith('gAAAAAB'):
        # 如果不是加密数据，直接返回
        return encrypted_data
    
    return encryption_tool.decrypt(encrypted_data)
