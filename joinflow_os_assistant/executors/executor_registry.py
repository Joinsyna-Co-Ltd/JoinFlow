"""
执行器注册表 - 管理所有执行器
"""
import logging
from typing import Any, Dict, List, Optional, Type

from .base import BaseExecutor, ExecutorResult
from .file_executor import FileExecutor
from .app_executor import AppExecutor
from .search_executor import SearchExecutor
from .system_executor import SystemExecutor
from .browser_executor import BrowserExecutor
from .compose_executor import ComposeExecutor

logger = logging.getLogger(__name__)


class ExecutorRegistry:
    """
    执行器注册表
    
    管理所有执行器，根据操作类型路由到对应的执行器
    """
    
    def __init__(self, config=None, llm_client=None):
        self.config = config
        self.llm_client = llm_client
        self._executors: Dict[str, BaseExecutor] = {}
        self._operation_map: Dict[str, str] = {}  # operation -> executor_name
        
        # 注册默认执行器
        self._register_default_executors()
    
    def _register_default_executors(self) -> None:
        """注册默认执行器"""
        # 文件执行器
        self.register(FileExecutor(self.config))
        
        # 应用执行器
        self.register(AppExecutor(self.config))
        
        # 搜索执行器
        self.register(SearchExecutor(self.config))
        
        # 系统执行器
        self.register(SystemExecutor(self.config))
        
        # 浏览器执行器
        self.register(BrowserExecutor(self.config))
        
        # 编写执行器
        compose_executor = ComposeExecutor(self.config, self.llm_client)
        self.register(compose_executor)
    
    def register(self, executor: BaseExecutor) -> None:
        """注册执行器"""
        self._executors[executor.name] = executor
        
        # 建立操作到执行器的映射
        for operation in executor.supported_operations:
            self._operation_map[operation] = executor.name
        
        logger.info(f"Registered executor: {executor.name} with {len(executor.supported_operations)} operations")
    
    def unregister(self, executor_name: str) -> bool:
        """注销执行器"""
        if executor_name not in self._executors:
            return False
        
        executor = self._executors[executor_name]
        
        # 移除操作映射
        for operation in executor.supported_operations:
            if self._operation_map.get(operation) == executor_name:
                del self._operation_map[operation]
        
        del self._executors[executor_name]
        return True
    
    def get_executor(self, operation: str) -> Optional[BaseExecutor]:
        """根据操作获取执行器"""
        executor_name = self._operation_map.get(operation)
        if executor_name:
            return self._executors.get(executor_name)
        
        # 尝试根据操作前缀查找
        prefix = operation.split(".")[0]
        return self._executors.get(prefix)
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行操作"""
        executor = self.get_executor(operation)
        
        if not executor:
            return ExecutorResult(
                success=False,
                message=f"未找到处理操作 '{operation}' 的执行器",
                error="NoExecutor"
            )
        
        # 验证参数
        valid, error = executor.validate_parameters(operation, parameters)
        if not valid:
            return ExecutorResult(
                success=False,
                message=f"参数验证失败: {error}",
                error="InvalidParameters"
            )
        
        # 执行操作
        try:
            result = executor.execute(operation, parameters)
            return result
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            return ExecutorResult(
                success=False,
                message=f"执行错误: {e}",
                error=str(type(e).__name__)
            )
    
    def can_handle(self, operation: str) -> bool:
        """检查是否可以处理该操作"""
        return operation in self._operation_map or operation.split(".")[0] in self._executors
    
    def get_all_operations(self) -> List[str]:
        """获取所有支持的操作"""
        return list(self._operation_map.keys())
    
    def get_executor_info(self) -> Dict[str, Any]:
        """获取执行器信息"""
        info = {}
        for name, executor in self._executors.items():
            info[name] = {
                "operations": executor.supported_operations,
                "operation_count": len(executor.supported_operations),
            }
        return info
    
    def set_llm_client(self, llm_client) -> None:
        """设置LLM客户端"""
        self.llm_client = llm_client
        
        # 更新需要LLM的执行器
        if "compose" in self._executors:
            self._executors["compose"].set_llm_client(llm_client)
    
    def get_action_logs(self) -> Dict[str, List[Dict]]:
        """获取所有执行器的操作日志"""
        logs = {}
        for name, executor in self._executors.items():
            logs[name] = executor.get_action_log()
        return logs
    
    def clear_action_logs(self) -> None:
        """清除所有操作日志"""
        for executor in self._executors.values():
            executor.clear_action_log()


# 全局执行器注册表
_global_registry: Optional[ExecutorRegistry] = None


def get_global_registry(config=None, llm_client=None) -> ExecutorRegistry:
    """获取全局执行器注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ExecutorRegistry(config, llm_client)
    return _global_registry


def reset_global_registry() -> None:
    """重置全局执行器注册表"""
    global _global_registry
    _global_registry = None

