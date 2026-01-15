"""
应用执行器
"""
import os
import platform
import subprocess
from typing import Dict, Optional

from .base import BaseExecutor
from ..core.runtime import ActionResult


class AppExecutor(BaseExecutor):
    """应用程序管理执行器"""
    
    name = "app"
    
    # 常见应用映射
    APP_MAP = {
        # Windows
        "notepad": "notepad",
        "记事本": "notepad",
        "calc": "calc",
        "计算器": "calc",
        "paint": "mspaint",
        "画图": "mspaint",
        "explorer": "explorer",
        "资源管理器": "explorer",
        "文件管理器": "explorer",
        "cmd": "cmd",
        "命令提示符": "cmd",
        "powershell": "powershell",
        "terminal": "wt",
        "终端": "wt",
        "taskmgr": "taskmgr",
        "任务管理器": "taskmgr",
        
        # 浏览器
        "chrome": "chrome",
        "谷歌浏览器": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "火狐": "firefox",
        "edge": "msedge",
        "微软edge": "msedge",
        "浏览器": "chrome",
        
        # 开发工具
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "visual studio code": "code",
        
        # 社交
        "微信": "WeChat",
        "wechat": "WeChat",
        "qq": "QQ",
        "钉钉": "DingTalk",
        
        # 办公
        "word": "WINWORD",
        "excel": "EXCEL",
        "ppt": "POWERPNT",
        "powerpoint": "POWERPNT",
    }
    
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行应用操作"""
        try:
            if action == "app.open":
                return self._open_app(command, params)
            elif action == "app.close":
                return self._close_app(command, params)
            elif action == "app.list":
                return self._list_apps(params)
            else:
                return ActionResult(False, action, f"不支持的操作: {action}")
        except Exception as e:
            return ActionResult(False, action, f"操作失败: {e}", error=str(e))
    
    def _open_app(self, command: str, params: Dict) -> ActionResult:
        """打开应用程序"""
        app_name = params.get("name") or self._extract_app_name(command)
        
        if not app_name:
            return ActionResult(False, "app.open", "请指定应用名称")
        
        # 解析应用名
        resolved = self.APP_MAP.get(app_name.lower(), app_name)
        
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windows: 使用 start 命令
                subprocess.Popen(f'start "" "{resolved}"', shell=True)
            elif system == "Darwin":
                # macOS: 使用 open 命令
                subprocess.Popen(["open", "-a", resolved])
            else:
                # Linux
                subprocess.Popen([resolved], start_new_session=True)
            
            self._log("open", f"Opened: {resolved}")
            
            return ActionResult(
                success=True,
                action="app.open",
                message=f"✓ 已启动: {app_name}",
                data={"app": resolved}
            )
        except Exception as e:
            return ActionResult(False, "app.open", f"无法打开应用: {app_name}", error=str(e))
    
    def _close_app(self, command: str, params: Dict) -> ActionResult:
        """关闭应用程序"""
        try:
            import psutil
        except ImportError:
            return ActionResult(False, "app.close", "需要安装 psutil: pip install psutil")
        
        app_name = params.get("name") or self._extract_app_name(command)
        
        if not app_name:
            return ActionResult(False, "app.close", "请指定应用名称")
        
        closed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed > 0:
            self._log("close", f"Closed: {app_name} ({closed} processes)")
            return ActionResult(
                success=True,
                action="app.close",
                message=f"✓ 已关闭 {closed} 个 {app_name} 进程",
                data={"app": app_name, "closed": closed}
            )
        else:
            return ActionResult(False, "app.close", f"未找到运行中的 {app_name}")
    
    def _list_apps(self, params: Dict) -> ActionResult:
        """列出运行中的应用"""
        try:
            import psutil
        except ImportError:
            return ActionResult(False, "app.list", "需要安装 psutil")
        
        apps = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                apps.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu": round(info['cpu_percent'] or 0, 1),
                    "memory": round(info['memory_percent'] or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按内存使用排序，取前20
        apps.sort(key=lambda x: x['memory'], reverse=True)
        apps = apps[:20]
        
        return ActionResult(
            success=True,
            action="app.list",
            message=f"📊 运行中的应用 (前20)",
            data={"apps": apps, "count": len(apps)}
        )

