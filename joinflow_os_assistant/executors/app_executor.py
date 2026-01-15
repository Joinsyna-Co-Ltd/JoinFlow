"""
应用执行器 - 处理应用程序的打开、关闭、管理
"""
import os
import platform
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseExecutor, ExecutorResult

logger = logging.getLogger(__name__)


class AppExecutor(BaseExecutor):
    """
    应用执行器
    
    处理应用程序的打开、关闭、列表等操作
    """
    
    name = "app"
    supported_operations = [
        "app.open", "app.close", "app.list", "app.find",
        "app.info", "app.switch",
    ]
    
    # 常见应用映射 (别名 -> 实际命令/名称)
    APP_ALIASES = {
        # Windows
        "记事本": "notepad",
        "计算器": "calc",
        "画图": "mspaint",
        "资源管理器": "explorer",
        "命令提示符": "cmd",
        "powershell": "powershell",
        "终端": "wt",
        "任务管理器": "taskmgr",
        "控制面板": "control",
        "设置": "ms-settings:",
        
        # 浏览器
        "浏览器": "chrome",
        "chrome": "chrome",
        "谷歌浏览器": "chrome",
        "google chrome": "chrome",
        "火狐": "firefox",
        "firefox": "firefox",
        "edge": "msedge",
        "微软edge": "msedge",
        
        # 开发工具
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "visual studio": "devenv",
        "pycharm": "pycharm",
        "idea": "idea",
        "sublime": "sublime_text",
        
        # 办公
        "word": "WINWORD",
        "微软word": "WINWORD",
        "excel": "EXCEL",
        "微软excel": "EXCEL",
        "ppt": "POWERPNT",
        "powerpoint": "POWERPNT",
        "outlook": "OUTLOOK",
        "onenote": "ONENOTE",
        
        # 社交
        "qq": "QQ",
        "微信": "WeChat",
        "wechat": "WeChat",
        "钉钉": "DingTalk",
        "teams": "Teams",
        
        # 媒体
        "spotify": "Spotify",
        "网易云音乐": "cloudmusic",
        "网易云": "cloudmusic",
        "vlc": "vlc",
        "potplayer": "PotPlayerMini64",
        
        # 工具
        "photoshop": "Photoshop",
        "ps": "Photoshop",
        "premiere": "Adobe Premiere Pro",
        "pr": "Adobe Premiere Pro",
    }
    
    # macOS 应用
    MACOS_APPS = {
        "finder": "Finder",
        "safari": "Safari",
        "终端": "Terminal",
        "terminal": "Terminal",
        "notes": "Notes",
        "备忘录": "Notes",
        "calendar": "Calendar",
        "日历": "Calendar",
        "mail": "Mail",
        "邮件": "Mail",
        "music": "Music",
        "音乐": "Music",
        "photos": "Photos",
        "照片": "Photos",
    }
    
    def __init__(self, config=None):
        super().__init__(config)
        self.system = platform.system()
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行应用操作"""
        try:
            if operation == "app.open":
                return self._open_app(parameters)
            elif operation == "app.close":
                return self._close_app(parameters)
            elif operation == "app.list":
                return self._list_apps(parameters)
            elif operation == "app.find":
                return self._find_app(parameters)
            elif operation == "app.info":
                return self._app_info(parameters)
            elif operation == "app.switch":
                return self._switch_app(parameters)
            else:
                return ExecutorResult(False, f"不支持的操作: {operation}")
        except Exception as e:
            logger.error(f"应用操作失败: {e}")
            return ExecutorResult(False, f"操作失败: {e}")
    
    def _open_app(self, params: Dict) -> ExecutorResult:
        """打开应用程序"""
        app_name = params.get("app_name") or params.get("name")
        args = params.get("args", [])
        
        if not app_name:
            return ExecutorResult(False, "缺少应用名称参数")
        
        # 解析别名
        resolved_name = self._resolve_app_name(app_name)
        
        try:
            if self.system == "Windows":
                return self._open_windows_app(resolved_name, args)
            elif self.system == "Darwin":
                return self._open_macos_app(resolved_name, args)
            else:
                return self._open_linux_app(resolved_name, args)
        except Exception as e:
            return ExecutorResult(False, f"打开应用失败: {e}")
    
    def _open_windows_app(self, app_name: str, args: List[str]) -> ExecutorResult:
        """在Windows上打开应用"""
        # 特殊处理 ms-settings 等协议
        if app_name.startswith("ms-"):
            os.startfile(app_name)
            return ExecutorResult(True, f"已打开: {app_name}")
        
        # 尝试直接启动
        try:
            if args:
                subprocess.Popen([app_name] + args, shell=True)
            else:
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
            
            self._log_action("open_app", f"Opened: {app_name}")
            return ExecutorResult(
                success=True,
                message=f"已打开应用: {app_name}",
                data={"app": app_name}
            )
        except Exception as e:
            # 尝试通过搜索找到应用
            found_path = self._find_windows_app(app_name)
            if found_path:
                subprocess.Popen(f'start "" "{found_path}"', shell=True)
                return ExecutorResult(True, f"已打开: {found_path}")
            
            return ExecutorResult(False, f"无法找到应用: {app_name}")
    
    def _open_macos_app(self, app_name: str, args: List[str]) -> ExecutorResult:
        """在macOS上打开应用"""
        # 检查 MACOS_APPS 映射
        if app_name.lower() in self.MACOS_APPS:
            app_name = self.MACOS_APPS[app_name.lower()]
        
        cmd = ["open", "-a", app_name]
        if args:
            cmd.extend(args)
        
        subprocess.Popen(cmd)
        
        self._log_action("open_app", f"Opened: {app_name}")
        return ExecutorResult(
            success=True,
            message=f"已打开应用: {app_name}",
            data={"app": app_name}
        )
    
    def _open_linux_app(self, app_name: str, args: List[str]) -> ExecutorResult:
        """在Linux上打开应用"""
        cmd = [app_name] + args
        subprocess.Popen(cmd, start_new_session=True)
        
        self._log_action("open_app", f"Opened: {app_name}")
        return ExecutorResult(
            success=True,
            message=f"已打开应用: {app_name}",
            data={"app": app_name}
        )
    
    def _close_app(self, params: Dict) -> ExecutorResult:
        """关闭应用程序"""
        try:
            import psutil
        except ImportError:
            return ExecutorResult(False, "需要安装 psutil: pip install psutil")
        
        app_name = params.get("app_name") or params.get("name")
        pid = params.get("pid")
        force = params.get("force", False)
        
        if not app_name and not pid:
            return ExecutorResult(False, "缺少应用名称或PID参数")
        
        closed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if pid and proc.info['pid'] == pid:
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    closed_count += 1
                    break
                elif app_name and app_name.lower() in proc.info['name'].lower():
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed_count > 0:
            self._log_action("close_app", f"Closed: {app_name or pid}")
            return ExecutorResult(
                success=True,
                message=f"已关闭 {closed_count} 个进程",
                data={"closed": closed_count}
            )
        else:
            return ExecutorResult(False, f"未找到应用: {app_name or pid}")
    
    def _list_apps(self, params: Dict) -> ExecutorResult:
        """列出运行中的应用"""
        try:
            import psutil
        except ImportError:
            return ExecutorResult(False, "需要安装 psutil: pip install psutil")
        
        filter_name = params.get("filter")
        limit = params.get("limit", 50)
        sort_by = params.get("sort_by", "memory")  # memory, cpu, name
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                
                if filter_name and filter_name.lower() not in info['name'].lower():
                    continue
                
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu_percent": round(info['cpu_percent'] or 0, 1),
                    "memory_percent": round(info['memory_percent'] or 0, 1),
                    "status": info['status'],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 排序
        if sort_by == "cpu":
            processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
        elif sort_by == "name":
            processes.sort(key=lambda x: x["name"].lower())
        else:  # memory
            processes.sort(key=lambda x: x["memory_percent"], reverse=True)
        
        # 限制数量
        processes = processes[:limit]
        
        return ExecutorResult(
            success=True,
            message=f"找到 {len(processes)} 个运行中的进程",
            data={"processes": processes, "count": len(processes)}
        )
    
    def _find_app(self, params: Dict) -> ExecutorResult:
        """查找应用程序"""
        app_name = params.get("app_name") or params.get("name") or params.get("query")
        
        if not app_name:
            return ExecutorResult(False, "缺少应用名称参数")
        
        found_apps = []
        
        if self.system == "Windows":
            # 搜索开始菜单和常见位置
            search_paths = [
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
                Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")),
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
                Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs",
            ]
            
            for base_path in search_paths:
                if not base_path.exists():
                    continue
                
                for exe in base_path.rglob("*.exe"):
                    if app_name.lower() in exe.name.lower():
                        found_apps.append({
                            "name": exe.name,
                            "path": str(exe),
                            "location": str(exe.parent),
                        })
                
                for lnk in base_path.rglob("*.lnk"):
                    if app_name.lower() in lnk.name.lower():
                        found_apps.append({
                            "name": lnk.stem,
                            "path": str(lnk),
                            "type": "shortcut",
                        })
        
        elif self.system == "Darwin":
            # macOS 应用目录
            apps_dir = Path("/Applications")
            user_apps = Path.home() / "Applications"
            
            for apps_path in [apps_dir, user_apps]:
                if not apps_path.exists():
                    continue
                
                for app in apps_path.glob("*.app"):
                    if app_name.lower() in app.name.lower():
                        found_apps.append({
                            "name": app.stem,
                            "path": str(app),
                        })
        
        else:  # Linux
            # 搜索 /usr/bin, /usr/local/bin 等
            for bin_dir in ["/usr/bin", "/usr/local/bin", str(Path.home() / ".local/bin")]:
                bin_path = Path(bin_dir)
                if bin_path.exists():
                    for exe in bin_path.iterdir():
                        if exe.is_file() and app_name.lower() in exe.name.lower():
                            found_apps.append({
                                "name": exe.name,
                                "path": str(exe),
                            })
        
        if found_apps:
            return ExecutorResult(
                success=True,
                message=f"找到 {len(found_apps)} 个匹配的应用",
                data={"apps": found_apps[:20], "count": len(found_apps)}
            )
        else:
            return ExecutorResult(
                success=False,
                message=f"未找到应用: {app_name}",
                data={"query": app_name}
            )
    
    def _app_info(self, params: Dict) -> ExecutorResult:
        """获取应用信息"""
        try:
            import psutil
        except ImportError:
            return ExecutorResult(False, "需要安装 psutil: pip install psutil")
        
        pid = params.get("pid")
        app_name = params.get("app_name") or params.get("name")
        
        if not pid and not app_name:
            return ExecutorResult(False, "缺少PID或应用名称")
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'create_time',
                                         'cpu_percent', 'memory_info', 'status', 'username']):
            try:
                info = proc.info
                
                if pid and info['pid'] == pid:
                    pass
                elif app_name and app_name.lower() in info['name'].lower():
                    pass
                else:
                    continue
                
                return ExecutorResult(
                    success=True,
                    message=f"应用信息: {info['name']}",
                    data={
                        "pid": info['pid'],
                        "name": info['name'],
                        "exe": info['exe'],
                        "cmdline": info['cmdline'],
                        "status": info['status'],
                        "username": info['username'],
                        "cpu_percent": info['cpu_percent'],
                        "memory_mb": round(info['memory_info'].rss / 1024 / 1024, 1) if info['memory_info'] else 0,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return ExecutorResult(False, f"未找到应用: {app_name or pid}")
    
    def _switch_app(self, params: Dict) -> ExecutorResult:
        """切换到应用（置前）"""
        app_name = params.get("app_name") or params.get("name")
        
        if not app_name:
            return ExecutorResult(False, "缺少应用名称参数")
        
        if self.system == "Windows":
            # 使用 PowerShell 激活窗口
            ps_script = f'''
            $app = Get-Process | Where-Object {{$_.MainWindowTitle -like "*{app_name}*" -or $_.ProcessName -like "*{app_name}*"}} | Select-Object -First 1
            if ($app) {{
                [void] [System.Reflection.Assembly]::LoadWithPartialName("Microsoft.VisualBasic")
                [Microsoft.VisualBasic.Interaction]::AppActivate($app.Id)
            }}
            '''
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            
        elif self.system == "Darwin":
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'])
        
        return ExecutorResult(
            success=True,
            message=f"已切换到: {app_name}",
            data={"app": app_name}
        )
    
    def _resolve_app_name(self, name: str) -> str:
        """解析应用名称别名"""
        name_lower = name.lower().strip()
        return self.APP_ALIASES.get(name_lower, name)
    
    def _find_windows_app(self, name: str) -> Optional[str]:
        """在Windows上查找应用路径"""
        # 常见位置
        search_paths = [
            f"C:\\Program Files\\{name}",
            f"C:\\Program Files (x86)\\{name}",
            os.path.expandvars(f"%LOCALAPPDATA%\\Programs\\{name}"),
        ]
        
        for path in search_paths:
            p = Path(path)
            if p.exists():
                # 查找可执行文件
                for exe in p.rglob("*.exe"):
                    if name.lower() in exe.name.lower():
                        return str(exe)
        
        return None

