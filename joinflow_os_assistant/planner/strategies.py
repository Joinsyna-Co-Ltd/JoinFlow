"""
执行策略
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Any
import asyncio
import logging

from .task import Task, TaskPlan, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class ExecutionStrategy(ABC):
    """执行策略基类"""
    
    @abstractmethod
    def execute(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """
        执行任务计划
        
        Args:
            plan: 任务计划
            executor: 任务执行器函数
        
        Returns:
            bool: 是否全部成功
        """
        pass
    
    @abstractmethod
    async def execute_async(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """异步执行"""
        pass


class SequentialStrategy(ExecutionStrategy):
    """
    顺序执行策略
    
    按顺序执行所有任务，遇到失败可选择停止或继续
    """
    
    def __init__(self, stop_on_failure: bool = True):
        self.stop_on_failure = stop_on_failure
    
    def execute(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """顺序执行任务"""
        plan.status = TaskStatus.RUNNING
        all_success = True
        
        for task in plan.tasks:
            if task.status in {TaskStatus.CANCELLED, TaskStatus.COMPLETED}:
                continue
            
            # 检查依赖
            if task.dependencies:
                deps_ok = all(
                    self._get_task_by_id(plan, dep_id).status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if not deps_ok:
                    task.fail("依赖任务未完成")
                    all_success = False
                    if self.stop_on_failure:
                        break
                    continue
            
            # 执行任务
            task.start()
            try:
                result = executor(task)
                task.complete(result)
                
                if not result.success:
                    all_success = False
                    if self.stop_on_failure:
                        break
                        
            except Exception as e:
                task.fail(str(e))
                all_success = False
                if self.stop_on_failure:
                    break
        
        plan.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        return all_success
    
    async def execute_async(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """异步顺序执行"""
        # 对于顺序执行，异步和同步基本相同
        return self.execute(plan, executor)
    
    def _get_task_by_id(self, plan: TaskPlan, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        for task in plan.tasks:
            if task.id == task_id:
                return task
        return None


class ParallelStrategy(ExecutionStrategy):
    """
    并行执行策略
    
    并行执行所有没有依赖的任务
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def execute(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """并行执行（使用线程池）"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        plan.status = TaskStatus.RUNNING
        all_success = True
        completed_ids = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while True:
                # 获取准备就绪的任务
                ready_tasks = [
                    t for t in plan.tasks
                    if t.status == TaskStatus.PENDING and t.is_ready(completed_ids)
                ]
                
                if not ready_tasks:
                    # 检查是否还有任务在执行
                    running = [t for t in plan.tasks if t.status == TaskStatus.RUNNING]
                    if not running:
                        break
                    continue
                
                # 提交任务
                futures = {}
                for task in ready_tasks:
                    task.start()
                    future = pool.submit(self._execute_task, task, executor)
                    futures[future] = task
                
                # 等待任务完成
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        task.complete(result)
                        
                        if result.success:
                            completed_ids.add(task.id)
                        else:
                            all_success = False
                            
                    except Exception as e:
                        task.fail(str(e))
                        all_success = False
        
        plan.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        return all_success
    
    async def execute_async(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """异步并行执行"""
        plan.status = TaskStatus.RUNNING
        all_success = True
        completed_ids = set()
        
        while True:
            # 获取准备就绪的任务
            ready_tasks = [
                t for t in plan.tasks
                if t.status == TaskStatus.PENDING and t.is_ready(completed_ids)
            ]
            
            if not ready_tasks:
                running = [t for t in plan.tasks if t.status == TaskStatus.RUNNING]
                if not running:
                    break
                await asyncio.sleep(0.1)
                continue
            
            # 限制并发数
            ready_tasks = ready_tasks[:self.max_workers]
            
            # 并发执行
            async def run_task(task):
                task.start()
                try:
                    # 如果执行器是协程，直接await，否则在线程中运行
                    if asyncio.iscoroutinefunction(executor):
                        result = await executor(task)
                    else:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, executor, task)
                    task.complete(result)
                    return task, result
                except Exception as e:
                    task.fail(str(e))
                    return task, TaskResult(success=False, error=str(e))
            
            results = await asyncio.gather(*[run_task(t) for t in ready_tasks])
            
            for task, result in results:
                if result.success:
                    completed_ids.add(task.id)
                else:
                    all_success = False
        
        plan.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        return all_success
    
    def _execute_task(self, task: Task, executor: Callable[[Task], TaskResult]) -> TaskResult:
        """执行单个任务"""
        try:
            return executor(task)
        except Exception as e:
            return TaskResult(success=False, error=str(e))


class MixedStrategy(ExecutionStrategy):
    """
    混合执行策略
    
    根据任务依赖关系自动决定顺序或并行执行
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.sequential = SequentialStrategy(stop_on_failure=False)
        self.parallel = ParallelStrategy(max_workers=max_workers)
    
    def execute(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """根据任务依赖关系选择执行策略"""
        # 分析任务依赖
        has_dependencies = any(t.dependencies for t in plan.tasks)
        
        if not has_dependencies:
            # 没有依赖，可以完全并行
            return self.parallel.execute(plan, executor)
        
        # 有依赖，分层执行
        return self._execute_layered(plan, executor)
    
    async def execute_async(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """异步混合执行"""
        has_dependencies = any(t.dependencies for t in plan.tasks)
        
        if not has_dependencies:
            return await self.parallel.execute_async(plan, executor)
        
        return await self._execute_layered_async(plan, executor)
    
    def _execute_layered(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """分层执行"""
        plan.status = TaskStatus.RUNNING
        all_success = True
        completed_ids = set()
        
        while True:
            # 获取当前层可执行的任务
            current_layer = [
                t for t in plan.tasks
                if t.status == TaskStatus.PENDING and t.is_ready(completed_ids)
            ]
            
            if not current_layer:
                break
            
            # 并行执行当前层
            layer_plan = TaskPlan(tasks=current_layer)
            layer_success = self.parallel.execute(layer_plan, executor)
            
            if not layer_success:
                all_success = False
            
            # 更新完成列表
            for task in current_layer:
                if task.status == TaskStatus.COMPLETED:
                    completed_ids.add(task.id)
        
        plan.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        return all_success
    
    async def _execute_layered_async(self, plan: TaskPlan, executor: Callable[[Task], TaskResult]) -> bool:
        """异步分层执行"""
        plan.status = TaskStatus.RUNNING
        all_success = True
        completed_ids = set()
        
        while True:
            current_layer = [
                t for t in plan.tasks
                if t.status == TaskStatus.PENDING and t.is_ready(completed_ids)
            ]
            
            if not current_layer:
                break
            
            layer_plan = TaskPlan(tasks=current_layer)
            layer_success = await self.parallel.execute_async(layer_plan, executor)
            
            if not layer_success:
                all_success = False
            
            for task in current_layer:
                if task.status == TaskStatus.COMPLETED:
                    completed_ids.add(task.id)
        
        plan.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        return all_success

