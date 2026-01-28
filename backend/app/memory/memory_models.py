"""
长期记忆机制 - 记忆存储模型

定义记忆数据的核心数据结构、数据库模型和存储管理。
"""
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pathlib import Path


class MemoryType(Enum):
    """记忆类型枚举"""
    CONVERSATION = "conversation"
    FACT = "fact"
    PREFERENCE = "preference"
    BEHAVIOR = "behavior"
    KNOWLEDGE = "knowledge"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    CUSTOM = "custom"


class MemoryPriority(Enum):
    """记忆优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryAccessPattern(Enum):
    """记忆访问模式枚举"""
    FREQUENT = "frequent"
    RECENT = "recent"
    IMPORTANT = "important"
    RANDOM = "random"


class MemoryItem:
    """记忆项类"""
    
    def __init__(self, 
                 memory_id: str = None,
                 agent_id: str = "",
                 user_id: str = "",
                 memory_type: MemoryType = MemoryType.CONVERSATION,
                 content: str = "",
                 summary: str = "",
                 priority: MemoryPriority = MemoryPriority.MEDIUM,
                 access_count: int = 0,
                 last_accessed: datetime = None,
                 created_at: datetime = None,
                 expires_at: datetime = None,
                 metadata: Dict[str, Any] = None,
                 tags: List[str] = None,
                 embedding: List[float] = None):
        """初始化记忆项
        
        Args:
            memory_id: 记忆ID
            agent_id: 智能体ID
            user_id: 用户ID
            memory_type: 记忆类型
            content: 记忆内容
            summary: 记忆摘要
            priority: 优先级
            access_count: 访问次数
            last_accessed: 最后访问时间
            created_at: 创建时间
            expires_at: 过期时间
            metadata: 元数据
            tags: 标签列表
            embedding: 向量嵌入
        """
        self.memory_id = memory_id or str(uuid.uuid4())
        self.agent_id = agent_id
        self.user_id = user_id
        self.memory_type = memory_type
        self.content = content
        self.summary = summary
        self.priority = priority
        self.access_count = access_count
        self.last_accessed = last_accessed or datetime.now()
        self.created_at = created_at or datetime.now()
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.tags = tags or []
        self.embedding = embedding or []
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            记忆项字典
        """
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "summary": self.summary,
            "priority": self.priority.value,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
            "tags": self.tags,
            "embedding": self.embedding
        }
        
    @classmethod
    def from_dict(cls, memory_dict: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建记忆项对象
        
        Args:
            memory_dict: 记忆项字典
            
        Returns:
            记忆项对象
        """
        # 解析枚举值
        try:
            memory_type = MemoryType(memory_dict.get("memory_type", "conversation"))
        except ValueError:
            memory_type = MemoryType.CONVERSATION
            
        try:
            priority = MemoryPriority(memory_dict.get("priority", "medium"))
        except ValueError:
            priority = MemoryPriority.MEDIUM
            
        # 解析时间戳
        last_accessed = datetime.fromisoformat(memory_dict["last_accessed"]) if memory_dict.get("last_accessed") else None
        created_at = datetime.fromisoformat(memory_dict["created_at"]) if memory_dict.get("created_at") else None
        expires_at = datetime.fromisoformat(memory_dict["expires_at"]) if memory_dict.get("expires_at") else None
        
        return cls(
            memory_id=memory_dict.get("memory_id"),
            agent_id=memory_dict.get("agent_id", ""),
            user_id=memory_dict.get("user_id", ""),
            memory_type=memory_type,
            content=memory_dict.get("content", ""),
            summary=memory_dict.get("summary", ""),
            priority=priority,
            access_count=memory_dict.get("access_count", 0),
            last_accessed=last_accessed,
            created_at=created_at,
            expires_at=expires_at,
            metadata=memory_dict.get("metadata", {}),
            tags=memory_dict.get("tags", []),
            embedding=memory_dict.get("embedding", [])
        )
        
    def is_expired(self) -> bool:
        """检查记忆是否过期
        
        Returns:
            是否过期
        """
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
        
    def record_access(self):
        """记录访问"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        
    def calculate_relevance_score(self, query: str = None) -> float:
        """计算相关性分数
        
        Args:
            query: 查询文本
            
        Returns:
            相关性分数（0-1）
        """
        # 基础分数基于优先级和访问频率
        priority_score = {
            MemoryPriority.LOW: 0.2,
            MemoryPriority.MEDIUM: 0.5,
            MemoryPriority.HIGH: 0.8,
            MemoryPriority.CRITICAL: 1.0
        }.get(self.priority, 0.5)
        
        # 访问频率分数（对数缩放）
        access_score = min(1.0, self.access_count / 100.0)
        
        # 时间衰减分数（最近访问的分数更高）
        days_since_access = (datetime.now() - self.last_accessed).days
        time_score = max(0.1, 1.0 - (days_since_access / 365.0))
        
        # 组合分数
        base_score = (priority_score * 0.4) + (access_score * 0.3) + (time_score * 0.3)
        
        # 如果提供了查询，计算文本相似度（简化实现）
        if query:
            # 简单的文本匹配分数
            query_lower = query.lower()
            content_lower = (self.content + " " + self.summary).lower()
            
            # 计算关键词匹配
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            if query_words and content_words:
                match_ratio = len(query_words & content_words) / len(query_words)
                text_score = match_ratio * 0.5  # 文本匹配占50%权重
                base_score = (base_score * 0.5) + text_score
                
        return min(1.0, base_score)


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, database_path: str = "backend/py_copilot.db"):
        """初始化记忆管理器
        
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
            
            # 创建记忆表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    priority TEXT NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed DATETIME NOT NULL,
                    created_at DATETIME NOT NULL,
                    expires_at DATETIME,
                    metadata TEXT,
                    tags TEXT,
                    embedding TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_agent_user 
                ON memories(agent_id, user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_type 
                ON memories(memory_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_priority 
                ON memories(priority)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_created_at 
                ON memories(created_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_last_accessed 
                ON memories(last_accessed)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise Exception(f"初始化记忆数据库失败: {e}")
            
    def store_memory(self, memory: MemoryItem) -> bool:
        """存储记忆
        
        Args:
            memory: 记忆项
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 序列化数据
            metadata_json = json.dumps(memory.metadata) if memory.metadata else None
            tags_json = json.dumps(memory.tags) if memory.tags else None
            embedding_json = json.dumps(memory.embedding) if memory.embedding else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO memories 
                (memory_id, agent_id, user_id, memory_type, content, summary, priority, 
                 access_count, last_accessed, created_at, expires_at, metadata, tags, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.memory_id,
                memory.agent_id,
                memory.user_id,
                memory.memory_type.value,
                memory.content,
                memory.summary,
                memory.priority.value,
                memory.access_count,
                memory.last_accessed.isoformat(),
                memory.created_at.isoformat(),
                memory.expires_at.isoformat() if memory.expires_at else None,
                metadata_json,
                tags_json,
                embedding_json
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"存储记忆失败: {e}")
            return False
            
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆项，如果未找到返回None
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM memories WHERE memory_id = ?
            ''', (memory_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                memory = self._row_to_memory(row)
                # 记录访问
                memory.record_access()
                self.store_memory(memory)  # 更新访问记录
                return memory
            else:
                return None
                
        except Exception as e:
            print(f"获取记忆失败: {e}")
            return None
            
    def search_memories(self, 
                       agent_id: str,
                       user_id: str,
                       query: str = None,
                       memory_type: Optional[MemoryType] = None,
                       priority: Optional[MemoryPriority] = None,
                       tags: List[str] = None,
                       limit: int = 10,
                       offset: int = 0) -> List[MemoryItem]:
        """搜索记忆
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            query: 查询文本
            memory_type: 记忆类型过滤
            priority: 优先级过滤
            tags: 标签过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            记忆项列表
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = ["agent_id = ?", "user_id = ?"]
            params = [agent_id, user_id]
            
            if memory_type:
                conditions.append("memory_type = ?")
                params.append(memory_type.value)
                
            if priority:
                conditions.append("priority = ?")
                params.append(priority.value)
                
            if tags:
                # 简单的标签匹配（实际应该使用全文搜索）
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                conditions.append(f"({' OR '.join(tag_conditions)})")
                
            where_clause = " AND ".join(conditions)
            
            query_sql = f'''
                SELECT * FROM memories 
                WHERE {where_clause}
                ORDER BY last_accessed DESC, access_count DESC
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limit, offset])
            cursor.execute(query_sql, params)
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = [self._row_to_memory(row) for row in rows]
            
            # 如果提供了查询，按相关性排序
            if query:
                memories.sort(key=lambda m: m.calculate_relevance_score(query), reverse=True)
                
            return memories
            
        except Exception as e:
            print(f"搜索记忆失败: {e}")
            return []
            
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM memories WHERE memory_id = ?
            ''', (memory_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"删除记忆失败: {e}")
            return False
            
    def cleanup_expired_memories(self) -> int:
        """清理过期记忆
        
        Returns:
            删除的记忆数量
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 获取要删除的记忆数量
            cursor.execute('''
                SELECT COUNT(*) FROM memories 
                WHERE expires_at < ?
            ''', (datetime.now().isoformat(),))
            
            count_before = cursor.fetchone()[0]
            
            # 删除过期记忆
            cursor.execute('''
                DELETE FROM memories 
                WHERE expires_at < ?
            ''', (datetime.now().isoformat(),))
            
            conn.commit()
            conn.close()
            
            return count_before
            
        except Exception as e:
            print(f"清理过期记忆失败: {e}")
            return 0
            
    def get_memory_stats(self, agent_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """获取记忆统计信息
        
        Args:
            agent_id: 智能体ID过滤
            user_id: 用户ID过滤
            
        Returns:
            统计信息
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)
                
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
                
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 总数统计
            cursor.execute(f'SELECT COUNT(*) FROM memories WHERE {where_clause}', params)
            total_memories = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute(f'''
                SELECT memory_type, COUNT(*) FROM memories 
                WHERE {where_clause}
                GROUP BY memory_type
            ''', params)
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按优先级统计
            cursor.execute(f'''
                SELECT priority, COUNT(*) FROM memories 
                WHERE {where_clause}
                GROUP BY priority
            ''', params)
            priority_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 过期记忆统计
            cursor.execute(f'''
                SELECT COUNT(*) FROM memories 
                WHERE {where_clause} AND expires_at < ?
            ''', params + [datetime.now().isoformat()])
            expired_count = cursor.fetchone()[0]
            
            # 最近访问统计
            cursor.execute(f'''
                SELECT COUNT(*) FROM memories 
                WHERE {where_clause} AND last_accessed > ?
            ''', params + [(datetime.now() - timedelta(days=7)).isoformat()])
            recent_access_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_memories": total_memories,
                "type_stats": type_stats,
                "priority_stats": priority_stats,
                "expired_count": expired_count,
                "recent_access_count": recent_access_count,
                "agent_id": agent_id,
                "user_id": user_id
            }
            
        except Exception as e:
            print(f"获取记忆统计失败: {e}")
            return {}
            
    def _row_to_memory(self, row: tuple) -> MemoryItem:
        """将数据库行转换为记忆项对象
        
        Args:
            row: 数据库行
            
        Returns:
            记忆项对象
        """
        memory_id, agent_id, user_id, memory_type_str, content, summary, \
        priority_str, access_count, last_accessed_str, created_at_str, \
        expires_at_str, metadata_json, tags_json, embedding_json = row
        
        # 解析枚举值
        try:
            memory_type = MemoryType(memory_type_str)
        except ValueError:
            memory_type = MemoryType.CONVERSATION
            
        try:
            priority = MemoryPriority(priority_str)
        except ValueError:
            priority = MemoryPriority.MEDIUM
            
        # 解析元数据
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        # 解析标签
        tags = json.loads(tags_json) if tags_json else []
        
        # 解析向量嵌入
        embedding = json.loads(embedding_json) if embedding_json else []
        
        # 解析时间戳
        last_accessed = datetime.fromisoformat(last_accessed_str)
        created_at = datetime.fromisoformat(created_at_str)
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
        
        return MemoryItem(
            memory_id=memory_id,
            agent_id=agent_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            summary=summary,
            priority=priority,
            access_count=access_count,
            last_accessed=last_accessed,
            created_at=created_at,
            expires_at=expires_at,
            metadata=metadata,
            tags=tags,
            embedding=embedding
        )


# 全局记忆管理器实例
memory_manager = MemoryManager()