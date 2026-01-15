"""
内容创作执行器
"""
from typing import Dict, Optional
from pathlib import Path

from .base import BaseExecutor
from ..core.runtime import ActionResult


class ComposeExecutor(BaseExecutor):
    """内容创作执行器（需要LLM）"""
    
    name = "compose"
    
    def __init__(self, config, runtime, llm_client=None):
        super().__init__(config, runtime)
        self.llm_client = llm_client
    
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行创作操作"""
        if not self.llm_client:
            return ActionResult(
                success=False,
                action=action,
                message="内容创作功能需要配置LLM",
                error="NoLLM"
            )
        
        try:
            if action == "compose.text":
                return self._compose_text(command, params)
            elif action == "compose.code":
                return self._compose_code(command, params)
            else:
                return ActionResult(False, action, f"不支持的操作: {action}")
        except Exception as e:
            return ActionResult(False, action, f"创作失败: {e}", error=str(e))
    
    def _compose_text(self, command: str, params: Dict) -> ActionResult:
        """生成文本"""
        prompt = params.get("prompt") or command
        
        try:
            response = self.llm_client.chat(f"请帮我写：{prompt}")
            
            return ActionResult(
                success=True,
                action="compose.text",
                message="✏️ 内容已生成",
                data={"content": response}
            )
        except Exception as e:
            return ActionResult(False, "compose.text", f"生成失败: {e}", error=str(e))
    
    def _compose_code(self, command: str, params: Dict) -> ActionResult:
        """生成代码"""
        prompt = params.get("prompt") or command
        language = params.get("language", "python")
        
        try:
            full_prompt = f"""请用 {language} 编写代码：{prompt}

只返回代码，不要解释。"""
            
            response = self.llm_client.chat(full_prompt)
            
            # 提取代码块
            code = self._extract_code(response)
            
            return ActionResult(
                success=True,
                action="compose.code",
                message=f"💻 {language} 代码已生成",
                data={"code": code, "language": language}
            )
        except Exception as e:
            return ActionResult(False, "compose.code", f"生成失败: {e}", error=str(e))
    
    def _extract_code(self, text: str) -> str:
        """提取代码块"""
        import re
        
        # 匹配代码块
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        return text.strip()
    
    def set_llm_client(self, client) -> None:
        """设置LLM客户端"""
        self.llm_client = client

