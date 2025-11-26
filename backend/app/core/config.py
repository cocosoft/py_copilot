"""应用配置管理"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""
    # 应用配置
    app_name: str = Field(default="Py Copilot", env="APP_NAME")
    debug: bool = Field(default=True, env="DEBUG")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql://admin:password@localhost:5432/example_db", 
        env="DATABASE_URL"
    )
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # API配置
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production", 
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # OpenAI API配置
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Hugging Face配置
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # DeepSeek API配置
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    deepseek_api_base: Optional[str] = Field(default="https://api.deepseek.com/v1", env="DEEPSEEK_API_BASE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()