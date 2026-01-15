"""
意图类型定义
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class IntentType(Enum):
    """意图类型"""
    
    # 文件操作
    FILE_CREATE = auto()        # 创建文件
    FILE_READ = auto()          # 读取文件
    FILE_WRITE = auto()         # 写入/编辑文件
    FILE_DELETE = auto()        # 删除文件
    FILE_COPY = auto()          # 复制文件
    FILE_MOVE = auto()          # 移动/重命名文件
    FILE_OPEN = auto()          # 打开文件（用默认程序）
    
    # 目录操作
    DIR_CREATE = auto()         # 创建目录
    DIR_LIST = auto()           # 列出目录内容
    DIR_DELETE = auto()         # 删除目录
    DIR_NAVIGATE = auto()       # 导航到目录
    
    # 搜索操作
    SEARCH_FILE = auto()        # 搜索文件
    SEARCH_CONTENT = auto()     # 搜索文件内容
    SEARCH_APP = auto()         # 搜索应用
    
    # 应用操作
    APP_OPEN = auto()           # 打开应用
    APP_CLOSE = auto()          # 关闭应用
    APP_LIST = auto()           # 列出运行的应用
    
    # 浏览器操作
    BROWSER_OPEN = auto()       # 打开浏览器
    BROWSER_SEARCH = auto()     # 浏览器搜索
    BROWSER_NAVIGATE = auto()   # 浏览器访问URL
    
    # 系统操作
    SYSTEM_INFO = auto()        # 获取系统信息
    SYSTEM_CLIPBOARD_GET = auto()   # 获取剪贴板
    SYSTEM_CLIPBOARD_SET = auto()   # 设置剪贴板
    SYSTEM_SCREENSHOT = auto()  # 截屏
    SYSTEM_NOTIFY = auto()      # 发送通知
    
    # 执行操作
    EXECUTE_COMMAND = auto()    # 执行命令
    EXECUTE_SCRIPT = auto()     # 执行脚本
    
    # 编写/创作
    COMPOSE_TEXT = auto()       # 编写文本
    COMPOSE_CODE = auto()       # 编写代码
    COMPOSE_EMAIL = auto()      # 编写邮件
    
    # 复合操作
    COMPOUND = auto()           # 复合意图（包含多个子意图）
    
    # 其他
    HELP = auto()               # 帮助/说明
    CANCEL = auto()             # 取消操作
    CONFIRM = auto()            # 确认操作
    UNDO = auto()               # 撤销
    UNKNOWN = auto()            # 未知意图


class EntityType(Enum):
    """实体类型"""
    FILE_PATH = auto()          # 文件路径
    DIR_PATH = auto()           # 目录路径
    FILE_NAME = auto()          # 文件名
    FILE_TYPE = auto()          # 文件类型/扩展名
    APP_NAME = auto()           # 应用名称
    URL = auto()                # URL
    SEARCH_QUERY = auto()       # 搜索关键词
    TEXT_CONTENT = auto()       # 文本内容
    COMMAND = auto()            # 命令
    NUMBER = auto()             # 数字
    DATE = auto()               # 日期
    TIME = auto()               # 时间
    LOCATION = auto()           # 位置
    UNKNOWN = auto()            # 未知


@dataclass
class Entity:
    """提取的实体"""
    type: EntityType
    value: Any
    text: str  # 原始文本
    start: int = 0  # 在原文中的起始位置
    end: int = 0    # 在原文中的结束位置
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.name,
            "value": self.value,
            "text": self.text,
            "confidence": self.confidence,
        }


@dataclass
class Intent:
    """解析后的意图"""
    
    # 主意图类型
    type: IntentType
    
    # 置信度 (0.0 - 1.0)
    confidence: float = 1.0
    
    # 提取的实体
    entities: List[Entity] = field(default_factory=list)
    
    # 原始输入
    raw_input: str = ""
    
    # 规范化的描述
    description: str = ""
    
    # 子意图（用于复合意图）
    sub_intents: List["Intent"] = field(default_factory=list)
    
    # 额外参数
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 是否需要确认
    requires_confirmation: bool = False
    
    # 优先级 (1-10, 10最高)
    priority: int = 5
    
    def get_entity(self, entity_type: EntityType) -> Optional[Entity]:
        """获取指定类型的第一个实体"""
        for entity in self.entities:
            if entity.type == entity_type:
                return entity
        return None
    
    def get_entities(self, entity_type: EntityType) -> List[Entity]:
        """获取指定类型的所有实体"""
        return [e for e in self.entities if e.type == entity_type]
    
    def get_entity_value(self, entity_type: EntityType, default: Any = None) -> Any:
        """获取实体值"""
        entity = self.get_entity(entity_type)
        return entity.value if entity else default
    
    def add_entity(self, entity: Entity) -> None:
        """添加实体"""
        self.entities.append(entity)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.name,
            "confidence": self.confidence,
            "entities": [e.to_dict() for e in self.entities],
            "raw_input": self.raw_input,
            "description": self.description,
            "parameters": self.parameters,
            "requires_confirmation": self.requires_confirmation,
            "sub_intents": [i.to_dict() for i in self.sub_intents],
        }
    
    def __str__(self) -> str:
        entities_str = ", ".join([f"{e.type.name}={e.value}" for e in self.entities])
        return f"Intent({self.type.name}, entities=[{entities_str}], conf={self.confidence:.2f})"


# 意图到操作的映射
INTENT_OPERATIONS = {
    IntentType.FILE_CREATE: "file.create",
    IntentType.FILE_READ: "file.read",
    IntentType.FILE_WRITE: "file.write",
    IntentType.FILE_DELETE: "file.delete",
    IntentType.FILE_COPY: "file.copy",
    IntentType.FILE_MOVE: "file.move",
    IntentType.FILE_OPEN: "file.open",
    IntentType.DIR_CREATE: "dir.create",
    IntentType.DIR_LIST: "dir.list",
    IntentType.DIR_DELETE: "dir.delete",
    IntentType.DIR_NAVIGATE: "dir.navigate",
    IntentType.SEARCH_FILE: "search.file",
    IntentType.SEARCH_CONTENT: "search.content",
    IntentType.SEARCH_APP: "search.app",
    IntentType.APP_OPEN: "app.open",
    IntentType.APP_CLOSE: "app.close",
    IntentType.APP_LIST: "app.list",
    IntentType.BROWSER_OPEN: "browser.open",
    IntentType.BROWSER_SEARCH: "browser.search",
    IntentType.BROWSER_NAVIGATE: "browser.navigate",
    IntentType.SYSTEM_INFO: "system.info",
    IntentType.SYSTEM_CLIPBOARD_GET: "system.clipboard.get",
    IntentType.SYSTEM_CLIPBOARD_SET: "system.clipboard.set",
    IntentType.SYSTEM_SCREENSHOT: "system.screenshot",
    IntentType.SYSTEM_NOTIFY: "system.notify",
    IntentType.EXECUTE_COMMAND: "execute.command",
    IntentType.EXECUTE_SCRIPT: "execute.script",
    IntentType.COMPOSE_TEXT: "compose.text",
    IntentType.COMPOSE_CODE: "compose.code",
    IntentType.COMPOSE_EMAIL: "compose.email",
}


# 危险操作（需要确认）
DANGEROUS_INTENTS = {
    IntentType.FILE_DELETE,
    IntentType.DIR_DELETE,
    IntentType.EXECUTE_COMMAND,
    IntentType.EXECUTE_SCRIPT,
}

