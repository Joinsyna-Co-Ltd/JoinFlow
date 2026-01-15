"""执行器模块"""
from .base import BaseExecutor, ExecutorResult
from .file_executor import FileExecutor
from .app_executor import AppExecutor
from .search_executor import SearchExecutor
from .system_executor import SystemExecutor
from .browser_executor import BrowserExecutor
from .compose_executor import ComposeExecutor
from .executor_registry import ExecutorRegistry

__all__ = [
    "BaseExecutor", "ExecutorResult",
    "FileExecutor", "AppExecutor", "SearchExecutor",
    "SystemExecutor", "BrowserExecutor", "ComposeExecutor",
    "ExecutorRegistry",
]

