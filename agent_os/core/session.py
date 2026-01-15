"""
Agent OS 会话管理
"""
import uuid
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class Message:
    """对话消息"""
    role: str  # user, agent, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class TaskRecord:
    """任务记录"""
    id: str
    command: str
    status: str  # pending, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "command": self.command,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
        }


class Session:
    """
    Agent OS 会话
    
    管理对话历史、任务记录和上下文状态
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.id = session_id or str(uuid.uuid4())[:8]
        self.created_at = datetime.now().isoformat()
        
        # 对话历史
        self.messages: List[Message] = []
        
        # 任务记录
        self.tasks: List[TaskRecord] = []
        
        # 上下文变量
        self.context: Dict[str, Any] = {
            "current_dir": str(Path.cwd()),
            "platform": "",
            "user": "",
        }
        
        # 最近操作
        self.recent_files: List[str] = []
        self.recent_apps: List[str] = []
        self.recent_searches: List[str] = []
        
        # 状态
        self.is_active = True
        self.last_activity = datetime.now().isoformat()
    
    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        msg = Message(role="user", content=content)
        self.messages.append(msg)
        self._update_activity()
        return msg
    
    def add_agent_message(self, content: str, metadata: Dict = None) -> Message:
        """添加代理消息"""
        msg = Message(role="agent", content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._update_activity()
        return msg
    
    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        msg = Message(role="system", content=content)
        self.messages.append(msg)
        return msg
    
    def start_task(self, command: str) -> TaskRecord:
        """开始任务"""
        task = TaskRecord(
            id=str(uuid.uuid4())[:8],
            command=command,
            status="running",
            started_at=datetime.now().isoformat(),
        )
        self.tasks.append(task)
        self._update_activity()
        return task
    
    def complete_task(self, task_id: str, result: Any = None, error: str = None) -> Optional[TaskRecord]:
        """完成任务"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = "failed" if error else "completed"
                task.result = result
                task.error = error
                task.completed_at = datetime.now().isoformat()
                
                if task.started_at:
                    start = datetime.fromisoformat(task.started_at)
                    task.duration_ms = (datetime.now() - start).total_seconds() * 1000
                
                return task
        return None
    
    def add_recent_file(self, path: str) -> None:
        """添加最近文件"""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:50]
    
    def add_recent_app(self, app: str) -> None:
        """添加最近应用"""
        if app in self.recent_apps:
            self.recent_apps.remove(app)
        self.recent_apps.insert(0, app)
        self.recent_apps = self.recent_apps[:20]
    
    def add_recent_search(self, query: str) -> None:
        """添加最近搜索"""
        if query in self.recent_searches:
            self.recent_searches.remove(query)
        self.recent_searches.insert(0, query)
        self.recent_searches = self.recent_searches[:30]
    
    def get_conversation_history(self, limit: int = 20) -> List[Dict]:
        """获取对话历史"""
        return [m.to_dict() for m in self.messages[-limit:]]
    
    def get_task_history(self, limit: int = 50) -> List[Dict]:
        """获取任务历史"""
        return [t.to_dict() for t in self.tasks[-limit:]]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        return {
            "session_id": self.id,
            "current_dir": self.context.get("current_dir"),
            "recent_files": self.recent_files[:5],
            "recent_apps": self.recent_apps[:5],
            "recent_searches": self.recent_searches[:5],
            "message_count": len(self.messages),
            "task_count": len(self.tasks),
            "last_activity": self.last_activity,
        }
    
    def _update_activity(self) -> None:
        """更新活动时间"""
        self.last_activity = datetime.now().isoformat()
    
    def save(self, path: str) -> None:
        """保存会话"""
        data = {
            "id": self.id,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages],
            "tasks": [t.to_dict() for t in self.tasks],
            "context": self.context,
            "recent_files": self.recent_files,
            "recent_apps": self.recent_apps,
            "recent_searches": self.recent_searches,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "Session":
        """加载会话"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session = cls(session_id=data.get("id"))
        session.created_at = data.get("created_at", session.created_at)
        session.context = data.get("context", {})
        session.recent_files = data.get("recent_files", [])
        session.recent_apps = data.get("recent_apps", [])
        session.recent_searches = data.get("recent_searches", [])
        
        for msg_data in data.get("messages", []):
            msg = Message(**msg_data)
            session.messages.append(msg)
        
        for task_data in data.get("tasks", []):
            task = TaskRecord(**task_data)
            session.tasks.append(task)
        
        return session
    
    def clear(self) -> None:
        """清除会话"""
        self.messages.clear()
        self.tasks.clear()
        self.recent_files.clear()
        self.recent_apps.clear()
        self.recent_searches.clear()

