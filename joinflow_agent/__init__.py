"""
JoinFlow Agent - Multi-Agent System for JoinFlow
===============================================

A complete multi-agent system including:

Core Agents:
- Browser Agent: Web automation and information extraction
- LLM Agent: Large Language Model interactions  
- OS Agent: Operating system file and process management
- Code Executor: Secure code execution in sandbox
- Data Agent: Data processing and analysis
- Vision Agent: Image understanding and multi-modal

Infrastructure:
- Orchestrator: Multi-agent coordination and task planning
- Session Manager: User session and conversation management
- Task Queue: Asynchronous task execution
- Web API: FastAPI-based REST/SSE endpoints

Example:
    from joinflow_agent import Orchestrator, AgentConfig
    
    orchestrator = Orchestrator(config=AgentConfig())
    result = orchestrator.execute("帮我搜索并总结今天的科技新闻")
    print(result.output)

API Server Example:
    from joinflow_agent import run_api, Orchestrator, SessionManager, TaskQueue
    
    orchestrator = Orchestrator()
    session_manager = SessionManager()
    task_queue = TaskQueue()
    
    run_api(orchestrator, session_manager, task_queue, port=8000)
"""

# Core base classes
from .base import (
    BaseAgent,
    AgentResult, 
    AgentConfig,
    AgentProtocol,
    AgentType,
    AgentStatus,
    AgentAction,
    Tool,
)

# Core agents
from .browser import BrowserAgent
from .browser_enhanced import EnhancedBrowserAgent, browse_and_analyze, search_web
from .llm import LLMAgent
from .os_agent import OSAgent
from .code_executor import CodeExecutorAgent, CodeSandbox, SandboxConfig
from .data_agent import DataProcessingAgent
from .vision_agent import VisionAgent

# Model manager
from .model_manager import ModelManager, get_model_manager, AgentType as ModelAgentType

# Orchestration
from .orchestrator import Orchestrator, TaskPlan, TaskStep

# Session management
from .session import SessionManager, Session, Message

# Task queue
from .task_queue import TaskQueue, Task, TaskStatus, TaskPriority, get_task_queue, submit_task

# API (optional - requires FastAPI)
try:
    from .api import create_api, run_api
    HAS_API = True
except ImportError:
    HAS_API = False
    create_api = None
    run_api = None

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    "AgentConfig", 
    "AgentProtocol",
    "AgentType",
    "AgentStatus",
    "AgentAction",
    "Tool",
    
    # Agents
    "BrowserAgent",
    "LLMAgent",
    "OSAgent",
    "CodeExecutorAgent",
    "CodeSandbox",
    "SandboxConfig",
    "DataProcessingAgent",
    "VisionAgent",
    
    # Orchestration
    "Orchestrator",
    "TaskPlan",
    "TaskStep",
    
    # Session
    "SessionManager",
    "Session",
    "Message",
    
    # Task Queue
    "TaskQueue",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "get_task_queue",
    "submit_task",
    
    # API
    "create_api",
    "run_api",
    "HAS_API",
]

__version__ = "0.2.0"
