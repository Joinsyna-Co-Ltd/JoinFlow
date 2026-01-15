"""
意图解析器
"""
import re
import logging
from typing import Dict, List, Optional, Tuple

from .types import Intent, IntentType

logger = logging.getLogger(__name__)


class IntentParser:
    """
    意图解析器
    
    通过规则和模式匹配解析用户命令
    """
    
    # 意图模式 (关键词列表, 意图类型, 是否需要确认)
    PATTERNS: List[Tuple[List[str], IntentType, bool]] = [
        # 文件操作
        (["创建文件", "新建文件", "create file"], IntentType.FILE_CREATE, False),
        (["读取", "查看文件", "打开文件", "read file"], IntentType.FILE_READ, False),
        (["写入", "编辑", "修改", "write"], IntentType.FILE_WRITE, False),
        (["删除文件", "移除文件", "delete file"], IntentType.FILE_DELETE, True),
        (["复制", "copy"], IntentType.FILE_COPY, False),
        (["移动", "重命名", "move", "rename"], IntentType.FILE_MOVE, False),
        
        # 目录操作
        (["创建目录", "创建文件夹", "新建文件夹", "mkdir"], IntentType.DIR_CREATE, False),
        (["列出", "显示目录", "查看文件夹", "ls", "dir"], IntentType.DIR_LIST, False),
        
        # 搜索
        (["查找", "搜索文件", "找文件", "find", "locate"], IntentType.SEARCH_FILE, False),
        (["搜索内容", "在文件中找"], IntentType.SEARCH_CONTENT, False),
        
        # 应用
        (["打开", "启动", "运行", "open", "start", "launch"], IntentType.APP_OPEN, False),
        (["关闭", "退出", "结束", "close", "quit", "kill"], IntentType.APP_CLOSE, False),
        
        # 浏览器搜索
        (["百度", "谷歌", "google", "搜索", "search"], IntentType.BROWSER_SEARCH, False),
        
        # URL导航
        (["网址", "网站", "http", "www", ".com", ".cn", ".org"], IntentType.BROWSER_NAVIGATE, False),
        
        # 系统
        (["系统信息", "电脑信息", "硬件", "system info"], IntentType.SYSTEM_INFO, False),
        (["截图", "截屏", "screenshot"], IntentType.SYSTEM_SCREENSHOT, False),
        (["剪贴板", "粘贴", "clipboard"], IntentType.SYSTEM_CLIPBOARD, False),
        (["执行", "运行命令", "命令", "terminal", "shell"], IntentType.SYSTEM_COMMAND, True),
        
        # 帮助
        (["帮助", "help", "怎么", "如何"], IntentType.HELP, False),
    ]
    
    # 危险操作关键词
    DANGEROUS_KEYWORDS = [
        "删除", "移除", "格式化", "清空", "destroy", "remove", "format", "wipe"
    ]
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def parse(self, command: str) -> Intent:
        """
        解析命令意图
        
        Args:
            command: 用户命令
            
        Returns:
            Intent: 解析的意图
        """
        command_lower = command.lower()
        
        # 匹配模式
        for keywords, intent_type, requires_confirm in self.PATTERNS:
            for keyword in keywords:
                if keyword in command_lower:
                    # 检查是否需要特殊处理
                    if intent_type == IntentType.APP_OPEN:
                        # 区分应用打开和URL导航
                        if self._is_url(command):
                            intent_type = IntentType.BROWSER_NAVIGATE
                        elif self._is_file_path(command):
                            intent_type = IntentType.FILE_OPEN
                    
                    return Intent(
                        type=intent_type,
                        action=self._get_action_name(intent_type),
                        command=command,
                        params=self._extract_params(command, intent_type),
                        requires_confirmation=requires_confirm or self._is_dangerous(command),
                    )
        
        # 尝试用LLM解析
        if self.llm_client:
            intent = self._parse_with_llm(command)
            if intent:
                return intent
        
        # 默认作为应用打开
        return Intent(
            type=IntentType.APP_OPEN,
            action="app.open",
            command=command,
            confidence=0.5,
        )
    
    def _get_action_name(self, intent_type: IntentType) -> str:
        """获取动作名称"""
        mapping = {
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
            IntentType.SEARCH_FILE: "search.file",
            IntentType.SEARCH_CONTENT: "search.content",
            IntentType.SEARCH_WEB: "browser.search",
            IntentType.APP_OPEN: "app.open",
            IntentType.APP_CLOSE: "app.close",
            IntentType.APP_LIST: "app.list",
            IntentType.BROWSER_NAVIGATE: "browser.navigate",
            IntentType.BROWSER_SEARCH: "browser.search",
            IntentType.SYSTEM_INFO: "system.info",
            IntentType.SYSTEM_SCREENSHOT: "system.screenshot",
            IntentType.SYSTEM_CLIPBOARD: "system.clipboard",
            IntentType.SYSTEM_COMMAND: "system.command",
            IntentType.COMPOSE_TEXT: "compose.text",
            IntentType.COMPOSE_CODE: "compose.code",
            IntentType.HELP: "help",
        }
        return mapping.get(intent_type, "unknown")
    
    def _extract_params(self, command: str, intent_type: IntentType) -> Dict:
        """提取参数"""
        params = {}
        
        # 提取路径
        path = self._extract_path(command)
        if path:
            params["path"] = path
        
        # 提取搜索关键词
        if intent_type in [IntentType.SEARCH_FILE, IntentType.BROWSER_SEARCH]:
            query = self._extract_query(command)
            if query:
                params["query"] = query
        
        # 提取应用名
        if intent_type in [IntentType.APP_OPEN, IntentType.APP_CLOSE]:
            app = self._extract_app_name(command)
            if app:
                params["name"] = app
        
        # 提取URL
        if intent_type == IntentType.BROWSER_NAVIGATE:
            url = self._extract_url(command)
            if url:
                params["url"] = url
        
        return params
    
    def _extract_path(self, text: str) -> Optional[str]:
        """提取文件路径"""
        # 引号内
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
    
    def _extract_query(self, text: str) -> Optional[str]:
        """提取搜索关键词"""
        for prefix in ["搜索", "查找", "找", "百度", "谷歌", "search", "find"]:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()
                break
        return text.strip('"\'') if text else None
    
    def _extract_app_name(self, text: str) -> Optional[str]:
        """提取应用名"""
        for verb in ["打开", "启动", "运行", "关闭", "退出", "open", "start", "close", "quit"]:
            text = text.replace(verb, "").strip()
        return text.split()[0] if text.strip() else None
    
    def _extract_url(self, text: str) -> Optional[str]:
        """提取URL"""
        pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(?:com|org|net|cn|io)[^\s]*)'
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    def _is_url(self, text: str) -> bool:
        """判断是否包含URL"""
        return bool(self._extract_url(text))
    
    def _is_file_path(self, text: str) -> bool:
        """判断是否包含文件路径"""
        path = self._extract_path(text)
        if not path:
            return False
        return '/' in path or '\\' in path or path.startswith('~')
    
    def _is_dangerous(self, command: str) -> bool:
        """判断是否为危险操作"""
        command_lower = command.lower()
        return any(kw in command_lower for kw in self.DANGEROUS_KEYWORDS)
    
    def _parse_with_llm(self, command: str) -> Optional[Intent]:
        """使用LLM解析意图"""
        if not self.llm_client:
            return None
        
        try:
            prompt = f"""分析以下用户命令，返回JSON格式的意图：

命令: "{command}"

返回格式:
{{"type": "意图类型", "action": "动作", "params": {{}}, "requires_confirmation": false}}

意图类型: FILE_CREATE, FILE_READ, FILE_WRITE, FILE_DELETE, 
         DIR_CREATE, DIR_LIST, SEARCH_FILE, APP_OPEN, APP_CLOSE,
         BROWSER_SEARCH, BROWSER_NAVIGATE, SYSTEM_INFO, SYSTEM_SCREENSHOT,
         SYSTEM_COMMAND, HELP, UNKNOWN

只返回JSON。"""
            
            response = self.llm_client.chat(prompt)
            import json
            data = json.loads(response.strip())
            
            return Intent(
                type=IntentType[data.get("type", "UNKNOWN")],
                action=data.get("action", "unknown"),
                command=command,
                params=data.get("params", {}),
                requires_confirmation=data.get("requires_confirmation", False),
                confidence=0.8,
            )
        except Exception as e:
            logger.warning(f"LLM解析失败: {e}")
            return None

