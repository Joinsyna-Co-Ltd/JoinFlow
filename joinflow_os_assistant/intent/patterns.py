"""
模式匹配器 - 基于规则的意图识别
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from .types import Intent, IntentType, Entity, EntityType, DANGEROUS_INTENTS


class PatternMatcher:
    """
    基于规则的模式匹配器
    
    用于快速识别常见意图，作为LLM识别的补充
    """
    
    # 意图关键词映射
    INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
        # 文件操作
        IntentType.FILE_CREATE: [
            "创建文件", "新建文件", "生成文件", "create file", "new file", "touch"
        ],
        IntentType.FILE_READ: [
            "读取", "查看", "打开文件", "显示", "看看", "read", "view", "cat", "show"
        ],
        IntentType.FILE_WRITE: [
            "写入", "编辑", "修改", "保存", "更新", "write", "edit", "save", "update"
        ],
        IntentType.FILE_DELETE: [
            "删除文件", "移除文件", "delete file", "remove file", "rm"
        ],
        IntentType.FILE_COPY: [
            "复制", "拷贝", "copy", "cp"
        ],
        IntentType.FILE_MOVE: [
            "移动", "重命名", "move", "rename", "mv"
        ],
        IntentType.FILE_OPEN: [
            "打开", "用.*打开", "open with", "使用.*打开"
        ],
        
        # 目录操作
        IntentType.DIR_CREATE: [
            "创建目录", "创建文件夹", "新建文件夹", "mkdir", "create folder", "create directory"
        ],
        IntentType.DIR_LIST: [
            "列出", "显示目录", "查看文件夹", "ls", "dir", "list"
        ],
        IntentType.DIR_DELETE: [
            "删除目录", "删除文件夹", "rmdir", "delete folder"
        ],
        IntentType.DIR_NAVIGATE: [
            "进入", "切换到", "去", "cd", "go to", "navigate"
        ],
        
        # 搜索操作
        IntentType.SEARCH_FILE: [
            "查找", "搜索", "找", "寻找", "搜", "find", "search", "locate", "where is"
        ],
        IntentType.SEARCH_CONTENT: [
            "搜索内容", "查找内容", "grep", "在.*中搜索", "search in", "find in"
        ],
        
        # 应用操作
        IntentType.APP_OPEN: [
            "打开", "启动", "运行", "open", "start", "launch", "run"
        ],
        IntentType.APP_CLOSE: [
            "关闭", "退出", "结束", "close", "quit", "exit", "kill"
        ],
        IntentType.APP_LIST: [
            "列出程序", "正在运行", "进程", "processes", "running apps"
        ],
        
        # 浏览器操作
        IntentType.BROWSER_OPEN: [
            "打开浏览器", "浏览器", "open browser"
        ],
        IntentType.BROWSER_SEARCH: [
            "搜索", "百度", "谷歌", "google", "bing", "search for", "查一下", "搜一下"
        ],
        IntentType.BROWSER_NAVIGATE: [
            "访问", "打开网址", "打开网站", "visit", "go to url", "navigate to"
        ],
        
        # 系统操作
        IntentType.SYSTEM_INFO: [
            "系统信息", "电脑信息", "硬件信息", "system info", "my computer"
        ],
        IntentType.SYSTEM_CLIPBOARD_GET: [
            "粘贴", "剪贴板", "clipboard", "paste"
        ],
        IntentType.SYSTEM_CLIPBOARD_SET: [
            "复制到剪贴板", "copy to clipboard"
        ],
        IntentType.SYSTEM_SCREENSHOT: [
            "截图", "截屏", "屏幕截图", "screenshot", "capture screen"
        ],
        IntentType.SYSTEM_NOTIFY: [
            "通知", "提醒", "notify", "remind", "alert"
        ],
        
        # 执行操作
        IntentType.EXECUTE_COMMAND: [
            "执行", "运行命令", "命令行", "终端", "execute", "run command", "terminal", "shell"
        ],
        IntentType.EXECUTE_SCRIPT: [
            "运行脚本", "执行脚本", "run script", "execute script"
        ],
        
        # 编写操作
        IntentType.COMPOSE_TEXT: [
            "写", "编写", "撰写", "起草", "write", "compose", "draft"
        ],
        IntentType.COMPOSE_CODE: [
            "写代码", "编程", "代码", "编写代码", "write code", "code"
        ],
        
        # 帮助
        IntentType.HELP: [
            "帮助", "怎么", "如何", "help", "how to", "what can you do"
        ],
        
        # 取消/撤销
        IntentType.CANCEL: [
            "取消", "算了", "不要了", "cancel", "never mind", "stop"
        ],
        IntentType.CONFIRM: [
            "确认", "确定", "是的", "好的", "yes", "ok", "confirm", "sure"
        ],
        IntentType.UNDO: [
            "撤销", "回退", "undo", "revert"
        ],
    }
    
    # 实体提取正则表达式
    ENTITY_PATTERNS = {
        EntityType.FILE_PATH: [
            r'["\']([^"\']+\.[a-zA-Z0-9]+)["\']',  # 引号内的文件路径
            r'([A-Za-z]:\\[^\s]+)',  # Windows路径
            r'((?:~|/)[^\s]+)',  # Unix路径
            r'([.\w-]+\.[a-zA-Z0-9]{1,5})',  # 简单文件名
        ],
        EntityType.DIR_PATH: [
            r'目录["\']?([^"\']+)["\']?',
            r'文件夹["\']?([^"\']+)["\']?',
            r'folder["\']?([^"\']+)["\']?',
            r'directory["\']?([^"\']+)["\']?',
        ],
        EntityType.APP_NAME: [
            r'打开\s*([^\s]+)',
            r'启动\s*([^\s]+)',
            r'open\s+([^\s]+)',
            r'start\s+([^\s]+)',
            r'(notepad|记事本|chrome|浏览器|firefox|edge|vscode|code|word|excel|powerpoint|qq|微信|wechat)',
        ],
        EntityType.URL: [
            r'(https?://[^\s]+)',
            r'(www\.[^\s]+)',
            r'([a-zA-Z0-9-]+\.(?:com|org|net|cn|io|dev|app)[^\s]*)',
        ],
        EntityType.SEARCH_QUERY: [
            r'搜索["\']?([^"\']+)["\']?',
            r'查找["\']?([^"\']+)["\']?',
            r'search\s+(?:for\s+)?["\']?([^"\']+)["\']?',
            r'find\s+["\']?([^"\']+)["\']?',
        ],
        EntityType.FILE_TYPE: [
            r'\.(txt|md|py|js|html|css|json|xml|csv|doc|docx|pdf|xls|xlsx|ppt|pptx|jpg|png|gif|mp3|mp4)',
            r'(文本文件|文档|图片|视频|音频|PDF|Word|Excel)',
        ],
        EntityType.COMMAND: [
            r'执行["`]([^"`]+)["`]',
            r'运行["`]([^"`]+)["`]',
            r'命令["`]([^"`]+)["`]',
            r'execute["`]([^"`]+)["`]',
            r'run["`]([^"`]+)["`]',
        ],
    }
    
    # 常见应用名称映射
    APP_ALIASES: Dict[str, str] = {
        # Windows
        "记事本": "notepad",
        "计算器": "calc",
        "画图": "mspaint",
        "资源管理器": "explorer",
        "命令提示符": "cmd",
        "终端": "wt",
        "文件管理器": "explorer",
        
        # 通用
        "浏览器": "chrome",
        "chrome": "chrome",
        "谷歌浏览器": "chrome",
        "火狐": "firefox",
        "edge": "msedge",
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "word": "winword",
        "excel": "excel",
        "ppt": "powerpnt",
        "powerpoint": "powerpnt",
        "qq": "qq",
        "微信": "wechat",
        "wechat": "wechat",
    }
    
    def __init__(self):
        # 编译正则表达式
        self._compiled_patterns = {}
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            self._compiled_patterns[entity_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def match(self, text: str) -> Optional[Intent]:
        """
        匹配意图
        
        返回最佳匹配的意图，如果无法匹配则返回None
        """
        text_lower = text.lower()
        
        best_intent = None
        best_score = 0
        
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = self._calculate_match_score(text_lower, keywords)
            if score > best_score:
                best_score = score
                best_intent = intent_type
        
        if best_intent and best_score > 0.3:  # 置信度阈值
            intent = Intent(
                type=best_intent,
                confidence=min(best_score, 1.0),
                raw_input=text,
                requires_confirmation=best_intent in DANGEROUS_INTENTS,
            )
            
            # 提取实体
            self._extract_entities(text, intent)
            
            # 生成描述
            intent.description = self._generate_description(intent)
            
            return intent
        
        return None
    
    def _calculate_match_score(self, text: str, keywords: List[str]) -> float:
        """计算匹配分数"""
        score = 0
        for keyword in keywords:
            if keyword.lower() in text:
                # 关键词越长，分数越高
                score += len(keyword) / 10
                # 完全匹配加分
                if text == keyword.lower():
                    score += 0.5
        return score
    
    def _extract_entities(self, text: str, intent: Intent) -> None:
        """提取实体"""
        for entity_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    value = match.group(1) if match.groups() else match.group()
                    
                    # 处理特殊实体
                    if entity_type == EntityType.APP_NAME:
                        value = self._normalize_app_name(value)
                    
                    entity = Entity(
                        type=entity_type,
                        value=value,
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                    )
                    intent.add_entity(entity)
    
    def _normalize_app_name(self, name: str) -> str:
        """标准化应用名称"""
        name_lower = name.lower().strip()
        return self.APP_ALIASES.get(name_lower, name)
    
    def _generate_description(self, intent: Intent) -> str:
        """生成意图描述"""
        descriptions = {
            IntentType.FILE_CREATE: "创建文件",
            IntentType.FILE_READ: "读取文件",
            IntentType.FILE_WRITE: "写入文件",
            IntentType.FILE_DELETE: "删除文件",
            IntentType.FILE_COPY: "复制文件",
            IntentType.FILE_MOVE: "移动文件",
            IntentType.FILE_OPEN: "打开文件",
            IntentType.DIR_CREATE: "创建目录",
            IntentType.DIR_LIST: "列出目录内容",
            IntentType.DIR_DELETE: "删除目录",
            IntentType.SEARCH_FILE: "搜索文件",
            IntentType.SEARCH_CONTENT: "搜索内容",
            IntentType.APP_OPEN: "打开应用",
            IntentType.APP_CLOSE: "关闭应用",
            IntentType.BROWSER_SEARCH: "浏览器搜索",
            IntentType.BROWSER_NAVIGATE: "访问网址",
            IntentType.SYSTEM_INFO: "获取系统信息",
            IntentType.SYSTEM_SCREENSHOT: "截取屏幕",
            IntentType.EXECUTE_COMMAND: "执行命令",
        }
        
        base_desc = descriptions.get(intent.type, "执行操作")
        
        # 添加实体信息
        file_entity = intent.get_entity(EntityType.FILE_PATH)
        if file_entity:
            base_desc += f": {file_entity.value}"
        
        app_entity = intent.get_entity(EntityType.APP_NAME)
        if app_entity:
            base_desc += f": {app_entity.value}"
        
        search_entity = intent.get_entity(EntityType.SEARCH_QUERY)
        if search_entity:
            base_desc += f": {search_entity.value}"
        
        return base_desc
    
    def extract_file_paths(self, text: str) -> List[str]:
        """提取文件路径"""
        paths = []
        for pattern in self._compiled_patterns.get(EntityType.FILE_PATH, []):
            matches = pattern.findall(text)
            paths.extend(matches)
        return list(set(paths))
    
    def extract_search_queries(self, text: str) -> List[str]:
        """提取搜索关键词"""
        queries = []
        for pattern in self._compiled_patterns.get(EntityType.SEARCH_QUERY, []):
            matches = pattern.findall(text)
            queries.extend(matches)
        return list(set(queries))
    
    def is_compound_intent(self, text: str) -> bool:
        """判断是否是复合意图"""
        # 检查是否包含连接词
        connectors = ["然后", "接着", "并且", "同时", "之后", "再", "and then", "then", "also", "and"]
        text_lower = text.lower()
        
        connector_count = sum(1 for c in connectors if c in text_lower)
        
        # 检查是否包含多个动词
        verbs = ["打开", "创建", "删除", "复制", "移动", "搜索", "查找", "写入", "编辑",
                "open", "create", "delete", "copy", "move", "search", "find", "write", "edit"]
        verb_count = sum(1 for v in verbs if v in text_lower)
        
        return connector_count >= 1 or verb_count >= 2

