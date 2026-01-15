"""
执行上下文模块
"""
import os
import platform
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    action: str
    message: str
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExecutionContext:
    """
    执行上下文
    
    跟踪当前执行状态、历史操作和环境信息
    """
    
    # 当前工作目录
    current_dir: str = field(default_factory=lambda: str(Path.cwd()))
    
    # 上一次操作结果
    last_result: Optional[ExecutionResult] = None
    
    # 操作历史
    history: List[ExecutionResult] = field(default_factory=list)
    
    # 会话变量（可以存储临时数据）
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # 剪贴板内容缓存
    clipboard_cache: Optional[str] = None
    
    # 最近访问的文件
    recent_files: List[str] = field(default_factory=list)
    
    # 最近打开的应用
    recent_apps: List[str] = field(default_factory=list)
    
    # 环境信息
    platform: str = field(default_factory=platform.system)
    user: str = field(default_factory=lambda: os.getenv("USER") or os.getenv("USERNAME", "unknown"))
    hostname: str = field(default_factory=platform.node)
    
    # 会话开始时间
    session_start: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_result(self, result: ExecutionResult) -> None:
        """添加执行结果到历史"""
        self.last_result = result
        self.history.append(result)
        
        # 限制历史长度
        if len(self.history) > 1000:
            self.history = self.history[-500:]
    
    def add_recent_file(self, path: str) -> None:
        """添加最近访问的文件"""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        
        # 限制列表长度
        if len(self.recent_files) > 50:
            self.recent_files = self.recent_files[:50]
    
    def add_recent_app(self, app: str) -> None:
        """添加最近打开的应用"""
        if app in self.recent_apps:
            self.recent_apps.remove(app)
        self.recent_apps.insert(0, app)
        
        # 限制列表长度
        if len(self.recent_apps) > 20:
            self.recent_apps = self.recent_apps[:20]
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取上下文摘要（用于LLM）"""
        return {
            "current_directory": self.current_dir,
            "platform": self.platform,
            "user": self.user,
            "recent_files": self.recent_files[:5],
            "recent_apps": self.recent_apps[:5],
            "last_action": self.last_result.action if self.last_result else None,
            "last_success": self.last_result.success if self.last_result else None,
            "session_duration": self._get_session_duration(),
            "total_actions": len(self.history),
        }
    
    def _get_session_duration(self) -> str:
        """获取会话持续时间"""
        start = datetime.fromisoformat(self.session_start)
        duration = datetime.now() - start
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def clear_history(self) -> None:
        """清除历史"""
        self.history.clear()
        self.last_result = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current_dir": self.current_dir,
            "platform": self.platform,
            "user": self.user,
            "hostname": self.hostname,
            "session_start": self.session_start,
            "variables": self.variables,
            "recent_files": self.recent_files,
            "recent_apps": self.recent_apps,
            "history_count": len(self.history),
        }

