"""
Agent OS 运行时
"""
import logging
import platform
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from .config import AgentConfig, SecurityLevel

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """操作结果"""
    success: bool
    action: str
    message: str
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Runtime:
    """
    Agent OS 运行时环境
    
    提供系统操作的底层接口
    """
    
    # 危险命令列表
    DANGEROUS_COMMANDS = [
        "rm -rf /", "rm -rf /*", "del /f /s /q c:\\",
        "format", "mkfs", "dd if=", ":(){ :|:& };:",
        "shutdown", "reboot", "halt", "poweroff",
    ]
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.platform = platform.system()
        self._action_log: List[Dict] = []
        
        # 初始化平台特定设置
        self._init_platform()
    
    def _init_platform(self) -> None:
        """初始化平台设置"""
        self.is_windows = self.platform == "Windows"
        self.is_macos = self.platform == "Darwin"
        self.is_linux = self.platform == "Linux"
        
        # 检测可用工具
        self._check_tools()
    
    def _check_tools(self) -> None:
        """检测可用工具"""
        self.has_pyautogui = self._try_import("pyautogui")
        self.has_pyperclip = self._try_import("pyperclip")
        self.has_pillow = self._try_import("PIL")
        self.has_psutil = self._try_import("psutil")
    
    def _try_import(self, module: str) -> bool:
        """尝试导入模块"""
        try:
            __import__(module)
            return True
        except ImportError:
            return False
    
    def check_permission(self, path: str, operation: str = "read") -> bool:
        """检查路径权限"""
        return self.config.is_path_allowed(path)
    
    def check_command_safety(self, command: str) -> tuple[bool, str]:
        """检查命令安全性"""
        cmd_lower = command.lower()
        
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in cmd_lower:
                return False, f"危险命令被阻止: {dangerous}"
        
        for blocked in self.config.blocked_operations:
            if blocked.lower() in cmd_lower:
                return False, f"操作被配置阻止: {blocked}"
        
        return True, ""
    
    def log_action(self, action: str, message: str, **extra) -> None:
        """记录操作"""
        if not self.config.log_actions:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "message": message,
            "platform": self.platform,
            **extra,
        }
        self._action_log.append(log_entry)
        logger.info(f"[Agent OS] {action}: {message}")
    
    def get_action_log(self) -> List[Dict]:
        """获取操作日志"""
        return self._action_log.copy()
    
    def clear_action_log(self) -> None:
        """清除操作日志"""
        self._action_log.clear()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
            },
        }
        
        if self.has_psutil:
            import psutil
            
            info["cpu"] = {
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=0.5),
            }
            
            freq = psutil.cpu_freq()
            if freq:
                info["cpu"]["frequency_mhz"] = round(freq.current)
            
            mem = psutil.virtual_memory()
            info["memory"] = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_percent": mem.percent,
            }
            
            disk_path = "C:\\" if self.is_windows else "/"
            disk = psutil.disk_usage(disk_path)
            info["disk"] = {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": disk.percent,
            }
            
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info["battery"] = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                    }
            except:
                pass
        
        return info
    
    def get_environment(self) -> Dict[str, str]:
        """获取环境变量"""
        return dict(os.environ)

