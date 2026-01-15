"""
任务定义
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    任务
    """
    id: str
    name: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    
    # 依赖
    depends_on: List[str] = field(default_factory=list)
    
    # 结果
    result: Any = None
    error: Optional[str] = None
    
    # 时间
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat()
    
    def complete(self, result: Any = None) -> None:
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now().isoformat()
    
    def fail(self, error: str) -> None:
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now().isoformat()
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now().isoformat()
    
    @property
    def is_done(self) -> bool:
        """是否已完成"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def duration_ms(self) -> float:
        """执行时间（毫秒）"""
        if not self.started_at or not self.completed_at:
            return 0
        
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at)
        return (end - start).total_seconds() * 1000
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "status": self.status.value,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
        }

