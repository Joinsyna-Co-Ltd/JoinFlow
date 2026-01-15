"""
执行器基类
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutorResult:
    """执行结果"""
    success: bool
    message: str
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


class BaseExecutor(ABC):
    """
    执行器基类
    
    所有具体执行器都需要继承此类
    """
    
    # 执行器名称
    name: str = "base"
    
    # 支持的操作列表
    supported_operations: List[str] = []
    
    def __init__(self, config=None):
        self.config = config
        self._action_log: List[Dict] = []
    
    @abstractmethod
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """
        执行操作
        
        Args:
            operation: 操作名称
            parameters: 操作参数
        
        Returns:
            ExecutorResult: 执行结果
        """
        pass
    
    def can_handle(self, operation: str) -> bool:
        """检查是否可以处理该操作"""
        return operation in self.supported_operations
    
    def validate_parameters(self, operation: str, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证参数
        
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        return True, ""
    
    def _log_action(self, action: str, message: str, **extra) -> None:
        """记录操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "executor": self.name,
            "action": action,
            "message": message,
            **extra
        }
        self._action_log.append(log_entry)
        logger.info(f"[{self.name}] {action}: {message}")
    
    def _measure_time(self, func, *args, **kwargs):
        """测量执行时间"""
        start = datetime.now()
        result = func(*args, **kwargs)
        duration = (datetime.now() - start).total_seconds() * 1000
        return result, duration
    
    def get_action_log(self) -> List[Dict]:
        """获取操作日志"""
        return self._action_log.copy()
    
    def clear_action_log(self) -> None:
        """清除操作日志"""
        self._action_log.clear()


class ExecutorError(Exception):
    """执行器错误"""
    
    def __init__(self, message: str, executor: str = "", operation: str = ""):
        self.message = message
        self.executor = executor
        self.operation = operation
        super().__init__(message)


class PermissionDeniedError(ExecutorError):
    """权限被拒绝"""
    pass


class ResourceNotFoundError(ExecutorError):
    """资源未找到"""
    pass


class OperationTimeoutError(ExecutorError):
    """操作超时"""
    pass

