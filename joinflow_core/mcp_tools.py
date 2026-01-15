"""
MCP Tools Integration
=====================

Model Context Protocol tools for extended capabilities.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MCPToolCategory(str, Enum):
    """工具分类"""
    PRODUCTIVITY = "productivity"    # 生产力工具
    COMMUNICATION = "communication"  # 通讯工具
    DATA = "data"                    # 数据工具
    DEVELOPMENT = "development"      # 开发工具
    UTILITY = "utility"              # 实用工具


@dataclass
class MCPToolDefinition:
    """MCP工具定义"""
    name: str
    description: str
    category: MCPToolCategory = MCPToolCategory.UTILITY
    
    # 参数定义
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 服务配置
    server: str = ""           # MCP服务器地址
    auth_required: bool = False
    api_key_env: str = ""      # 环境变量名
    
    # 元数据
    version: str = "1.0.0"
    enabled: bool = True
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['category'] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPToolDefinition":
        if 'category' in data:
            data['category'] = MCPToolCategory(data['category'])
        return cls(**data)


# 内置工具定义
BUILTIN_TOOLS = [
    MCPToolDefinition(
        name="web_search",
        description="搜索网络信息",
        category=MCPToolCategory.DATA,
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "num_results": {"type": "integer", "description": "结果数量", "default": 10}
            },
            "required": ["query"]
        }
    ),
    MCPToolDefinition(
        name="calculator",
        description="数学计算",
        category=MCPToolCategory.UTILITY,
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "required": ["expression"]
        }
    ),
    MCPToolDefinition(
        name="datetime_now",
        description="获取当前日期时间",
        category=MCPToolCategory.UTILITY,
        parameters={
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "时区", "default": "UTC"},
                "format": {"type": "string", "description": "格式", "default": "%Y-%m-%d %H:%M:%S"}
            }
        }
    ),
    MCPToolDefinition(
        name="weather",
        description="获取天气信息",
        category=MCPToolCategory.DATA,
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名称"}
            },
            "required": ["location"]
        },
        auth_required=True,
        api_key_env="WEATHER_API_KEY"
    ),
    MCPToolDefinition(
        name="translate",
        description="文本翻译",
        category=MCPToolCategory.PRODUCTIVITY,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要翻译的文本"},
                "source_lang": {"type": "string", "description": "源语言", "default": "auto"},
                "target_lang": {"type": "string", "description": "目标语言", "default": "en"}
            },
            "required": ["text", "target_lang"]
        }
    ),
    MCPToolDefinition(
        name="url_fetch",
        description="获取URL内容",
        category=MCPToolCategory.DATA,
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL地址"},
                "extract_text": {"type": "boolean", "description": "是否提取纯文本", "default": True}
            },
            "required": ["url"]
        }
    ),
    MCPToolDefinition(
        name="json_parse",
        description="解析JSON数据",
        category=MCPToolCategory.DATA,
        parameters={
            "type": "object",
            "properties": {
                "json_string": {"type": "string", "description": "JSON字符串"},
                "path": {"type": "string", "description": "JSONPath表达式", "default": "$"}
            },
            "required": ["json_string"]
        }
    ),
    MCPToolDefinition(
        name="text_summary",
        description="文本摘要",
        category=MCPToolCategory.PRODUCTIVITY,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要摘要的文本"},
                "max_length": {"type": "integer", "description": "最大长度", "default": 200}
            },
            "required": ["text"]
        }
    ),
    MCPToolDefinition(
        name="regex_match",
        description="正则表达式匹配",
        category=MCPToolCategory.UTILITY,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "输入文本"},
                "pattern": {"type": "string", "description": "正则表达式"},
                "find_all": {"type": "boolean", "description": "是否查找所有", "default": False}
            },
            "required": ["text", "pattern"]
        }
    ),
    MCPToolDefinition(
        name="hash_generate",
        description="生成哈希值",
        category=MCPToolCategory.UTILITY,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "输入文本"},
                "algorithm": {"type": "string", "description": "算法", "enum": ["md5", "sha1", "sha256"], "default": "sha256"}
            },
            "required": ["text"]
        }
    ),
]


class MCPToolExecutor:
    """MCP工具执行器"""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._register_builtin_handlers()
    
    def _register_builtin_handlers(self):
        """注册内置工具处理器"""
        self._handlers['calculator'] = self._handle_calculator
        self._handlers['datetime_now'] = self._handle_datetime
        self._handlers['json_parse'] = self._handle_json_parse
        self._handlers['regex_match'] = self._handle_regex
        self._handlers['hash_generate'] = self._handle_hash
        self._handlers['url_fetch'] = self._handle_url_fetch
    
    def register_handler(self, tool_name: str, handler: Callable):
        """注册工具处理器"""
        self._handlers[tool_name] = handler
    
    def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        handler = self._handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            result = handler(**params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {"success": False, "error": str(e)}
    
    def _handle_calculator(self, expression: str) -> str:
        """计算器"""
        import ast
        import operator
        
        # 安全的操作符
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.Mod: operator.mod,
        }
        
        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")
        
        try:
            tree = ast.parse(expression, mode='eval')
            result = eval_expr(tree.body)
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    
    def _handle_datetime(self, timezone: str = "UTC", format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """获取当前时间"""
        from datetime import datetime, timezone as tz
        
        if timezone.upper() == "UTC":
            now = datetime.now(tz.utc)
        else:
            now = datetime.now()
        
        return now.strftime(format)
    
    def _handle_json_parse(self, json_string: str, path: str = "$") -> Any:
        """解析JSON"""
        data = json.loads(json_string)
        
        if path == "$" or not path:
            return data
        
        # 简单的路径解析
        parts = path.replace('$', '').strip('.').split('.')
        result = data
        for part in parts:
            if not part:
                continue
            if isinstance(result, dict):
                result = result.get(part)
            elif isinstance(result, list) and part.isdigit():
                result = result[int(part)]
            else:
                return None
        
        return result
    
    def _handle_regex(self, text: str, pattern: str, find_all: bool = False) -> Any:
        """正则匹配"""
        import re
        
        if find_all:
            return re.findall(pattern, text)
        else:
            match = re.search(pattern, text)
            return match.group() if match else None
    
    def _handle_hash(self, text: str, algorithm: str = "sha256") -> str:
        """生成哈希"""
        import hashlib
        
        if algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(text.encode()).hexdigest()
        else:
            return hashlib.sha256(text.encode()).hexdigest()
    
    def _handle_url_fetch(self, url: str, extract_text: bool = True) -> str:
        """获取URL内容"""
        try:
            import requests
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if extract_text:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # 移除script和style
                    for script in soup(["script", "style"]):
                        script.decompose()
                    return soup.get_text(separator='\n', strip=True)
                except ImportError:
                    return response.text
            
            return response.text
            
        except Exception as e:
            return f"Error fetching URL: {e}"


class MCPToolManager:
    """MCP工具管理器"""
    
    def __init__(self, storage_path: str = "./mcp_tools"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.executor = MCPToolExecutor()
        
        self._load_tools()
        self._init_builtin_tools()
    
    def _load_tools(self):
        """加载工具配置"""
        config_file = self.storage_path / "tools.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for tool_data in data.get('tools', []):
                    tool = MCPToolDefinition.from_dict(tool_data)
                    self.tools[tool.name] = tool
            except Exception as e:
                logger.error(f"Failed to load MCP tools: {e}")
    
    def _save_tools(self):
        """保存工具配置"""
        config_file = self.storage_path / "tools.json"
        try:
            # 只保存非内置工具
            custom_tools = [t for t in self.tools.values() 
                          if t.name not in [bt.name for bt in BUILTIN_TOOLS]]
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'tools': [t.to_dict() for t in custom_tools]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save MCP tools: {e}")
    
    def _init_builtin_tools(self):
        """初始化内置工具"""
        for tool in BUILTIN_TOOLS:
            if tool.name not in self.tools:
                self.tools[tool.name] = tool
    
    def register_tool(self, tool: MCPToolDefinition, handler: Callable = None):
        """注册工具"""
        self.tools[tool.name] = tool
        if handler:
            self.executor.register_handler(tool.name, handler)
        self._save_tools()
    
    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
            self._save_tools()
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(
        self,
        category: MCPToolCategory = None,
        enabled_only: bool = True
    ) -> List[MCPToolDefinition]:
        """列出工具"""
        tools = list(self.tools.values())
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        if category:
            tools = [t for t in tools if t.category == category]
        
        return sorted(tools, key=lambda t: t.name)
    
    def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool not found: {name}"}
        
        if not tool.enabled:
            return {"error": f"Tool is disabled: {name}"}
        
        return self.executor.execute(name, params)
    
    def get_tools_for_llm(self) -> List[Dict]:
        """获取LLM可用的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
            if tool.enabled
        ]

