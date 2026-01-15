"""
执行器基类
"""
import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import AgentConfig
from ..core.runtime import Runtime, ActionResult

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """执行器基类"""
    
    name: str = "base"
    
    def __init__(self, config: AgentConfig, runtime: Runtime):
        self.config = config
        self.runtime = runtime
    
    @abstractmethod
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行操作"""
        pass
    
    def _extract_path(self, text: str) -> Optional[str]:
        """从文本中提取路径"""
        # 引号内的路径
        match = re.search(r'["\']([^"\']+)["\']', text)
        if match:
            return match.group(1)
        
        # Windows路径
        match = re.search(r'([A-Za-z]:\\[^\s]+)', text)
        if match:
            return match.group(1)
        
        # Unix路径
        match = re.search(r'((?:~|/)[^\s]+)', text)
        if match:
            return match.group(1)
        
        # 简单文件名
        match = re.search(r'([.\w-]+\.[a-zA-Z0-9]{1,5})', text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_app_name(self, text: str) -> Optional[str]:
        """从文本中提取应用名称"""
        # 移除动词
        for verb in ["打开", "启动", "运行", "关闭", "退出", "open", "start", "close", "quit"]:
            text = text.replace(verb, "").strip()
        
        # 常见应用别名
        aliases = {
            "记事本": "notepad",
            "计算器": "calc",
            "浏览器": "chrome",
            "谷歌浏览器": "chrome",
            "火狐": "firefox",
            "vscode": "code",
            "vs code": "code",
            "微信": "wechat",
            "qq": "qq",
        }
        
        text_lower = text.lower()
        for alias, app in aliases.items():
            if alias in text_lower:
                return app
        
        # 返回清理后的文本作为应用名
        return text.strip().split()[0] if text.strip() else None
    
    def _extract_query(self, text: str) -> Optional[str]:
        """从文本中提取搜索关键词"""
        # 移除搜索动词
        for prefix in ["搜索", "查找", "找", "百度", "谷歌", "search", "find"]:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()
        
        # 移除引号
        text = text.strip('"\'')
        
        return text if text else None
    
    def _log(self, action: str, message: str) -> None:
        """记录日志"""
        self.runtime.log_action(f"{self.name}.{action}", message)

