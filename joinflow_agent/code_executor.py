"""
Code Executor Agent
===================

Provides secure code execution capabilities:
- Python code execution in sandboxed environment
- Shell command execution
- Multi-language support (Python, JavaScript, Shell)
- Output capture and error handling
- Timeout and resource limits
"""

import ast
import io
import sys
import traceback
import subprocess
import tempfile
import os
import signal
import threading
import queue
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List
from pathlib import Path
import logging
import uuid
import json

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType,
    AgentAction, Tool
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution"""
    success: bool
    output: str
    error: Optional[str] = None
    return_value: Any = None
    execution_time_ms: float = 0
    memory_used_mb: float = 0


@dataclass 
class SandboxConfig:
    """Configuration for code sandbox"""
    timeout_seconds: int = 30
    max_memory_mb: int = 512
    max_output_size: int = 100000  # 100KB
    allowed_imports: List[str] = field(default_factory=lambda: [
        "math", "random", "datetime", "json", "re", "collections",
        "itertools", "functools", "string", "textwrap", "unicodedata",
        "statistics", "decimal", "fractions", "numbers",
        "numpy", "pandas", "matplotlib", "seaborn", "scipy",
        "requests", "urllib", "csv", "xml", "html",
    ])
    blocked_builtins: List[str] = field(default_factory=lambda: [
        "eval", "exec", "compile", "__import__", "open", 
        "input", "breakpoint", "exit", "quit"
    ])
    workspace_dir: str = "./sandbox_workspace"


class RestrictedImporter:
    """Custom importer that restricts allowed modules"""
    
    def __init__(self, allowed_modules: List[str]):
        self.allowed_modules = set(allowed_modules)
        self._original_import = __builtins__.__dict__.get('__import__')
    
    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        # Check if the base module is allowed
        base_module = name.split('.')[0]
        if base_module not in self.allowed_modules:
            raise ImportError(f"Import of '{name}' is not allowed in sandbox")
        return self._original_import(name, globals, locals, fromlist, level)


class CodeSandbox:
    """
    Secure sandbox for code execution.
    
    Features:
    - Restricted imports
    - Blocked dangerous builtins
    - Timeout enforcement
    - Output capture
    - Memory limits (best effort)
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._workspace = Path(self.config.workspace_dir)
        self._workspace.mkdir(parents=True, exist_ok=True)
    
    def execute_python(self, code: str, context: Optional[Dict] = None) -> ExecutionResult:
        """
        Execute Python code in sandbox.
        
        Args:
            code: Python code to execute
            context: Variables to inject into execution context
            
        Returns:
            ExecutionResult with output and any errors
        """
        start_time = datetime.now()
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Validate code first
        try:
            ast.parse(code)
        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Syntax error: {e}"
            )
        
        # Create restricted globals
        restricted_globals = self._create_restricted_globals()
        if context:
            restricted_globals.update(context)
        
        # Result queue for timeout handling
        result_queue = queue.Queue()
        
        def execute_code():
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(code, restricted_globals)
                
                # Check for return value
                return_val = restricted_globals.get('result', restricted_globals.get('output', None))
                
                result_queue.put(ExecutionResult(
                    success=True,
                    output=stdout_capture.getvalue()[:self.config.max_output_size],
                    return_value=return_val
                ))
            except Exception as e:
                result_queue.put(ExecutionResult(
                    success=False,
                    output=stdout_capture.getvalue(),
                    error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                ))
        
        # Run with timeout
        thread = threading.Thread(target=execute_code)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.config.timeout_seconds)
        
        if thread.is_alive():
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"Execution timed out after {self.config.timeout_seconds} seconds"
            )
        
        try:
            result = result_queue.get_nowait()
            end_time = datetime.now()
            result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
            return result
        except queue.Empty:
            return ExecutionResult(
                success=False,
                output="",
                error="Execution failed with no result"
            )
    
    def execute_shell(self, command: str, cwd: Optional[str] = None) -> ExecutionResult:
        """Execute shell command with restrictions"""
        start_time = datetime.now()
        
        # Block dangerous commands
        dangerous_patterns = [
            "rm -rf /", "rm -rf /*", "dd if=", "mkfs", "format",
            ":(){:|:&};:", "chmod -R 777 /", "shutdown", "reboot",
            "wget", "curl", "> /dev/", "| sh", "| bash"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Command blocked for security: contains '{pattern}'"
                )
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=cwd or str(self._workspace)
            )
            
            end_time = datetime.now()
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout[:self.config.max_output_size],
                error=result.stderr if result.returncode != 0 else None,
                execution_time_ms=(end_time - start_time).total_seconds() * 1000
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Command timed out after {self.config.timeout_seconds} seconds"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def execute_javascript(self, code: str) -> ExecutionResult:
        """Execute JavaScript using Node.js"""
        start_time = datetime.now()
        
        # Write code to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.js', delete=False, dir=str(self._workspace)
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=str(self._workspace)
            )
            
            end_time = datetime.now()
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout[:self.config.max_output_size],
                error=result.stderr if result.returncode != 0 else None,
                execution_time_ms=(end_time - start_time).total_seconds() * 1000
            )
            
        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                output="",
                error="Node.js not found. Install with: apt install nodejs"
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {self.config.timeout_seconds} seconds"
            )
        finally:
            os.unlink(temp_file)
    
    def _create_restricted_globals(self) -> Dict:
        """Create restricted globals for Python execution"""
        import math
        import random
        import datetime as dt
        import json as json_mod
        import re as re_mod
        
        # Safe builtins
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
            'chr': chr, 'dict': dict, 'dir': dir, 'divmod': divmod,
            'enumerate': enumerate, 'filter': filter, 'float': float,
            'format': format, 'frozenset': frozenset, 'getattr': getattr,
            'hasattr': hasattr, 'hash': hash, 'hex': hex, 'int': int,
            'isinstance': isinstance, 'issubclass': issubclass, 'iter': iter,
            'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
            'next': next, 'oct': oct, 'ord': ord, 'pow': pow, 'print': print,
            'range': range, 'repr': repr, 'reversed': reversed, 'round': round,
            'set': set, 'slice': slice, 'sorted': sorted, 'str': str,
            'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip,
            'True': True, 'False': False, 'None': None,
        }
        
        # Restricted import
        safe_builtins['__import__'] = RestrictedImporter(self.config.allowed_imports)
        
        return {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
            # Pre-imported safe modules
            'math': math,
            'random': random,
            'datetime': dt,
            'json': json_mod,
            're': re_mod,
        }


class CodeExecutorAgent(BaseAgent):
    """
    Agent for executing code in a sandboxed environment.
    
    Capabilities:
    - Execute Python code safely
    - Run shell commands with restrictions
    - Execute JavaScript (if Node.js available)
    - Handle data processing tasks
    - Generate and execute code from natural language
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self._sandbox = CodeSandbox(SandboxConfig(
            workspace_dir=config.os_workspace if config else "./sandbox_workspace"
        ))
        self._execution_history: List[Dict] = []
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.LLM  # Using LLM type as it's a specialized executor
    
    @property
    def name(self) -> str:
        return "Code Executor Agent"
    
    @property
    def description(self) -> str:
        return """Code execution agent capable of:
        - Executing Python code in a secure sandbox
        - Running shell commands safely
        - Processing data with pandas/numpy
        - Generating visualizations
        - Handling computation tasks
        """
    
    def can_handle(self, task: str) -> bool:
        """Check if this is a code execution task"""
        code_keywords = [
            "执行", "运行", "代码", "python", "脚本", "计算",
            "execute", "run", "code", "script", "compute",
            "```python", "```js", "```shell", "```bash"
        ]
        return any(kw in task.lower() for kw in code_keywords)
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute a code task"""
        result = self._create_result()
        
        try:
            # Extract code from task
            code, language = self._extract_code(task)
            
            if not code:
                # Generate code from natural language
                result.output = "No code found in task. Please provide code to execute."
                result.finalize(success=False, error="No code provided")
                return result
            
            self._log_action(result, "execute_code", f"Executing {language} code")
            
            # Execute based on language
            if language == "python":
                exec_result = self._sandbox.execute_python(code, context)
            elif language in ("shell", "bash"):
                exec_result = self._sandbox.execute_shell(code)
            elif language in ("javascript", "js"):
                exec_result = self._sandbox.execute_javascript(code)
            else:
                result.output = f"Unsupported language: {language}"
                result.finalize(success=False, error="Unsupported language")
                return result
            
            # Build output
            if exec_result.success:
                result.output = exec_result.output or "Code executed successfully (no output)"
                if exec_result.return_value is not None:
                    result.output += f"\n\nReturn value: {exec_result.return_value}"
            else:
                result.output = f"Execution failed:\n{exec_result.error}"
                if exec_result.output:
                    result.output = f"Output before error:\n{exec_result.output}\n\n{result.output}"
            
            result.data = {
                "language": language,
                "success": exec_result.success,
                "execution_time_ms": exec_result.execution_time_ms,
                "return_value": exec_result.return_value
            }
            
            # Save to history
            self._execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "language": language,
                "code": code[:500],
                "success": exec_result.success
            })
            
            result.finalize(success=exec_result.success)
            
        except Exception as e:
            self._handle_error(result, e)
        
        return result
    
    def _extract_code(self, task: str) -> tuple[str, str]:
        """Extract code and language from task"""
        import re
        
        # Look for code blocks
        code_block_pattern = r'```(\w+)?\n([\s\S]*?)```'
        matches = re.findall(code_block_pattern, task)
        
        if matches:
            lang, code = matches[0]
            lang = lang.lower() if lang else "python"
            return code.strip(), lang
        
        # Look for inline code
        inline_pattern = r'`([^`]+)`'
        inline_matches = re.findall(inline_pattern, task)
        
        if inline_matches and len(inline_matches[0]) > 10:
            return inline_matches[0], "python"
        
        return "", "python"
    
    def execute_python(self, code: str, context: Optional[Dict] = None) -> ExecutionResult:
        """Direct Python execution"""
        return self._sandbox.execute_python(code, context)
    
    def execute_shell(self, command: str) -> ExecutionResult:
        """Direct shell execution"""
        return self._sandbox.execute_shell(command)
    
    def get_tools(self) -> List[Tool]:
        """Get tools for LLM function calling"""
        return [
            Tool(
                name="execute_python",
                description="Execute Python code in a secure sandbox",
                func=lambda code: self._sandbox.execute_python(code).__dict__,
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"]
                }
            ),
            Tool(
                name="execute_shell",
                description="Execute a shell command safely",
                func=lambda cmd: self._sandbox.execute_shell(cmd).__dict__,
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"}
                    },
                    "required": ["command"]
                }
            ),
        ]
    
    def get_execution_history(self) -> List[Dict]:
        """Get code execution history"""
        return self._execution_history.copy()

