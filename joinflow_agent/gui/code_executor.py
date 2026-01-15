"""
Local Code Executor - 本地代码执行环境
======================================

实现类似 Agent-S 的本地代码执行能力：
1. 执行 Python 代码
2. 执行 Shell/Bash 命令
3. 安全沙盒控制
"""

import os
import sys
import subprocess
import tempfile
import logging
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CodeLanguage(Enum):
    """支持的代码语言"""
    PYTHON = "python"
    BASH = "bash"
    POWERSHELL = "powershell"
    BATCH = "batch"


@dataclass
class CodeExecutionResult:
    """代码执行结果"""
    success: bool
    language: CodeLanguage
    code: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    duration_ms: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "language": self.language.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass 
class CodeExecutorConfig:
    """代码执行器配置"""
    enabled: bool = True
    timeout: int = 30                            # 执行超时（秒）
    max_output_size: int = 100000                # 最大输出大小
    working_dir: Optional[str] = None            # 工作目录
    
    # 安全配置
    allow_network: bool = True                   # 允许网络访问
    allow_file_write: bool = True                # 允许文件写入
    blocked_imports: List[str] = field(default_factory=lambda: [
        "os.system", "subprocess.call", "eval", "exec",
        "__import__", "compile"
    ])
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf", "del /f /s", "format", "mkfs",
        "shutdown", "reboot", ":(){:|:&};:"
    ])


class LocalCodeExecutor:
    """
    本地代码执行器
    
    提供安全的代码执行环境，支持：
    - Python 代码执行
    - Shell 命令执行
    - PowerShell 脚本（Windows）
    """
    
    def __init__(self, config: Optional[CodeExecutorConfig] = None):
        self.config = config or CodeExecutorConfig()
        self._python_path = sys.executable
        self._platform = sys.platform
        
        # 设置工作目录
        if self.config.working_dir:
            self._working_dir = Path(self.config.working_dir)
        else:
            self._working_dir = Path.cwd() / "workspace"
        
        self._working_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LocalCodeExecutor initialized (working_dir: {self._working_dir})")
    
    def execute_python(self, code: str, **kwargs) -> CodeExecutionResult:
        """
        执行 Python 代码
        
        Args:
            code: Python 代码
            **kwargs: 额外参数
            
        Returns:
            CodeExecutionResult
        """
        if not self.config.enabled:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.PYTHON,
                code=code,
                error="Code execution is disabled"
            )
        
        # 安全检查
        security_check = self._check_python_security(code)
        if security_check:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.PYTHON,
                code=code,
                error=f"Security violation: {security_check}"
            )
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            start_time = datetime.now()
            
            result = subprocess.run(
                [self._python_path, temp_file],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=str(self._working_dir),
                env=self._get_safe_env(),
            )
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return CodeExecutionResult(
                success=(result.returncode == 0),
                language=CodeLanguage.PYTHON,
                code=code,
                stdout=result.stdout[:self.config.max_output_size],
                stderr=result.stderr[:self.config.max_output_size],
                return_code=result.returncode,
                duration_ms=duration,
            )
            
        except subprocess.TimeoutExpired:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.PYTHON,
                code=code,
                error=f"Execution timed out ({self.config.timeout}s)"
            )
        except Exception as e:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.PYTHON,
                code=code,
                error=str(e)
            )
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def execute_shell(self, command: str, **kwargs) -> CodeExecutionResult:
        """
        执行 Shell 命令
        
        Args:
            command: Shell 命令
            
        Returns:
            CodeExecutionResult
        """
        if not self.config.enabled:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.BASH,
                code=command,
                error="Code execution is disabled"
            )
        
        # 安全检查
        security_check = self._check_command_security(command)
        if security_check:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.BASH,
                code=command,
                error=f"Security violation: {security_check}"
            )
        
        try:
            start_time = datetime.now()
            
            # 选择 shell
            if self._platform == "win32":
                shell_cmd = ["cmd", "/c", command]
                lang = CodeLanguage.BATCH
            else:
                shell_cmd = ["/bin/bash", "-c", command]
                lang = CodeLanguage.BASH
            
            result = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=str(self._working_dir),
                env=self._get_safe_env(),
            )
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return CodeExecutionResult(
                success=(result.returncode == 0),
                language=lang,
                code=command,
                stdout=result.stdout[:self.config.max_output_size],
                stderr=result.stderr[:self.config.max_output_size],
                return_code=result.returncode,
                duration_ms=duration,
            )
            
        except subprocess.TimeoutExpired:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.BASH,
                code=command,
                error=f"Execution timed out ({self.config.timeout}s)"
            )
        except Exception as e:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.BASH,
                code=command,
                error=str(e)
            )
    
    def execute_powershell(self, script: str, **kwargs) -> CodeExecutionResult:
        """
        执行 PowerShell 脚本（仅 Windows）
        
        Args:
            script: PowerShell 脚本
            
        Returns:
            CodeExecutionResult
        """
        if self._platform != "win32":
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.POWERSHELL,
                code=script,
                error="PowerShell is only available on Windows"
            )
        
        if not self.config.enabled:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.POWERSHELL,
                code=script,
                error="Code execution is disabled"
            )
        
        # 安全检查
        security_check = self._check_command_security(script)
        if security_check:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.POWERSHELL,
                code=script,
                error=f"Security violation: {security_check}"
            )
        
        try:
            start_time = datetime.now()
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=str(self._working_dir),
            )
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return CodeExecutionResult(
                success=(result.returncode == 0),
                language=CodeLanguage.POWERSHELL,
                code=script,
                stdout=result.stdout[:self.config.max_output_size],
                stderr=result.stderr[:self.config.max_output_size],
                return_code=result.returncode,
                duration_ms=duration,
            )
            
        except subprocess.TimeoutExpired:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.POWERSHELL,
                code=script,
                error=f"Execution timed out ({self.config.timeout}s)"
            )
        except Exception as e:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.POWERSHELL,
                code=script,
                error=str(e)
            )
    
    def _check_python_security(self, code: str) -> Optional[str]:
        """检查 Python 代码安全性"""
        code_lower = code.lower()
        
        for blocked in self.config.blocked_imports:
            if blocked.lower() in code_lower:
                return f"Blocked import/function: {blocked}"
        
        # 检查危险模式
        dangerous_patterns = [
            "open('/etc", "open('c:\\\\windows",
            "shutil.rmtree('/'", "shutil.rmtree('c:\\\\'",
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                return f"Dangerous pattern detected: {pattern}"
        
        return None
    
    def _check_command_security(self, command: str) -> Optional[str]:
        """检查命令安全性"""
        cmd_lower = command.lower()
        
        for blocked in self.config.blocked_commands:
            if blocked.lower() in cmd_lower:
                return f"Blocked command: {blocked}"
        
        return None
    
    def _get_safe_env(self) -> Dict[str, str]:
        """获取安全的环境变量"""
        env = os.environ.copy()
        
        # 设置工作目录
        env["PWD"] = str(self._working_dir)
        
        # 可以根据需要过滤敏感环境变量
        sensitive_vars = ["AWS_SECRET", "OPENAI_API_KEY", "DATABASE_URL"]
        for var in sensitive_vars:
            if var in env:
                env[var] = "***HIDDEN***"
        
        return env
    
    def execute(
        self, 
        code: str, 
        language: str = "python"
    ) -> CodeExecutionResult:
        """
        通用执行入口
        
        Args:
            code: 代码内容
            language: 语言类型 (python/bash/powershell/shell)
            
        Returns:
            CodeExecutionResult
        """
        lang_lower = language.lower()
        
        if lang_lower == "python":
            return self.execute_python(code)
        elif lang_lower in ("bash", "shell", "sh"):
            return self.execute_shell(code)
        elif lang_lower in ("powershell", "ps1"):
            return self.execute_powershell(code)
        elif lang_lower in ("batch", "cmd", "bat"):
            return self.execute_shell(code)
        else:
            return CodeExecutionResult(
                success=False,
                language=CodeLanguage.PYTHON,
                code=code,
                error=f"Unsupported language: {language}"
            )


# 便捷函数
def run_python(code: str) -> CodeExecutionResult:
    """快速执行 Python 代码"""
    executor = LocalCodeExecutor()
    return executor.execute_python(code)


def run_shell(command: str) -> CodeExecutionResult:
    """快速执行 Shell 命令"""
    executor = LocalCodeExecutor()
    return executor.execute_shell(command)

