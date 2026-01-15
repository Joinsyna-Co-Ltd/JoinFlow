"""
Task Scheduler
==============

Cron-based task scheduling system.
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import json
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class ScheduleType(str, Enum):
    ONCE = "once"          # 一次性执行
    INTERVAL = "interval"  # 固定间隔
    CRON = "cron"          # Cron表达式
    DAILY = "daily"        # 每日
    WEEKLY = "weekly"      # 每周
    MONTHLY = "monthly"    # 每月


@dataclass
class ScheduledTask:
    """定时任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    schedule_type: ScheduleType = ScheduleType.ONCE
    
    # 调度配置
    cron_expression: str = ""        # Cron表达式 (分 时 日 月 周)
    interval_seconds: int = 3600     # 间隔秒数
    run_at: Optional[str] = None     # 具体运行时间 (HH:MM)
    run_days: List[int] = field(default_factory=list)  # 周几 (0-6) 或 每月几号
    
    # 任务内容
    task_description: str = ""       # 要执行的任务描述
    workflow_id: Optional[str] = None  # 关联的工作流ID
    agents: List[str] = field(default_factory=list)
    
    # 状态
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "default"
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['schedule_type'] = self.schedule_type.value
        data['last_run'] = self.last_run.isoformat() if self.last_run else None
        data['next_run'] = self.next_run.isoformat() if self.next_run else None
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledTask":
        if 'schedule_type' in data:
            data['schedule_type'] = ScheduleType(data['schedule_type'])
        if isinstance(data.get('last_run'), str):
            data['last_run'] = datetime.fromisoformat(data['last_run'])
        if isinstance(data.get('next_run'), str):
            data['next_run'] = datetime.fromisoformat(data['next_run'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class CronParser:
    """简单的Cron表达式解析器"""
    
    @staticmethod
    def parse(expression: str) -> Dict[str, List[int]]:
        """
        解析Cron表达式: 分 时 日 月 周
        返回各字段的有效值列表
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        
        ranges = [
            (0, 59),   # 分钟
            (0, 23),   # 小时
            (1, 31),   # 日期
            (1, 12),   # 月份
            (0, 6),    # 星期
        ]
        
        fields = ['minute', 'hour', 'day', 'month', 'weekday']
        result = {}
        
        for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges)):
            result[fields[i]] = CronParser._parse_field(part, min_val, max_val)
        
        return result
    
    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """解析单个字段"""
        if field == '*':
            return list(range(min_val, max_val + 1))
        
        values = set()
        
        for part in field.split(','):
            if '/' in part:
                # 步进: */5 或 0-30/5
                range_part, step = part.split('/')
                step = int(step)
                if range_part == '*':
                    values.update(range(min_val, max_val + 1, step))
                else:
                    start, end = map(int, range_part.split('-'))
                    values.update(range(start, end + 1, step))
            elif '-' in part:
                # 范围: 1-5
                start, end = map(int, part.split('-'))
                values.update(range(start, end + 1))
            else:
                # 单个值
                values.add(int(part))
        
        return sorted(values)
    
    @staticmethod
    def get_next_run(expression: str, after: datetime = None) -> datetime:
        """计算下一次执行时间"""
        if after is None:
            after = datetime.now()
        
        parsed = CronParser.parse(expression)
        
        # 从当前时间往后找
        current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        for _ in range(366 * 24 * 60):  # 最多查找一年
            if (current.minute in parsed['minute'] and
                current.hour in parsed['hour'] and
                current.day in parsed['day'] and
                current.month in parsed['month'] and
                current.weekday() in parsed['weekday']):
                return current
            current += timedelta(minutes=1)
        
        raise ValueError(f"Could not find next run time for: {expression}")


class TaskScheduler:
    """任务调度器"""
    
    def __init__(
        self,
        storage_path: str = "./schedules",
        executor: Optional[Callable] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.executor = executor  # 任务执行函数
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self._load_tasks()
    
    def _load_tasks(self):
        """从存储加载任务"""
        tasks_file = self.storage_path / "scheduled_tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for task_data in data.get('tasks', []):
                    task = ScheduledTask.from_dict(task_data)
                    self.tasks[task.id] = task
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
            except Exception as e:
                logger.error(f"Failed to load scheduled tasks: {e}")
    
    def _save_tasks(self):
        """保存任务到存储"""
        tasks_file = self.storage_path / "scheduled_tasks.json"
        try:
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'tasks': [t.to_dict() for t in self.tasks.values()]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save scheduled tasks: {e}")
    
    def add_task(self, task: ScheduledTask) -> ScheduledTask:
        """添加定时任务"""
        with self._lock:
            # 计算下次执行时间
            task.next_run = self._calculate_next_run(task)
            self.tasks[task.id] = task
            self._save_tasks()
        logger.info(f"Added scheduled task: {task.name} (next run: {task.next_run})")
        return task
    
    def update_task(self, task_id: str, updates: dict) -> Optional[ScheduledTask]:
        """更新任务"""
        with self._lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            task.next_run = self._calculate_next_run(task)
            self._save_tasks()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                self._save_tasks()
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """计算下次执行时间"""
        now = datetime.now()
        
        if task.schedule_type == ScheduleType.ONCE:
            if task.run_at:
                h, m = map(int, task.run_at.split(':'))
                next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            return None
        
        elif task.schedule_type == ScheduleType.INTERVAL:
            if task.last_run:
                return task.last_run + timedelta(seconds=task.interval_seconds)
            return now + timedelta(seconds=task.interval_seconds)
        
        elif task.schedule_type == ScheduleType.CRON:
            try:
                return CronParser.get_next_run(task.cron_expression, now)
            except Exception as e:
                logger.error(f"Failed to parse cron: {e}")
                return None
        
        elif task.schedule_type == ScheduleType.DAILY:
            if task.run_at:
                h, m = map(int, task.run_at.split(':'))
                next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            return now + timedelta(days=1)
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            if task.run_at and task.run_days:
                h, m = map(int, task.run_at.split(':'))
                for i in range(7):
                    check_date = now + timedelta(days=i)
                    if check_date.weekday() in task.run_days:
                        next_run = check_date.replace(hour=h, minute=m, second=0, microsecond=0)
                        if next_run > now:
                            return next_run
            return now + timedelta(weeks=1)
        
        elif task.schedule_type == ScheduleType.MONTHLY:
            if task.run_at and task.run_days:
                h, m = map(int, task.run_at.split(':'))
                for i in range(31):
                    check_date = now + timedelta(days=i)
                    if check_date.day in task.run_days:
                        next_run = check_date.replace(hour=h, minute=m, second=0, microsecond=0)
                        if next_run > now:
                            return next_run
            return now + timedelta(days=30)
        
        return None
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Task scheduler started")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Task scheduler stopped")
    
    def _run_loop(self):
        """调度循环"""
        while self._running:
            try:
                now = datetime.now()
                
                with self._lock:
                    for task in self.tasks.values():
                        if not task.enabled:
                            continue
                        
                        if task.next_run and task.next_run <= now:
                            self._execute_task(task)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            # 每30秒检查一次
            for _ in range(30):
                if not self._running:
                    break
                threading.Event().wait(1)
    
    def _execute_task(self, task: ScheduledTask):
        """执行任务"""
        logger.info(f"Executing scheduled task: {task.name}")
        
        try:
            if self.executor:
                self.executor(task)
            
            task.last_run = datetime.now()
            task.run_count += 1
            task.next_run = self._calculate_next_run(task)
            
            # 一次性任务执行后禁用
            if task.schedule_type == ScheduleType.ONCE:
                task.enabled = False
            
            self._save_tasks()
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.error_count += 1
            task.last_error = str(e)
            self._save_tasks()

