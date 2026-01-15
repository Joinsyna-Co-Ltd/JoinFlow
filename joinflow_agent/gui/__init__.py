"""
GUI Agent 模块
==============

类似 Agent-S 的 GUI 自动化框架，让 AI 像人一样操作电脑。

核心组件:
- GUIAgent: 主控制器
- ScreenParser: 屏幕截图和解析
- GroundingAgent: UI 元素定位
- ActionExecutor: 动作执行器
- HierarchicalPlanner: 分层任务规划
- ExperienceMemory: 经验记忆学习
- LocalCodeExecutor: 本地代码执行
"""

from .gui_agent import GUIAgent, GUIAgentConfig
from .screen_parser import ScreenParser, ScreenState
from .grounding import GroundingAgent, GroundingConfig, UIElement
from .action_space import Action, ActionType, ActionExecutor
from .prompts import SYSTEM_PROMPTS
from .planner import HierarchicalPlanner, TaskPlan, Subtask
from .memory import ExperienceMemory, Experience, get_experience_memory
from .code_executor import LocalCodeExecutor, CodeExecutionResult
from .config import OPENROUTER_API_KEY, DEFAULT_MODEL, get_api_key, get_model_config

__all__ = [
    # 核心
    "GUIAgent",
    "GUIAgentConfig",
    # 屏幕
    "ScreenParser",
    "ScreenState", 
    # 定位
    "GroundingAgent",
    "GroundingConfig",
    "UIElement",
    # 动作
    "Action",
    "ActionType",
    "ActionExecutor",
    # 规划
    "HierarchicalPlanner",
    "TaskPlan",
    "Subtask",
    # 记忆
    "ExperienceMemory",
    "Experience",
    "get_experience_memory",
    # 代码执行
    "LocalCodeExecutor",
    "CodeExecutionResult",
    # 配置
    "OPENROUTER_API_KEY",
    "DEFAULT_MODEL",
    "get_api_key",
    "get_model_config",
    # 提示词
    "SYSTEM_PROMPTS",
]

