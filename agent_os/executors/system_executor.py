"""
系统执行器
"""
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict

from .base import BaseExecutor
from ..core.runtime import ActionResult


class SystemExecutor(BaseExecutor):
    """系统操作执行器"""
    
    name = "system"
    
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行系统操作"""
        try:
            if action == "system.info":
                return self._system_info(params)
            elif action == "system.screenshot":
                return self._screenshot(params)
            elif action == "system.clipboard":
                return self._clipboard(command, params)
            elif action == "system.command":
                return self._run_command(command, params)
            elif action == "system.notify":
                return self._notify(params)
            else:
                return ActionResult(False, action, f"不支持的操作: {action}")
        except Exception as e:
            return ActionResult(False, action, f"操作失败: {e}", error=str(e))
    
    def _system_info(self, params: Dict) -> ActionResult:
        """获取系统信息"""
        info = self.runtime.get_system_info()
        
        # 格式化输出
        msg_parts = [
            f"💻 系统信息",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"🖥️ 系统: {info['platform']['system']} {info['platform']['release']}",
            f"📟 主机: {info['platform']['hostname']}",
        ]
        
        if 'cpu' in info:
            msg_parts.append(f"⚡ CPU: {info['cpu']['cores_logical']} 核心, 使用率 {info['cpu']['usage_percent']}%")
        
        if 'memory' in info:
            msg_parts.append(f"🧠 内存: {info['memory']['total_gb']}GB 总计, 使用率 {info['memory']['used_percent']}%")
        
        if 'disk' in info:
            msg_parts.append(f"💾 磁盘: {info['disk']['total_gb']}GB 总计, 剩余 {info['disk']['free_gb']}GB")
        
        if 'battery' in info:
            status = "🔌 充电中" if info['battery']['plugged'] else "🔋 电池"
            msg_parts.append(f"{status}: {info['battery']['percent']}%")
        
        return ActionResult(
            success=True,
            action="system.info",
            message="\n".join(msg_parts),
            data=info
        )
    
    def _screenshot(self, params: Dict) -> ActionResult:
        """截图"""
        save_path = params.get("path")
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(Path(tempfile.gettempdir()) / f"screenshot_{timestamp}.png")
        
        save_path = str(Path(save_path).expanduser())
        
        system = platform.system()
        
        try:
            # 尝试使用 pyautogui
            try:
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(save_path)
            except ImportError:
                # 使用系统命令
                if system == "Windows":
                    self._windows_screenshot(save_path)
                elif system == "Darwin":
                    subprocess.run(["screencapture", "-x", save_path], check=True)
                else:
                    subprocess.run(["scrot", save_path], check=True)
            
            self._log("screenshot", f"Saved: {save_path}")
            
            return ActionResult(
                success=True,
                action="system.screenshot",
                message=f"📸 截图已保存: {save_path}",
                data={"path": save_path}
            )
        except Exception as e:
            return ActionResult(False, "system.screenshot", f"截图失败: {e}", error=str(e))
    
    def _windows_screenshot(self, path: str) -> None:
        """Windows截图"""
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
        $bitmap.Save("{path}")
        '''
        subprocess.run(["powershell", "-Command", ps_script], check=True)
    
    def _clipboard(self, command: str, params: Dict) -> ActionResult:
        """剪贴板操作"""
        content = params.get("content")
        
        if content:
            # 设置剪贴板
            return self._set_clipboard(content)
        else:
            # 获取剪贴板
            return self._get_clipboard()
    
    def _get_clipboard(self) -> ActionResult:
        """获取剪贴板内容"""
        system = platform.system()
        
        try:
            try:
                import pyperclip
                content = pyperclip.paste()
            except ImportError:
                if system == "Windows":
                    result = subprocess.run(["powershell", "-Command", "Get-Clipboard"],
                                          capture_output=True, text=True)
                    content = result.stdout.strip()
                elif system == "Darwin":
                    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                    content = result.stdout
                else:
                    result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                          capture_output=True, text=True)
                    content = result.stdout
            
            return ActionResult(
                success=True,
                action="system.clipboard.get",
                message=f"📋 剪贴板内容 ({len(content)} 字符)",
                data={"content": content}
            )
        except Exception as e:
            return ActionResult(False, "system.clipboard.get", f"获取失败: {e}", error=str(e))
    
    def _set_clipboard(self, content: str) -> ActionResult:
        """设置剪贴板内容"""
        system = platform.system()
        
        try:
            try:
                import pyperclip
                pyperclip.copy(content)
            except ImportError:
                if system == "Windows":
                    subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{content}'"])
                elif system == "Darwin":
                    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                    proc.communicate(content.encode())
                else:
                    proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                    proc.communicate(content.encode())
            
            return ActionResult(
                success=True,
                action="system.clipboard.set",
                message="✓ 已复制到剪贴板",
                data={"length": len(content)}
            )
        except Exception as e:
            return ActionResult(False, "system.clipboard.set", f"设置失败: {e}", error=str(e))
    
    def _run_command(self, command: str, params: Dict) -> ActionResult:
        """执行命令"""
        cmd = params.get("command")
        
        # 从命令中提取
        if not cmd:
            for prefix in ["执行", "运行", "命令", "execute", "run"]:
                if prefix in command.lower():
                    parts = command.lower().split(prefix)
                    if len(parts) > 1:
                        cmd = parts[1].strip()
                        break
        
        if not cmd:
            return ActionResult(False, "system.command", "请指定要执行的命令")
        
        # 安全检查
        safe, msg = self.runtime.check_command_safety(cmd)
        if not safe:
            return ActionResult(False, "system.command", msg, error="Blocked")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            self._log("command", f"Executed: {cmd}")
            
            return ActionResult(
                success=(result.returncode == 0),
                action="system.command",
                message=f"⚡ 命令执行完成 (返回码: {result.returncode})",
                data={
                    "command": cmd,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
        except subprocess.TimeoutExpired:
            return ActionResult(False, "system.command", "命令执行超时")
        except Exception as e:
            return ActionResult(False, "system.command", f"执行失败: {e}", error=str(e))
    
    def _notify(self, params: Dict) -> ActionResult:
        """发送系统通知"""
        title = params.get("title", "Agent OS")
        message = params.get("message", "")
        
        if not message:
            return ActionResult(False, "system.notify", "请指定通知内容")
        
        system = platform.system()
        
        try:
            if system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                except ImportError:
                    ps_script = f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'
                    subprocess.run(["powershell", "-Command", ps_script])
            elif system == "Darwin":
                subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
            else:
                subprocess.run(["notify-send", title, message])
            
            return ActionResult(
                success=True,
                action="system.notify",
                message="🔔 通知已发送",
                data={"title": title, "message": message}
            )
        except Exception as e:
            return ActionResult(False, "system.notify", f"通知失败: {e}", error=str(e))

