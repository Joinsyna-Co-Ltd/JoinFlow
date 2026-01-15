"""
智能操作系统助手 - 核心类
"""
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .config import AssistantConfig, PermissionLevel
from .context import ExecutionContext, ExecutionResult
from .memory import AssistantMemory
from ..intent.parser import IntentParser
from ..intent.types import Intent, IntentType
from ..planner.task_planner import TaskPlanner, SmartTaskPlanner
from ..planner.task import Task, TaskPlan, TaskResult, TaskStatus
from ..planner.strategies import SequentialStrategy, ParallelStrategy, MixedStrategy
from ..executors.executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


class OSAssistant:
    """
    智能操作系统助手
    
    主要功能：
    - 理解自然语言指令
    - 自动规划和执行任务
    - 控制操作系统（文件、应用、搜索等）
    - 结合大模型进行智能决策
    
    使用示例:
        assistant = OSAssistant()
        
        # 执行单个命令
        result = assistant.execute("打开记事本")
        
        # 执行复杂任务
        result = assistant.execute("在桌面创建一个名为'项目'的文件夹，然后在里面创建README.md文件")
        
        # 搜索文件
        result = assistant.execute("查找最近修改的PDF文件")
    """
    
    def __init__(
        self,
        config: Optional[AssistantConfig] = None,
        llm_client=None,
        enable_memory: bool = True,
    ):
        """
        初始化助手
        
        Args:
            config: 配置对象
            llm_client: LLM客户端（用于智能理解和生成）
            enable_memory: 是否启用记忆功能
        """
        self.config = config or AssistantConfig()
        self.llm_client = llm_client
        
        # 初始化组件
        self.context = ExecutionContext()
        self.memory = AssistantMemory() if enable_memory else None
        
        # 意图解析器
        self.intent_parser = IntentParser(llm_client)
        
        # 任务规划器
        if self.memory:
            self.task_planner = SmartTaskPlanner(llm_client, self.memory)
        else:
            self.task_planner = TaskPlanner(llm_client)
        
        # 执行器注册表
        self.executor_registry = ExecutorRegistry(self.config, llm_client)
        
        # 执行策略
        self.strategies = {
            "sequential": SequentialStrategy(),
            "parallel": ParallelStrategy(),
            "mixed": MixedStrategy(),
        }
        
        # 回调函数
        self._on_task_start: Optional[Callable[[Task], None]] = None
        self._on_task_complete: Optional[Callable[[Task], None]] = None
        self._on_task_error: Optional[Callable[[Task, str], None]] = None
        self._confirmation_handler: Optional[Callable[[str], bool]] = None
        
        # 状态
        self._is_running = False
        self._current_plan: Optional[TaskPlan] = None
        
        logger.info("OSAssistant initialized")
    
    def execute(self, command: str, auto_confirm: bool = False) -> ExecutionResult:
        """
        执行自然语言命令
        
        Args:
            command: 自然语言指令
            auto_confirm: 是否自动确认危险操作
        
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 1. 解析意图
            logger.info(f"Parsing command: {command}")
            parse_result = self.intent_parser.parse(command)
            intent = parse_result.intent
            
            logger.info(f"Detected intent: {intent.type.name} (confidence: {intent.confidence:.2f})")
            
            # 处理特殊意图
            if intent.type == IntentType.HELP:
                return self._handle_help()
            elif intent.type == IntentType.CANCEL:
                return self._handle_cancel()
            elif intent.type == IntentType.UNKNOWN:
                return ExecutionResult(
                    success=False,
                    action="parse",
                    message="抱歉，我不太理解您的意图。请尝试更具体的描述。",
                    data={"raw_input": command}
                )
            
            # 2. 规划任务
            logger.info("Planning tasks...")
            if isinstance(self.task_planner, SmartTaskPlanner):
                plan = self.task_planner.plan(intent, self.context)
            else:
                plan = self.task_planner.plan(intent)
            
            logger.info(f"Created plan with {len(plan.tasks)} tasks")
            
            # 3. 确认危险操作
            if intent.requires_confirmation and not auto_confirm:
                if not self._confirm_operation(plan):
                    return ExecutionResult(
                        success=False,
                        action="confirm",
                        message="操作已取消",
                        data={"plan": plan.to_dict()}
                    )
            
            # 4. 执行任务
            logger.info(f"Executing plan with strategy: {plan.strategy}")
            self._current_plan = plan
            self._is_running = True
            
            strategy = self.strategies.get(plan.strategy, self.strategies["sequential"])
            success = strategy.execute(plan, self._execute_task)
            
            self._is_running = False
            self._current_plan = None
            
            # 5. 收集结果
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            results = []
            for task in plan.tasks:
                if task.result:
                    results.append({
                        "task": task.name,
                        "success": task.result.success,
                        "output": task.result.output,
                        "error": task.result.error,
                    })
            
            # 更新上下文
            execution_result = ExecutionResult(
                success=success,
                action=intent.type.name,
                message=self._generate_summary(plan),
                data={
                    "intent": intent.to_dict(),
                    "plan": plan.to_dict(),
                    "results": results,
                },
                duration_ms=duration
            )
            
            self.context.add_result(execution_result)
            
            # 学习模式
            if self.memory:
                self._learn_from_execution(command, plan, success)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                action="error",
                message=f"执行出错: {e}",
                error=str(e)
            )
    
    def _execute_task(self, task: Task) -> TaskResult:
        """执行单个任务"""
        logger.info(f"Executing task: {task.name} ({task.operation})")
        
        # 触发回调
        if self._on_task_start:
            self._on_task_start(task)
        
        try:
            # 通过执行器注册表执行
            result = self.executor_registry.execute(task.operation, task.parameters)
            
            task_result = TaskResult(
                success=result.success,
                output=result.data,
                error=result.error,
                duration_ms=result.duration_ms,
            )
            
            # 更新上下文
            if result.success:
                self._update_context_after_task(task, result)
                if self._on_task_complete:
                    self._on_task_complete(task)
            else:
                if self._on_task_error:
                    self._on_task_error(task, result.error or result.message)
            
            return task_result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            if self._on_task_error:
                self._on_task_error(task, str(e))
            
            return TaskResult(success=False, error=str(e))
    
    def _update_context_after_task(self, task: Task, result) -> None:
        """任务完成后更新上下文"""
        # 更新当前目录
        if task.operation == "dir.navigate" and result.data:
            self.context.current_dir = result.data.get("path", self.context.current_dir)
        
        # 记录最近文件
        if task.operation.startswith("file.") and task.parameters.get("path"):
            self.context.add_recent_file(task.parameters["path"])
        
        # 记录最近应用
        if task.operation.startswith("app.") and task.parameters.get("app_name"):
            self.context.add_recent_app(task.parameters["app_name"])
    
    def _confirm_operation(self, plan: TaskPlan) -> bool:
        """确认危险操作"""
        if self._confirmation_handler:
            # 生成确认消息
            dangerous_tasks = [t for t in plan.tasks if t.requires_confirmation]
            if dangerous_tasks:
                message = "以下操作需要确认：\n"
                for task in dangerous_tasks:
                    message += f"  - {task.name}: {task.description}\n"
                message += "\n是否继续？"
                
                return self._confirmation_handler(message)
        
        # 默认不确认（需要设置 auto_confirm=True）
        return False
    
    def _generate_summary(self, plan: TaskPlan) -> str:
        """生成执行摘要"""
        progress = plan.get_progress()
        
        if progress["failed"] == 0 and progress["completed"] == progress["total"]:
            return f"✓ 全部完成！执行了 {progress['total']} 个任务。"
        elif progress["failed"] > 0:
            return f"⚠ 部分失败：{progress['completed']} 个成功，{progress['failed']} 个失败。"
        else:
            return f"执行中：{progress['completed']}/{progress['total']} 完成。"
    
    def _handle_help(self) -> ExecutionResult:
        """处理帮助请求"""
        help_text = """
我是您的智能操作系统助手，可以帮您完成以下操作：

📁 文件操作
  - 创建、读取、编辑、删除文件
  - 复制、移动、重命名文件
  - 查找文件

📂 目录操作
  - 创建、列出、删除文件夹
  - 切换目录

🔍 搜索功能
  - 搜索文件和文件夹
  - 搜索文件内容
  - 查找大文件、重复文件

🚀 应用管理
  - 打开、关闭应用程序
  - 查看运行中的程序

🌐 浏览器
  - 打开浏览器搜索
  - 访问网址

⚙️ 系统功能
  - 查看系统信息
  - 截图
  - 剪贴板操作
  - 执行命令

✏️ 内容创作
  - 编写文本、代码
  - 生成文档

示例命令：
  "打开记事本"
  "在桌面创建一个test.txt文件"
  "查找最近修改的PDF文件"
  "搜索Python教程"
  "查看系统信息"
        """
        
        return ExecutionResult(
            success=True,
            action="help",
            message=help_text.strip()
        )
    
    def _handle_cancel(self) -> ExecutionResult:
        """处理取消请求"""
        if self._is_running and self._current_plan:
            # 取消当前任务
            for task in self._current_plan.tasks:
                if task.status == TaskStatus.PENDING:
                    task.cancel()
            
            self._is_running = False
            return ExecutionResult(
                success=True,
                action="cancel",
                message="当前操作已取消"
            )
        
        return ExecutionResult(
            success=True,
            action="cancel",
            message="没有正在执行的操作"
        )
    
    def _learn_from_execution(self, command: str, plan: TaskPlan, success: bool) -> None:
        """从执行中学习"""
        if not self.memory:
            return
        
        # 记录常用命令模式
        self.memory.learn_pattern("command_patterns", {
            "command": command,
            "intent": plan.tasks[0].operation if plan.tasks else None,
            "success": success,
        })
        
        # 记录常用文件/应用
        for task in plan.tasks:
            if task.operation.startswith("file.") and task.parameters.get("path"):
                self.memory.add_frequently_used("files", task.parameters["path"])
            elif task.operation.startswith("app.") and task.parameters.get("app_name"):
                self.memory.add_frequently_used("apps", task.parameters["app_name"])
    
    # ==================
    # 快捷方法
    # ==================
    
    def open_app(self, app_name: str) -> ExecutionResult:
        """快速打开应用"""
        return self.execute(f"打开 {app_name}")
    
    def search_files(self, query: str, path: Optional[str] = None) -> ExecutionResult:
        """快速搜索文件"""
        cmd = f"搜索文件 {query}"
        if path:
            cmd += f" 在 {path}"
        return self.execute(cmd)
    
    def create_file(self, path: str, content: str = "") -> ExecutionResult:
        """快速创建文件"""
        result = self.executor_registry.execute("file.create", {
            "path": path,
            "content": content,
        })
        return ExecutionResult(
            success=result.success,
            action="file.create",
            message=result.message,
            data=result.data,
        )
    
    def read_file(self, path: str) -> ExecutionResult:
        """快速读取文件"""
        result = self.executor_registry.execute("file.read", {"path": path})
        return ExecutionResult(
            success=result.success,
            action="file.read",
            message=result.message,
            data=result.data,
        )
    
    def run_command(self, command: str) -> ExecutionResult:
        """快速执行命令"""
        result = self.executor_registry.execute("command.execute", {"command": command})
        return ExecutionResult(
            success=result.success,
            action="command.execute",
            message=result.message,
            data=result.data,
        )
    
    def get_system_info(self) -> ExecutionResult:
        """获取系统信息"""
        result = self.executor_registry.execute("system.info", {})
        return ExecutionResult(
            success=result.success,
            action="system.info",
            message=result.message,
            data=result.data,
        )
    
    def screenshot(self, path: Optional[str] = None) -> ExecutionResult:
        """截图"""
        result = self.executor_registry.execute("system.screenshot", {"path": path})
        return ExecutionResult(
            success=result.success,
            action="system.screenshot",
            message=result.message,
            data=result.data,
        )
    
    def search_web(self, query: str, engine: str = "google") -> ExecutionResult:
        """网页搜索"""
        result = self.executor_registry.execute("browser.search", {
            "query": query,
            "engine": engine,
        })
        return ExecutionResult(
            success=result.success,
            action="browser.search",
            message=result.message,
            data=result.data,
        )
    
    # ==================
    # 配置和回调
    # ==================
    
    def set_llm_client(self, llm_client) -> None:
        """设置LLM客户端"""
        self.llm_client = llm_client
        self.intent_parser.set_llm_client(llm_client)
        self.task_planner.set_llm_client(llm_client)
        self.executor_registry.set_llm_client(llm_client)
    
    def set_permission_level(self, level: PermissionLevel) -> None:
        """设置权限级别"""
        self.config.permission_level = level
    
    def on_task_start(self, callback: Callable[[Task], None]) -> None:
        """设置任务开始回调"""
        self._on_task_start = callback
    
    def on_task_complete(self, callback: Callable[[Task], None]) -> None:
        """设置任务完成回调"""
        self._on_task_complete = callback
    
    def on_task_error(self, callback: Callable[[Task, str], None]) -> None:
        """设置任务错误回调"""
        self._on_task_error = callback
    
    def set_confirmation_handler(self, handler: Callable[[str], bool]) -> None:
        """设置确认处理器"""
        self._confirmation_handler = handler
    
    # ==================
    # 状态和信息
    # ==================
    
    def get_context(self) -> ExecutionContext:
        """获取当前上下文"""
        return self.context
    
    def get_memory_summary(self) -> Optional[Dict]:
        """获取记忆摘要"""
        if self.memory:
            return self.memory.get_summary()
        return None
    
    def get_available_operations(self) -> List[str]:
        """获取可用操作列表"""
        return self.executor_registry.get_all_operations()
    
    def is_running(self) -> bool:
        """检查是否正在执行"""
        return self._is_running
    
    def get_current_plan(self) -> Optional[TaskPlan]:
        """获取当前执行计划"""
        return self._current_plan

