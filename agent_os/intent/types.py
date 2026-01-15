"""
意图类型定义
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


class IntentType(Enum):
    """意图类型"""
    # 文件操作
    FILE_CREATE = auto()
    FILE_READ = auto()
    FILE_WRITE = auto()
    FILE_DELETE = auto()
    FILE_COPY = auto()
    FILE_MOVE = auto()
    FILE_OPEN = auto()
    
    # 目录操作
    DIR_CREATE = auto()
    DIR_LIST = auto()
    DIR_DELETE = auto()
    
    # 搜索
    SEARCH_FILE = auto()
    SEARCH_CONTENT = auto()
    SEARCH_WEB = auto()
    
    # 应用
    APP_OPEN = auto()
    APP_CLOSE = auto()
    APP_LIST = auto()
    
    # 浏览器
    BROWSER_NAVIGATE = auto()
    BROWSER_SEARCH = auto()
    
    # 系统
    SYSTEM_INFO = auto()
    SYSTEM_SCREENSHOT = auto()
    SYSTEM_CLIPBOARD = auto()
    SYSTEM_COMMAND = auto()
    SYSTEM_NOTIFY = auto()
    
    # 内容生成
    COMPOSE_TEXT = auto()
    COMPOSE_CODE = auto()
    
    # 帮助
    HELP = auto()
    
    # 未知
    UNKNOWN = auto()


@dataclass
class Intent:
    """
    解析后的意图
    """
    type: IntentType
    action: str
    command: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    requires_confirmation: bool = False
    alternatives: List["Intent"] = field(default_factory=list)
    
    @property
    def category(self) -> str:
        """获取类别"""
        name = self.type.name
        return name.split('_')[0].lower()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "type": self.type.name,
            "action": self.action,
            "command": self.command,
            "params": self.params,
            "confidence": self.confidence,
            "requires_confirmation": self.requires_confirmation,
        }

