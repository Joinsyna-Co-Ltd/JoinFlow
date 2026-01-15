"""
OS Agent
========

Provides operating system interaction capabilities:
- File operations (read, write, create, delete)
- Directory management
- Process execution
- System information
"""

import os
import shutil
import subprocess
import platform
import psutil
import glob as glob_module
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence
import logging
import json

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType,
    AgentAction, Tool
)

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file"""
    path: str
    name: str
    extension: str
    size: int
    created: datetime
    modified: datetime
    is_directory: bool
    permissions: str
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "size": self.size,
            "size_human": self._human_size(self.size),
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "is_directory": self.is_directory,
            "permissions": self.permissions
        }
    
    @staticmethod
    def _human_size(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


@dataclass
class ProcessInfo:
    """Information about a process"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    created: datetime


@dataclass
class CommandResult:
    """Result of a command execution"""
    command: str
    return_code: int
    stdout: str
    stderr: str
    duration_ms: float


class OSAgent(BaseAgent):
    """
    Agent for operating system interactions.
    
    Capabilities:
    - File operations: read, write, create, delete, copy, move
    - Directory operations: list, create, delete
    - Process management: run commands, list processes
    - System information: disk, memory, CPU
    
    Security:
    - Restricted to workspace directory by default
    - Blocked dangerous commands
    - File size limits
    """
    
    # Dangerous commands that should be blocked
    BLOCKED_COMMANDS = [
        "rm -rf /", "rm -rf /*", "dd if=", "mkfs",
        "format", ":(){:|:&};:", "chmod -R 777 /",
        "shutdown", "reboot", "halt", "poweroff"
    ]
    
    # Dangerous file patterns
    BLOCKED_PATHS = [
        "/etc/passwd", "/etc/shadow", "~/.ssh",
        "C:\\Windows\\System32", "/System", "/usr/bin"
    ]
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self._workspace = Path(self.config.os_workspace).resolve()
        self._ensure_workspace()
    
    def _ensure_workspace(self) -> None:
        """Ensure workspace directory exists"""
        self._workspace.mkdir(parents=True, exist_ok=True)
        logger.info(f"OS Agent workspace: {self._workspace}")
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.OS
    
    @property
    def name(self) -> str:
        return "OS Agent"
    
    @property
    def description(self) -> str:
        return """Operating system agent capable of:
        - Reading and writing files
        - Managing directories
        - Running shell commands
        - Getting system information
        - Managing processes
        """
    
    def can_handle(self, task: str) -> bool:
        """Check if this is an OS-related task"""
        os_keywords = [
            "文件", "目录", "文件夹", "创建", "删除", "读取", "写入",
            "复制", "移动", "重命名", "执行", "命令", "运行", "进程",
            "系统", "磁盘", "内存", "CPU",
            "file", "directory", "folder", "create", "delete", "read", "write",
            "copy", "move", "rename", "execute", "command", "run", "process",
            "system", "disk", "memory"
        ]
        task_lower = task.lower()
        return any(kw in task_lower for kw in os_keywords)
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute an OS task"""
        result = self._create_result()
        
        try:
            # Parse task and execute appropriate action
            action, params = self._parse_task(task)
            output = self._execute_action(action, params, result)
            
            result.output = str(output) if output else "操作完成"
            result.data = output
            result.finalize(success=True)
            
        except PermissionError as e:
            result.output = f"权限错误: {e}"
            result.finalize(success=False, error=str(e))
        except FileNotFoundError as e:
            result.output = f"文件未找到: {e}"
            result.finalize(success=False, error=str(e))
        except Exception as e:
            self._handle_error(result, e)
        
        return result
    
    def _parse_task(self, task: str) -> tuple[str, dict]:
        """Parse task into action and parameters"""
        task_lower = task.lower()
        
        # Read file
        if any(kw in task_lower for kw in ["读取", "查看", "打开文件", "read", "view", "cat"]):
            path = self._extract_path(task)
            return "read_file", {"path": path}
        
        # Write file
        if any(kw in task_lower for kw in ["写入", "保存", "创建文件", "write", "save"]):
            path = self._extract_path(task)
            content = self._extract_content(task)
            return "write_file", {"path": path, "content": content}
        
        # List directory
        if any(kw in task_lower for kw in ["列出", "显示目录", "ls", "dir", "list"]):
            path = self._extract_path(task) or "."
            return "list_dir", {"path": path}
        
        # Create directory
        if any(kw in task_lower for kw in ["创建目录", "创建文件夹", "mkdir"]):
            path = self._extract_path(task)
            return "create_dir", {"path": path}
        
        # Delete
        if any(kw in task_lower for kw in ["删除", "移除", "delete", "remove", "rm"]):
            path = self._extract_path(task)
            return "delete", {"path": path}
        
        # Copy
        if any(kw in task_lower for kw in ["复制", "拷贝", "copy", "cp"]):
            paths = self._extract_paths(task)
            return "copy", {"src": paths[0], "dst": paths[1] if len(paths) > 1 else None}
        
        # Move/rename
        if any(kw in task_lower for kw in ["移动", "重命名", "move", "rename", "mv"]):
            paths = self._extract_paths(task)
            return "move", {"src": paths[0], "dst": paths[1] if len(paths) > 1 else None}
        
        # Run command
        if any(kw in task_lower for kw in ["执行", "运行命令", "execute", "run", "shell"]):
            command = self._extract_command(task)
            return "run_command", {"command": command}
        
        # System info
        if any(kw in task_lower for kw in ["系统信息", "system info", "系统状态"]):
            return "system_info", {}
        
        # Process list
        if any(kw in task_lower for kw in ["进程", "process"]):
            return "list_processes", {}
        
        # Default: try to understand as a command
        return "run_command", {"command": task}
    
    def _extract_path(self, task: str) -> str:
        """Extract file path from task"""
        import re
        # Look for quoted paths
        match = re.search(r'["\']([^"\']+)["\']', task)
        if match:
            return match.group(1)
        
        # Look for path-like patterns
        match = re.search(r'([./\\]?[\w./\\-]+\.\w+)', task)
        if match:
            return match.group(1)
        
        match = re.search(r'([./\\]?[\w./\\-]+)', task)
        if match:
            return match.group(1)
        
        return ""
    
    def _extract_paths(self, task: str) -> list[str]:
        """Extract multiple paths from task"""
        import re
        paths = re.findall(r'["\']([^"\']+)["\']', task)
        if not paths:
            paths = re.findall(r'([./\\]?[\w./\\-]+\.\w+)', task)
        return paths
    
    def _extract_content(self, task: str) -> str:
        """Extract content to write from task"""
        import re
        # Look for content in quotes
        match = re.search(r'内容[：:]\s*["\'](.+)["\']', task, re.DOTALL)
        if match:
            return match.group(1)
        
        match = re.search(r'content[:\s]+["\'](.+)["\']', task, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
        
        return ""
    
    def _extract_command(self, task: str) -> str:
        """Extract command from task"""
        import re
        # Look for command in backticks or quotes
        match = re.search(r'`([^`]+)`', task)
        if match:
            return match.group(1)
        
        match = re.search(r'["\']([^"\']+)["\']', task)
        if match:
            return match.group(1)
        
        # Remove common prefixes
        for prefix in ["执行", "运行", "execute", "run"]:
            if task.lower().startswith(prefix):
                return task[len(prefix):].strip()
        
        return task
    
    def _execute_action(self, action: str, params: dict, result: AgentResult) -> Any:
        """Execute the parsed action"""
        
        if action == "read_file":
            return self.read_file(params["path"], result)
        
        elif action == "write_file":
            return self.write_file(params["path"], params["content"], result)
        
        elif action == "list_dir":
            return self.list_directory(params["path"], result)
        
        elif action == "create_dir":
            return self.create_directory(params["path"], result)
        
        elif action == "delete":
            return self.delete(params["path"], result)
        
        elif action == "copy":
            return self.copy(params["src"], params["dst"], result)
        
        elif action == "move":
            return self.move(params["src"], params["dst"], result)
        
        elif action == "run_command":
            return self.run_command(params["command"], result)
        
        elif action == "system_info":
            return self.get_system_info(result)
        
        elif action == "list_processes":
            return self.list_processes(result)
        
        return None
    
    # -------------------------
    # File Operations
    # -------------------------
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path within workspace"""
        if not path:
            return self._workspace
        
        p = Path(path)
        if not p.is_absolute():
            p = self._workspace / p
        
        resolved = p.resolve()
        
        # Security check: ensure path is within workspace
        try:
            resolved.relative_to(self._workspace)
        except ValueError:
            raise PermissionError(f"Access denied: path outside workspace: {path}")
        
        # Check for blocked paths
        for blocked in self.BLOCKED_PATHS:
            if blocked in str(resolved):
                raise PermissionError(f"Access denied: blocked path: {path}")
        
        return resolved
    
    def _check_extension(self, path: Path) -> None:
        """Check if file extension is allowed"""
        if path.suffix and path.suffix not in self.config.os_allowed_extensions:
            raise PermissionError(
                f"File type not allowed: {path.suffix}. "
                f"Allowed: {self.config.os_allowed_extensions}"
            )
    
    def read_file(self, path: str, result: AgentResult) -> str:
        """Read a file"""
        resolved = self._resolve_path(path)
        self._log_action(result, "read_file", f"Reading: {resolved}", path=str(resolved))
        
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if resolved.stat().st_size > self.config.os_max_file_size:
            raise ValueError(f"File too large: {resolved.stat().st_size} bytes")
        
        return resolved.read_text(encoding="utf-8")
    
    def write_file(self, path: str, content: str, result: AgentResult) -> str:
        """Write content to a file"""
        resolved = self._resolve_path(path)
        self._check_extension(resolved)
        self._log_action(result, "write_file", f"Writing: {resolved}", path=str(resolved))
        
        # Create parent directories if needed
        resolved.parent.mkdir(parents=True, exist_ok=True)
        
        resolved.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} bytes to {path}"
    
    def list_directory(self, path: str, result: AgentResult) -> list[FileInfo]:
        """List directory contents"""
        resolved = self._resolve_path(path)
        self._log_action(result, "list_dir", f"Listing: {resolved}", path=str(resolved))
        
        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not resolved.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        files = []
        for item in resolved.iterdir():
            stat = item.stat()
            files.append(FileInfo(
                path=str(item),
                name=item.name,
                extension=item.suffix,
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
                is_directory=item.is_dir(),
                permissions=oct(stat.st_mode)[-3:]
            ))
        
        return files
    
    def create_directory(self, path: str, result: AgentResult) -> str:
        """Create a directory"""
        resolved = self._resolve_path(path)
        self._log_action(result, "create_dir", f"Creating directory: {resolved}", path=str(resolved))
        
        resolved.mkdir(parents=True, exist_ok=True)
        return f"Directory created: {path}"
    
    def delete(self, path: str, result: AgentResult) -> str:
        """Delete a file or directory"""
        resolved = self._resolve_path(path)
        self._log_action(result, "delete", f"Deleting: {resolved}", path=str(resolved))
        
        if not resolved.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        if resolved.is_dir():
            shutil.rmtree(resolved)
        else:
            resolved.unlink()
        
        return f"Deleted: {path}"
    
    def copy(self, src: str, dst: str, result: AgentResult) -> str:
        """Copy a file or directory"""
        src_resolved = self._resolve_path(src)
        dst_resolved = self._resolve_path(dst)
        self._log_action(result, "copy", f"Copying: {src} -> {dst}")
        
        if src_resolved.is_dir():
            shutil.copytree(src_resolved, dst_resolved)
        else:
            self._check_extension(src_resolved)
            shutil.copy2(src_resolved, dst_resolved)
        
        return f"Copied: {src} -> {dst}"
    
    def move(self, src: str, dst: str, result: AgentResult) -> str:
        """Move/rename a file or directory"""
        src_resolved = self._resolve_path(src)
        dst_resolved = self._resolve_path(dst)
        self._log_action(result, "move", f"Moving: {src} -> {dst}")
        
        shutil.move(src_resolved, dst_resolved)
        return f"Moved: {src} -> {dst}"
    
    # -------------------------
    # Command Execution
    # -------------------------
    
    def run_command(self, command: str, result: AgentResult) -> CommandResult:
        """Run a shell command"""
        # Security check
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command.lower():
                raise PermissionError(f"Command blocked for security: {command}")
        
        self._log_action(result, "run_command", f"Executing: {command}", command=command)
        
        start_time = datetime.now()
        
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self._workspace)
            )
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return CommandResult(
                command=command,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration
            )
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out: {command}")
    
    # -------------------------
    # System Information
    # -------------------------
    
    def get_system_info(self, result: AgentResult) -> dict:
        """Get system information"""
        self._log_action(result, "system_info", "Getting system information")
        
        return {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "cpu": {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
    
    def list_processes(self, result: AgentResult, limit: int = 20) -> list[ProcessInfo]:
        """List running processes"""
        self._log_action(result, "list_processes", "Listing processes")
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                info = proc.info
                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    status=info['status'],
                    cpu_percent=info['cpu_percent'] or 0,
                    memory_percent=info['memory_percent'] or 0,
                    created=datetime.fromtimestamp(info['create_time'])
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage and limit
        processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        return processes[:limit]
    
    # -------------------------
    # Tool Interface
    # -------------------------
    
    def get_tools(self) -> list[Tool]:
        """Get tools for LLM function calling"""
        return [
            Tool(
                name="os_read_file",
                description="Read content from a file",
                func=lambda path: self.read_file(path, self._create_result()),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="os_write_file",
                description="Write content to a file",
                func=lambda path, content: self.write_file(path, content, self._create_result()),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            ),
            Tool(
                name="os_list_directory",
                description="List files in a directory",
                func=lambda path=".": [f.to_dict() for f in self.list_directory(path, self._create_result())],
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"}
                    }
                }
            ),
            Tool(
                name="os_run_command",
                description="Run a shell command",
                func=lambda cmd: self.run_command(cmd, self._create_result()).__dict__,
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"}
                    },
                    "required": ["command"]
                }
            ),
            Tool(
                name="os_system_info",
                description="Get system information (CPU, memory, disk)",
                func=lambda: self.get_system_info(self._create_result()),
                parameters={"type": "object", "properties": {}}
            ),
        ]

