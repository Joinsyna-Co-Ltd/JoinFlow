"""
任务规划器
"""
import uuid
import logging
from typing import Dict, List, Optional

from .task import Task, TaskStatus
from ..intent.types import Intent, IntentType

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    任务规划器
    
    将用户意图分解为可执行的任务序列
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def plan(self, intent: Intent) -> List[Task]:
        """
        规划任务
        
        Args:
            intent: 用户意图
            
        Returns:
            List[Task]: 任务列表
        """
        # 简单意图 -> 单个任务
        if self._is_simple_intent(intent):
            return [self._create_task(intent)]
        
        # 复杂意图 -> 多任务分解
        if self.llm_client:
            return self._plan_with_llm(intent)
        
        # 默认单任务
        return [self._create_task(intent)]
    
    def _is_simple_intent(self, intent: Intent) -> bool:
        """判断是否为简单意图"""
        simple_types = [
            IntentType.FILE_READ,
            IntentType.FILE_OPEN,
            IntentType.DIR_LIST,
            IntentType.APP_OPEN,
            IntentType.APP_CLOSE,
            IntentType.BROWSER_NAVIGATE,
            IntentType.BROWSER_SEARCH,
            IntentType.SYSTEM_INFO,
            IntentType.SYSTEM_SCREENSHOT,
            IntentType.SYSTEM_CLIPBOARD,
            IntentType.HELP,
        ]
        return intent.type in simple_types
    
    def _create_task(self, intent: Intent, name: str = None) -> Task:
        """创建任务"""
        return Task(
            id=str(uuid.uuid4())[:8],
            name=name or f"执行: {intent.action}",
            action=intent.action,
            params=intent.params,
            metadata={"intent_type": intent.type.name},
        )
    
    def _plan_with_llm(self, intent: Intent) -> List[Task]:
        """使用LLM规划复杂任务"""
        try:
            prompt = f"""将以下任务分解为步骤：

任务: "{intent.command}"
类型: {intent.type.name}

返回JSON格式的步骤列表:
[{{"name": "步骤名", "action": "动作", "params": {{}}}}]

可用动作:
- file.create, file.read, file.write, file.delete, file.copy, file.move
- dir.create, dir.list
- search.file, search.content
- app.open, app.close
- browser.search, browser.navigate
- system.info, system.screenshot, system.command

只返回JSON数组。"""
            
            response = self.llm_client.chat(prompt)
            import json
            
            steps = json.loads(response.strip())
            
            tasks = []
            prev_id = None
            
            for step in steps:
                task = Task(
                    id=str(uuid.uuid4())[:8],
                    name=step.get("name", "未命名步骤"),
                    action=step.get("action", "unknown"),
                    params=step.get("params", {}),
                    depends_on=[prev_id] if prev_id else [],
                )
                tasks.append(task)
                prev_id = task.id
            
            return tasks if tasks else [self._create_task(intent)]
            
        except Exception as e:
            logger.warning(f"LLM规划失败: {e}")
            return [self._create_task(intent)]
    
    def replan(self, failed_task: Task, error: str, remaining_tasks: List[Task]) -> List[Task]:
        """
        任务失败后重新规划
        
        Args:
            failed_task: 失败的任务
            error: 错误信息
            remaining_tasks: 剩余任务
            
        Returns:
            List[Task]: 新的任务列表
        """
        if not self.llm_client:
            return []
        
        try:
            remaining_info = [{"name": t.name, "action": t.action} for t in remaining_tasks]
            
            prompt = f"""任务执行失败，请提供替代方案：

失败任务: {failed_task.name}
动作: {failed_task.action}
错误: {error}

剩余任务: {remaining_info}

返回JSON格式的替代步骤:
[{{"name": "步骤名", "action": "动作", "params": {{}}}}]

如果无法替代，返回空数组 []"""
            
            response = self.llm_client.chat(prompt)
            import json
            
            steps = json.loads(response.strip())
            
            return [
                Task(
                    id=str(uuid.uuid4())[:8],
                    name=step.get("name", "替代步骤"),
                    action=step.get("action", "unknown"),
                    params=step.get("params", {}),
                    metadata={"replanned": True},
                )
                for step in steps
            ]
            
        except Exception as e:
            logger.warning(f"重新规划失败: {e}")
            return []

