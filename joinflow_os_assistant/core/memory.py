"""
助手记忆模块

用于存储和检索用户偏好、常用操作模式和历史信息
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    value: Any
    category: str  # preference, pattern, history, fact
    importance: float = 1.0  # 0.0 - 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "importance": self.importance,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryEntry":
        return cls(**data)


class AssistantMemory:
    """
    助手记忆系统
    
    功能：
    - 记住用户偏好（如常用应用、默认路径等）
    - 学习使用模式（如常用文件类型、工作时间等）
    - 存储任务历史（用于智能建议）
    - 保存事实信息（用于上下文理解）
    """
    
    def __init__(self, storage_path: Optional[str] = None, max_entries: int = 1000):
        self.storage_path = storage_path or str(Path.home() / ".joinflow" / "memory.json")
        self.max_entries = max_entries
        
        self.memories: Dict[str, MemoryEntry] = {}
        self.category_index: Dict[str, List[str]] = defaultdict(list)
        
        # 加载已有记忆
        self._load()
    
    def remember(self, key: str, value: Any, category: str = "fact", importance: float = 1.0) -> None:
        """记住一个信息"""
        if key in self.memories:
            # 更新现有记忆
            entry = self.memories[key]
            entry.value = value
            entry.accessed_at = datetime.now().isoformat()
            entry.access_count += 1
            # 提升重要性
            entry.importance = min(1.0, entry.importance + 0.1)
        else:
            # 创建新记忆
            entry = MemoryEntry(
                key=key,
                value=value,
                category=category,
                importance=importance,
            )
            self.memories[key] = entry
            self.category_index[category].append(key)
        
        # 检查容量
        self._trim_if_needed()
        
        # 保存
        self._save()
    
    def recall(self, key: str) -> Optional[Any]:
        """回忆一个信息"""
        if key in self.memories:
            entry = self.memories[key]
            entry.accessed_at = datetime.now().isoformat()
            entry.access_count += 1
            return entry.value
        return None
    
    def search(self, query: str, category: Optional[str] = None) -> List[MemoryEntry]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()
        
        for key, entry in self.memories.items():
            if category and entry.category != category:
                continue
            
            # 在键和值中搜索
            if query_lower in key.lower():
                results.append(entry)
            elif isinstance(entry.value, str) and query_lower in entry.value.lower():
                results.append(entry)
        
        # 按重要性和访问次数排序
        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        return results
    
    def get_by_category(self, category: str) -> List[MemoryEntry]:
        """获取某个类别的所有记忆"""
        keys = self.category_index.get(category, [])
        return [self.memories[k] for k in keys if k in self.memories]
    
    def forget(self, key: str) -> bool:
        """忘记一个信息"""
        if key in self.memories:
            entry = self.memories[key]
            self.category_index[entry.category].remove(key)
            del self.memories[key]
            self._save()
            return True
        return False
    
    def clear_category(self, category: str) -> int:
        """清除某个类别的所有记忆"""
        keys = self.category_index.get(category, []).copy()
        count = 0
        for key in keys:
            if self.forget(key):
                count += 1
        return count
    
    # ==================
    # 偏好管理
    # ==================
    
    def set_preference(self, name: str, value: Any) -> None:
        """设置用户偏好"""
        self.remember(f"pref:{name}", value, category="preference", importance=0.9)
    
    def get_preference(self, name: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self.recall(f"pref:{name}") or default
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """获取所有偏好"""
        result = {}
        for entry in self.get_by_category("preference"):
            name = entry.key.replace("pref:", "")
            result[name] = entry.value
        return result
    
    # ==================
    # 模式学习
    # ==================
    
    def learn_pattern(self, pattern_type: str, pattern_data: Any) -> None:
        """学习使用模式"""
        key = f"pattern:{pattern_type}"
        existing = self.recall(key)
        
        if existing:
            # 合并模式数据
            if isinstance(existing, list):
                if pattern_data not in existing:
                    existing.append(pattern_data)
                    existing = existing[-20:]  # 保留最新20个
            elif isinstance(existing, dict) and isinstance(pattern_data, dict):
                existing.update(pattern_data)
            else:
                existing = [existing, pattern_data]
        else:
            existing = pattern_data
        
        self.remember(key, existing, category="pattern", importance=0.7)
    
    def get_patterns(self, pattern_type: str) -> Any:
        """获取学习到的模式"""
        return self.recall(f"pattern:{pattern_type}")
    
    # ==================
    # 常用项目
    # ==================
    
    def add_frequently_used(self, item_type: str, item: str) -> None:
        """添加常用项目"""
        key = f"frequent:{item_type}"
        items = self.recall(key) or []
        
        if item in items:
            items.remove(item)
        items.insert(0, item)
        items = items[:20]  # 保留最近20个
        
        self.remember(key, items, category="pattern", importance=0.8)
    
    def get_frequently_used(self, item_type: str, limit: int = 10) -> List[str]:
        """获取常用项目"""
        items = self.recall(f"frequent:{item_type}") or []
        return items[:limit]
    
    # ==================
    # 内部方法
    # ==================
    
    def _trim_if_needed(self) -> None:
        """如果超出容量，删除最不重要的记忆"""
        if len(self.memories) <= self.max_entries:
            return
        
        # 按重要性和访问时间排序
        sorted_entries = sorted(
            self.memories.values(),
            key=lambda x: (x.importance, x.accessed_at)
        )
        
        # 删除最不重要的
        to_remove = len(self.memories) - self.max_entries + 100  # 多删100个，避免频繁删除
        for entry in sorted_entries[:to_remove]:
            self.forget(entry.key)
    
    def _save(self) -> None:
        """保存记忆到文件"""
        try:
            path = Path(self.storage_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "memories": {k: v.to_dict() for k, v in self.memories.items()},
                "saved_at": datetime.now().isoformat(),
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def _load(self) -> None:
        """从文件加载记忆"""
        try:
            path = Path(self.storage_path)
            if not path.exists():
                return
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, entry_data in data.get("memories", {}).items():
                entry = MemoryEntry.from_dict(entry_data)
                self.memories[key] = entry
                self.category_index[entry.category].append(key)
                
        except Exception as e:
            print(f"加载记忆失败: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        return {
            "total_entries": len(self.memories),
            "categories": {cat: len(keys) for cat, keys in self.category_index.items()},
            "preferences_count": len(self.get_by_category("preference")),
            "patterns_count": len(self.get_by_category("pattern")),
        }

