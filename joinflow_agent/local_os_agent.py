"""
Local OS Agent - 本地操作系统控制
===================================

提供对本地操作系统的完整控制能力：
- 文件系统操作（全系统范围）
- 应用程序管理（打开、关闭应用）
- 系统控制（截屏、剪贴板、通知）
- 自动化操作（鼠标、键盘模拟）

⚠️ 安全警告：此模块需要用户明确授权才能启用
"""

import os
import sys
import platform
import subprocess
import shutil
import logging
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class OSPlatform(Enum):
    """操作系统平台"""
    WINDOWS = "Windows"
    MACOS = "Darwin"
    LINUX = "Linux"
    UNKNOWN = "Unknown"


class PermissionLevel(Enum):
    """权限级别"""
    NONE = 0          # 无权限
    READONLY = 1      # 只读
    WORKSPACE = 2     # 仅workspace
    AUTHORIZED = 3    # 用户授权（全系统）


@dataclass
class LocalOSConfig:
    """本地OS Agent配置"""
    permission_level: PermissionLevel = PermissionLevel.WORKSPACE
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    allowed_commands: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=list)
    require_confirmation: bool = True  # 危险操作需要确认
    log_all_actions: bool = True       # 记录所有操作
    max_file_size_mb: int = 100        # 最大文件大小
    command_timeout: int = 120         # 命令超时（秒）


@dataclass
class ActionResult:
    """操作结果"""
    success: bool
    action: str
    message: str
    data: Any = None
    platform: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        self.platform = platform.system()
        self.timestamp = datetime.now().isoformat()


class LocalOSAgent:
    """
    本地操作系统Agent
    
    支持 Windows、macOS、Linux 三大平台
    需要用户明确授权后才能执行系统级操作
    """
    
    # 默认危险命令（跨平台）
    DANGEROUS_COMMANDS = [
        # 通用危险命令
        "rm -rf /", "rm -rf /*", ":(){ :|:& };:",
        # Windows
        "format", "del /f /s /q c:\\", "rd /s /q c:\\",
        # Linux/Mac
        "dd if=", "mkfs", "chmod -R 777 /",
        # 关机/重启
        "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6"
    ]
    
    # 敏感路径
    SENSITIVE_PATHS = {
        "Windows": [
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64",
            "C:\\Program Files",
        ],
        "Darwin": [  # macOS
            "/System",
            "/usr/bin",
            "/sbin",
        ],
        "Linux": [
            "/etc/passwd",
            "/etc/shadow",
            "/usr/bin",
            "/sbin",
        ]
    }
    
    def __init__(self, config: Optional[LocalOSConfig] = None):
        self.config = config or LocalOSConfig()
        self.platform = self._detect_platform()
        self._authorized = False
        self._action_log: List[Dict] = []
        
        # 平台特定初始化
        self._init_platform_tools()
        
        logger.info(f"LocalOSAgent initialized on {self.platform.value}")
    
    def _detect_platform(self) -> OSPlatform:
        """检测当前操作系统"""
        system = platform.system()
        return {
            "Windows": OSPlatform.WINDOWS,
            "Darwin": OSPlatform.MACOS,
            "Linux": OSPlatform.LINUX,
        }.get(system, OSPlatform.UNKNOWN)
    
    def _init_platform_tools(self):
        """初始化平台特定工具"""
        self._has_pyautogui = False
        self._has_pillow = False
        self._has_pyperclip = False
        
        try:
            import pyautogui
            self._has_pyautogui = True
        except ImportError:
            logger.warning("pyautogui not installed - mouse/keyboard control disabled")
        
        try:
            from PIL import Image
            self._has_pillow = True
        except ImportError:
            logger.warning("Pillow not installed - screenshot functionality limited")
        
        try:
            import pyperclip
            self._has_pyperclip = True
        except ImportError:
            logger.warning("pyperclip not installed - clipboard functionality limited")
    
    # =====================
    # 授权管理
    # =====================
    
    def request_authorization(self, scope: str = "full") -> Dict:
        """
        请求用户授权
        
        Args:
            scope: 授权范围 ("readonly", "workspace", "full")
        
        Returns:
            授权请求信息，需要用户确认
        """
        scopes = {
            "readonly": PermissionLevel.READONLY,
            "workspace": PermissionLevel.WORKSPACE,
            "full": PermissionLevel.AUTHORIZED
        }
        
        requested_level = scopes.get(scope, PermissionLevel.WORKSPACE)
        
        warnings = []
        if requested_level == PermissionLevel.AUTHORIZED:
            warnings = [
                "⚠️ 完整系统授权将允许AI执行以下操作：",
                "  - 读写系统任意文件",
                "  - 执行任意Shell命令",
                "  - 启动和关闭应用程序",
                "  - 控制鼠标和键盘",
                "  - 访问剪贴板内容",
                "",
                "🔒 安全建议：",
                "  - 仅在受信任环境下授权",
                "  - 定期检查操作日志",
                "  - 敏感数据请勿暴露"
            ]
        
        return {
            "authorization_request": True,
            "scope": scope,
            "permission_level": requested_level.value,
            "platform": self.platform.value,
            "warnings": warnings,
            "message": f"请确认是否授权 JoinFlow OS Agent 获取 '{scope}' 级别权限？"
        }
    
    def authorize(self, level: PermissionLevel = PermissionLevel.AUTHORIZED) -> ActionResult:
        """用户确认授权"""
        self.config.permission_level = level
        self._authorized = (level == PermissionLevel.AUTHORIZED)
        
        self._log_action("authorize", f"Authorization granted: {level.name}")
        
        return ActionResult(
            success=True,
            action="authorize",
            message=f"授权成功！权限级别: {level.name}",
            data={"permission_level": level.value}
        )
    
    def revoke_authorization(self) -> ActionResult:
        """撤销授权"""
        self.config.permission_level = PermissionLevel.WORKSPACE
        self._authorized = False
        
        self._log_action("revoke", "Authorization revoked")
        
        return ActionResult(
            success=True,
            action="revoke_authorization",
            message="授权已撤销，恢复为workspace权限"
        )
    
    def is_authorized(self) -> bool:
        """检查是否已授权"""
        return self._authorized
    
    # =====================
    # 文件系统操作
    # =====================
    
    def read_file(self, path: str, encoding: str = "utf-8") -> ActionResult:
        """读取文件"""
        try:
            self._check_permission(path, "read")
            
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                return ActionResult(False, "read_file", f"文件不存在: {path}")
            
            if file_path.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
                return ActionResult(False, "read_file", f"文件过大，超过 {self.config.max_file_size_mb}MB 限制")
            
            content = file_path.read_text(encoding=encoding)
            
            self._log_action("read_file", f"Read: {path}", {"size": len(content)})
            
            return ActionResult(
                success=True,
                action="read_file",
                message=f"成功读取文件: {path}",
                data={"path": str(file_path), "content": content, "size": len(content)}
            )
            
        except Exception as e:
            return ActionResult(False, "read_file", f"读取文件失败: {e}")
    
    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> ActionResult:
        """写入文件"""
        try:
            self._check_permission(path, "write")
            
            file_path = Path(path).expanduser().resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(content, encoding=encoding)
            
            self._log_action("write_file", f"Write: {path}", {"size": len(content)})
            
            return ActionResult(
                success=True,
                action="write_file",
                message=f"成功写入文件: {path}",
                data={"path": str(file_path), "size": len(content)}
            )
            
        except Exception as e:
            return ActionResult(False, "write_file", f"写入文件失败: {e}")
    
    def list_directory(self, path: str = ".", include_hidden: bool = False) -> ActionResult:
        """列出目录内容"""
        try:
            self._check_permission(path, "read")
            
            dir_path = Path(path).expanduser().resolve()
            
            if not dir_path.exists():
                return ActionResult(False, "list_directory", f"目录不存在: {path}")
            
            items = []
            for item in dir_path.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return ActionResult(
                success=True,
                action="list_directory",
                message=f"列出目录: {path} ({len(items)} 项)",
                data={"path": str(dir_path), "items": items}
            )
            
        except Exception as e:
            return ActionResult(False, "list_directory", f"列出目录失败: {e}")
    
    def create_directory(self, path: str) -> ActionResult:
        """创建目录"""
        try:
            self._check_permission(path, "write")
            
            dir_path = Path(path).expanduser().resolve()
            dir_path.mkdir(parents=True, exist_ok=True)
            
            self._log_action("create_directory", f"Created: {path}")
            
            return ActionResult(
                success=True,
                action="create_directory",
                message=f"目录已创建: {path}",
                data={"path": str(dir_path)}
            )
            
        except Exception as e:
            return ActionResult(False, "create_directory", f"创建目录失败: {e}")
    
    def delete_path(self, path: str) -> ActionResult:
        """删除文件或目录"""
        try:
            self._check_permission(path, "write")
            
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return ActionResult(False, "delete", f"路径不存在: {path}")
            
            if self.config.require_confirmation:
                # 返回确认请求
                return ActionResult(
                    success=True,
                    action="delete_confirm",
                    message=f"确认删除: {path}？",
                    data={"path": str(target), "is_dir": target.is_dir(), "needs_confirmation": True}
                )
            
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            
            self._log_action("delete", f"Deleted: {path}")
            
            return ActionResult(
                success=True,
                action="delete",
                message=f"已删除: {path}"
            )
            
        except Exception as e:
            return ActionResult(False, "delete", f"删除失败: {e}")
    
    def copy_path(self, src: str, dst: str) -> ActionResult:
        """复制文件或目录"""
        try:
            self._check_permission(src, "read")
            self._check_permission(dst, "write")
            
            src_path = Path(src).expanduser().resolve()
            dst_path = Path(dst).expanduser().resolve()
            
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            self._log_action("copy", f"Copied: {src} -> {dst}")
            
            return ActionResult(
                success=True,
                action="copy",
                message=f"复制成功: {src} -> {dst}"
            )
            
        except Exception as e:
            return ActionResult(False, "copy", f"复制失败: {e}")
    
    def move_path(self, src: str, dst: str) -> ActionResult:
        """移动/重命名文件或目录"""
        try:
            self._check_permission(src, "write")
            self._check_permission(dst, "write")
            
            src_path = Path(src).expanduser().resolve()
            dst_path = Path(dst).expanduser().resolve()
            
            shutil.move(str(src_path), str(dst_path))
            
            self._log_action("move", f"Moved: {src} -> {dst}")
            
            return ActionResult(
                success=True,
                action="move",
                message=f"移动成功: {src} -> {dst}"
            )
            
        except Exception as e:
            return ActionResult(False, "move", f"移动失败: {e}")
    
    # =====================
    # 命令执行
    # =====================
    
    def run_command(self, command: str, working_dir: Optional[str] = None) -> ActionResult:
        """执行Shell命令"""
        try:
            # 安全检查
            self._check_permission(working_dir or ".", "execute")
            self._check_command_safety(command)
            
            cwd = Path(working_dir).expanduser().resolve() if working_dir else None
            
            self._log_action("run_command", f"Executing: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout,
                cwd=cwd
            )
            
            return ActionResult(
                success=(result.returncode == 0),
                action="run_command",
                message=f"命令执行完成 (返回码: {result.returncode})",
                data={
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )
            
        except subprocess.TimeoutExpired:
            return ActionResult(False, "run_command", f"命令执行超时 ({self.config.command_timeout}秒)")
        except Exception as e:
            return ActionResult(False, "run_command", f"命令执行失败: {e}")
    
    # =====================
    # 应用程序管理
    # =====================
    
    def open_application(self, app_name: str) -> ActionResult:
        """打开应用程序"""
        try:
            self._check_permission(".", "execute")
            
            if self.platform == OSPlatform.WINDOWS:
                # Windows: 使用 start 命令
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                
            elif self.platform == OSPlatform.MACOS:
                # macOS: 使用 open 命令
                subprocess.Popen(['open', '-a', app_name])
                
            elif self.platform == OSPlatform.LINUX:
                # Linux: 直接运行或使用 xdg-open
                subprocess.Popen([app_name], start_new_session=True)
            
            self._log_action("open_application", f"Opened: {app_name}")
            
            return ActionResult(
                success=True,
                action="open_application",
                message=f"已打开应用: {app_name}"
            )
            
        except Exception as e:
            return ActionResult(False, "open_application", f"打开应用失败: {e}")
    
    def open_file_with_default_app(self, file_path: str) -> ActionResult:
        """使用默认程序打开文件"""
        try:
            self._check_permission(file_path, "read")
            
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return ActionResult(False, "open_file", f"文件不存在: {file_path}")
            
            if self.platform == OSPlatform.WINDOWS:
                os.startfile(str(path))
            elif self.platform == OSPlatform.MACOS:
                subprocess.Popen(['open', str(path)])
            elif self.platform == OSPlatform.LINUX:
                subprocess.Popen(['xdg-open', str(path)])
            
            self._log_action("open_file", f"Opened: {file_path}")
            
            return ActionResult(
                success=True,
                action="open_file",
                message=f"已打开文件: {file_path}"
            )
            
        except Exception as e:
            return ActionResult(False, "open_file", f"打开文件失败: {e}")
    
    def open_url(self, url: str) -> ActionResult:
        """在浏览器中打开URL"""
        try:
            import webbrowser
            webbrowser.open(url)
            
            self._log_action("open_url", f"Opened: {url}")
            
            return ActionResult(
                success=True,
                action="open_url",
                message=f"已在浏览器中打开: {url}"
            )
            
        except Exception as e:
            return ActionResult(False, "open_url", f"打开URL失败: {e}")
    
    def get_running_processes(self, name_filter: Optional[str] = None) -> ActionResult:
        """获取运行中的进程"""
        try:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if name_filter and name_filter.lower() not in info['name'].lower():
                        continue
                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu_percent": info['cpu_percent'],
                        "memory_percent": round(info['memory_percent'] or 0, 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 按内存使用排序
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return ActionResult(
                success=True,
                action="get_processes",
                message=f"获取到 {len(processes)} 个进程",
                data={"processes": processes[:50]}  # 限制返回前50个
            )
            
        except Exception as e:
            return ActionResult(False, "get_processes", f"获取进程失败: {e}")
    
    def kill_process(self, pid: int) -> ActionResult:
        """终止进程"""
        try:
            self._check_permission(".", "execute")
            
            import psutil
            
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            if self.config.require_confirmation:
                return ActionResult(
                    success=True,
                    action="kill_process_confirm",
                    message=f"确认终止进程: {proc_name} (PID: {pid})？",
                    data={"pid": pid, "name": proc_name, "needs_confirmation": True}
                )
            
            proc.terminate()
            
            self._log_action("kill_process", f"Killed: {proc_name} (PID: {pid})")
            
            return ActionResult(
                success=True,
                action="kill_process",
                message=f"已终止进程: {proc_name} (PID: {pid})"
            )
            
        except Exception as e:
            return ActionResult(False, "kill_process", f"终止进程失败: {e}")
    
    # =====================
    # 系统工具
    # =====================
    
    def take_screenshot(self, save_path: Optional[str] = None) -> ActionResult:
        """截取屏幕"""
        try:
            if not self._has_pillow:
                return ActionResult(False, "screenshot", "需要安装 Pillow: pip install Pillow")
            
            if not self._has_pyautogui:
                # 尝试平台特定方法
                return self._take_screenshot_native(save_path)
            
            import pyautogui
            
            screenshot = pyautogui.screenshot()
            
            if save_path:
                path = Path(save_path).expanduser().resolve()
                screenshot.save(str(path))
                
                self._log_action("screenshot", f"Saved to: {path}")
                
                return ActionResult(
                    success=True,
                    action="screenshot",
                    message=f"截图已保存: {path}",
                    data={"path": str(path)}
                )
            else:
                # 保存到临时文件
                temp_path = Path(tempfile.gettempdir()) / f"screenshot_{int(time.time())}.png"
                screenshot.save(str(temp_path))
                
                return ActionResult(
                    success=True,
                    action="screenshot",
                    message=f"截图已保存: {temp_path}",
                    data={"path": str(temp_path)}
                )
            
        except Exception as e:
            return ActionResult(False, "screenshot", f"截图失败: {e}")
    
    def _take_screenshot_native(self, save_path: Optional[str] = None) -> ActionResult:
        """使用原生方法截图"""
        try:
            temp_path = save_path or str(Path(tempfile.gettempdir()) / f"screenshot_{int(time.time())}.png")
            
            if self.platform == OSPlatform.WINDOWS:
                # Windows: 使用 PowerShell
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {{
                    $bitmap = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height)
                    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                    $graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size)
                    $bitmap.Save("{temp_path}")
                }}
                '''
                subprocess.run(["powershell", "-Command", ps_script], check=True)
                
            elif self.platform == OSPlatform.MACOS:
                subprocess.run(["screencapture", "-x", temp_path], check=True)
                
            elif self.platform == OSPlatform.LINUX:
                # 尝试使用 scrot 或 gnome-screenshot
                try:
                    subprocess.run(["scrot", temp_path], check=True)
                except:
                    subprocess.run(["gnome-screenshot", "-f", temp_path], check=True)
            
            return ActionResult(
                success=True,
                action="screenshot",
                message=f"截图已保存: {temp_path}",
                data={"path": temp_path}
            )
            
        except Exception as e:
            return ActionResult(False, "screenshot", f"原生截图失败: {e}")
    
    def get_clipboard(self) -> ActionResult:
        """获取剪贴板内容"""
        try:
            if self._has_pyperclip:
                import pyperclip
                content = pyperclip.paste()
            else:
                # 平台特定方法
                if self.platform == OSPlatform.WINDOWS:
                    result = subprocess.run(["powershell", "-Command", "Get-Clipboard"], 
                                          capture_output=True, text=True)
                    content = result.stdout.strip()
                elif self.platform == OSPlatform.MACOS:
                    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                    content = result.stdout
                else:
                    result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                          capture_output=True, text=True)
                    content = result.stdout
            
            return ActionResult(
                success=True,
                action="get_clipboard",
                message="获取剪贴板成功",
                data={"content": content}
            )
            
        except Exception as e:
            return ActionResult(False, "get_clipboard", f"获取剪贴板失败: {e}")
    
    def set_clipboard(self, content: str) -> ActionResult:
        """设置剪贴板内容"""
        try:
            if self._has_pyperclip:
                import pyperclip
                pyperclip.copy(content)
            else:
                # 平台特定方法
                if self.platform == OSPlatform.WINDOWS:
                    subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{content}'"])
                elif self.platform == OSPlatform.MACOS:
                    process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                    process.communicate(content.encode())
                else:
                    process = subprocess.Popen(["xclip", "-selection", "clipboard"],
                                             stdin=subprocess.PIPE)
                    process.communicate(content.encode())
            
            self._log_action("set_clipboard", f"Set clipboard: {len(content)} chars")
            
            return ActionResult(
                success=True,
                action="set_clipboard",
                message="剪贴板已设置"
            )
            
        except Exception as e:
            return ActionResult(False, "set_clipboard", f"设置剪贴板失败: {e}")
    
    def show_notification(self, title: str, message: str) -> ActionResult:
        """显示系统通知"""
        try:
            if self.platform == OSPlatform.WINDOWS:
                # Windows Toast 通知
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) | Out-Null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("JoinFlow").Show($toast)
                '''
                subprocess.run(["powershell", "-Command", ps_script])
                
            elif self.platform == OSPlatform.MACOS:
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ])
                
            elif self.platform == OSPlatform.LINUX:
                subprocess.run(["notify-send", title, message])
            
            return ActionResult(
                success=True,
                action="notification",
                message=f"通知已发送: {title}"
            )
            
        except Exception as e:
            return ActionResult(False, "notification", f"发送通知失败: {e}")
    
    def get_system_info(self) -> ActionResult:
        """获取系统信息"""
        try:
            import psutil
            
            info = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "hostname": platform.node()
                },
                "cpu": {
                    "cores_physical": psutil.cpu_count(logical=False),
                    "cores_logical": psutil.cpu_count(logical=True),
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None
                },
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "used_percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                    "used_percent": psutil.disk_usage('/').percent
                }
            }
            
            return ActionResult(
                success=True,
                action="system_info",
                message="获取系统信息成功",
                data=info
            )
            
        except Exception as e:
            return ActionResult(False, "system_info", f"获取系统信息失败: {e}")
    
    # =====================
    # 鼠标键盘控制
    # =====================
    
    def type_text(self, text: str, interval: float = 0.05) -> ActionResult:
        """模拟键盘输入"""
        try:
            if not self._has_pyautogui:
                return ActionResult(False, "type_text", "需要安装 pyautogui: pip install pyautogui")
            
            self._check_permission(".", "execute")
            
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
            
            self._log_action("type_text", f"Typed: {len(text)} chars")
            
            return ActionResult(
                success=True,
                action="type_text",
                message=f"已输入 {len(text)} 个字符"
            )
            
        except Exception as e:
            return ActionResult(False, "type_text", f"输入失败: {e}")
    
    def press_key(self, key: str) -> ActionResult:
        """模拟按键"""
        try:
            if not self._has_pyautogui:
                return ActionResult(False, "press_key", "需要安装 pyautogui: pip install pyautogui")
            
            self._check_permission(".", "execute")
            
            import pyautogui
            pyautogui.press(key)
            
            self._log_action("press_key", f"Pressed: {key}")
            
            return ActionResult(
                success=True,
                action="press_key",
                message=f"已按下: {key}"
            )
            
        except Exception as e:
            return ActionResult(False, "press_key", f"按键失败: {e}")
    
    def hotkey(self, *keys) -> ActionResult:
        """模拟组合键"""
        try:
            if not self._has_pyautogui:
                return ActionResult(False, "hotkey", "需要安装 pyautogui: pip install pyautogui")
            
            self._check_permission(".", "execute")
            
            import pyautogui
            pyautogui.hotkey(*keys)
            
            key_combo = "+".join(keys)
            self._log_action("hotkey", f"Hotkey: {key_combo}")
            
            return ActionResult(
                success=True,
                action="hotkey",
                message=f"已执行组合键: {key_combo}"
            )
            
        except Exception as e:
            return ActionResult(False, "hotkey", f"组合键失败: {e}")
    
    def mouse_click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """模拟鼠标点击"""
        try:
            if not self._has_pyautogui:
                return ActionResult(False, "mouse_click", "需要安装 pyautogui: pip install pyautogui")
            
            self._check_permission(".", "execute")
            
            import pyautogui
            pyautogui.click(x, y, button=button)
            
            self._log_action("mouse_click", f"Click: ({x}, {y}) {button}")
            
            return ActionResult(
                success=True,
                action="mouse_click",
                message=f"已点击: ({x}, {y})"
            )
            
        except Exception as e:
            return ActionResult(False, "mouse_click", f"点击失败: {e}")
    
    def mouse_move(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """移动鼠标"""
        try:
            if not self._has_pyautogui:
                return ActionResult(False, "mouse_move", "需要安装 pyautogui: pip install pyautogui")
            
            import pyautogui
            pyautogui.moveTo(x, y, duration=duration)
            
            return ActionResult(
                success=True,
                action="mouse_move",
                message=f"鼠标已移动到: ({x}, {y})"
            )
            
        except Exception as e:
            return ActionResult(False, "mouse_move", f"移动鼠标失败: {e}")
    
    # =====================
    # 内部方法
    # =====================
    
    def _check_permission(self, path: str, operation: str) -> None:
        """检查权限"""
        if self.config.permission_level == PermissionLevel.NONE:
            raise PermissionError("无权限执行此操作")
        
        if self.config.permission_level == PermissionLevel.READONLY and operation != "read":
            raise PermissionError("只读模式，无法执行写入操作")
        
        if self.config.permission_level != PermissionLevel.AUTHORIZED:
            # 检查是否在允许的路径内
            resolved = Path(path).expanduser().resolve()
            
            # 检查敏感路径
            sensitive = self.SENSITIVE_PATHS.get(self.platform.value, [])
            for s_path in sensitive:
                if str(resolved).startswith(s_path):
                    raise PermissionError(f"访问受限路径: {path}")
    
    def _check_command_safety(self, command: str) -> None:
        """检查命令安全性"""
        cmd_lower = command.lower()
        
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in cmd_lower:
                raise PermissionError(f"危险命令被阻止: {command}")
        
        # 检查配置的阻止命令
        for blocked in self.config.blocked_commands:
            if blocked.lower() in cmd_lower:
                raise PermissionError(f"命令被配置阻止: {command}")
    
    def _log_action(self, action: str, message: str, extra: Optional[Dict] = None) -> None:
        """记录操作"""
        if self.config.log_all_actions:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "message": message,
                "platform": self.platform.value,
                **(extra or {})
            }
            self._action_log.append(log_entry)
            logger.info(f"[LocalOS] {action}: {message}")
    
    def get_action_log(self) -> List[Dict]:
        """获取操作日志"""
        return self._action_log.copy()
    
    def clear_action_log(self) -> None:
        """清除操作日志"""
        self._action_log.clear()


# =====================
# 便捷函数
# =====================

def create_local_os_agent(authorized: bool = False) -> LocalOSAgent:
    """
    创建本地OS Agent
    
    Args:
        authorized: 是否自动授权（仅在用户明确同意时使用）
    """
    config = LocalOSConfig(
        permission_level=PermissionLevel.AUTHORIZED if authorized else PermissionLevel.WORKSPACE,
        require_confirmation=not authorized
    )
    agent = LocalOSAgent(config)
    
    if authorized:
        agent.authorize(PermissionLevel.AUTHORIZED)
    
    return agent

