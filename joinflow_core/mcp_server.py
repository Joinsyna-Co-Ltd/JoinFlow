"""
MCP Server Implementation
=========================

Implements Model Context Protocol (MCP) server to expose JoinFlow tools
to external clients like Claude, Cursor, etc.

MCP Specification: https://modelcontextprotocol.io/
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MCPMessageType(str, Enum):
    """MCP消息类型"""
    # 请求
    INITIALIZE = "initialize"
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    LIST_RESOURCES = "resources/list"
    READ_RESOURCE = "resources/read"
    LIST_PROMPTS = "prompts/list"
    GET_PROMPT = "prompts/get"
    
    # 通知
    INITIALIZED = "notifications/initialized"
    PROGRESS = "notifications/progress"
    
    # 响应
    RESULT = "result"
    ERROR = "error"


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Callable] = None
    
    def to_mcp_format(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResource:
    """MCP资源定义"""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    
    def to_mcp_format(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPPrompt:
    """MCP提示模板"""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_mcp_format(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


class MCPServer:
    """
    MCP Server实现
    
    暴露JoinFlow的能力给外部MCP客户端：
    - 工具调用 (Browser, OS, LLM等Agent)
    - 资源访问 (知识库、文件等)
    - 提示模板 (预定义任务模板)
    """
    
    def __init__(
        self,
        name: str = "joinflow-mcp",
        version: str = "1.0.0"
    ):
        self.name = name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        
        self._initialized = False
        self._register_builtin_tools()
        self._register_builtin_resources()
        self._register_builtin_prompts()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        # 浏览器搜索工具
        self.register_tool(MCPTool(
            name="browser_search",
            description="使用浏览器搜索网络信息",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "engine": {
                        "type": "string",
                        "enum": ["bing", "baidu", "google"],
                        "default": "bing",
                        "description": "搜索引擎"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "最大结果数"
                    }
                },
                "required": ["query"]
            },
            handler=self._handle_browser_search
        ))
        
        # 文件操作工具
        self.register_tool(MCPTool(
            name="file_read",
            description="读取文件内容",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    }
                },
                "required": ["path"]
            },
            handler=self._handle_file_read
        ))
        
        self.register_tool(MCPTool(
            name="file_write",
            description="写入文件内容",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容"
                    }
                },
                "required": ["path", "content"]
            },
            handler=self._handle_file_write
        ))
        
        # 系统命令工具
        self.register_tool(MCPTool(
            name="system_command",
            description="执行系统命令",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "description": "超时时间（秒）"
                    }
                },
                "required": ["command"]
            },
            handler=self._handle_system_command
        ))
        
        # LLM生成工具
        self.register_tool(MCPTool(
            name="llm_generate",
            description="使用大模型生成内容",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "提示词"
                    },
                    "model": {
                        "type": "string",
                        "default": "gpt-4o-mini",
                        "description": "模型名称"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "default": 1000,
                        "description": "最大token数"
                    }
                },
                "required": ["prompt"]
            },
            handler=self._handle_llm_generate
        ))
        
        # 任务执行工具
        self.register_tool(MCPTool(
            name="execute_task",
            description="执行JoinFlow任务",
            input_schema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "任务描述"
                    },
                    "agents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "使用的Agent列表"
                    }
                },
                "required": ["description"]
            },
            handler=self._handle_execute_task
        ))
        
        # 知识库查询工具
        self.register_tool(MCPTool(
            name="knowledge_query",
            description="查询知识库",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询内容"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "description": "返回结果数"
                    }
                },
                "required": ["query"]
            },
            handler=self._handle_knowledge_query
        ))
    
    def _register_builtin_resources(self):
        """注册内置资源"""
        self.register_resource(MCPResource(
            uri="joinflow://knowledge",
            name="知识库",
            description="JoinFlow知识库内容",
            mime_type="application/json"
        ))
        
        self.register_resource(MCPResource(
            uri="joinflow://tasks",
            name="任务列表",
            description="当前任务列表",
            mime_type="application/json"
        ))
        
        self.register_resource(MCPResource(
            uri="joinflow://config",
            name="配置信息",
            description="JoinFlow配置",
            mime_type="application/json"
        ))
    
    def _register_builtin_prompts(self):
        """注册内置提示模板"""
        self.register_prompt(MCPPrompt(
            name="research_report",
            description="生成研究报告",
            arguments=[
                {"name": "topic", "description": "研究主题", "required": True},
                {"name": "depth", "description": "研究深度", "required": False}
            ]
        ))
        
        self.register_prompt(MCPPrompt(
            name="code_review",
            description="代码审查",
            arguments=[
                {"name": "code", "description": "要审查的代码", "required": True},
                {"name": "language", "description": "编程语言", "required": False}
            ]
        ))
        
        self.register_prompt(MCPPrompt(
            name="data_analysis",
            description="数据分析",
            arguments=[
                {"name": "data_source", "description": "数据源", "required": True},
                {"name": "analysis_type", "description": "分析类型", "required": False}
            ]
        ))
    
    # ========================
    # 工具/资源/提示注册
    # ========================
    
    def register_tool(self, tool: MCPTool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered MCP tool: {tool.name}")
    
    def register_resource(self, resource: MCPResource):
        """注册资源"""
        self.resources[resource.uri] = resource
        logger.debug(f"Registered MCP resource: {resource.uri}")
    
    def register_prompt(self, prompt: MCPPrompt):
        """注册提示模板"""
        self.prompts[prompt.name] = prompt
        logger.debug(f"Registered MCP prompt: {prompt.name}")
    
    # ========================
    # MCP协议处理
    # ========================
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP消息"""
        msg_type = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        try:
            if msg_type == MCPMessageType.INITIALIZE.value:
                result = await self._handle_initialize(params)
            elif msg_type == MCPMessageType.LIST_TOOLS.value:
                result = await self._handle_list_tools(params)
            elif msg_type == MCPMessageType.CALL_TOOL.value:
                result = await self._handle_call_tool(params)
            elif msg_type == MCPMessageType.LIST_RESOURCES.value:
                result = await self._handle_list_resources(params)
            elif msg_type == MCPMessageType.READ_RESOURCE.value:
                result = await self._handle_read_resource(params)
            elif msg_type == MCPMessageType.LIST_PROMPTS.value:
                result = await self._handle_list_prompts(params)
            elif msg_type == MCPMessageType.GET_PROMPT.value:
                result = await self._handle_get_prompt(params)
            else:
                return self._error_response(msg_id, -32601, f"Unknown method: {msg_type}")
            
            return self._success_response(msg_id, result)
            
        except Exception as e:
            logger.error(f"MCP error: {e}")
            return self._error_response(msg_id, -32603, str(e))
    
    async def _handle_initialize(self, params: Dict) -> Dict:
        """处理初始化请求"""
        self._initialized = True
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
    
    async def _handle_list_tools(self, params: Dict) -> Dict:
        """列出可用工具"""
        return {
            "tools": [tool.to_mcp_format() for tool in self.tools.values()]
        }
    
    async def _handle_call_tool(self, params: Dict) -> Dict:
        """调用工具"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        if not tool.handler:
            raise ValueError(f"Tool has no handler: {tool_name}")
        
        # 调用工具处理器
        if asyncio.iscoroutinefunction(tool.handler):
            result = await tool.handler(arguments)
        else:
            result = tool.handler(arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
                }
            ]
        }
    
    async def _handle_list_resources(self, params: Dict) -> Dict:
        """列出可用资源"""
        return {
            "resources": [res.to_mcp_format() for res in self.resources.values()]
        }
    
    async def _handle_read_resource(self, params: Dict) -> Dict:
        """读取资源"""
        uri = params.get("uri")
        
        resource = self.resources.get(uri)
        if not resource:
            raise ValueError(f"Unknown resource: {uri}")
        
        # 根据资源类型读取内容
        content = await self._read_resource_content(uri)
        
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": resource.mime_type,
                    "text": content
                }
            ]
        }
    
    async def _handle_list_prompts(self, params: Dict) -> Dict:
        """列出提示模板"""
        return {
            "prompts": [prompt.to_mcp_format() for prompt in self.prompts.values()]
        }
    
    async def _handle_get_prompt(self, params: Dict) -> Dict:
        """获取提示模板"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        prompt = self.prompts.get(name)
        if not prompt:
            raise ValueError(f"Unknown prompt: {name}")
        
        # 生成提示内容
        content = await self._generate_prompt_content(name, arguments)
        
        return {
            "description": prompt.description,
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": content
                    }
                }
            ]
        }
    
    # ========================
    # 工具处理器实现
    # ========================
    
    async def _handle_browser_search(self, args: Dict) -> Dict:
        """浏览器搜索"""
        try:
            from joinflow_agent.browser_enhanced import EnhancedBrowserAgent
            
            agent = EnhancedBrowserAgent()
            query = args.get("query", "")
            engine = args.get("engine", "bing")
            max_results = args.get("max_results", 10)
            
            results = await asyncio.to_thread(
                agent.search, query, engine=engine, max_results=max_results
            )
            
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_file_read(self, args: Dict) -> Dict:
        """读取文件"""
        try:
            from pathlib import Path
            
            path = Path(args.get("path", ""))
            if not path.exists():
                return {"success": False, "error": "File not found"}
            
            content = path.read_text(encoding='utf-8')
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_file_write(self, args: Dict) -> Dict:
        """写入文件"""
        try:
            from pathlib import Path
            
            path = Path(args.get("path", ""))
            content = args.get("content", "")
            
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            
            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_system_command(self, args: Dict) -> Dict:
        """执行系统命令"""
        try:
            import subprocess
            
            command = args.get("command", "")
            timeout = args.get("timeout", 30)
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_llm_generate(self, args: Dict) -> Dict:
        """LLM生成"""
        try:
            from joinflow_agent.model_manager import get_model_manager
            
            manager = get_model_manager()
            prompt = args.get("prompt", "")
            model = args.get("model", "gpt-4o-mini")
            max_tokens = args.get("max_tokens", 1000)
            
            response = await asyncio.to_thread(
                manager.generate,
                prompt,
                model=model,
                max_tokens=max_tokens
            )
            
            return {"success": True, "content": response}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_execute_task(self, args: Dict) -> Dict:
        """执行任务"""
        try:
            description = args.get("description", "")
            agents = args.get("agents", [])
            
            # 这里简化处理，实际应该调用完整的任务执行流程
            return {
                "success": True,
                "task_id": str(uuid.uuid4()),
                "description": description,
                "agents": agents,
                "status": "created"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_knowledge_query(self, args: Dict) -> Dict:
        """知识库查询"""
        try:
            query = args.get("query", "")
            top_k = args.get("top_k", 5)
            
            # 简化实现
            return {
                "success": True,
                "query": query,
                "results": [],
                "message": "Knowledge query executed"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _read_resource_content(self, uri: str) -> str:
        """读取资源内容"""
        if uri == "joinflow://knowledge":
            return json.dumps({"items": []})
        elif uri == "joinflow://tasks":
            return json.dumps({"tasks": []})
        elif uri == "joinflow://config":
            return json.dumps({"version": self.version})
        else:
            return "{}"
    
    async def _generate_prompt_content(self, name: str, arguments: Dict) -> str:
        """生成提示内容"""
        if name == "research_report":
            topic = arguments.get("topic", "")
            depth = arguments.get("depth", "medium")
            return f"请对以下主题进行{depth}深度的研究并生成报告：{topic}"
        elif name == "code_review":
            code = arguments.get("code", "")
            language = arguments.get("language", "")
            return f"请审查以下{language}代码并提供改进建议：\n{code}"
        elif name == "data_analysis":
            data_source = arguments.get("data_source", "")
            analysis_type = arguments.get("analysis_type", "general")
            return f"请对数据源 {data_source} 进行{analysis_type}分析"
        else:
            return f"执行任务: {name}"
    
    # ========================
    # 响应构造
    # ========================
    
    def _success_response(self, msg_id: Any, result: Any) -> Dict:
        """构造成功响应"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
    
    def _error_response(self, msg_id: Any, code: int, message: str) -> Dict:
        """构造错误响应"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }


# 全局实例
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """获取全局MCP Server实例"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server

