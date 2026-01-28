"""
智能体数据模型

定义智能体的核心数据结构、数据库模型和状态管理。
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path


class AgentStatus(Enum):
    """智能体状态枚举"""
    CREATED = "created"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DELETED = "deleted"


class AgentType(Enum):
    """智能体类型枚举"""
    CHATBOT = "chatbot"
    ASSISTANT = "assistant"
    ANALYZER = "analyzer"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


class AgentCapability(Enum):
    """智能体能力枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    FILE_PROCESSING = "file_processing"
    WEB_SEARCH = "web_search"
    IMAGE_PROCESSING = "image_processing"
    AUDIO_PROCESSING = "audio_processing"
    WORKFLOW_EXECUTION = "workflow_execution"


class AgentConfig:
    """智能体配置类"""
    
    def __init__(self, 
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 max_tokens: int = 2000,
                 system_prompt: str = "",
                 capabilities: List[AgentCapability] = None,
                 skills: List[str] = None,
                 knowledge_base: List[str] = None,
                 memory_enabled: bool = True,
                 web_search_enabled: bool = False,
                 **kwargs):
        """初始化智能体配置
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system_prompt: 系统提示词
            capabilities: 能力列表
            skills: 技能列表
            knowledge_base: 知识库列表
            memory_enabled: 是否启用记忆
            web_search_enabled: 是否启用网络搜索
            **kwargs: 其他配置参数
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.capabilities = capabilities or []
        self.skills = skills or []
        self.knowledge_base = knowledge_base or []
        self.memory_enabled = memory_enabled
        self.web_search_enabled = web_search_enabled
        self.extra_config = kwargs
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            配置字典
        """
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "capabilities": [cap.value for cap in self.capabilities],
            "skills": self.skills,
            "knowledge_base": self.knowledge_base,
            "memory_enabled": self.memory_enabled,
            "web_search_enabled": self.web_search_enabled,
            **self.extra_config
        }
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AgentConfig':
        """从字典创建配置对象
        
        Args:
            config_dict: 配置字典
            
        Returns:
            配置对象
        """
        # 提取基础配置
        base_config = {
            "model_name": config_dict.get("model_name", "gpt-3.5-turbo"),
            "temperature": config_dict.get("temperature", 0.7),
            "max_tokens": config_dict.get("max_tokens", 2000),
            "system_prompt": config_dict.get("system_prompt", ""),
            "memory_enabled": config_dict.get("memory_enabled", True),
            "web_search_enabled": config_dict.get("web_search_enabled", False)
        }
        
        # 处理能力列表
        capabilities = []
        for cap_str in config_dict.get("capabilities", []):
            try:
                capabilities.append(AgentCapability(cap_str))
            except ValueError:
                # 跳过无效的能力类型
                continue
                
        base_config["capabilities"] = capabilities
        
        # 处理技能和知识库
        base_config["skills"] = config_dict.get("skills", [])
        base_config["knowledge_base"] = config_dict.get("knowledge_base", [])
        
        # 提取额外配置
        extra_config = {k: v for k, v in config_dict.items() 
                       if k not in base_config}
        
        return cls(**base_config, **extra_config)


class Agent:
    """智能体类"""
    
    def __init__(self, 
                 agent_id: str = None,
                 name: str = "",
                 description: str = "",
                 agent_type: AgentType = AgentType.CHATBOT,
                 status: AgentStatus = AgentStatus.CREATED,
                 config: AgentConfig = None,
                 created_by: str = "system",
                 created_at: datetime = None,
                 updated_at: datetime = None,
                 metadata: Dict[str, Any] = None):
        """初始化智能体
        
        Args:
            agent_id: 智能体ID
            name: 智能体名称
            description: 智能体描述
            agent_type: 智能体类型
            status: 智能体状态
            config: 智能体配置
            created_by: 创建者
            created_at: 创建时间
            updated_at: 更新时间
            metadata: 元数据
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.status = status
        self.config = config or AgentConfig()
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            智能体字典
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "config": self.config.to_dict(),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, agent_dict: Dict[str, Any]) -> 'Agent':
        """从字典创建智能体对象
        
        Args:
            agent_dict: 智能体字典
            
        Returns:
            智能体对象
        """
        # 解析枚举值
        try:
            agent_type = AgentType(agent_dict.get("agent_type", "chatbot"))
        except ValueError:
            agent_type = AgentType.CHATBOT
            
        try:
            status = AgentStatus(agent_dict.get("status", "created"))
        except ValueError:
            status = AgentStatus.CREATED
            
        # 解析配置
        config_dict = agent_dict.get("config", {})
        config = AgentConfig.from_dict(config_dict)
        
        # 解析时间戳
        created_at = datetime.fromisoformat(agent_dict["created_at"]) if agent_dict.get("created_at") else None
        updated_at = datetime.fromisoformat(agent_dict["updated_at"]) if agent_dict.get("updated_at") else None
        
        return cls(
            agent_id=agent_dict.get("agent_id"),
            name=agent_dict.get("name", ""),
            description=agent_dict.get("description", ""),
            agent_type=agent_type,
            status=status,
            config=config,
            created_by=agent_dict.get("created_by", "system"),
            created_at=created_at,
            updated_at=updated_at,
            metadata=agent_dict.get("metadata", {})
        )


class AgentManager:
    """智能体管理器"""
    
    def __init__(self, database_path: str = "backend/py_copilot.db"):
        """初始化智能体管理器
        
        Args:
            database_path: 数据库文件路径
        """
        self.database_path = database_path
        self._init_database()
        
    def _init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 创建智能体表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    agent_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_agents_name 
                ON agents(name)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_agents_type 
                ON agents(agent_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_agents_status 
                ON agents(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_agents_created_at 
                ON agents(created_at)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise Exception(f"初始化智能体数据库失败: {e}")
            
    def create_agent(self, agent: Agent) -> bool:
        """创建智能体
        
        Args:
            agent: 智能体对象
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 序列化配置和元数据
            config_json = json.dumps(agent.config.to_dict())
            metadata_json = json.dumps(agent.metadata) if agent.metadata else None
            
            cursor.execute('''
                INSERT INTO agents 
                (agent_id, name, description, agent_type, status, config, 
                 created_by, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent.agent_id,
                agent.name,
                agent.description,
                agent.agent_type.value,
                agent.status.value,
                config_json,
                agent.created_by,
                agent.created_at.isoformat(),
                agent.updated_at.isoformat(),
                metadata_json
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"创建智能体失败: {e}")
            return False
            
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            智能体对象，如果未找到返回None
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM agents WHERE agent_id = ?
            ''', (agent_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_agent(row)
            else:
                return None
                
        except Exception as e:
            print(f"获取智能体失败: {e}")
            return None
            
    def update_agent(self, agent: Agent) -> bool:
        """更新智能体
        
        Args:
            agent: 智能体对象
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 序列化配置和元数据
            config_json = json.dumps(agent.config.to_dict())
            metadata_json = json.dumps(agent.metadata) if agent.metadata else None
            
            cursor.execute('''
                UPDATE agents SET
                name = ?, description = ?, agent_type = ?, status = ?, config = ?,
                updated_at = ?, metadata = ?
                WHERE agent_id = ?
            ''', (
                agent.name,
                agent.description,
                agent.agent_type.value,
                agent.status.value,
                config_json,
                datetime.now().isoformat(),
                metadata_json,
                agent.agent_id
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"更新智能体失败: {e}")
            return False
            
    def delete_agent(self, agent_id: str) -> bool:
        """删除智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM agents WHERE agent_id = ?
            ''', (agent_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"删除智能体失败: {e}")
            return False
            
    def list_agents(self, 
                   agent_type: Optional[AgentType] = None,
                   status: Optional[AgentStatus] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[Agent]:
        """列出智能体
        
        Args:
            agent_type: 智能体类型过滤
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            智能体列表
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if agent_type:
                conditions.append("agent_type = ?")
                params.append(agent_type.value)
                
            if status:
                conditions.append("status = ?")
                params.append(status.value)
                
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f'''
                SELECT * FROM agents 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            conn.close()
            
            agents = [self._row_to_agent(row) for row in rows]
            return agents
            
        except Exception as e:
            print(f"列出智能体失败: {e}")
            return []
            
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息
        
        Returns:
            统计信息
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 总数统计
            cursor.execute('SELECT COUNT(*) FROM agents')
            total_agents = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute('SELECT agent_type, COUNT(*) FROM agents GROUP BY agent_type')
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按状态统计
            cursor.execute('SELECT status, COUNT(*) FROM agents GROUP BY status')
            status_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 最近创建的智能体
            cursor.execute('''
                SELECT name, created_at FROM agents 
                ORDER BY created_at DESC LIMIT 5
            ''')
            recent_agents = [{"name": row[0], "created_at": row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "total_agents": total_agents,
                "type_stats": type_stats,
                "status_stats": status_stats,
                "recent_agents": recent_agents
            }
            
        except Exception as e:
            print(f"获取智能体统计失败: {e}")
            return {}
            
    def _row_to_agent(self, row: tuple) -> Agent:
        """将数据库行转换为智能体对象
        
        Args:
            row: 数据库行
            
        Returns:
            智能体对象
        """
        agent_id, name, description, agent_type_str, status_str, \
        config_json, created_by, created_at_str, updated_at_str, metadata_json = row
        
        # 解析枚举值
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            agent_type = AgentType.CHATBOT
            
        try:
            status = AgentStatus(status_str)
        except ValueError:
            status = AgentStatus.CREATED
            
        # 解析配置
        config_dict = json.loads(config_json)
        config = AgentConfig.from_dict(config_dict)
        
        # 解析元数据
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        # 解析时间戳
        created_at = datetime.fromisoformat(created_at_str)
        updated_at = datetime.fromisoformat(updated_at_str)
        
        return Agent(
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=agent_type,
            status=status,
            config=config,
            created_by=created_by,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata
        )


# 全局智能体管理器实例
agent_manager = AgentManager()


class AgentTemplate:
    """智能体模板类"""
    
    def __init__(self):
        """初始化智能体模板"""
        self.templates = {
            "chatbot": self._create_chatbot_template(),
            "assistant": self._create_assistant_template(),
            "analyzer": self._create_analyzer_template(),
            "workflow": self._create_workflow_template()
        }
        
    def _create_chatbot_template(self) -> Agent:
        """创建聊天机器人模板
        
        Returns:
            聊天机器人智能体
        """
        config = AgentConfig(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2000,
            system_prompt="你是一个友好的聊天机器人，能够回答用户的各种问题。",
            capabilities=[AgentCapability.TEXT_GENERATION],
            memory_enabled=True
        )
        
        return Agent(
            name="聊天机器人",
            description="一个通用的聊天机器人，能够进行自然对话",
            agent_type=AgentType.CHATBOT,
            config=config
        )
        
    def _create_assistant_template(self) -> Agent:
        """创建助手模板
        
        Returns:
            助手智能体
        """
        config = AgentConfig(
            model_name="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=4000,
            system_prompt="你是一个专业的助手，能够帮助用户完成各种任务。",
            capabilities=[
                AgentCapability.TEXT_GENERATION,
                AgentCapability.CODE_GENERATION,
                AgentCapability.DATA_ANALYSIS
            ],
            memory_enabled=True,
            web_search_enabled=True
        )
        
        return Agent(
            name="智能助手",
            description="一个多功能的智能助手，能够处理复杂任务",
            agent_type=AgentType.ASSISTANT,
            config=config
        )
        
    def _create_analyzer_template(self) -> Agent:
        """创建分析器模板
        
        Returns:
            分析器智能体
        """
        config = AgentConfig(
            model_name="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=6000,
            system_prompt="你是一个数据分析专家，能够分析和解释数据。",
            capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.FILE_PROCESSING
            ],
            memory_enabled=False
        )
        
        return Agent(
            name="数据分析器",
            description="专门用于数据分析和处理的智能体",
            agent_type=AgentType.ANALYZER,
            config=config
        )
        
    def _create_workflow_template(self) -> Agent:
        """创建工作流模板
        
        Returns:
            工作流智能体
        """
        config = AgentConfig(
            model_name="gpt-3.5-turbo",
            temperature=0.2,
            max_tokens=3000,
            system_prompt="你是一个工作流执行器，能够协调多个任务。",
            capabilities=[
                AgentCapability.WORKFLOW_EXECUTION
            ],
            memory_enabled=True
        )
        
        return Agent(
            name="工作流执行器",
            description="用于执行复杂工作流的智能体",
            agent_type=AgentType.WORKFLOW,
            config=config
        )
        
    def get_template(self, template_name: str) -> Optional[Agent]:
        """获取模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            智能体模板，如果未找到返回None
        """
        return self.templates.get(template_name)
        
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有模板
        
        Returns:
            模板列表
        """
        templates = []
        for name, agent in self.templates.items():
            templates.append({
                "name": name,
                "display_name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type.value,
                "capabilities": [cap.value for cap in agent.config.capabilities]
            })
        
        return templates


# 全局智能体模板实例
agent_template = AgentTemplate()