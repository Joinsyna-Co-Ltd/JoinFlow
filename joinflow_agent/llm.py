"""
LLM Agent
=========

Provides large language model capabilities:
- Text generation and completion
- Reasoning and analysis
- Function calling and tool use
- Multi-turn conversations
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Sequence
import logging

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType,
    AgentAction, Tool
)

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A chat message"""
    role: str  # "system", "user", "assistant", "function"
    content: str
    name: Optional[str] = None  # For function messages
    function_call: Optional[dict] = None
    
    def to_dict(self) -> dict:
        msg = {"role": self.role, "content": self.content}
        if self.name:
            msg["name"] = self.name
        if self.function_call:
            msg["function_call"] = self.function_call
        return msg


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    finish_reason: str = "stop"
    function_call: Optional[dict] = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    model: str = ""


class LLMAgent(BaseAgent):
    """
    Agent for Large Language Model interactions.
    
    Capabilities:
    - Generate text completions
    - Multi-turn conversations
    - Function/tool calling
    - Reasoning and analysis
    - Code generation
    
    Supports multiple LLM providers through LiteLLM.
    """
    
    # System prompts for different modes
    SYSTEM_PROMPTS = {
        "default": """你是一个智能助手，能够帮助用户完成各种任务。
你应该：
1. 仔细理解用户的需求
2. 提供准确、有帮助的回答
3. 如果需要使用工具，清晰地说明你要做什么
4. 如果不确定，诚实地告诉用户""",
        
        "reasoning": """你是一个擅长分析和推理的助手。
在回答问题时：
1. 先分析问题的关键点
2. 逐步推理，展示思考过程
3. 得出结论并解释原因
4. 如果有多种可能，列出并比较""",
        
        "coding": """你是一个专业的编程助手。
在编写代码时：
1. 首先理解需求
2. 选择合适的技术方案
3. 编写清晰、高效的代码
4. 添加必要的注释
5. 考虑边界情况和错误处理""",
        
        "planner": """你是一个任务规划专家。
在规划任务时：
1. 分析任务的复杂度和依赖关系
2. 将大任务分解为小步骤
3. 确定每个步骤需要的工具或能力
4. 考虑可能的风险和备选方案
5. 输出清晰的执行计划"""
    }
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[Sequence[Tool]] = None,
        system_prompt: Optional[str] = None,
        mode: str = "default"
    ):
        super().__init__(config)
        self.tools = list(tools) if tools else []
        self.mode = mode
        self.system_prompt = system_prompt or self.SYSTEM_PROMPTS.get(mode, self.SYSTEM_PROMPTS["default"])
        self._conversation_history: list[Message] = []
        self._client = None
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.LLM
    
    @property
    def name(self) -> str:
        return "LLM Agent"
    
    @property
    def description(self) -> str:
        return """Large Language Model agent capable of:
        - Natural language understanding and generation
        - Complex reasoning and analysis
        - Code generation and explanation
        - Multi-turn conversations
        - Tool/function calling
        """
    
    def can_handle(self, task: str) -> bool:
        """LLM can handle most text-based tasks"""
        # LLM is a generalist - can handle most tasks as fallback
        return True
    
    def _get_client(self):
        """Get or create LLM client"""
        if self._client is None:
            try:
                import litellm
                self._client = litellm
                
                # Configure API key if provided
                if self.config.llm_api_key:
                    import os
                    os.environ["OPENAI_API_KEY"] = self.config.llm_api_key
                
            except ImportError:
                raise RuntimeError(
                    "LiteLLM is required for LLMAgent. "
                    "Install it with: pip install litellm"
                )
        return self._client
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute an LLM task"""
        result = self._create_result()
        
        try:
            # Build messages
            messages = self._build_messages(task, context)
            
            # Check if we should use function calling
            if self.tools and self._should_use_tools(task):
                response = self._execute_with_tools(messages, result)
            else:
                response = self._execute_completion(messages, result)
            
            result.output = response.content
            result.tokens_used = response.tokens_prompt + response.tokens_completion
            result.data = {
                "model": response.model,
                "tokens": {
                    "prompt": response.tokens_prompt,
                    "completion": response.tokens_completion
                },
                "finish_reason": response.finish_reason
            }
            
            # Add to conversation history
            self._conversation_history.append(Message(role="user", content=task))
            self._conversation_history.append(Message(role="assistant", content=response.content))
            
            result.finalize(success=True)
            
        except Exception as e:
            self._handle_error(result, e)
        
        return result
    
    def _build_messages(self, task: str, context: Optional[dict]) -> list[dict]:
        """Build message list for LLM"""
        messages = []
        
        # System message
        system_content = self.system_prompt
        if context:
            # Add context to system message
            if context.get("similar_tasks"):
                system_content += "\n\n相关的历史任务:\n"
                for t in context["similar_tasks"][:3]:
                    system_content += f"- {t['description']}: {t['result']}\n"
            
            if context.get("recent_messages"):
                system_content += "\n\n最近的对话:\n"
                for m in context["recent_messages"][-5:]:
                    system_content += f"- [{m['role']}]: {m['content'][:100]}\n"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history (limited)
        for msg in self._conversation_history[-10:]:
            messages.append(msg.to_dict())
        
        # Add current task
        messages.append({"role": "user", "content": task})
        
        return messages
    
    def _should_use_tools(self, task: str) -> bool:
        """Determine if tools should be used for this task"""
        # Keywords that suggest tool use
        tool_keywords = [
            "搜索", "查找", "打开", "访问", "文件", "创建", "删除",
            "执行", "运行", "浏览", "下载", "上传", "分析数据",
            "search", "find", "open", "file", "create", "delete",
            "execute", "run", "browse", "download", "upload"
        ]
        return any(kw in task.lower() for kw in tool_keywords)
    
    def _execute_completion(self, messages: list[dict], result: AgentResult) -> LLMResponse:
        """Execute a simple completion"""
        self._log_action(result, "completion", "Generating LLM response")
        
        client = self._get_client()
        
        response = client.completion(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
        )
        
        choice = response.choices[0]
        usage = response.usage
        
        return LLMResponse(
            content=choice.message.content,
            finish_reason=choice.finish_reason,
            tokens_prompt=usage.prompt_tokens,
            tokens_completion=usage.completion_tokens,
            model=response.model
        )
    
    def _execute_with_tools(self, messages: list[dict], result: AgentResult) -> LLMResponse:
        """Execute with function calling"""
        self._log_action(result, "tool_call", "Executing with tools")
        
        client = self._get_client()
        
        # Convert tools to OpenAI format
        functions = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
        
        response = client.completion(
            model=self.config.llm_model,
            messages=messages,
            functions=functions,
            function_call="auto",
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
        )
        
        choice = response.choices[0]
        usage = response.usage
        
        # Check if a function was called
        if hasattr(choice.message, 'function_call') and choice.message.function_call:
            func_call = choice.message.function_call
            func_name = func_call.name
            func_args = json.loads(func_call.arguments)
            
            self._log_action(
                result, "function_execute",
                f"Calling function: {func_name}",
                function=func_name, arguments=func_args
            )
            
            # Find and execute the tool
            tool_result = self._execute_tool(func_name, func_args)
            
            # Add function result to messages and get final response
            messages.append(choice.message.to_dict())
            messages.append({
                "role": "function",
                "name": func_name,
                "content": str(tool_result)
            })
            
            # Get final response
            final_response = client.completion(
                model=self.config.llm_model,
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
            
            final_choice = final_response.choices[0]
            final_usage = final_response.usage
            
            return LLMResponse(
                content=final_choice.message.content,
                finish_reason=final_choice.finish_reason,
                function_call={"name": func_name, "result": tool_result},
                tokens_prompt=usage.prompt_tokens + final_usage.prompt_tokens,
                tokens_completion=usage.completion_tokens + final_usage.completion_tokens,
                model=response.model
            )
        
        return LLMResponse(
            content=choice.message.content,
            finish_reason=choice.finish_reason,
            tokens_prompt=usage.prompt_tokens,
            tokens_completion=usage.completion_tokens,
            model=response.model
        )
    
    def _execute_tool(self, name: str, args: dict) -> Any:
        """Execute a tool by name"""
        for tool in self.tools:
            if tool.name == name:
                return tool(**args)
        raise ValueError(f"Tool not found: {name}")
    
    # -------------------------
    # Conversation Management
    # -------------------------
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self._conversation_history = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to history"""
        self._conversation_history.append(Message(role=role, content=content))
    
    def get_history(self) -> list[Message]:
        """Get conversation history"""
        return self._conversation_history.copy()
    
    # -------------------------
    # Specialized Methods
    # -------------------------
    
    def analyze(self, text: str, instruction: str = "分析以下内容") -> AgentResult:
        """Analyze text with specific instruction"""
        task = f"{instruction}:\n\n{text}"
        old_prompt = self.system_prompt
        self.system_prompt = self.SYSTEM_PROMPTS["reasoning"]
        result = self.execute(task)
        self.system_prompt = old_prompt
        return result
    
    def generate_code(self, requirement: str, language: str = "python") -> AgentResult:
        """Generate code for a requirement"""
        task = f"用 {language} 实现以下需求:\n\n{requirement}"
        old_prompt = self.system_prompt
        self.system_prompt = self.SYSTEM_PROMPTS["coding"]
        result = self.execute(task)
        self.system_prompt = old_prompt
        return result
    
    def plan_task(self, task_description: str) -> AgentResult:
        """Create a task execution plan"""
        task = f"为以下任务制定详细的执行计划:\n\n{task_description}"
        old_prompt = self.system_prompt
        self.system_prompt = self.SYSTEM_PROMPTS["planner"]
        result = self.execute(task)
        self.system_prompt = old_prompt
        return result
    
    def summarize(self, text: str, max_length: int = 500) -> AgentResult:
        """Summarize text"""
        task = f"请将以下内容总结为不超过{max_length}字的摘要:\n\n{text}"
        return self.execute(task)
    
    def translate(self, text: str, target_language: str = "英语") -> AgentResult:
        """Translate text"""
        task = f"将以下内容翻译成{target_language}:\n\n{text}"
        return self.execute(task)
    
    # -------------------------
    # Tool Registration
    # -------------------------
    
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool"""
        self.tools.append(tool)
    
    def register_function(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[dict] = None
    ) -> None:
        """Register a function as a tool"""
        self.tools.append(Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {"type": "object", "properties": {}}
        ))
    
    def get_tools(self) -> list[Tool]:
        """Get all registered tools"""
        return self.tools.copy()

