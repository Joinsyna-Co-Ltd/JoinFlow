"""
Long-term Memory System
=======================

Provides persistent memory capabilities:
- User preferences and habits
- Task patterns and learning
- Knowledge accumulation
- Context-aware recall
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """记忆类型"""
    PREFERENCE = "preference"      # 用户偏好
    TASK_PATTERN = "task_pattern"  # 任务模式
    KNOWLEDGE = "knowledge"        # 知识积累
    CONTEXT = "context"           # 上下文记忆
    FEEDBACK = "feedback"         # 用户反馈


class MemoryPriority(str, Enum):
    """记忆优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Memory:
    """记忆条目"""
    id: str = ""
    user_id: str = "default"
    memory_type: MemoryType = MemoryType.KNOWLEDGE
    
    # 内容
    key: str = ""           # 记忆键（用于快速查找）
    content: str = ""       # 记忆内容
    summary: str = ""       # 摘要
    
    # 元数据
    source: str = ""        # 来源（task_id, user_input等）
    tags: List[str] = field(default_factory=list)
    priority: MemoryPriority = MemoryPriority.MEDIUM
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 统计信息
    access_count: int = 0
    usefulness_score: float = 0.5  # 0-1，记忆有用程度
    
    # 关联
    related_memories: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['memory_type'] = self.memory_type.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        data['tags'] = json.dumps(self.tags)
        data['related_memories'] = json.dumps(self.related_memories)
        data['context'] = json.dumps(self.context)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        if isinstance(data.get('memory_type'), str):
            data['memory_type'] = MemoryType(data['memory_type'])
        if isinstance(data.get('priority'), str):
            data['priority'] = MemoryPriority(data['priority'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if isinstance(data.get('last_accessed'), str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        if isinstance(data.get('expires_at'), str) and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        if isinstance(data.get('tags'), str):
            data['tags'] = json.loads(data['tags'])
        if isinstance(data.get('related_memories'), str):
            data['related_memories'] = json.loads(data['related_memories'])
        if isinstance(data.get('context'), str):
            data['context'] = json.loads(data['context'])
        return cls(**data)


@dataclass
class UserPreference:
    """用户偏好"""
    user_id: str = "default"
    
    # Agent偏好
    preferred_agents: List[str] = field(default_factory=list)
    agent_combinations: Dict[str, List[str]] = field(default_factory=dict)
    
    # 输出偏好
    preferred_format: str = "markdown"  # markdown, html, json
    language: str = "zh-CN"
    detail_level: str = "medium"  # brief, medium, detailed
    
    # 工作习惯
    working_hours: Dict[str, Any] = field(default_factory=dict)
    common_tasks: List[str] = field(default_factory=list)
    
    # 个性化设置
    auto_suggestions: bool = True
    notification_enabled: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserPreference":
        return cls(**data)


class LongTermMemoryStore:
    """
    长期记忆存储
    
    使用SQLite进行持久化存储，支持：
    - 记忆的增删改查
    - 基于关键词的搜索
    - 基于时间的过滤
    - 记忆的自动衰减和清理
    """
    
    def __init__(self, db_path: str = "./workspace/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    key TEXT,
                    content TEXT NOT NULL,
                    summary TEXT,
                    source TEXT,
                    tags TEXT,
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    usefulness_score REAL DEFAULT 0.5,
                    related_memories TEXT,
                    context TEXT
                )
            """)
            
            # 用户偏好表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # 索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)")
            
            conn.commit()
    
    def _generate_id(self, content: str, user_id: str) -> str:
        """生成记忆ID"""
        data = f"{user_id}:{content}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    # ========================
    # 记忆操作
    # ========================
    
    def store(self, memory: Memory) -> str:
        """存储记忆"""
        if not memory.id:
            memory.id = self._generate_id(memory.content, memory.user_id)
        
        memory.updated_at = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            data = memory.to_dict()
            
            cursor.execute("""
                INSERT OR REPLACE INTO memories 
                (id, user_id, memory_type, key, content, summary, source, tags,
                 priority, created_at, updated_at, last_accessed, expires_at,
                 access_count, usefulness_score, related_memories, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id'], data['user_id'], data['memory_type'], data['key'],
                data['content'], data['summary'], data['source'], data['tags'],
                data['priority'], data['created_at'], data['updated_at'],
                data['last_accessed'], data['expires_at'], data['access_count'],
                data['usefulness_score'], data['related_memories'], data['context']
            ))
            conn.commit()
        
        logger.debug(f"Stored memory: {memory.id}")
        return memory.id
    
    def recall(
        self,
        query: Optional[str] = None,
        user_id: str = "default",
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_usefulness: float = 0.0
    ) -> List[Memory]:
        """检索记忆"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            sql = "SELECT * FROM memories WHERE user_id = ?"
            params = [user_id]
            
            if memory_type:
                sql += " AND memory_type = ?"
                params.append(memory_type.value)
            
            if query:
                sql += " AND (content LIKE ? OR summary LIKE ? OR key LIKE ?)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern, query_pattern])
            
            if tags:
                for tag in tags:
                    sql += " AND tags LIKE ?"
                    params.append(f'%"{tag}"%')
            
            sql += " AND usefulness_score >= ?"
            params.append(min_usefulness)
            
            sql += " AND (expires_at IS NULL OR expires_at > ?)"
            params.append(datetime.now().isoformat())
            
            sql += " ORDER BY usefulness_score DESC, access_count DESC, updated_at DESC"
            sql += f" LIMIT {limit}"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = Memory.from_dict(dict(row))
                # 更新访问信息
                self._update_access(memory.id)
                memories.append(memory)
            
            return memories
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取单个记忆"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                memory = Memory.from_dict(dict(row))
                self._update_access(memory_id)
                return memory
            return None
    
    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates['updated_at'] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [memory_id]
            
            cursor.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def _update_access(self, memory_id: str):
        """更新访问信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE id = ?
            """, (datetime.now().isoformat(), memory_id))
            conn.commit()
    
    # ========================
    # 用户偏好
    # ========================
    
    def save_preference(self, preference: UserPreference):
        """保存用户偏好"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences (user_id, preferences, updated_at)
                VALUES (?, ?, ?)
            """, (
                preference.user_id,
                json.dumps(preference.to_dict()),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def get_preference(self, user_id: str = "default") -> UserPreference:
        """获取用户偏好"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT preferences FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return UserPreference.from_dict(json.loads(row['preferences']))
            return UserPreference(user_id=user_id)
    
    # ========================
    # 高级功能
    # ========================
    
    def learn_from_task(
        self,
        task_description: str,
        task_result: str,
        agents_used: List[str],
        success: bool,
        user_id: str = "default"
    ) -> str:
        """从任务中学习"""
        # 创建任务模式记忆
        memory = Memory(
            user_id=user_id,
            memory_type=MemoryType.TASK_PATTERN,
            key=f"task:{hashlib.md5(task_description.encode()).hexdigest()[:8]}",
            content=task_description,
            summary=f"任务: {task_description[:50]}... -> {'成功' if success else '失败'}",
            source="task_learning",
            tags=["task"] + agents_used,
            priority=MemoryPriority.MEDIUM if success else MemoryPriority.LOW,
            usefulness_score=0.8 if success else 0.3,
            context={
                "agents": agents_used,
                "success": success,
                "result_preview": task_result[:200] if task_result else ""
            }
        )
        
        return self.store(memory)
    
    def remember_preference(
        self,
        key: str,
        value: Any,
        user_id: str = "default"
    ) -> str:
        """记住用户偏好"""
        memory = Memory(
            user_id=user_id,
            memory_type=MemoryType.PREFERENCE,
            key=f"pref:{key}",
            content=json.dumps(value) if not isinstance(value, str) else value,
            summary=f"偏好: {key}",
            source="user_preference",
            tags=["preference", key],
            priority=MemoryPriority.HIGH,
            usefulness_score=0.9
        )
        
        return self.store(memory)
    
    def add_knowledge(
        self,
        title: str,
        content: str,
        tags: List[str] = None,
        user_id: str = "default"
    ) -> str:
        """添加知识"""
        memory = Memory(
            user_id=user_id,
            memory_type=MemoryType.KNOWLEDGE,
            key=f"knowledge:{hashlib.md5(title.encode()).hexdigest()[:8]}",
            content=content,
            summary=title,
            source="knowledge_base",
            tags=tags or ["knowledge"],
            priority=MemoryPriority.MEDIUM,
            usefulness_score=0.7
        )
        
        return self.store(memory)
    
    def get_relevant_context(
        self,
        query: str,
        user_id: str = "default",
        max_memories: int = 5
    ) -> Dict[str, Any]:
        """获取相关上下文"""
        # 获取相关记忆
        memories = self.recall(
            query=query,
            user_id=user_id,
            limit=max_memories
        )
        
        # 获取用户偏好
        preference = self.get_preference(user_id)
        
        # 获取最近的任务模式
        recent_patterns = self.recall(
            user_id=user_id,
            memory_type=MemoryType.TASK_PATTERN,
            limit=3
        )
        
        return {
            "relevant_memories": [m.to_dict() for m in memories],
            "user_preference": preference.to_dict(),
            "recent_patterns": [p.to_dict() for p in recent_patterns],
            "query": query
        }
    
    def update_usefulness(self, memory_id: str, delta: float):
        """更新记忆有用程度"""
        memory = self.get(memory_id)
        if memory:
            new_score = max(0, min(1, memory.usefulness_score + delta))
            self.update(memory_id, {"usefulness_score": new_score})
    
    def cleanup_expired(self) -> int:
        """清理过期记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at < ?",
                (datetime.now().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
    
    def decay_memories(self, decay_rate: float = 0.01):
        """记忆衰减（降低长期未访问记忆的有用程度）"""
        threshold = datetime.now() - timedelta(days=30)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories 
                SET usefulness_score = MAX(0.1, usefulness_score - ?)
                WHERE last_accessed < ? AND priority != 'critical'
            """, (decay_rate, threshold.isoformat()))
            conn.commit()
            return cursor.rowcount
    
    def get_statistics(self, user_id: str = "default") -> Dict[str, Any]:
        """获取记忆统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总数
            cursor.execute(
                "SELECT COUNT(*) FROM memories WHERE user_id = ?",
                (user_id,)
            )
            total = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute("""
                SELECT memory_type, COUNT(*) as count
                FROM memories WHERE user_id = ?
                GROUP BY memory_type
            """, (user_id,))
            by_type = dict(cursor.fetchall())
            
            # 平均有用程度
            cursor.execute(
                "SELECT AVG(usefulness_score) FROM memories WHERE user_id = ?",
                (user_id,)
            )
            avg_usefulness = cursor.fetchone()[0] or 0
            
            return {
                "total_memories": total,
                "by_type": by_type,
                "average_usefulness": round(avg_usefulness, 2),
                "user_id": user_id
            }


# 全局实例
_memory_store: Optional[LongTermMemoryStore] = None


def get_memory_store(db_path: str = "./workspace/memory.db") -> LongTermMemoryStore:
    """获取全局记忆存储实例"""
    global _memory_store
    if _memory_store is None:
        _memory_store = LongTermMemoryStore(db_path)
    return _memory_store

