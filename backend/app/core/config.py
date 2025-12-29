"""应用配置管理"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    """应用配置类"""
    # 应用配置
    app_name: str = Field(default="Py Copilot", env="APP_NAME")
    debug: bool = Field(default=True, env="DEBUG")
    
    # 加密配置
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # 数据库配置
    database_url: str = Field(
        default=f"sqlite:///{os.path.join(BASE_DIR, 'py_copilot.db')}", 
        env="DATABASE_URL"
    )
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # API配置
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production", 
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    enable_auth: bool = Field(default=False, env="ENABLE_AUTH")
    
    # OpenAI API配置
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Hugging Face配置
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # DeepSeek API配置
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    deepseek_api_base: Optional[str] = Field(default="https://api.deepseek.com/v1", env="DEEPSEEK_API_BASE")
    
    # 服务器配置
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="SERVER_PORT")
    server_reload: bool = Field(default=False, env="SERVER_RELOAD")
    server_workers: int = Field(default=1, env="SERVER_WORKERS")
    
    # 外部集成API配置
    external_api_key: Optional[str] = Field(default="your-external-api-key-change-this-in-production", env="EXTERNAL_API_KEY")
    enable_external_api: bool = Field(default=True, env="ENABLE_EXTERNAL_API")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()