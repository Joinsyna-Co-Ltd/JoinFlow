"""
Agent OS 配置
"""
import os
import json
import platform
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum


class SecurityLevel(Enum):
    """安全级别"""
    SANDBOX = 1      # 沙箱模式（仅工作目录）
    USER = 2         # 用户模式（用户目录）
    SYSTEM = 3       # 系统模式（全系统）


class AgentMode(Enum):
    """代理模式"""
    INTERACTIVE = "interactive"  # 交互模式
    AUTONOMOUS = "autonomous"    # 自主模式
    SUPERVISED = "supervised"    # 监督模式


@dataclass
class AgentConfig:
    """Agent OS 配置"""
    
    # 基本设置
    name: str = "Agent OS"
    version: str = "2.0.0"
    
    # 安全设置
    security_level: SecurityLevel = SecurityLevel.USER
    require_confirmation: bool = True
    allowed_operations: List[str] = field(default_factory=list)
    blocked_operations: List[str] = field(default_factory=list)
    
    # 工作目录
    workspace: str = field(default_factory=lambda: str(Path.cwd() / "workspace"))
    home_dir: str = field(default_factory=lambda: str(Path.home()))
    
    # LLM设置
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    
    # 运行设置
    mode: AgentMode = AgentMode.INTERACTIVE
    max_retries: int = 3
    timeout: int = 120
    parallel_tasks: int = 4
    
    # 记忆设置
    enable_memory: bool = True
    memory_file: str = field(default_factory=lambda: str(Path.home() / ".agent_os" / "memory.json"))
    max_memory_items: int = 1000
    
    # 日志设置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_actions: bool = True
    
    # UI设置
    theme: str = "dark"  # dark, light, auto
    language: str = "zh-CN"
    
    @classmethod
    def load(cls, path: str) -> "AgentConfig":
        """从文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'security_level' in data:
            data['security_level'] = SecurityLevel[data['security_level'].upper()]
        if 'mode' in data:
            data['mode'] = AgentMode[data['mode'].upper()]
        
        return cls(**data)
    
    def save(self, path: str) -> None:
        """保存配置到文件"""
        data = {
            'name': self.name,
            'version': self.version,
            'security_level': self.security_level.name,
            'require_confirmation': self.require_confirmation,
            'workspace': self.workspace,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'mode': self.mode.name,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'enable_memory': self.enable_memory,
            'theme': self.theme,
            'language': self.language,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_platform() -> str:
        """获取当前平台"""
        return platform.system()
    
    def is_path_allowed(self, path: str) -> bool:
        """检查路径是否允许访问"""
        path_obj = Path(path).resolve()
        
        if self.security_level == SecurityLevel.SANDBOX:
            workspace = Path(self.workspace).resolve()
            try:
                path_obj.relative_to(workspace)
                return True
            except ValueError:
                return False
        
        elif self.security_level == SecurityLevel.USER:
            home = Path(self.home_dir).resolve()
            workspace = Path(self.workspace).resolve()
            
            for allowed in [home, workspace]:
                try:
                    path_obj.relative_to(allowed)
                    return True
                except ValueError:
                    continue
            return False
        
        else:  # SYSTEM
            # 排除系统关键目录
            blocked = self._get_blocked_paths()
            for blocked_path in blocked:
                if str(path_obj).lower().startswith(blocked_path.lower()):
                    return False
            return True
    
    def _get_blocked_paths(self) -> List[str]:
        """获取受保护的系统路径"""
        system = platform.system()
        
        if system == "Windows":
            return [
                "C:\\Windows\\System32",
                "C:\\Windows\\SysWOW64",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
            ]
        elif system == "Darwin":
            return ["/System", "/usr", "/bin", "/sbin", "/private"]
        else:
            return ["/etc", "/usr", "/bin", "/sbin", "/boot", "/root"]

