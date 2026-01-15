"""
任务规划器
"""
import json
import logging
from typing import Any, Dict, List, Optional

from ..intent.types import Intent, IntentType, EntityType
from .task import Task, TaskPlan, TaskPriority

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    任务规划器
    
    将意图转换为可执行的任务计划
    """
    
    # 意图到操作的映射
    INTENT_TO_OPERATION = {
        IntentType.FILE_CREATE: "file.create",
        IntentType.FILE_READ: "file.read",
        IntentType.FILE_WRITE: "file.write",
        IntentType.FILE_DELETE: "file.delete",
        IntentType.FILE_COPY: "file.copy",
        IntentType.FILE_MOVE: "file.move",
        IntentType.FILE_OPEN: "file.open",
        IntentType.DIR_CREATE: "dir.create",
        IntentType.DIR_LIST: "dir.list",
        IntentType.DIR_DELETE: "dir.delete",
        IntentType.DIR_NAVIGATE: "dir.navigate",
        IntentType.SEARCH_FILE: "search.file",
        IntentType.SEARCH_CONTENT: "search.content",
        IntentType.SEARCH_APP: "search.app",
        IntentType.APP_OPEN: "app.open",
        IntentType.APP_CLOSE: "app.close",
        IntentType.APP_LIST: "app.list",
        IntentType.BROWSER_OPEN: "browser.open",
        IntentType.BROWSER_SEARCH: "browser.search",
        IntentType.BROWSER_NAVIGATE: "browser.navigate",
        IntentType.SYSTEM_INFO: "system.info",
        IntentType.SYSTEM_CLIPBOARD_GET: "clipboard.get",
        IntentType.SYSTEM_CLIPBOARD_SET: "clipboard.set",
        IntentType.SYSTEM_SCREENSHOT: "system.screenshot",
        IntentType.SYSTEM_NOTIFY: "system.notify",
        IntentType.EXECUTE_COMMAND: "command.execute",
        IntentType.EXECUTE_SCRIPT: "script.execute",
        IntentType.COMPOSE_TEXT: "compose.text",
        IntentType.COMPOSE_CODE: "compose.code",
        IntentType.COMPOSE_EMAIL: "compose.email",
    }
    
    # LLM 任务规划提示词
    PLAN_PROMPT = """你是一个任务规划器。将用户的复杂请求分解为具体的执行步骤。

用户请求: "{user_input}"
已识别意图: {intent_info}

请规划执行步骤，返回JSON格式：
{{
    "plan_name": "计划名称",
    "strategy": "sequential 或 parallel",
    "tasks": [
        {{
            "name": "任务名称",
            "description": "任务描述",
            "operation": "操作类型",
            "parameters": {{}},
            "dependencies": [],  // 依赖的任务索引
            "priority": "NORMAL"  // LOW, NORMAL, HIGH, CRITICAL
        }}
    ]
}}

可用的操作类型：
- file.create, file.read, file.write, file.delete, file.copy, file.move, file.open
- dir.create, dir.list, dir.delete, dir.navigate
- search.file, search.content
- app.open, app.close, app.list
- browser.open, browser.search, browser.navigate
- system.info, system.screenshot, system.notify
- clipboard.get, clipboard.set
- command.execute, script.execute
- compose.text, compose.code

只返回JSON，不要其他内容。"""

    def __init__(self, llm_client=None):
        """
        初始化规划器
        
        Args:
            llm_client: LLM客户端（可选）
        """
        self.llm_client = llm_client
    
    def plan(self, intent: Intent) -> TaskPlan:
        """
        根据意图创建任务计划
        
        Args:
            intent: 解析后的意图
        
        Returns:
            TaskPlan: 任务计划
        """
        # 处理复合意图
        if intent.type == IntentType.COMPOUND and intent.sub_intents:
            return self._plan_compound(intent)
        
        # 简单意图 - 直接映射
        if intent.type in self.INTENT_TO_OPERATION:
            return self._plan_simple(intent)
        
        # 未知意图或复杂意图 - 使用LLM规划
        if self.llm_client:
            return self._plan_with_llm(intent)
        
        # 创建默认空计划
        return TaskPlan(
            name="未知任务",
            user_input=intent.raw_input,
            tasks=[],
        )
    
    def _plan_simple(self, intent: Intent) -> TaskPlan:
        """规划简单任务"""
        operation = self.INTENT_TO_OPERATION.get(intent.type, "unknown")
        
        # 从意图中提取参数
        parameters = self._extract_parameters(intent)
        
        task = Task(
            name=intent.description or f"执行 {operation}",
            description=intent.description,
            operation=operation,
            parameters=parameters,
            priority=self._get_priority(intent),
            requires_confirmation=intent.requires_confirmation,
        )
        
        plan = TaskPlan(
            name=intent.description or "任务计划",
            user_input=intent.raw_input,
            tasks=[task],
            strategy="sequential",
        )
        
        return plan
    
    def _plan_compound(self, intent: Intent) -> TaskPlan:
        """规划复合任务"""
        tasks = []
        
        for i, sub_intent in enumerate(intent.sub_intents):
            operation = self.INTENT_TO_OPERATION.get(sub_intent.type, "unknown")
            parameters = self._extract_parameters(sub_intent)
            
            task = Task(
                name=sub_intent.description or f"步骤 {i+1}",
                description=sub_intent.description,
                operation=operation,
                parameters=parameters,
                priority=self._get_priority(sub_intent),
                requires_confirmation=sub_intent.requires_confirmation,
                # 默认顺序依赖
                dependencies=[tasks[-1].id] if tasks else [],
            )
            tasks.append(task)
        
        plan = TaskPlan(
            name=intent.description or "复合任务计划",
            user_input=intent.raw_input,
            tasks=tasks,
            strategy="sequential",
        )
        
        return plan
    
    def _plan_with_llm(self, intent: Intent) -> TaskPlan:
        """使用LLM进行复杂规划"""
        try:
            prompt = self.PLAN_PROMPT.format(
                user_input=intent.raw_input,
                intent_info=json.dumps(intent.to_dict(), ensure_ascii=False)
            )
            
            response = self.llm_client.chat(prompt)
            
            # 解析响应
            return self._parse_llm_plan(response, intent)
            
        except Exception as e:
            logger.error(f"LLM规划失败: {e}")
            return self._plan_simple(intent)
    
    def _parse_llm_plan(self, response: str, intent: Intent) -> TaskPlan:
        """解析LLM返回的计划"""
        try:
            # 提取JSON
            json_str = response.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            
            data = json.loads(json_str)
            
            # 创建任务
            tasks = []
            task_id_map = {}  # 索引到ID的映射
            
            for i, task_data in enumerate(data.get("tasks", [])):
                task = Task(
                    name=task_data.get("name", f"任务 {i+1}"),
                    description=task_data.get("description", ""),
                    operation=task_data.get("operation", "unknown"),
                    parameters=task_data.get("parameters", {}),
                    priority=self._parse_priority(task_data.get("priority", "NORMAL")),
                )
                
                task_id_map[i] = task.id
                tasks.append(task)
            
            # 处理依赖关系
            for i, task_data in enumerate(data.get("tasks", [])):
                deps = task_data.get("dependencies", [])
                tasks[i].dependencies = [task_id_map[d] for d in deps if d in task_id_map]
            
            plan = TaskPlan(
                name=data.get("plan_name", "AI规划任务"),
                user_input=intent.raw_input,
                tasks=tasks,
                strategy=data.get("strategy", "sequential"),
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"解析LLM计划失败: {e}")
            return self._plan_simple(intent)
    
    def _extract_parameters(self, intent: Intent) -> Dict[str, Any]:
        """从意图中提取参数"""
        params = {}
        
        # 文件路径
        file_entity = intent.get_entity(EntityType.FILE_PATH)
        if file_entity:
            params["path"] = file_entity.value
        
        # 目录路径
        dir_entity = intent.get_entity(EntityType.DIR_PATH)
        if dir_entity:
            params["directory"] = dir_entity.value
        
        # 应用名称
        app_entity = intent.get_entity(EntityType.APP_NAME)
        if app_entity:
            params["app_name"] = app_entity.value
        
        # URL
        url_entity = intent.get_entity(EntityType.URL)
        if url_entity:
            params["url"] = url_entity.value
        
        # 搜索关键词
        search_entity = intent.get_entity(EntityType.SEARCH_QUERY)
        if search_entity:
            params["query"] = search_entity.value
        
        # 文本内容
        content_entity = intent.get_entity(EntityType.TEXT_CONTENT)
        if content_entity:
            params["content"] = content_entity.value
        
        # 命令
        command_entity = intent.get_entity(EntityType.COMMAND)
        if command_entity:
            params["command"] = command_entity.value
        
        # 文件类型
        type_entity = intent.get_entity(EntityType.FILE_TYPE)
        if type_entity:
            params["file_type"] = type_entity.value
        
        # 从意图参数中补充
        params.update(intent.parameters)
        
        return params
    
    def _get_priority(self, intent: Intent) -> TaskPriority:
        """获取任务优先级"""
        # 根据意图优先级映射
        if intent.priority >= 8:
            return TaskPriority.CRITICAL
        elif intent.priority >= 6:
            return TaskPriority.HIGH
        elif intent.priority >= 3:
            return TaskPriority.NORMAL
        else:
            return TaskPriority.LOW
    
    def _parse_priority(self, priority_str: str) -> TaskPriority:
        """解析优先级字符串"""
        try:
            return TaskPriority[priority_str.upper()]
        except KeyError:
            return TaskPriority.NORMAL
    
    def set_llm_client(self, llm_client) -> None:
        """设置LLM客户端"""
        self.llm_client = llm_client
    
    def optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """优化任务计划"""
        # 检测可以并行执行的任务
        can_parallel = self._detect_parallelism(plan)
        
        if can_parallel:
            plan.strategy = "parallel"
        
        # 重新排序任务（按优先级）
        plan.tasks.sort(
            key=lambda t: (len(t.dependencies), -t.priority.value),
        )
        
        return plan
    
    def _detect_parallelism(self, plan: TaskPlan) -> bool:
        """检测是否可以并行执行"""
        # 如果没有依赖关系，可以并行
        if not any(t.dependencies for t in plan.tasks):
            return True
        
        # 检查是否有独立的任务组
        independent_count = sum(1 for t in plan.tasks if not t.dependencies)
        return independent_count >= 2


class SmartTaskPlanner(TaskPlanner):
    """
    智能任务规划器
    
    在基础规划器上增加：
    - 上下文感知
    - 学习用户习惯
    - 智能参数补全
    """
    
    def __init__(self, llm_client=None, memory=None):
        super().__init__(llm_client)
        self.memory = memory
    
    def plan(self, intent: Intent, context=None) -> TaskPlan:
        """
        根据意图和上下文创建任务计划
        """
        # 参数补全
        self._complete_parameters(intent, context)
        
        # 调用父类规划
        plan = super().plan(intent)
        
        # 根据记忆优化
        if self.memory:
            plan = self._optimize_with_memory(plan)
        
        return plan
    
    def _complete_parameters(self, intent: Intent, context=None) -> None:
        """补全缺失的参数"""
        if not context:
            return
        
        # 如果没有文件路径，使用当前目录
        if not intent.get_entity(EntityType.FILE_PATH):
            if intent.type in {IntentType.FILE_CREATE, IntentType.DIR_CREATE}:
                intent.parameters.setdefault("directory", context.current_dir)
        
        # 搜索时使用默认位置
        if intent.type == IntentType.SEARCH_FILE:
            if "search_paths" not in intent.parameters:
                intent.parameters["search_paths"] = [context.current_dir]
    
    def _optimize_with_memory(self, plan: TaskPlan) -> TaskPlan:
        """根据记忆优化计划"""
        if not self.memory:
            return plan
        
        # 获取用户的常用操作模式
        patterns = self.memory.get_patterns("task_execution")
        
        if patterns:
            # 根据历史模式调整策略
            pass
        
        return plan

