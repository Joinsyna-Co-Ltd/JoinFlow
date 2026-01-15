"""
Hierarchical Planner - 分层任务规划器
=====================================

实现类似 Agent-S 的分层规划能力：
1. 将复杂任务分解为子任务
2. 为每个子任务生成具体步骤
3. 动态调整计划
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SubtaskStatus(Enum):
    """子任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Subtask:
    """子任务"""
    id: int
    description: str
    expected_result: str
    status: SubtaskStatus = SubtaskStatus.PENDING
    steps_taken: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "expected_result": self.expected_result,
            "status": self.status.value,
            "steps_taken": self.steps_taken,
            "error": self.error,
        }


@dataclass
class TaskPlan:
    """任务计划"""
    task: str
    task_understanding: str
    prerequisites: List[str]
    subtasks: List[Subtask]
    success_criteria: str
    current_subtask_index: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def current_subtask(self) -> Optional[Subtask]:
        if 0 <= self.current_subtask_index < len(self.subtasks):
            return self.subtasks[self.current_subtask_index]
        return None
    
    @property
    def progress(self) -> float:
        if not self.subtasks:
            return 0.0
        completed = sum(1 for s in self.subtasks if s.status == SubtaskStatus.COMPLETED)
        return completed / len(self.subtasks) * 100
    
    @property
    def is_complete(self) -> bool:
        return all(s.status in (SubtaskStatus.COMPLETED, SubtaskStatus.SKIPPED) 
                   for s in self.subtasks)
    
    def advance(self) -> bool:
        """前进到下一个子任务"""
        if self.current_subtask:
            self.current_subtask.status = SubtaskStatus.COMPLETED
        self.current_subtask_index += 1
        if self.current_subtask:
            self.current_subtask.status = SubtaskStatus.IN_PROGRESS
            return True
        return False
    
    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "task_understanding": self.task_understanding,
            "prerequisites": self.prerequisites,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "success_criteria": self.success_criteria,
            "current_subtask_index": self.current_subtask_index,
            "progress": self.progress,
        }


class HierarchicalPlanner:
    """
    分层规划器
    
    将复杂任务分解为可管理的子任务序列
    """
    
    PLANNING_PROMPT = """你是一个任务规划专家。分析用户任务，制定详细的执行计划。

任务：{task}
当前屏幕状态：{screen_description}

请制定分层执行计划，返回 JSON 格式：
```json
{{
    "task_understanding": "对任务的理解和分析",
    "prerequisites": ["前置条件1", "前置条件2"],
    "subtasks": [
        {{
            "id": 1,
            "description": "子任务描述",
            "expected_result": "预期结果"
        }},
        {{
            "id": 2,
            "description": "子任务描述",
            "expected_result": "预期结果"
        }}
    ],
    "success_criteria": "任务完成的判断标准"
}}
```

规划原则：
1. 每个子任务应该是原子操作（1-3步可完成）
2. 子任务之间有清晰的依赖关系
3. 考虑可能的失败情况
4. 预期结果要具体可验证

只返回 JSON，不要其他内容。"""

    REPLAN_PROMPT = """任务执行遇到问题，需要重新规划。

原始任务：{task}
当前计划：{current_plan}
已完成子任务：{completed_subtasks}
当前问题：{error}
当前屏幕：{screen_description}

请根据当前情况调整计划，返回新的子任务列表：
```json
{{
    "analysis": "问题分析",
    "should_continue": true/false,
    "new_subtasks": [
        {{
            "id": 1,
            "description": "新的子任务描述",
            "expected_result": "预期结果"
        }}
    ],
    "alternative_approach": "替代方案（如有）"
}}
```
"""

    def __init__(self, llm_client=None, model: str = "openrouter/google/gemini-2.0-flash-exp:free"):
        self._llm_client = llm_client
        self.model = model
        self._current_plan: Optional[TaskPlan] = None
    
    def set_llm_client(self, client, model: str = None):
        """设置 LLM 客户端"""
        self._llm_client = client
        if model:
            self.model = model
    
    def create_plan(
        self, 
        task: str, 
        screen_description: str = "",
        api_key: str = None,
        base_url: str = None
    ) -> Optional[TaskPlan]:
        """
        为任务创建执行计划
        
        Args:
            task: 任务描述
            screen_description: 当前屏幕描述
            
        Returns:
            TaskPlan 或 None
        """
        if not self._llm_client:
            # 没有 LLM，返回简单计划
            return self._create_simple_plan(task)
        
        prompt = self.PLANNING_PROMPT.format(
            task=task,
            screen_description=screen_description or "未提供"
        )
        
        try:
            response = self._llm_client.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
                max_tokens=1500,
            )
            
            content = response.choices[0].message.content
            plan = self._parse_plan_response(content, task)
            
            if plan:
                self._current_plan = plan
                if plan.subtasks:
                    plan.subtasks[0].status = SubtaskStatus.IN_PROGRESS
                logger.info(f"Created plan with {len(plan.subtasks)} subtasks")
            
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return self._create_simple_plan(task)
    
    def _parse_plan_response(self, response: str, task: str) -> Optional[TaskPlan]:
        """解析规划响应"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return None
            
            data = json.loads(json_match.group())
            
            subtasks = []
            for st_data in data.get("subtasks", []):
                subtasks.append(Subtask(
                    id=st_data.get("id", len(subtasks) + 1),
                    description=st_data.get("description", ""),
                    expected_result=st_data.get("expected_result", ""),
                ))
            
            return TaskPlan(
                task=task,
                task_understanding=data.get("task_understanding", ""),
                prerequisites=data.get("prerequisites", []),
                subtasks=subtasks,
                success_criteria=data.get("success_criteria", ""),
            )
            
        except Exception as e:
            logger.error(f"Failed to parse plan: {e}")
            return None
    
    def _create_simple_plan(self, task: str) -> TaskPlan:
        """创建简单计划（无 LLM 时使用）"""
        return TaskPlan(
            task=task,
            task_understanding=f"执行任务: {task}",
            prerequisites=[],
            subtasks=[
                Subtask(
                    id=1,
                    description=task,
                    expected_result="任务完成",
                    status=SubtaskStatus.IN_PROGRESS,
                )
            ],
            success_criteria="任务成功执行",
        )
    
    def replan(
        self,
        error: str,
        screen_description: str = "",
        api_key: str = None,
        base_url: str = None
    ) -> Optional[TaskPlan]:
        """
        根据错误重新规划
        """
        if not self._current_plan or not self._llm_client:
            return None
        
        completed = [s.description for s in self._current_plan.subtasks 
                    if s.status == SubtaskStatus.COMPLETED]
        
        prompt = self.REPLAN_PROMPT.format(
            task=self._current_plan.task,
            current_plan=json.dumps([s.to_dict() for s in self._current_plan.subtasks], ensure_ascii=False),
            completed_subtasks=", ".join(completed) or "无",
            error=error,
            screen_description=screen_description or "未提供"
        )
        
        try:
            response = self._llm_client.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', content)
            
            if json_match:
                data = json.loads(json_match.group())
                
                if not data.get("should_continue", True):
                    return None
                
                # 创建新的子任务
                new_subtasks = []
                for st_data in data.get("new_subtasks", []):
                    new_subtasks.append(Subtask(
                        id=st_data.get("id", len(new_subtasks) + 1),
                        description=st_data.get("description", ""),
                        expected_result=st_data.get("expected_result", ""),
                    ))
                
                if new_subtasks:
                    # 保留已完成的子任务，替换未完成的
                    completed_subtasks = [s for s in self._current_plan.subtasks 
                                         if s.status == SubtaskStatus.COMPLETED]
                    self._current_plan.subtasks = completed_subtasks + new_subtasks
                    self._current_plan.current_subtask_index = len(completed_subtasks)
                    
                    if self._current_plan.current_subtask:
                        self._current_plan.current_subtask.status = SubtaskStatus.IN_PROGRESS
                    
                    logger.info(f"Replanned with {len(new_subtasks)} new subtasks")
                    return self._current_plan
            
        except Exception as e:
            logger.error(f"Replan failed: {e}")
        
        return None
    
    @property
    def current_plan(self) -> Optional[TaskPlan]:
        return self._current_plan
    
    def get_current_focus(self) -> str:
        """获取当前关注的子任务描述"""
        if self._current_plan and self._current_plan.current_subtask:
            return self._current_plan.current_subtask.description
        return ""
    
    def mark_subtask_complete(self) -> bool:
        """标记当前子任务完成，前进到下一个"""
        if self._current_plan:
            return self._current_plan.advance()
        return False
    
    def mark_subtask_failed(self, error: str) -> None:
        """标记当前子任务失败"""
        if self._current_plan and self._current_plan.current_subtask:
            self._current_plan.current_subtask.status = SubtaskStatus.FAILED
            self._current_plan.current_subtask.error = error

