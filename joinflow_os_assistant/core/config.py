"""
助手配置模块
"""
import os
import json
import platform
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum


class PermissionLevel(Enum):
    """权限级别"""
    RESTRICTED = 1    # 受限模式（仅工作空间）
    STANDARD = 2      # 标准模式（用户目录）
    ELEVATED = 3      # 提升模式（全系统用户级）


class OSType(Enum):
    """操作系统类型"""
    WINDOWS = "Windows"
    MACOS = "Darwin"
    LINUX = "Linux"
    UNKNOWN = "Unknown"


@dataclass
class AssistantConfig:
    """智能助手配置"""
    
    # 权限设置
    permission_level: PermissionLevel = PermissionLevel.STANDARD
    require_confirmation: bool = True  # 危险操作需要确认
    
    # 工作目录
    workspace_dir: str = field(default_factory=lambda: str(Path.cwd() / "workspace"))
    
    # 用户目录（根据系统自动设置）
    user_home: str = field(default_factory=lambda: str(Path.home()))
    
    # 搜索设置
    max_search_results: int = 100
    search_timeout: int = 30  # 秒
    indexed_locations: List[str] = field(default_factory=list)
    
    # 文件操作设置
    max_file_size_mb: int = 100
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".txt", ".md", ".json", ".xml", ".csv", ".log",
        ".py", ".js", ".html", ".css", ".yml", ".yaml",
        ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
        ".mp3", ".mp4", ".avi", ".mov", ".zip", ".rar", ".7z"
    ])
    
    # 命令执行设置
    command_timeout: int = 120  # 秒
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf /", "format c:", "del /f /s /q c:\\",
        "shutdown", "reboot", "dd if=", "mkfs"
    ])
    
    # LLM 设置
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    
    # 记忆设置
    enable_memory: bool = True
    memory_size: int = 100  # 最大记忆条数
    
    # 日志设置
    log_all_actions: bool = True
    log_file: str = "os_assistant.log"
    
    @classmethod
    def from_file(cls, path: str) -> "AssistantConfig":
        """从文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理枚举类型
        if 'permission_level' in data:
            data['permission_level'] = PermissionLevel[data['permission_level'].upper()]
        
        return cls(**data)
    
    def to_file(self, path: str) -> None:
        """保存配置到文件"""
        data = {
            'permission_level': self.permission_level.name,
            'require_confirmation': self.require_confirmation,
            'workspace_dir': self.workspace_dir,
            'max_search_results': self.max_search_results,
            'search_timeout': self.search_timeout,
            'max_file_size_mb': self.max_file_size_mb,
            'command_timeout': self.command_timeout,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'enable_memory': self.enable_memory,
            'log_all_actions': self.log_all_actions,
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_os_type() -> OSType:
        """获取当前操作系统类型"""
        system = platform.system()
        return {
            "Windows": OSType.WINDOWS,
            "Darwin": OSType.MACOS,
            "Linux": OSType.LINUX,
        }.get(system, OSType.UNKNOWN)
    
    def get_default_locations(self) -> List[str]:
        """获取默认搜索位置"""
        os_type = self.get_os_type()
        home = Path(self.user_home)
        
        if os_type == OSType.WINDOWS:
            return [
                str(home / "Desktop"),
                str(home / "Documents"),
                str(home / "Downloads"),
                str(home / "Pictures"),
                str(home / "Videos"),
                str(home / "Music"),
            ]
        elif os_type == OSType.MACOS:
            return [
                str(home / "Desktop"),
                str(home / "Documents"),
                str(home / "Downloads"),
                str(home / "Pictures"),
                str(home / "Movies"),
                str(home / "Music"),
            ]
        else:  # Linux
            return [
                str(home / "Desktop"),
                str(home / "Documents"),
                str(home / "Downloads"),
                str(home / "Pictures"),
                str(home / "Videos"),
                str(home / "Music"),
            ]
    
    def is_path_allowed(self, path: str) -> bool:
        """检查路径是否允许访问"""
        path_obj = Path(path).resolve()
        
        if self.permission_level == PermissionLevel.RESTRICTED:
            # 仅允许工作空间
            workspace = Path(self.workspace_dir).resolve()
            try:
                path_obj.relative_to(workspace)
                return True
            except ValueError:
                return False
        
        elif self.permission_level == PermissionLevel.STANDARD:
            # 允许用户目录
            home = Path(self.user_home).resolve()
            workspace = Path(self.workspace_dir).resolve()
            try:
                path_obj.relative_to(home)
                return True
            except ValueError:
                pass
            try:
                path_obj.relative_to(workspace)
                return True
            except ValueError:
                return False
        
        else:  # ELEVATED
            # 允许全系统用户级别（排除系统目录）
            system_dirs = self._get_system_dirs()
            for sys_dir in system_dirs:
                if str(path_obj).startswith(sys_dir):
                    return False
            return True
    
    def _get_system_dirs(self) -> List[str]:
        """获取系统受保护目录"""
        os_type = self.get_os_type()
        
        if os_type == OSType.WINDOWS:
            return [
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                "C:\\ProgramData",
            ]
        elif os_type == OSType.MACOS:
            return [
                "/System",
                "/Library",
                "/usr",
                "/bin",
                "/sbin",
                "/private",
            ]
        else:  # Linux
            return [
                "/etc",
                "/usr",
                "/bin",
                "/sbin",
                "/lib",
                "/lib64",
                "/boot",
                "/root",
            ]

