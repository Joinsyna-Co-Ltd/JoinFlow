"""
Task Checkpoint & Resume System
================================

Provides task checkpoint and resume capabilities:
- Save task state at any point
- Resume interrupted tasks
- Manage checkpoint storage
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class CheckpointStatus(str, Enum):
    """检查点状态"""
    ACTIVE = "active"       # 任务正在执行
    PAUSED = "paused"       # 任务已暂停
    FAILED = "failed"       # 任务失败
    COMPLETED = "completed" # 任务完成
    EXPIRED = "expired"     # 检查点已过期


@dataclass
class StepResult:
    """步骤执行结果"""
    step_index: int
    step_name: str
    agent_type: str
    status: str  # "completed", "failed", "skipped"
    output: str = ""
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "StepResult":
        if isinstance(data.get('started_at'), str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if isinstance(data.get('completed_at'), str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class StepConfig:
    """步骤配置"""
    step_index: int
    step_name: str
    agent_type: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "StepConfig":
        return cls(**data)


@dataclass
class TaskCheckpoint:
    """任务检查点"""
    task_id: str
    user_id: str = "default"
    
    # 任务信息
    task_description: str = ""
    task_type: str = ""
    
    # 状态
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    current_step: int = 0
    total_steps: int = 0
    
    # 执行记录
    completed_steps: List[StepResult] = field(default_factory=list)
    pending_steps: List[StepConfig] = field(default_factory=list)
    
    # 上下文
    context: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)  # 任务变量
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    paused_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # 统计
    total_tokens: int = 0
    retry_count: int = 0
    
    # 错误信息
    last_error: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = {
            'task_id': self.task_id,
            'user_id': self.user_id,
            'task_description': self.task_description,
            'task_type': self.task_type,
            'status': self.status.value,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'completed_steps': json.dumps([s.to_dict() for s in self.completed_steps]),
            'pending_steps': json.dumps([s.to_dict() for s in self.pending_steps]),
            'context': json.dumps(self.context),
            'variables': json.dumps(self.variables),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'total_tokens': self.total_tokens,
            'retry_count': self.retry_count,
            'last_error': self.last_error
        }
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskCheckpoint":
        # 解析状态
        if isinstance(data.get('status'), str):
            data['status'] = CheckpointStatus(data['status'])
        
        # 解析时间
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if isinstance(data.get('paused_at'), str) and data['paused_at']:
            data['paused_at'] = datetime.fromisoformat(data['paused_at'])
        if isinstance(data.get('expires_at'), str) and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        
        # 解析步骤
        if isinstance(data.get('completed_steps'), str):
            steps_data = json.loads(data['completed_steps'])
            data['completed_steps'] = [StepResult.from_dict(s) for s in steps_data]
        if isinstance(data.get('pending_steps'), str):
            steps_data = json.loads(data['pending_steps'])
            data['pending_steps'] = [StepConfig.from_dict(s) for s in steps_data]
        
        # 解析JSON字段
        if isinstance(data.get('context'), str):
            data['context'] = json.loads(data['context'])
        if isinstance(data.get('variables'), str):
            data['variables'] = json.loads(data['variables'])
        
        return cls(**data)
    
    @property
    def progress(self) -> float:
        """计算进度百分比"""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100
    
    @property
    def is_resumable(self) -> bool:
        """检查是否可恢复"""
        return self.status in [CheckpointStatus.PAUSED, CheckpointStatus.FAILED]


class CheckpointManager:
    """
    检查点管理器
    
    功能：
    - 保存任务检查点
    - 加载和恢复任务
    - 管理检查点生命周期
    """
    
    def __init__(self, db_path: str = "./workspace/checkpoints.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_description TEXT,
                    task_type TEXT,
                    status TEXT NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    total_steps INTEGER DEFAULT 0,
                    completed_steps TEXT,
                    pending_steps TEXT,
                    context TEXT,
                    variables TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    paused_at TEXT,
                    expires_at TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)
            
            # 索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_user ON checkpoints(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_status ON checkpoints(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_updated ON checkpoints(updated_at)")
            
            conn.commit()
    
    # ========================
    # 检查点操作
    # ========================
    
    def save(self, checkpoint: TaskCheckpoint) -> str:
        """
        保存检查点
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            任务ID
        """
        checkpoint.updated_at = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            data = checkpoint.to_dict()
            
            cursor.execute("""
                INSERT OR REPLACE INTO checkpoints 
                (task_id, user_id, task_description, task_type, status,
                 current_step, total_steps, completed_steps, pending_steps,
                 context, variables, created_at, updated_at, paused_at,
                 expires_at, total_tokens, retry_count, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['task_id'], data['user_id'], data['task_description'],
                data['task_type'], data['status'], data['current_step'],
                data['total_steps'], data['completed_steps'], data['pending_steps'],
                data['context'], data['variables'], data['created_at'],
                data['updated_at'], data['paused_at'], data['expires_at'],
                data['total_tokens'], data['retry_count'], data['last_error']
            ))
            conn.commit()
        
        logger.info(f"Saved checkpoint: {checkpoint.task_id}")
        return checkpoint.task_id
    
    def load(self, task_id: str) -> Optional[TaskCheckpoint]:
        """
        加载检查点
        
        Args:
            task_id: 任务ID
            
        Returns:
            检查点对象，不存在返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM checkpoints WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return TaskCheckpoint.from_dict(dict(row))
            return None
    
    def delete(self, task_id: str) -> bool:
        """
        删除检查点
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功删除
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE task_id = ?", (task_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted checkpoint: {task_id}")
            return deleted
    
    def list_checkpoints(
        self,
        user_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        limit: int = 50
    ) -> List[TaskCheckpoint]:
        """
        列出检查点
        
        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            limit: 最大数量
            
        Returns:
            检查点列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            sql = "SELECT * FROM checkpoints WHERE 1=1"
            params = []
            
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            
            if status:
                sql += " AND status = ?"
                params.append(status.value)
            
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [TaskCheckpoint.from_dict(dict(row)) for row in rows]
    
    def get_resumable(self, user_id: str = "default") -> List[TaskCheckpoint]:
        """
        获取可恢复的检查点
        
        Args:
            user_id: 用户ID
            
        Returns:
            可恢复的检查点列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM checkpoints 
                WHERE user_id = ? AND status IN (?, ?)
                ORDER BY updated_at DESC
            """, (user_id, CheckpointStatus.PAUSED.value, CheckpointStatus.FAILED.value))
            
            rows = cursor.fetchall()
            return [TaskCheckpoint.from_dict(dict(row)) for row in rows]
    
    # ========================
    # 任务控制
    # ========================
    
    def pause_task(self, task_id: str) -> bool:
        """
        暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功暂停
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return False
        
        if checkpoint.status != CheckpointStatus.ACTIVE:
            return False
        
        checkpoint.status = CheckpointStatus.PAUSED
        checkpoint.paused_at = datetime.now()
        self.save(checkpoint)
        
        logger.info(f"Paused task: {task_id}")
        return True
    
    def resume_task(self, task_id: str) -> Optional[TaskCheckpoint]:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            恢复的检查点，失败返回None
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            logger.error(f"Checkpoint not found: {task_id}")
            return None
        
        if not checkpoint.is_resumable:
            logger.error(f"Task not resumable: {task_id}, status={checkpoint.status}")
            return None
        
        checkpoint.status = CheckpointStatus.ACTIVE
        checkpoint.paused_at = None
        checkpoint.retry_count += 1
        self.save(checkpoint)
        
        logger.info(f"Resumed task: {task_id}")
        return checkpoint
    
    def complete_task(self, task_id: str) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return False
        
        checkpoint.status = CheckpointStatus.COMPLETED
        self.save(checkpoint)
        
        logger.info(f"Completed task: {task_id}")
        return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            
        Returns:
            是否成功
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return False
        
        checkpoint.status = CheckpointStatus.FAILED
        checkpoint.last_error = error
        self.save(checkpoint)
        
        logger.info(f"Failed task: {task_id}, error: {error}")
        return True
    
    # ========================
    # 步骤管理
    # ========================
    
    def update_step(
        self,
        task_id: str,
        step_result: StepResult
    ) -> bool:
        """
        更新步骤执行结果
        
        Args:
            task_id: 任务ID
            step_result: 步骤结果
            
        Returns:
            是否成功
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return False
        
        # 添加到已完成步骤
        checkpoint.completed_steps.append(step_result)
        checkpoint.current_step = step_result.step_index + 1
        checkpoint.total_tokens += step_result.tokens_used
        
        # 从待执行步骤中移除
        checkpoint.pending_steps = [
            s for s in checkpoint.pending_steps 
            if s.step_index != step_result.step_index
        ]
        
        # 检查是否完成
        if not checkpoint.pending_steps:
            checkpoint.status = CheckpointStatus.COMPLETED
        
        self.save(checkpoint)
        return True
    
    def get_next_step(self, task_id: str) -> Optional[StepConfig]:
        """
        获取下一个待执行步骤
        
        Args:
            task_id: 任务ID
            
        Returns:
            下一个步骤配置，没有则返回None
        """
        checkpoint = self.load(task_id)
        if not checkpoint or not checkpoint.pending_steps:
            return None
        
        # 检查依赖
        completed_indices = {s.step_index for s in checkpoint.completed_steps}
        
        for step in checkpoint.pending_steps:
            # 检查所有依赖是否已完成
            if all(dep in completed_indices for dep in step.depends_on):
                return step
        
        return None
    
    # ========================
    # 上下文管理
    # ========================
    
    def set_variable(self, task_id: str, key: str, value: Any) -> bool:
        """
        设置任务变量
        
        Args:
            task_id: 任务ID
            key: 变量名
            value: 变量值
            
        Returns:
            是否成功
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return False
        
        checkpoint.variables[key] = value
        self.save(checkpoint)
        return True
    
    def get_variable(self, task_id: str, key: str, default: Any = None) -> Any:
        """
        获取任务变量
        
        Args:
            task_id: 任务ID
            key: 变量名
            default: 默认值
            
        Returns:
            变量值
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return default
        
        return checkpoint.variables.get(key, default)
    
    def update_context(self, task_id: str, context: Dict[str, Any]) -> bool:
        """
        更新任务上下文
        
        Args:
            task_id: 任务ID
            context: 上下文数据
            
        Returns:
            是否成功
        """
        checkpoint = self.load(task_id)
        if not checkpoint:
            return False
        
        checkpoint.context.update(context)
        self.save(checkpoint)
        return True
    
    # ========================
    # 清理
    # ========================
    
    def cleanup_expired(self) -> int:
        """
        清理过期检查点
        
        Returns:
            清理的数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM checkpoints 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (datetime.now().isoformat(),))
            
            conn.commit()
            
            count = cursor.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired checkpoints")
            return count
    
    def cleanup_completed(self, older_than_days: int = 7) -> int:
        """
        清理已完成的旧检查点
        
        Args:
            older_than_days: 保留天数
            
        Returns:
            清理的数量
        """
        from datetime import timedelta
        
        threshold = (datetime.now() - timedelta(days=older_than_days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM checkpoints 
                WHERE status = ? AND updated_at < ?
            """, (CheckpointStatus.COMPLETED.value, threshold))
            
            conn.commit()
            
            count = cursor.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} completed checkpoints")
            return count
    
    def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取检查点统计
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            统计数据
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            user_filter = " AND user_id = ?" if user_id else ""
            params = (user_id,) if user_id else ()
            
            # 总数
            cursor.execute(
                f"SELECT COUNT(*) FROM checkpoints WHERE 1=1{user_filter}",
                params
            )
            total = cursor.fetchone()[0]
            
            # 按状态统计
            cursor.execute(f"""
                SELECT status, COUNT(*) as count
                FROM checkpoints WHERE 1=1{user_filter}
                GROUP BY status
            """, params)
            by_status = dict(cursor.fetchall())
            
            # 总Token
            cursor.execute(
                f"SELECT SUM(total_tokens) FROM checkpoints WHERE 1=1{user_filter}",
                params
            )
            total_tokens = cursor.fetchone()[0] or 0
            
            return {
                "total_checkpoints": total,
                "by_status": by_status,
                "total_tokens": total_tokens,
                "resumable": by_status.get(CheckpointStatus.PAUSED.value, 0) + 
                           by_status.get(CheckpointStatus.FAILED.value, 0)
            }


# 全局实例
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager(db_path: str = "./workspace/checkpoints.db") -> CheckpointManager:
    """获取全局检查点管理器实例"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(db_path)
    return _checkpoint_manager

