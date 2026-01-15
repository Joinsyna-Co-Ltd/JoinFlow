"""
Agent Orchestrator
==================

Coordinates multiple agents to complete complex tasks:
- Task planning and decomposition
- Agent selection and routing
- Execution coordination
- Result aggregation
"""

import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Sequence
from enum import Enum
import logging
import uuid

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType,
    AgentAction, AgentStatus, Tool
)
from .browser import BrowserAgent
from .llm import LLMAgent
from .os_agent import OSAgent
from .code_executor import CodeExecutorAgent
from .data_agent import DataProcessingAgent
from .vision_agent import VisionAgent

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskStep:
    """A single step in a task plan"""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    agent_type: AgentType = AgentType.LLM
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Optional[AgentResult] = None
    
    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "dependencies": self.dependencies,
            "status": self.status
        }


@dataclass
class TaskPlan:
    """Execution plan for a complex task"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_task: str = ""
    steps: list[TaskStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_next_step(self) -> Optional[TaskStep]:
        """Get the next executable step"""
        for step in self.steps:
            if step.status == "pending":
                # Check if all dependencies are completed
                deps_completed = all(
                    self.get_step(dep_id).status == "completed"
                    for dep_id in step.dependencies
                    if self.get_step(dep_id)
                )
                if deps_completed:
                    return step
        return None
    
    def get_step(self, step_id: str) -> Optional[TaskStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are complete"""
        return all(s.status in ("completed", "skipped", "failed") for s in self.steps)
    
    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "original_task": self.original_task,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat()
        }


class Orchestrator(BaseAgent):
    """
    Main orchestrator that coordinates multiple agents.
    
    Capabilities:
    - Analyze tasks and create execution plans
    - Route tasks to appropriate agents
    - Manage multi-step workflows
    - Aggregate results from multiple agents
    - Handle errors and retries
    
    Integrates with:
    - RAG Engine (JoinFlow) for knowledge retrieval
    - Browser Agent for web interactions
    - LLM Agent for reasoning and generation
    - OS Agent for file and system operations
    - Memory Store for user history
    """
    
    PLANNING_PROMPT = """分析以下任务，并将其分解为具体的执行步骤。

任务: {task}

可用的 Agent 类型:
- browser: 网页浏览、搜索、信息提取、网页交互
- llm: 文本生成、分析、推理、对话
- os: 文件操作、命令执行、系统管理
- code: 代码执行、Python/Shell脚本运行
- data: 数据处理、CSV/Excel分析、统计、图表生成
- vision: 图片分析、OCR文字识别、图像理解
- rag: 知识库检索、文档问答

请输出 JSON 格式的执行计划:
{{
    "analysis": "任务分析",
    "steps": [
        {{
            "id": "1",
            "description": "步骤描述",
            "agent": "agent类型",
            "depends_on": []
        }}
    ]
}}

注意:
1. 步骤要具体可执行
2. 正确标注步骤依赖关系
3. 选择最合适的 Agent
4. 简单任务可以只有1-2步
5. 需要执行代码时使用 code agent
6. 处理数据文件时使用 data agent
7. 分析图片时使用 vision agent"""
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        rag_engine: Optional[Any] = None,
        memory_store: Optional[Any] = None
    ):
        super().__init__(config)
        
        # Initialize all sub-agents
        self._browser_agent = BrowserAgent(config)
        self._llm_agent = LLMAgent(config)
        self._os_agent = OSAgent(config)
        self._code_agent = CodeExecutorAgent(config)
        self._data_agent = DataProcessingAgent(config)
        self._vision_agent = VisionAgent(config)
        
        # External components
        self._rag_engine = rag_engine
        self._memory_store = memory_store
        
        # Register tools from all agents
        self._register_all_tools()
        
        # Execution state
        self._current_plan: Optional[TaskPlan] = None
        self._execution_history: list[TaskPlan] = []
        
        # Retry configuration
        self._max_retries = config.max_retries if config else 3
        self._retry_delay = config.retry_delay if config else 1.0
    
    def _register_all_tools(self) -> None:
        """Register tools from all sub-agents to LLM agent"""
        all_tools = []
        all_tools.extend(self._browser_agent.get_tools())
        all_tools.extend(self._os_agent.get_tools())
        all_tools.extend(self._code_agent.get_tools())
        all_tools.extend(self._data_agent.get_tools())
        all_tools.extend(self._vision_agent.get_tools())
        
        # Add RAG tool if available
        if self._rag_engine:
            all_tools.append(Tool(
                name="knowledge_search",
                description="Search the knowledge base for relevant information",
                func=self._rag_search,
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            ))
        
        for tool in all_tools:
            self._llm_agent.register_tool(tool)
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.ORCHESTRATOR
    
    @property
    def name(self) -> str:
        return "Orchestrator"
    
    @property
    def description(self) -> str:
        return """Master orchestrator that coordinates multiple agents:
        - Plans complex multi-step tasks
        - Routes to appropriate specialized agents
        - Manages execution workflow
        - Aggregates results
        """
    
    def can_handle(self, task: str) -> bool:
        """Orchestrator can handle any task"""
        return True
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute a task using multiple agents"""
        result = self._create_result()
        result.data = {"task": task, "steps": []}
        
        try:
            # Get relevant context from memory
            if self._memory_store and not context:
                context = self._memory_store.get_relevant_context(task)
            
            # Log user message
            if self._memory_store:
                self._memory_store.add_message(content=task, role="user")
            
            # Analyze and plan
            self._log_action(result, "planning", f"Planning task: {task[:100]}...")
            plan = self._create_plan(task, context)
            self._current_plan = plan
            
            # Execute plan
            step_results = []
            while not plan.is_complete():
                step = plan.get_next_step()
                if not step:
                    break
                
                self._log_action(
                    result, "execute_step",
                    f"Step {step.step_id}: {step.description}",
                    agent=step.agent_type.value
                )
                
                step.status = "running"
                step_result = self._execute_step(step, context, step_results)
                step.result = step_result
                step.status = "completed" if step_result.status == AgentStatus.SUCCESS else "failed"
                
                step_results.append({
                    "step_id": step.step_id,
                    "description": step.description,
                    "output": step_result.output,
                    "success": step.status == "completed"
                })
                
                result.data["steps"].append(step_results[-1])
            
            # Aggregate results
            final_output = self._aggregate_results(task, step_results)
            result.output = final_output
            
            # Calculate total tokens
            result.tokens_used = sum(
                s.result.tokens_used for s in plan.steps
                if s.result and s.result.tokens_used
            )
            
            # Log assistant response
            if self._memory_store:
                self._memory_store.add_message(content=final_output, role="assistant")
                
                # Record task
                from joinflow_memory.history import TaskRecord
                task_record = TaskRecord(
                    task_description=task,
                    task_type="multi" if len(plan.steps) > 1 else plan.steps[0].agent_type.value if plan.steps else "llm",
                    status="completed",
                    start_time=result.start_time,
                    end_time=datetime.now(),
                    result_summary=final_output[:500],
                    agents_used=[s.agent_type.value for s in plan.steps],
                    actions_count=len(plan.steps),
                    tokens_used=result.tokens_used
                )
                self._memory_store.add_task(task_record)
            
            self._execution_history.append(plan)
            result.finalize(success=True)
            
        except Exception as e:
            self._handle_error(result, e)
            
            # Log error
            if self._memory_store:
                self._memory_store.add_message(
                    content=f"任务执行失败: {str(e)}",
                    role="assistant"
                )
        
        return result
    
    def _create_plan(self, task: str, context: Optional[dict]) -> TaskPlan:
        """Create an execution plan for the task"""
        plan = TaskPlan(original_task=task)
        
        # Use LLM to analyze and plan
        planning_prompt = self.PLANNING_PROMPT.format(task=task)
        if context and context.get("similar_tasks"):
            planning_prompt += "\n\n参考相似任务:\n"
            for t in context["similar_tasks"][:2]:
                planning_prompt += f"- {t['description']}: 使用了 {t['agents']}\n"
        
        llm_result = self._llm_agent.execute(planning_prompt)
        
        # Parse the plan
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', llm_result.output)
            if json_match:
                plan_data = json.loads(json_match.group())
                
                for step_data in plan_data.get("steps", []):
                    agent_type = self._parse_agent_type(step_data.get("agent", "llm"))
                    plan.steps.append(TaskStep(
                        step_id=str(step_data.get("id", len(plan.steps) + 1)),
                        description=step_data.get("description", ""),
                        agent_type=agent_type,
                        dependencies=step_data.get("depends_on", [])
                    ))
        except json.JSONDecodeError:
            # Fallback: single-step plan
            logger.warning("Failed to parse plan, using single-step fallback")
            agent_type = self._determine_agent_type(task)
            plan.steps.append(TaskStep(
                description=task,
                agent_type=agent_type
            ))
        
        # Ensure at least one step
        if not plan.steps:
            plan.steps.append(TaskStep(
                description=task,
                agent_type=self._determine_agent_type(task)
            ))
        
        return plan
    
    def _parse_agent_type(self, agent_str: str) -> AgentType:
        """Parse agent type from string"""
        mapping = {
            "browser": AgentType.BROWSER,
            "llm": AgentType.LLM,
            "os": AgentType.OS,
            "rag": AgentType.RAG,
            "code": AgentType.LLM,  # Code executor uses LLM type internally
            "data": AgentType.OS,   # Data agent uses OS type internally
            "vision": AgentType.LLM,  # Vision agent uses LLM type internally
        }
        # Store the original type for routing
        self._last_parsed_agent = agent_str.lower()
        return mapping.get(agent_str.lower(), AgentType.LLM)
    
    def _determine_agent_type(self, task: str) -> AgentType:
        """Determine the best agent type for a task"""
        task_lower = task.lower()
        
        # Vision keywords (check first due to specificity)
        if any(kw in task_lower for kw in ["图片", "图像", "照片", "截图", "image", "picture", "photo", "ocr", "看图"]):
            self._last_parsed_agent = "vision"
            return AgentType.LLM
        
        # Code keywords
        if any(kw in task_lower for kw in ["代码", "python", "脚本", "运行", "执行代码", "```", "code", "script", "run"]):
            self._last_parsed_agent = "code"
            return AgentType.LLM
        
        # Data keywords
        if any(kw in task_lower for kw in ["csv", "excel", "xlsx", "数据", "统计", "图表", "分析数据", "data", "pandas"]):
            self._last_parsed_agent = "data"
            return AgentType.OS
        
        # Browser keywords
        if any(kw in task_lower for kw in ["搜索", "网页", "浏览", "网站", "链接", "search", "web", "browse", "http"]):
            self._last_parsed_agent = "browser"
            return AgentType.BROWSER
        
        # OS keywords
        if any(kw in task_lower for kw in ["文件", "目录", "命令", "系统", "file", "directory", "folder"]):
            self._last_parsed_agent = "os"
            return AgentType.OS
        
        # RAG keywords
        if any(kw in task_lower for kw in ["知识库", "文档", "检索", "knowledge", "document", "retrieve"]):
            self._last_parsed_agent = "rag"
            return AgentType.RAG
        
        # Default to LLM
        self._last_parsed_agent = "llm"
        return AgentType.LLM
    
    def _execute_step(
        self,
        step: TaskStep,
        context: Optional[dict],
        previous_results: list[dict]
    ) -> AgentResult:
        """Execute a single step with retry support"""
        # Build step context with previous results
        step_context = context.copy() if context else {}
        if previous_results:
            step_context["previous_steps"] = previous_results
        
        # Get the specific agent type from planning
        specific_agent = getattr(self, '_last_parsed_agent', None)
        
        # Execute with retry
        last_error = None
        for attempt in range(self._max_retries):
            try:
                result = self._execute_step_internal(step, step_context, previous_results, specific_agent)
                if result.status == AgentStatus.SUCCESS:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Step execution attempt {attempt + 1} failed: {e}")
            
            if attempt < self._max_retries - 1:
                import time
                time.sleep(self._retry_delay)
        
        # All retries failed
        result = self._create_result()
        result.output = f"执行失败 (尝试 {self._max_retries} 次): {last_error}"
        result.finalize(success=False, error=last_error)
        return result
    
    def _execute_step_internal(
        self,
        step: TaskStep,
        step_context: dict,
        previous_results: list[dict],
        specific_agent: Optional[str]
    ) -> AgentResult:
        """Internal step execution logic"""
        # Route to specific agent based on planning
        if specific_agent == "code":
            return self._code_agent.execute(step.description, step_context)
        
        elif specific_agent == "data":
            return self._data_agent.execute(step.description, step_context)
        
        elif specific_agent == "vision":
            return self._vision_agent.execute(step.description, step_context)
        
        # Route by AgentType
        elif step.agent_type == AgentType.BROWSER:
            return self._browser_agent.execute(step.description, step_context)
        
        elif step.agent_type == AgentType.OS:
            return self._os_agent.execute(step.description, step_context)
        
        elif step.agent_type == AgentType.RAG:
            return self._execute_rag(step.description, step_context)
        
        else:  # LLM
            # Add previous context to task
            if previous_results:
                enhanced_task = f"{step.description}\n\n前面步骤的结果:\n"
                for prev in previous_results[-3:]:  # Last 3 steps
                    enhanced_task += f"- {prev['description']}: {prev['output'][:200]}\n"
                return self._llm_agent.execute(enhanced_task, step_context)
            return self._llm_agent.execute(step.description, step_context)
    
    def _execute_rag(self, task: str, context: Optional[dict]) -> AgentResult:
        """Execute RAG retrieval"""
        result = self._create_result()
        result.agent_type = AgentType.RAG
        
        if not self._rag_engine:
            result.output = "RAG engine not configured"
            result.finalize(success=False, error="RAG engine not available")
            return result
        
        try:
            rag_response = self._rag_engine.query(task)
            result.output = rag_response.answer
            result.data = {
                "context": [
                    {"doc_id": c.doc_id, "score": c.score}
                    for c in rag_response.context
                ]
            }
            result.finalize(success=True)
        except Exception as e:
            result.finalize(success=False, error=str(e))
        
        return result
    
    def _rag_search(self, query: str) -> str:
        """RAG search tool function"""
        if not self._rag_engine:
            return "Knowledge base not available"
        
        try:
            response = self._rag_engine.query(query)
            return response.answer
        except Exception as e:
            return f"Search error: {e}"
    
    def _aggregate_results(self, task: str, step_results: list[dict]) -> str:
        """Aggregate results from multiple steps"""
        if not step_results:
            return "任务未能执行"
        
        if len(step_results) == 1:
            return step_results[0]["output"]
        
        # Use LLM to summarize multiple results
        summary_prompt = f"""请根据以下执行结果，为用户任务提供最终答案。

用户任务: {task}

执行步骤结果:
"""
        for i, sr in enumerate(step_results, 1):
            summary_prompt += f"\n{i}. {sr['description']}:\n{sr['output'][:500]}\n"
        
        summary_prompt += "\n请综合以上结果，给出简洁完整的最终答案:"
        
        summary_result = self._llm_agent.execute(summary_prompt)
        return summary_result.output
    
    # -------------------------
    # Public API
    # -------------------------
    
    def chat(self, message: str, user_id: str = "default") -> str:
        """Simple chat interface"""
        result = self.execute(message)
        return result.output
    
    def search_web(self, query: str) -> AgentResult:
        """Convenience method for web search"""
        return self._browser_agent.execute(f"搜索: {query}")
    
    def ask_knowledge(self, question: str) -> AgentResult:
        """Query the knowledge base"""
        return self._execute_rag(question, None)
    
    def run_command(self, command: str) -> AgentResult:
        """Run an OS command"""
        return self._os_agent.execute(f"执行命令: {command}")
    
    def analyze(self, text: str, instruction: str = "分析") -> AgentResult:
        """Analyze text with LLM"""
        return self._llm_agent.analyze(text, instruction)
    
    def get_execution_history(self) -> list[TaskPlan]:
        """Get execution history"""
        return self._execution_history.copy()
    
    def clear_history(self) -> None:
        """Clear execution history"""
        self._execution_history = []
        self._llm_agent.clear_history()
    
    # -------------------------
    # Configuration
    # -------------------------
    
    def set_rag_engine(self, engine: Any) -> None:
        """Set the RAG engine"""
        self._rag_engine = engine
        
        # Register RAG tool
        self._llm_agent.register_tool(Tool(
            name="knowledge_search",
            description="Search the knowledge base for relevant information",
            func=self._rag_search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ))
    
    def set_memory_store(self, store: Any) -> None:
        """Set the memory store"""
        self._memory_store = store
    
    def get_agents(self) -> dict[str, BaseAgent]:
        """Get all sub-agents"""
        return {
            "browser": self._browser_agent,
            "llm": self._llm_agent,
            "os": self._os_agent,
            "code": self._code_agent,
            "data": self._data_agent,
            "vision": self._vision_agent,
        }
    
    # -------------------------
    # Convenience Methods
    # -------------------------
    
    def execute_code(self, code: str, language: str = "python") -> AgentResult:
        """Execute code in sandbox"""
        return self._code_agent.execute(f"```{language}\n{code}\n```")
    
    def process_data(self, task: str) -> AgentResult:
        """Process data with data agent"""
        return self._data_agent.execute(task)
    
    def analyze_image(self, image_path: str, question: str = "") -> AgentResult:
        """Analyze an image"""
        task = f"{image_path} {question}" if question else f"描述图片 {image_path}"
        return self._vision_agent.execute(task)

