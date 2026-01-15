"""
MCP Client Implementation
=========================

Connects to external MCP servers to use their tools.
Supports connecting to filesystem, github, slack and other MCP servers.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pathlib import Path
import subprocess
import sys

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    command: str                          # 启动命令
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPServerConfig":
        return cls(**data)


@dataclass 
class MCPToolInfo:
    """外部MCP工具信息"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "server_name": self.server_name
        }


class MCPClientTransport:
    """MCP客户端传输层 - 使用stdio与MCP服务器通信"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._message_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """连接到MCP服务器"""
        try:
            # 准备环境变量
            env = dict(subprocess.os.environ)
            env.update(self.config.env)
            
            # 启动服务器进程
            self.process = subprocess.Popen(
                [self.config.command] + self.config.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )
            
            # 启动读取任务
            self._read_task = asyncio.create_task(self._read_loop())
            
            logger.info(f"Connected to MCP server: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.config.name}: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        logger.info(f"Disconnected from MCP server: {self.config.name}")
    
    async def send_request(self, method: str, params: Dict = None) -> Any:
        """发送请求并等待响应"""
        if not self.process or self.process.poll() is not None:
            raise ConnectionError("Not connected to MCP server")
        
        self._message_id += 1
        msg_id = self._message_id
        
        request = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params or {}
        }
        
        # 创建Future等待响应
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[msg_id] = future
        
        try:
            # 发送请求
            message = json.dumps(request) + "\n"
            self.process.stdin.write(message)
            self.process.stdin.flush()
            
            # 等待响应
            result = await asyncio.wait_for(future, timeout=30)
            return result
            
        except asyncio.TimeoutError:
            del self._pending_requests[msg_id]
            raise TimeoutError(f"Request timed out: {method}")
        except Exception as e:
            if msg_id in self._pending_requests:
                del self._pending_requests[msg_id]
            raise
    
    async def _read_loop(self):
        """读取服务器响应"""
        try:
            while self.process and self.process.poll() is None:
                line = await asyncio.to_thread(self.process.stdout.readline)
                if not line:
                    break
                
                try:
                    response = json.loads(line.strip())
                    msg_id = response.get("id")
                    
                    if msg_id and msg_id in self._pending_requests:
                        future = self._pending_requests.pop(msg_id)
                        
                        if "error" in response:
                            future.set_exception(
                                Exception(response["error"].get("message", "Unknown error"))
                            )
                        else:
                            future.set_result(response.get("result"))
                            
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from MCP server: {line}")
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in MCP read loop: {e}")


class MCPClient:
    """
    MCP客户端
    
    连接外部MCP服务器并使用其工具：
    - 发现可用工具
    - 调用外部工具
    - 管理多个MCP服务器连接
    """
    
    def __init__(self, config_path: str = "./mcp_servers.json"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connections: Dict[str, MCPClientTransport] = {}
        self.tools: Dict[str, MCPToolInfo] = {}  # tool_name -> info
        
        self._load_config()
    
    def _load_config(self):
        """加载服务器配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for server_data in data.get("servers", []):
                    config = MCPServerConfig.from_dict(server_data)
                    self.servers[config.name] = config
                    
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")
        
        # 添加默认服务器配置
        self._add_default_servers()
    
    def _add_default_servers(self):
        """添加默认服务器配置"""
        defaults = [
            MCPServerConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
                description="文件系统操作",
                enabled=False  # 默认禁用，需要用户手动启用
            ),
            MCPServerConfig(
                name="github",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
                description="GitHub集成",
                enabled=False
            ),
            MCPServerConfig(
                name="sqlite",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-sqlite", "./workspace/data.db"],
                description="SQLite数据库操作",
                enabled=False
            ),
        ]
        
        for config in defaults:
            if config.name not in self.servers:
                self.servers[config.name] = config
    
    def _save_config(self):
        """保存服务器配置"""
        try:
            data = {
                "servers": [s.to_dict() for s in self.servers.values()]
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save MCP config: {e}")
    
    # ========================
    # 服务器管理
    # ========================
    
    def add_server(self, config: MCPServerConfig):
        """添加服务器配置"""
        self.servers[config.name] = config
        self._save_config()
        logger.info(f"Added MCP server: {config.name}")
    
    def remove_server(self, name: str) -> bool:
        """移除服务器配置"""
        if name in self.servers:
            # 先断开连接
            if name in self.connections:
                asyncio.create_task(self.disconnect(name))
            
            del self.servers[name]
            self._save_config()
            logger.info(f"Removed MCP server: {name}")
            return True
        return False
    
    def list_servers(self) -> List[MCPServerConfig]:
        """列出所有服务器"""
        return list(self.servers.values())
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """获取服务器配置"""
        return self.servers.get(name)
    
    # ========================
    # 连接管理
    # ========================
    
    async def connect(self, server_name: str) -> bool:
        """连接到MCP服务器"""
        config = self.servers.get(server_name)
        if not config:
            logger.error(f"Unknown MCP server: {server_name}")
            return False
        
        if not config.enabled:
            logger.warning(f"MCP server is disabled: {server_name}")
            return False
        
        if server_name in self.connections:
            logger.info(f"Already connected to: {server_name}")
            return True
        
        transport = MCPClientTransport(config)
        if await transport.connect():
            self.connections[server_name] = transport
            
            # 初始化并发现工具
            await self._initialize_server(server_name)
            await self._discover_tools(server_name)
            
            return True
        return False
    
    async def disconnect(self, server_name: str):
        """断开与MCP服务器的连接"""
        if server_name in self.connections:
            await self.connections[server_name].disconnect()
            del self.connections[server_name]
            
            # 移除该服务器的工具
            self.tools = {
                k: v for k, v in self.tools.items() 
                if v.server_name != server_name
            }
    
    async def connect_all(self):
        """连接所有启用的服务器"""
        for name, config in self.servers.items():
            if config.enabled:
                await self.connect(name)
    
    async def disconnect_all(self):
        """断开所有连接"""
        for name in list(self.connections.keys()):
            await self.disconnect(name)
    
    async def _initialize_server(self, server_name: str):
        """初始化服务器"""
        transport = self.connections.get(server_name)
        if not transport:
            return
        
        try:
            result = await transport.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "joinflow-mcp-client",
                    "version": "1.0.0"
                }
            })
            logger.info(f"Initialized MCP server {server_name}: {result}")
            
            # 发送initialized通知
            await transport.send_request("notifications/initialized", {})
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server {server_name}: {e}")
    
    async def _discover_tools(self, server_name: str):
        """发现服务器提供的工具"""
        transport = self.connections.get(server_name)
        if not transport:
            return
        
        try:
            result = await transport.send_request("tools/list", {})
            
            for tool_data in result.get("tools", []):
                tool = MCPToolInfo(
                    name=f"{server_name}/{tool_data['name']}",
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=server_name
                )
                self.tools[tool.name] = tool
                logger.debug(f"Discovered tool: {tool.name}")
                
        except Exception as e:
            logger.error(f"Failed to discover tools from {server_name}: {e}")
    
    # ========================
    # 工具调用
    # ========================
    
    def list_tools(self) -> List[MCPToolInfo]:
        """列出所有可用工具"""
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> Optional[MCPToolInfo]:
        """获取工具信息"""
        return self.tools.get(name)
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用工具"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        transport = self.connections.get(tool.server_name)
        if not transport:
            return {"success": False, "error": f"Not connected to server: {tool.server_name}"}
        
        try:
            # 提取原始工具名（去掉服务器前缀）
            original_name = tool_name.split("/", 1)[1] if "/" in tool_name else tool_name
            
            result = await transport.send_request("tools/call", {
                "name": original_name,
                "arguments": arguments
            })
            
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # 资源访问
    # ========================
    
    async def list_resources(self, server_name: str) -> List[Dict]:
        """列出服务器资源"""
        transport = self.connections.get(server_name)
        if not transport:
            return []
        
        try:
            result = await transport.send_request("resources/list", {})
            return result.get("resources", [])
        except Exception as e:
            logger.error(f"Failed to list resources from {server_name}: {e}")
            return []
    
    async def read_resource(self, server_name: str, uri: str) -> Optional[str]:
        """读取资源"""
        transport = self.connections.get(server_name)
        if not transport:
            return None
        
        try:
            result = await transport.send_request("resources/read", {"uri": uri})
            contents = result.get("contents", [])
            if contents:
                return contents[0].get("text")
            return None
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            return None
    
    # ========================
    # 便捷方法
    # ========================
    
    def get_tools_for_llm(self) -> List[Dict]:
        """获取LLM可用的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": f"[{tool.server_name}] {tool.description}",
                    "parameters": tool.input_schema
                }
            }
            for tool in self.tools.values()
        ]
    
    def is_connected(self, server_name: str) -> bool:
        """检查是否已连接"""
        return server_name in self.connections


# 全局实例
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """获取全局MCP Client实例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client

