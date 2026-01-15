"""
Agent OS 核心代理
"""
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .config import AgentConfig, AgentMode
from .session import Session, TaskRecord
from .runtime import Runtime, ActionResult

logger = logging.getLogger(__name__)


class AgentOS:
    """
    Agent OS - 智能操作系统代理
    
    核心功能:
    - 自然语言理解和执行
    - 任务规划和调度
    - 系统资源管理
    - 智能记忆和学习
    
    使用示例:
        agent = AgentOS()
        result = agent.run("打开浏览器搜索Python教程")
        result = agent.run("查找桌面上所有PDF文件")
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_client=None,
    ):
        self.config = config or AgentConfig()
        self.llm_client = llm_client
        
        # 运行时环境
        self.runtime = Runtime(self.config)
        
        # 当前会话
        self.session = Session()
        
        # 执行器
        self._executors: Dict[str, Any] = {}
        self._init_executors()
        
        # 回调
        self._on_thinking: Optional[Callable[[str], None]] = None
        self._on_action: Optional[Callable[[str, Dict], None]] = None
        self._on_result: Optional[Callable[[ActionResult], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        
        # 状态
        self._is_running = False
        self._current_task: Optional[TaskRecord] = None
        
        logger.info(f"Agent OS initialized (mode: {self.config.mode.value})")
    
    def _init_executors(self) -> None:
        """初始化执行器"""
        from ..executors import (
            FileExecutor, AppExecutor, SearchExecutor,
            SystemExecutor, BrowserExecutor, ComposeExecutor
        )
        
        self._executors = {
            "file": FileExecutor(self.config, self.runtime),
            "app": AppExecutor(self.config, self.runtime),
            "search": SearchExecutor(self.config, self.runtime),
            "system": SystemExecutor(self.config, self.runtime),
            "browser": BrowserExecutor(self.config, self.runtime),
            "compose": ComposeExecutor(self.config, self.runtime, self.llm_client),
        }
    
    def run(self, command: str, auto_confirm: bool = False) -> ActionResult:
        """
        执行自然语言命令
        
        Args:
            command: 自然语言指令
            auto_confirm: 是否自动确认危险操作
        
        Returns:
            ActionResult: 执行结果
        """
        start_time = time.time()
        
        # 添加用户消息
        self.session.add_user_message(command)
        
        # 开始任务
        task = self.session.start_task(command)
        self._current_task = task
        self._is_running = True
        
        try:
            # 发送思考回调
            self._emit_thinking("正在分析您的指令...")
            
            # 解析意图
            intent = self._parse_intent(command)
            
            if not intent:
                return self._fail_task(task, "无法理解您的指令，请尝试更具体的描述")
            
            # 发送动作回调
            self._emit_action(intent["action"], intent)
            
            # 检查是否需要确认
            if intent.get("requires_confirmation") and not auto_confirm:
                if self.config.require_confirmation:
                    return self._fail_task(task, "操作需要确认", requires_confirm=True)
            
            # 执行操作
            result = self._execute_intent(intent)
            
            # 计算执行时间
            duration = (time.time() - start_time) * 1000
            result.duration_ms = duration
            
            # 完成任务
            if result.success:
                self.session.complete_task(task.id, result=result.data)
                self.session.add_agent_message(result.message, {"action": result.action})
            else:
                self.session.complete_task(task.id, error=result.error or result.message)
            
            # 发送结果回调
            self._emit_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"执行错误: {e}", exc_info=True)
            return self._fail_task(task, f"执行出错: {e}")
        
        finally:
            self._is_running = False
            self._current_task = None
    
    def _parse_intent(self, command: str) -> Optional[Dict]:
        """解析用户意图"""
        command_lower = command.lower()
        
        # 帮助命令
        if any(kw in command_lower for kw in ["帮助", "help", "怎么", "如何"]):
            return {"action": "help", "type": "system"}
        
        # 文件操作
        if any(kw in command_lower for kw in ["创建文件", "新建文件", "create file"]):
            return {"action": "file.create", "type": "file", "command": command}
        if any(kw in command_lower for kw in ["读取", "查看文件", "打开文件", "read"]):
            return {"action": "file.read", "type": "file", "command": command}
        if any(kw in command_lower for kw in ["写入", "编辑", "修改", "write"]):
            return {"action": "file.write", "type": "file", "command": command}
        if any(kw in command_lower for kw in ["删除文件", "移除文件", "delete file"]):
            return {"action": "file.delete", "type": "file", "command": command, "requires_confirmation": True}
        if any(kw in command_lower for kw in ["复制", "copy"]):
            return {"action": "file.copy", "type": "file", "command": command}
        if any(kw in command_lower for kw in ["移动", "重命名", "move", "rename"]):
            return {"action": "file.move", "type": "file", "command": command}
        
        # 目录操作
        if any(kw in command_lower for kw in ["创建目录", "创建文件夹", "新建文件夹", "mkdir"]):
            return {"action": "dir.create", "type": "file", "command": command}
        if any(kw in command_lower for kw in ["列出", "显示目录", "查看文件夹", "ls", "dir"]):
            return {"action": "dir.list", "type": "file", "command": command}
        
        # 搜索操作
        if any(kw in command_lower for kw in ["查找", "搜索", "找", "find", "search", "locate"]):
            return {"action": "search.file", "type": "search", "command": command}
        
        # 应用操作
        if any(kw in command_lower for kw in ["打开", "启动", "运行", "open", "start", "launch"]):
            # 判断是应用还是文件/URL
            if any(kw in command_lower for kw in ["网址", "网站", "http", "www", ".com", ".cn"]):
                return {"action": "browser.navigate", "type": "browser", "command": command}
            return {"action": "app.open", "type": "app", "command": command}
        if any(kw in command_lower for kw in ["关闭", "退出", "结束", "close", "quit", "kill"]):
            return {"action": "app.close", "type": "app", "command": command}
        
        # 浏览器搜索
        if any(kw in command_lower for kw in ["搜索", "百度", "谷歌", "google", "bing", "查一下"]):
            if any(kw in command_lower for kw in ["文件", "本地", "电脑"]):
                return {"action": "search.file", "type": "search", "command": command}
            return {"action": "browser.search", "type": "browser", "command": command}
        
        # 系统操作
        if any(kw in command_lower for kw in ["系统信息", "电脑信息", "硬件", "system info"]):
            return {"action": "system.info", "type": "system", "command": command}
        if any(kw in command_lower for kw in ["截图", "截屏", "screenshot"]):
            return {"action": "system.screenshot", "type": "system", "command": command}
        if any(kw in command_lower for kw in ["剪贴板", "粘贴", "clipboard"]):
            return {"action": "system.clipboard", "type": "system", "command": command}
        
        # 命令执行
        if any(kw in command_lower for kw in ["执行", "运行命令", "命令", "terminal", "shell"]):
            return {"action": "system.command", "type": "system", "command": command, "requires_confirmation": True}
        
        # 使用LLM理解（如果可用）
        if self.llm_client:
            return self._parse_with_llm(command)
        
        # 默认尝试作为应用打开
        return {"action": "app.open", "type": "app", "command": command}
    
    def _parse_with_llm(self, command: str) -> Optional[Dict]:
        """使用LLM解析意图"""
        try:
            prompt = f"""分析用户命令，返回JSON格式的意图：
用户命令: "{command}"

返回格式:
{{"action": "操作类型", "type": "类别", "params": {{}}, "command": "原命令"}}

操作类型: file.create/read/write/delete/copy/move, dir.create/list, search.file, 
         app.open/close, browser.search/navigate, system.info/screenshot/command
类别: file, app, search, browser, system

只返回JSON。"""
            
            response = self.llm_client.chat(prompt)
            import json
            return json.loads(response.strip())
        except:
            return None
    
    def _execute_intent(self, intent: Dict) -> ActionResult:
        """执行意图"""
        action = intent.get("action", "")
        command = intent.get("command", "")
        
        # 帮助
        if action == "help":
            return self._show_help()
        
        # 获取执行器
        executor_type = action.split(".")[0]
        executor = self._executors.get(executor_type)
        
        if not executor:
            return ActionResult(
                success=False,
                action=action,
                message=f"未找到执行器: {executor_type}",
                error="NoExecutor"
            )
        
        # 执行操作
        return executor.execute(action, command, intent.get("params", {}))
    
    def _show_help(self) -> ActionResult:
        """显示帮助"""
        help_text = """
🤖 Agent OS - 智能操作系统代理

📁 文件操作:
  • 创建文件 test.txt
  • 读取/查看 config.json
  • 在桌面创建项目文件夹

🔍 搜索:
  • 查找PDF文件
  • 搜索最近修改的文档
  • 在文档文件夹找report

🚀 应用:
  • 打开记事本
  • 启动Chrome浏览器
  • 关闭微信

🌐 浏览器:
  • 搜索Python教程
  • 百度一下天气预报
  • 打开 github.com

⚙️ 系统:
  • 系统信息
  • 截图保存到桌面
  • 执行 dir 命令

💡 提示: 直接用自然语言描述您想做的事情！
        """
        return ActionResult(
            success=True,
            action="help",
            message=help_text.strip()
        )
    
    def _fail_task(self, task: TaskRecord, message: str, **kwargs) -> ActionResult:
        """任务失败"""
        self.session.complete_task(task.id, error=message)
        self._emit_error(message)
        
        return ActionResult(
            success=False,
            action="error",
            message=message,
            error=message,
            **kwargs
        )
    
    # ==================
    # 快捷方法
    # ==================
    
    def open_app(self, name: str) -> ActionResult:
        """打开应用"""
        return self.run(f"打开 {name}")
    
    def search_files(self, query: str, path: str = None) -> ActionResult:
        """搜索文件"""
        cmd = f"查找文件 {query}"
        if path:
            cmd += f" 在 {path}"
        return self.run(cmd)
    
    def search_web(self, query: str, engine: str = "google") -> ActionResult:
        """网页搜索"""
        return self._executors["browser"].execute("browser.search", query, {"engine": engine})
    
    def get_system_info(self) -> ActionResult:
        """获取系统信息"""
        return self._executors["system"].execute("system.info", "", {})
    
    def screenshot(self, path: str = None) -> ActionResult:
        """截图"""
        return self._executors["system"].execute("system.screenshot", "", {"path": path})
    
    # ==================
    # 回调设置
    # ==================
    
    def on_thinking(self, callback: Callable[[str], None]) -> None:
        """设置思考回调"""
        self._on_thinking = callback
    
    def on_action(self, callback: Callable[[str, Dict], None]) -> None:
        """设置动作回调"""
        self._on_action = callback
    
    def on_result(self, callback: Callable[[ActionResult], None]) -> None:
        """设置结果回调"""
        self._on_result = callback
    
    def on_error(self, callback: Callable[[str], None]) -> None:
        """设置错误回调"""
        self._on_error = callback
    
    def _emit_thinking(self, message: str) -> None:
        if self._on_thinking:
            self._on_thinking(message)
    
    def _emit_action(self, action: str, data: Dict) -> None:
        if self._on_action:
            self._on_action(action, data)
    
    def _emit_result(self, result: ActionResult) -> None:
        if self._on_result:
            self._on_result(result)
    
    def _emit_error(self, message: str) -> None:
        if self._on_error:
            self._on_error(message)
    
    # ==================
    # 状态
    # ==================
    
    def is_running(self) -> bool:
        return self._is_running
    
    def get_session(self) -> Session:
        return self.session
    
    def new_session(self) -> Session:
        """创建新会话"""
        self.session = Session()
        return self.session
    
    def set_llm_client(self, client) -> None:
        """设置LLM客户端"""
        self.llm_client = client
        if "compose" in self._executors:
            self._executors["compose"].set_llm_client(client)

