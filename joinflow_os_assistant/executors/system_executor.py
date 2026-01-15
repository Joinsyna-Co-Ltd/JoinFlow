"""
系统执行器 - 处理系统级操作
"""
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from .base import BaseExecutor, ExecutorResult


class SystemExecutor(BaseExecutor):
    """
    系统执行器
    
    处理系统信息、剪贴板、截图、通知、命令执行等操作
    """
    
    name = "system"
    supported_operations = [
        "system.info", "system.screenshot", "system.notify",
        "clipboard.get", "clipboard.set",
        "command.execute", "script.execute",
        "system.env", "system.path",
    ]
    
    def __init__(self, config=None):
        super().__init__(config)
        self.system = platform.system()
        self.command_timeout = config.command_timeout if config else 120
        
        # 危险命令列表
        self.blocked_commands = [
            "rm -rf /", "rm -rf /*", "format c:", "del /f /s /q c:\\",
            "shutdown", "reboot", "halt", "poweroff",
            "dd if=", "mkfs", ":(){ :|:& };:",
        ]
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行系统操作"""
        try:
            if operation == "system.info":
                return self._system_info(parameters)
            elif operation == "system.screenshot":
                return self._screenshot(parameters)
            elif operation == "system.notify":
                return self._notify(parameters)
            elif operation == "clipboard.get":
                return self._clipboard_get(parameters)
            elif operation == "clipboard.set":
                return self._clipboard_set(parameters)
            elif operation == "command.execute":
                return self._execute_command(parameters)
            elif operation == "script.execute":
                return self._execute_script(parameters)
            elif operation == "system.env":
                return self._get_env(parameters)
            elif operation == "system.path":
                return self._get_path(parameters)
            else:
                return ExecutorResult(False, f"不支持的操作: {operation}")
        except Exception as e:
            return ExecutorResult(False, f"操作失败: {e}")
    
    def _system_info(self, params: Dict) -> ExecutorResult:
        """获取系统信息"""
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
            }
        }
        
        if has_psutil:
            # CPU信息
            info["cpu"] = {
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=1),
            }
            
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                info["cpu"]["frequency_mhz"] = round(cpu_freq.current)
            
            # 内存信息
            mem = psutil.virtual_memory()
            info["memory"] = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent,
            }
            
            # 磁盘信息
            if self.system == "Windows":
                disk_path = "C:\\"
            else:
                disk_path = "/"
            
            disk = psutil.disk_usage(disk_path)
            info["disk"] = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            }
            
            # 网络信息
            try:
                net = psutil.net_io_counters()
                info["network"] = {
                    "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
                }
            except:
                pass
            
            # 电池信息（笔记本）
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info["battery"] = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                        "seconds_left": battery.secsleft if battery.secsleft > 0 else None,
                    }
            except:
                pass
        
        return ExecutorResult(
            success=True,
            message="系统信息获取成功",
            data=info
        )
    
    def _screenshot(self, params: Dict) -> ExecutorResult:
        """截取屏幕"""
        save_path = params.get("path") or params.get("save_path")
        region = params.get("region")  # (x, y, width, height)
        
        # 生成默认路径
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(Path(tempfile.gettempdir()) / f"screenshot_{timestamp}.png")
        
        save_path = str(Path(save_path).expanduser())
        
        try:
            # 尝试使用 pyautogui
            try:
                import pyautogui
                
                if region:
                    screenshot = pyautogui.screenshot(region=region)
                else:
                    screenshot = pyautogui.screenshot()
                
                screenshot.save(save_path)
                
            except ImportError:
                # 使用系统命令
                if self.system == "Windows":
                    self._windows_screenshot(save_path)
                elif self.system == "Darwin":
                    subprocess.run(["screencapture", "-x", save_path], check=True)
                else:
                    # Linux - 尝试多种工具
                    for cmd in [
                        ["scrot", save_path],
                        ["gnome-screenshot", "-f", save_path],
                        ["import", "-window", "root", save_path],
                    ]:
                        try:
                            subprocess.run(cmd, check=True)
                            break
                        except:
                            continue
            
            self._log_action("screenshot", f"Saved to: {save_path}")
            
            return ExecutorResult(
                success=True,
                message=f"截图已保存: {save_path}",
                data={"path": save_path}
            )
            
        except Exception as e:
            return ExecutorResult(False, f"截图失败: {e}")
    
    def _windows_screenshot(self, save_path: str) -> None:
        """Windows系统截图"""
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
        $bitmap.Save("{save_path}")
        '''
        subprocess.run(["powershell", "-Command", ps_script], check=True)
    
    def _notify(self, params: Dict) -> ExecutorResult:
        """发送系统通知"""
        title = params.get("title", "JoinFlow")
        message = params.get("message") or params.get("content", "")
        
        if not message:
            return ExecutorResult(False, "缺少通知内容")
        
        try:
            if self.system == "Windows":
                # Windows Toast通知
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                except ImportError:
                    # 使用PowerShell
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
                    
            elif self.system == "Darwin":
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ])
                
            else:  # Linux
                subprocess.run(["notify-send", title, message])
            
            self._log_action("notify", f"Sent: {title}")
            
            return ExecutorResult(
                success=True,
                message="通知已发送",
                data={"title": title, "message": message}
            )
            
        except Exception as e:
            return ExecutorResult(False, f"发送通知失败: {e}")
    
    def _clipboard_get(self, params: Dict) -> ExecutorResult:
        """获取剪贴板内容"""
        try:
            try:
                import pyperclip
                content = pyperclip.paste()
            except ImportError:
                if self.system == "Windows":
                    result = subprocess.run(
                        ["powershell", "-Command", "Get-Clipboard"],
                        capture_output=True, text=True
                    )
                    content = result.stdout.strip()
                elif self.system == "Darwin":
                    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                    content = result.stdout
                else:
                    result = subprocess.run(
                        ["xclip", "-selection", "clipboard", "-o"],
                        capture_output=True, text=True
                    )
                    content = result.stdout
            
            return ExecutorResult(
                success=True,
                message="剪贴板内容获取成功",
                data={"content": content, "length": len(content)}
            )
            
        except Exception as e:
            return ExecutorResult(False, f"获取剪贴板失败: {e}")
    
    def _clipboard_set(self, params: Dict) -> ExecutorResult:
        """设置剪贴板内容"""
        content = params.get("content") or params.get("text", "")
        
        if not content:
            return ExecutorResult(False, "缺少要复制的内容")
        
        try:
            try:
                import pyperclip
                pyperclip.copy(content)
            except ImportError:
                if self.system == "Windows":
                    # 需要转义特殊字符
                    escaped = content.replace("'", "''")
                    subprocess.run(
                        ["powershell", "-Command", f"Set-Clipboard -Value '{escaped}'"]
                    )
                elif self.system == "Darwin":
                    process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                    process.communicate(content.encode())
                else:
                    process = subprocess.Popen(
                        ["xclip", "-selection", "clipboard"],
                        stdin=subprocess.PIPE
                    )
                    process.communicate(content.encode())
            
            self._log_action("clipboard_set", f"Set {len(content)} chars")
            
            return ExecutorResult(
                success=True,
                message="内容已复制到剪贴板",
                data={"length": len(content)}
            )
            
        except Exception as e:
            return ExecutorResult(False, f"设置剪贴板失败: {e}")
    
    def _execute_command(self, params: Dict) -> ExecutorResult:
        """执行Shell命令"""
        command = params.get("command") or params.get("cmd")
        working_dir = params.get("cwd") or params.get("working_dir")
        timeout = params.get("timeout", self.command_timeout)
        
        if not command:
            return ExecutorResult(False, "缺少命令参数")
        
        # 安全检查
        cmd_lower = command.lower()
        for blocked in self.blocked_commands:
            if blocked.lower() in cmd_lower:
                return ExecutorResult(
                    success=False,
                    message=f"命令被阻止（安全原因）: {command}",
                    error="BlockedCommand"
                )
        
        try:
            cwd = Path(working_dir).expanduser() if working_dir else None
            
            self._log_action("execute_command", f"Running: {command}")
            
            start_time = time.time()
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            duration = (time.time() - start_time) * 1000
            
            return ExecutorResult(
                success=(result.returncode == 0),
                message=f"命令执行完成 (返回码: {result.returncode})",
                data={
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "duration_ms": round(duration),
                },
                duration_ms=duration
            )
            
        except subprocess.TimeoutExpired:
            return ExecutorResult(False, f"命令执行超时 ({timeout}秒)")
        except Exception as e:
            return ExecutorResult(False, f"命令执行失败: {e}")
    
    def _execute_script(self, params: Dict) -> ExecutorResult:
        """执行脚本文件"""
        script_path = params.get("path") or params.get("script")
        script_type = params.get("type")  # python, bash, powershell, etc.
        args = params.get("args", [])
        
        if not script_path:
            return ExecutorResult(False, "缺少脚本路径")
        
        path = Path(script_path).expanduser()
        
        if not path.exists():
            return ExecutorResult(False, f"脚本不存在: {script_path}")
        
        # 自动检测脚本类型
        if not script_type:
            ext = path.suffix.lower()
            type_map = {
                ".py": "python",
                ".sh": "bash",
                ".ps1": "powershell",
                ".bat": "batch",
                ".cmd": "batch",
                ".js": "node",
            }
            script_type = type_map.get(ext, "bash")
        
        # 构建命令
        if script_type == "python":
            cmd = ["python", str(path)] + args
        elif script_type == "bash":
            cmd = ["bash", str(path)] + args
        elif script_type == "powershell":
            cmd = ["powershell", "-File", str(path)] + args
        elif script_type == "batch":
            cmd = [str(path)] + args
        elif script_type == "node":
            cmd = ["node", str(path)] + args
        else:
            cmd = [str(path)] + args
        
        try:
            self._log_action("execute_script", f"Running: {path}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.command_timeout
            )
            
            return ExecutorResult(
                success=(result.returncode == 0),
                message=f"脚本执行完成 (返回码: {result.returncode})",
                data={
                    "script": str(path),
                    "type": script_type,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            
        except subprocess.TimeoutExpired:
            return ExecutorResult(False, f"脚本执行超时")
        except Exception as e:
            return ExecutorResult(False, f"脚本执行失败: {e}")
    
    def _get_env(self, params: Dict) -> ExecutorResult:
        """获取环境变量"""
        name = params.get("name")
        
        if name:
            value = os.environ.get(name)
            if value:
                return ExecutorResult(
                    success=True,
                    message=f"环境变量 {name}",
                    data={"name": name, "value": value}
                )
            else:
                return ExecutorResult(False, f"环境变量不存在: {name}")
        else:
            # 返回所有环境变量
            return ExecutorResult(
                success=True,
                message=f"共 {len(os.environ)} 个环境变量",
                data={"variables": dict(os.environ)}
            )
    
    def _get_path(self, params: Dict) -> ExecutorResult:
        """获取系统PATH"""
        path = os.environ.get("PATH", "")
        
        if self.system == "Windows":
            paths = path.split(";")
        else:
            paths = path.split(":")
        
        # 检查路径是否存在
        valid_paths = []
        invalid_paths = []
        
        for p in paths:
            if p and Path(p).exists():
                valid_paths.append(p)
            elif p:
                invalid_paths.append(p)
        
        return ExecutorResult(
            success=True,
            message=f"PATH包含 {len(valid_paths)} 个有效路径",
            data={
                "paths": valid_paths,
                "invalid_paths": invalid_paths,
                "total": len(paths),
            }
        )

