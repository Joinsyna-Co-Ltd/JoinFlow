"""
任务定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
import uuid


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()      # 等待执行
    READY = auto()        # 准备就绪
    RUNNING = auto()      # 执行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消
    PAUSED = auto()       # 暂停
    WAITING = auto()      # 等待依赖


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """
    任务定义
    
    表示一个可执行的操作单元
    """
    
    # 任务ID
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 任务名称
    name: str = ""
    
    # 任务描述
    description: str = ""
    
    # 操作类型（对应执行器）
    operation: str = ""
    
    # 操作参数
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    
    # 优先级
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 依赖的任务ID列表
    dependencies: List[str] = field(default_factory=list)
    
    # 执行结果
    result: Optional[TaskResult] = None
    
    # 重试次数
    retry_count: int = 0
    max_retries: int = 3
    
    # 超时时间（秒）
    timeout: int = 60
    
    # 是否需要确认
    requires_confirmation: bool = False
    
    # 回调函数
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_ready(self, completed_tasks: set) -> bool:
        """检查任务是否准备就绪"""
        if self.status != TaskStatus.PENDING:
            return False
        
        # 检查依赖是否都已完成
        for dep_id in self.dependencies:
            if dep_id not in completed_tasks:
                return False
        
        return True
    
    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat()
    
    def complete(self, result: TaskResult) -> None:
        """完成任务"""
        self.result = result
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        
        # 调用回调
        if result.success and self.on_complete:
            self.on_complete(self)
        elif not result.success and self.on_error:
            self.on_error(self)
    
    def fail(self, error: str) -> None:
        """任务失败"""
        self.result = TaskResult(success=False, error=error)
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        
        if self.on_error:
            self.on_error(self)
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now().isoformat()
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries
    
    def retry(self) -> None:
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            self.started_at = None
            self.completed_at = None
            self.result = None
    
    def get_duration(self) -> Optional[float]:
        """获取执行时长（毫秒）"""
        if self.started_at and self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "operation": self.operation,
            "parameters": self.parameters,
            "status": self.status.name,
            "priority": self.priority.name,
            "dependencies": self.dependencies,
            "result": self.result.__dict__ if self.result else None,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
    
    def __str__(self) -> str:
        return f"Task({self.id}: {self.name}, status={self.status.name})"


@dataclass
class TaskPlan:
    """
    任务计划
    
    包含一组要执行的任务
    """
    
    # 计划ID
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 计划名称
    name: str = ""
    
    # 原始用户输入
    user_input: str = ""
    
    # 任务列表
    tasks: List[Task] = field(default_factory=list)
    
    # 执行策略
    strategy: str = "sequential"  # sequential, parallel, mixed
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    
    # 当前执行的任务索引
    current_task_index: int = 0
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks.append(task)
    
    def get_next_tasks(self) -> List[Task]:
        """获取下一批要执行的任务"""
        completed_ids = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        
        ready_tasks = []
        for task in self.tasks:
            if task.is_ready(completed_ids):
                ready_tasks.append(task)
        
        return ready_tasks
    
    def is_complete(self) -> bool:
        """检查计划是否完成"""
        return all(
            t.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED}
            for t in self.tasks
        )
    
    def get_progress(self) -> Dict[str, int]:
        """获取进度"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self.tasks if t.status == TaskStatus.RUNNING)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }
    
    def get_failed_tasks(self) -> List[Task]:
        """获取失败的任务"""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "user_input": self.user_input,
            "tasks": [t.to_dict() for t in self.tasks],
            "strategy": self.strategy,
            "status": self.status.name,
            "progress": self.get_progress(),
            "created_at": self.created_at,
        }

