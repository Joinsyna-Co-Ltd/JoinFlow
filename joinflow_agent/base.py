"""
Agent Base Classes and Protocols
================================

Defines the core abstractions for all agents in the system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Protocol, Sequence
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    """Types of agents in the system"""
    BROWSER = "browser"
    LLM = "llm"
    OS = "os"
    RAG = "rag"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentConfig:
    """Global agent configuration"""
    # LLM settings
    llm_model: str = "gpt-4o-mini"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    
    # Browser settings
    browser_headless: bool = True
    browser_timeout: int = 30000  # ms
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 720
    
    # OS Agent settings
    os_workspace: str = "./workspace"
    os_allowed_extensions: Sequence[str] = field(default_factory=lambda: [
        ".txt", ".md", ".py", ".json", ".csv", ".html", ".xml", ".yaml", ".yml"
    ])
    os_max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Memory settings
    memory_collection: str = "user_history"
    memory_vector_dim: int = 384
    
    # Execution settings
    max_retries: int = 3
    retry_delay: float = 1.0
    execution_timeout: int = 300  # seconds
    
    # Logging
    verbose: bool = True
    log_level: str = "INFO"


@dataclass
class AgentAction:
    """Represents a single action taken by an agent"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class AgentResult:
    """Result returned by agent execution"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.LLM
    status: AgentStatus = AgentStatus.SUCCESS
    
    # Main output
    output: str = ""
    data: Optional[Any] = None
    
    # Execution trace
    actions: list[AgentAction] = field(default_factory=list)
    
    # Metadata
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    tokens_used: int = 0
    cost: float = 0.0
    
    # Error handling
    error: Optional[str] = None
    error_trace: Optional[str] = None
    
    def add_action(self, action: AgentAction) -> None:
        """Add an action to the execution trace"""
        self.actions.append(action)
    
    def finalize(self, success: bool = True, error: Optional[str] = None) -> None:
        """Finalize the result with end time and status"""
        self.end_time = datetime.now()
        self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = AgentStatus.SUCCESS if success else AgentStatus.FAILED
        if error:
            self.error = error


class AgentProtocol(Protocol):
    """Protocol that all agents must implement"""
    
    @property
    def agent_type(self) -> AgentType: ...
    
    @property
    def name(self) -> str: ...
    
    @property
    def description(self) -> str: ...
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult: ...
    
    def can_handle(self, task: str) -> bool: ...


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides common functionality:
    - Configuration management
    - Logging
    - Error handling
    - Action tracking
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self._setup_logging()
        self._status = AgentStatus.IDLE
    
    def _setup_logging(self) -> None:
        """Setup logging for the agent"""
        self.logger = logging.getLogger(f"joinflow.{self.__class__.__name__}")
        if self.config.verbose:
            self.logger.setLevel(getattr(logging, self.config.log_level))
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the type of this agent"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the agent"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this agent can do"""
        pass
    
    @abstractmethod
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """
        Execute a task.
        
        Args:
            task: The task description to execute
            context: Optional context from previous agents or user
            
        Returns:
            AgentResult with the execution outcome
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: str) -> bool:
        """
        Check if this agent can handle the given task.
        
        Args:
            task: Task description
            
        Returns:
            True if this agent is suitable for the task
        """
        pass
    
    def _create_result(self) -> AgentResult:
        """Create a new result object for this agent"""
        return AgentResult(agent_type=self.agent_type)
    
    def _log_action(self, result: AgentResult, action_type: str, 
                    description: str, **params) -> AgentAction:
        """Log an action and add it to the result"""
        action = AgentAction(
            action_type=action_type,
            description=description,
            parameters=params
        )
        result.add_action(action)
        self.logger.info(f"[{action_type}] {description}")
        return action
    
    def _handle_error(self, result: AgentResult, error: Exception) -> AgentResult:
        """Handle an error during execution"""
        import traceback
        result.error = str(error)
        result.error_trace = traceback.format_exc()
        result.finalize(success=False, error=str(error))
        self.logger.error(f"Agent error: {error}")
        return result


class Tool:
    """
    Represents a tool that agents can use.
    
    Tools are callable functions with metadata.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[dict] = None
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}
    
    def __call__(self, *args, **kwargs) -> Any:
        return self.func(*args, **kwargs)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for LLM function calling"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

