"""
JoinFlow 智能操作系统助手
=========================

一个基于大模型的智能操作系统助手，能够：
- 理解自然语言指令
- 自动规划和执行复杂任务
- 控制操作系统的用户级别功能
- 查找资源、打开应用、编写文件等

使用示例:
    from joinflow_os_assistant import OSAssistant
    
    assistant = OSAssistant()
    assistant.execute("打开浏览器搜索Python教程")
    assistant.execute("查找桌面上所有的PDF文件")
    assistant.execute("创建一个新的工作文件夹并在里面创建项目说明文档")
"""

from .core.assistant import OSAssistant
from .core.config import AssistantConfig
from .core.context import ExecutionContext
from .intent.parser import IntentParser
from .intent.types import Intent, IntentType
from .planner.task_planner import TaskPlanner
from .planner.task import Task, TaskStatus

__version__ = "1.0.0"
__all__ = [
    "OSAssistant",
    "AssistantConfig",
    "ExecutionContext",
    "IntentParser",
    "Intent",
    "IntentType",
    "TaskPlanner",
    "Task",
    "TaskStatus",
]

