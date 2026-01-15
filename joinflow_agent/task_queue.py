"""
Task Queue System
=================

Provides asynchronous task execution:
- Background task processing
- Task priority and scheduling
- Progress tracking
- Result callbacks
"""

import uuid
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Dict, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """A task to be executed"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Execution
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    progress: float = 0.0  # 0-100
    progress_message: str = ""
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Result
    result: Any = None
    error: Optional[str] = None
    
    # Callbacks
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None
    
    # Metadata
    user_id: str = "default"
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_progress(self, progress: float, message: str = "") -> None:
        """Update task progress"""
        self.progress = min(100, max(0, progress))
        self.progress_message = message
        
        if self.on_progress:
            try:
                self.on_progress(self)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata
        }


class TaskQueue:
    """
    Asynchronous task queue with priority support.
    
    Features:
    - Priority-based task scheduling
    - Concurrent execution with thread pool
    - Progress tracking
    - Task callbacks
    - Result retrieval
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 1000
    ):
        self._queue = queue.PriorityQueue(maxsize=max_queue_size)
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()
        
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: Dict[str, Future] = {}
        
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Event callbacks
        self._global_progress_callback: Optional[Callable] = None
        self._global_complete_callback: Optional[Callable] = None
    
    def start(self) -> None:
        """Start the task queue worker"""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Task queue started")
    
    def stop(self, wait: bool = True) -> None:
        """Stop the task queue"""
        self._running = False
        
        if wait and self._worker_thread:
            self._worker_thread.join(timeout=10)
        
        self._executor.shutdown(wait=wait)
        logger.info("Task queue stopped")
    
    def submit(
        self,
        func: Callable,
        *args,
        name: str = "",
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str = "default",
        session_id: Optional[str] = None,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        **kwargs
    ) -> Task:
        """Submit a task to the queue"""
        task = Task(
            name=name or func.__name__,
            description=description,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            user_id=user_id,
            session_id=session_id,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error
        )
        
        with self._lock:
            self._tasks[task.id] = task
            
            # Priority queue uses (priority_value, timestamp, task_id)
            # Lower priority value = higher priority
            priority_item = (
                -priority.value,  # Negative so higher priority comes first
                task.created_at.timestamp(),
                task.id
            )
            
            try:
                self._queue.put_nowait(priority_item)
                task.status = TaskStatus.QUEUED
            except queue.Full:
                task.status = TaskStatus.FAILED
                task.error = "Queue is full"
        
        logger.info(f"Task {task.id} ({task.name}) submitted")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status as dictionary"""
        task = self.get_task(task_id)
        return task.to_dict() if task else None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status in (TaskStatus.PENDING, TaskStatus.QUEUED):
                task.status = TaskStatus.CANCELLED
                return True
            
            if task.status == TaskStatus.RUNNING:
                future = self._futures.get(task_id)
                if future and not future.done():
                    future.cancel()
                    task.status = TaskStatus.CANCELLED
                    return True
        
        return False
    
    def get_user_tasks(self, user_id: str, limit: int = 50) -> List[Task]:
        """Get tasks for a user"""
        with self._lock:
            tasks = [
                t for t in self._tasks.values()
                if t.user_id == user_id
            ]
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return tasks[:limit]
    
    def get_pending_count(self) -> int:
        """Get number of pending tasks"""
        return self._queue.qsize()
    
    def get_stats(self) -> dict:
        """Get queue statistics"""
        with self._lock:
            status_counts = {}
            for task in self._tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_tasks": len(self._tasks),
                "queue_size": self._queue.qsize(),
                "status_counts": status_counts,
                "running": self._running
            }
    
    def _worker_loop(self) -> None:
        """Main worker loop that processes tasks"""
        while self._running:
            try:
                # Get next task from queue
                try:
                    priority_item = self._queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                _, _, task_id = priority_item
                
                with self._lock:
                    task = self._tasks.get(task_id)
                    if not task or task.status == TaskStatus.CANCELLED:
                        continue
                
                # Execute task
                self._execute_task(task)
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
    
    def _execute_task(self, task: Task) -> None:
        """Execute a single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        def run_task():
            try:
                # Execute the task function
                result = task.func(*task.args, **task.kwargs)
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress = 100
                
                # Call completion callbacks
                if task.on_complete:
                    try:
                        task.on_complete(task)
                    except Exception as e:
                        logger.error(f"Complete callback error: {e}")
                
                if self._global_complete_callback:
                    try:
                        self._global_complete_callback(task)
                    except Exception as e:
                        logger.error(f"Global complete callback error: {e}")
                
                logger.info(f"Task {task.id} completed")
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                
                # Call error callbacks
                if task.on_error:
                    try:
                        task.on_error(task, e)
                    except Exception as cb_error:
                        logger.error(f"Error callback error: {cb_error}")
                
                logger.error(f"Task {task.id} failed: {e}")
        
        # Submit to thread pool
        future = self._executor.submit(run_task)
        
        with self._lock:
            self._futures[task.id] = future
    
    def set_progress_callback(self, callback: Callable) -> None:
        """Set global progress callback"""
        self._global_progress_callback = callback
    
    def set_complete_callback(self, callback: Callable) -> None:
        """Set global completion callback"""
        self._global_complete_callback = callback
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Remove completed/failed tasks older than max_age"""
        cutoff = datetime.now() - __import__('datetime').timedelta(hours=max_age_hours)
        removed = 0
        
        with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    if task.completed_at and task.completed_at < cutoff:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
                self._futures.pop(task_id, None)
                removed += 1
        
        logger.info(f"Cleaned up {removed} old tasks")
        return removed


# Global task queue instance
_default_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get or create the default task queue"""
    global _default_queue
    if _default_queue is None:
        _default_queue = TaskQueue()
        _default_queue.start()
    return _default_queue


def submit_task(func: Callable, *args, **kwargs) -> Task:
    """Convenience function to submit a task to the default queue"""
    return get_task_queue().submit(func, *args, **kwargs)

