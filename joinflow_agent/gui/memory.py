"""
Experience Memory - 经验记忆模块
================================

实现类似 Agent-S 的经验增强学习：
1. 记录成功的操作序列
2. 从过去经验中学习
3. 为相似任务提供参考
"""

import json
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ActionRecord:
    """动作记录"""
    action_type: str
    target: Optional[str] = None
    text: Optional[str] = None
    coordinates: Optional[tuple] = None
    success: bool = True
    
    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "text": self.text,
            "coordinates": self.coordinates,
            "success": self.success,
        }


@dataclass
class Experience:
    """
    一次任务执行的经验
    """
    id: str
    task: str
    task_hash: str                              # 用于快速匹配
    success: bool
    actions: List[ActionRecord]
    steps_count: int
    duration_ms: float
    error: Optional[str] = None
    app_context: Optional[str] = None           # 应用上下文（如 Chrome, Notepad）
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    used_count: int = 0                         # 被引用次数
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "task_hash": self.task_hash,
            "success": self.success,
            "actions": [a.to_dict() for a in self.actions],
            "steps_count": self.steps_count,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "app_context": self.app_context,
            "tags": self.tags,
            "created_at": self.created_at,
            "used_count": self.used_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Experience":
        actions = [ActionRecord(**a) for a in data.get("actions", [])]
        return cls(
            id=data["id"],
            task=data["task"],
            task_hash=data["task_hash"],
            success=data["success"],
            actions=actions,
            steps_count=data["steps_count"],
            duration_ms=data["duration_ms"],
            error=data.get("error"),
            app_context=data.get("app_context"),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            used_count=data.get("used_count", 0),
        )


class ExperienceMemory:
    """
    经验记忆库
    
    存储和检索任务执行经验，实现：
    1. 经验持久化（JSON 文件）
    2. 相似任务匹配
    3. 成功经验优先
    """
    
    def __init__(self, storage_path: str = "./workspace/experience_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._experiences: Dict[str, Experience] = {}
        self._task_index: Dict[str, List[str]] = {}  # task_hash -> experience_ids
        
        self._load()
    
    def _load(self) -> None:
        """从文件加载经验"""
        memory_file = self.storage_path / "experiences.json"
        
        if memory_file.exists():
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for exp_data in data.get("experiences", []):
                    exp = Experience.from_dict(exp_data)
                    self._experiences[exp.id] = exp
                    
                    if exp.task_hash not in self._task_index:
                        self._task_index[exp.task_hash] = []
                    self._task_index[exp.task_hash].append(exp.id)
                
                logger.info(f"Loaded {len(self._experiences)} experiences from memory")
                
            except Exception as e:
                logger.warning(f"Failed to load experience memory: {e}")
    
    def _save(self) -> None:
        """保存经验到文件"""
        memory_file = self.storage_path / "experiences.json"
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "experiences": [exp.to_dict() for exp in self._experiences.values()]
            }
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save experience memory: {e}")
    
    @staticmethod
    def _hash_task(task: str) -> str:
        """生成任务哈希（用于快速匹配）"""
        # 简化任务文本
        normalized = task.lower().strip()
        # 移除数字和特殊字符
        import re
        normalized = re.sub(r'[0-9]+', 'N', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def add_experience(
        self,
        task: str,
        success: bool,
        actions: List[Dict],
        duration_ms: float,
        error: Optional[str] = None,
        app_context: Optional[str] = None,
        tags: List[str] = None,
    ) -> Experience:
        """
        添加新经验
        
        Args:
            task: 任务描述
            success: 是否成功
            actions: 动作列表
            duration_ms: 执行时间
            error: 错误信息（如失败）
            app_context: 应用上下文
            tags: 标签
            
        Returns:
            创建的 Experience
        """
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._experiences)}"
        task_hash = self._hash_task(task)
        
        action_records = []
        for a in actions:
            action_records.append(ActionRecord(
                action_type=a.get("action_type", a.get("type", "unknown")),
                target=a.get("target"),
                text=a.get("text"),
                coordinates=tuple(a["coordinates"]) if a.get("coordinates") else None,
                success=a.get("success", True),
            ))
        
        experience = Experience(
            id=exp_id,
            task=task,
            task_hash=task_hash,
            success=success,
            actions=action_records,
            steps_count=len(action_records),
            duration_ms=duration_ms,
            error=error,
            app_context=app_context,
            tags=tags or [],
        )
        
        self._experiences[exp_id] = experience
        
        if task_hash not in self._task_index:
            self._task_index[task_hash] = []
        self._task_index[task_hash].append(exp_id)
        
        self._save()
        
        logger.info(f"Added experience: {exp_id} (success={success})")
        
        return experience
    
    def find_similar(
        self,
        task: str,
        limit: int = 5,
        success_only: bool = True
    ) -> List[Experience]:
        """
        查找相似任务的经验
        
        Args:
            task: 任务描述
            limit: 最大返回数量
            success_only: 只返回成功的经验
            
        Returns:
            相似经验列表
        """
        task_hash = self._hash_task(task)
        
        # 精确匹配
        exact_matches = []
        if task_hash in self._task_index:
            for exp_id in self._task_index[task_hash]:
                exp = self._experiences.get(exp_id)
                if exp and (not success_only or exp.success):
                    exact_matches.append(exp)
        
        # 按使用次数和成功率排序
        exact_matches.sort(key=lambda x: (-x.used_count, -x.success))
        
        if exact_matches:
            return exact_matches[:limit]
        
        # 模糊匹配（关键词）
        task_keywords = set(task.lower().split())
        fuzzy_matches = []
        
        for exp in self._experiences.values():
            if success_only and not exp.success:
                continue
            
            exp_keywords = set(exp.task.lower().split())
            overlap = len(task_keywords & exp_keywords)
            
            if overlap > 0:
                fuzzy_matches.append((overlap, exp))
        
        fuzzy_matches.sort(key=lambda x: -x[0])
        
        return [exp for _, exp in fuzzy_matches[:limit]]
    
    def get_action_hints(self, task: str) -> List[str]:
        """
        获取任务的动作提示
        
        基于历史经验，返回建议的动作序列
        """
        experiences = self.find_similar(task, limit=3, success_only=True)
        
        if not experiences:
            return []
        
        # 统计常见的动作模式
        action_patterns = []
        
        for exp in experiences:
            exp.used_count += 1  # 增加引用计数
            
            pattern = " -> ".join([a.action_type for a in exp.actions[:5]])
            action_patterns.append(pattern)
        
        self._save()  # 保存更新的引用计数
        
        return action_patterns
    
    def get_success_rate(self, task: str = None) -> float:
        """获取成功率"""
        if task:
            task_hash = self._hash_task(task)
            relevant = [self._experiences[eid] for eid in self._task_index.get(task_hash, [])]
        else:
            relevant = list(self._experiences.values())
        
        if not relevant:
            return 0.0
        
        successes = sum(1 for exp in relevant if exp.success)
        return successes / len(relevant) * 100
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = len(self._experiences)
        successes = sum(1 for exp in self._experiences.values() if exp.success)
        
        return {
            "total_experiences": total,
            "successful": successes,
            "failed": total - successes,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "unique_tasks": len(self._task_index),
        }
    
    def clear(self) -> None:
        """清空所有经验"""
        self._experiences.clear()
        self._task_index.clear()
        self._save()
        logger.info("Experience memory cleared")
    
    def export(self, path: str) -> None:
        """导出经验到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "statistics": self.get_statistics(),
                "experiences": [exp.to_dict() for exp in self._experiences.values()]
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Exported {len(self._experiences)} experiences to {path}")


# 全局经验记忆实例
_global_memory: Optional[ExperienceMemory] = None


def get_experience_memory(storage_path: str = None) -> ExperienceMemory:
    """获取全局经验记忆实例"""
    global _global_memory
    
    if _global_memory is None:
        _global_memory = ExperienceMemory(storage_path or "./workspace/experience_memory")
    
    return _global_memory

