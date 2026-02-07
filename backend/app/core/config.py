"""应用配置管理"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取项目根目录（用于数据库路径）
PROJECT_ROOT = os.path.dirname(BASE_DIR)


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
    
    # API基础URL配置（用于API测试）
    api_base_url: str = Field(default="http://localhost:8007", env="API_BASE_URL")
    
    # 前端配置
    frontend_url: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    frontend_ports: str = Field(default="5173,5174,5175,5176,5177", env="FRONTEND_PORTS")
    
    # Redis配置
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    # Ollama配置
    ollama_api_endpoint: str = Field(default="http://localhost:11434/v1", env="OLLAMA_API_ENDPOINT")
    ollama_port: int = Field(default=11434, env="OLLAMA_PORT")
    
    # 微服务端口配置
    gateway_port: int = Field(default=8000, env="GATEWAY_PORT")
    chat_service_port: int = Field(default=8001, env="CHAT_SERVICE_PORT")
    search_service_port: int = Field(default=8002, env="SEARCH_SERVICE_PORT")
    file_service_port: int = Field(default=8003, env="FILE_SERVICE_PORT")
    voice_service_port: int = Field(default=8004, env="VOICE_SERVICE_PORT")
    monitoring_service_port: int = Field(default=8005, env="MONITORING_SERVICE_PORT")
    enhanced_chat_service_port: int = Field(default=8006, env="ENHANCED_CHAT_SERVICE_PORT")
    
    # 服务器配置
    server_host: str = Field(default="127.0.0.1", env="SERVER_HOST")
    
    # 功能开关配置
    enable_knowledge_graph: bool = Field(default=False, env="ENABLE_KNOWLEDGE_GRAPH", description="是否启用知识图谱功能")
    server_port: int = Field(default=8001, env="SERVER_PORT")
    server_reload: bool = Field(default=False, env="SERVER_RELOAD")
    server_workers: int = Field(default=1, env="SERVER_WORKERS")
    
    # 外部集成API配置
    external_api_key: Optional[str] = Field(default="your-external-api-key-change-this-in-production", env="EXTERNAL_API_KEY")
    enable_external_api: bool = Field(default=True, env="ENABLE_EXTERNAL_API")
    
    # 文件上传配置
    upload_folder: str = Field(default=os.path.join(BASE_DIR, "uploads"), env="UPLOAD_FOLDER")
    
    # 性能监控配置
    enable_performance_logging: bool = Field(default=True, env="ENABLE_PERFORMANCE_LOGGING")
    performance_log_level: str = Field(default="INFO", env="PERFORMANCE_LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()