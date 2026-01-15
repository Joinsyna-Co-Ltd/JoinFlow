"""
编写执行器 - 处理文本、代码生成
"""
from typing import Any, Dict, Optional
from pathlib import Path

from .base import BaseExecutor, ExecutorResult


class ComposeExecutor(BaseExecutor):
    """
    编写执行器
    
    使用LLM生成文本、代码等内容
    """
    
    name = "compose"
    supported_operations = [
        "compose.text", "compose.code", "compose.email",
        "compose.document", "compose.summary",
    ]
    
    # 提示词模板
    PROMPTS = {
        "text": "请根据以下要求编写文本内容：\n\n{instruction}\n\n要求：{requirements}",
        "code": """请编写以下代码：

任务描述：{instruction}
编程语言：{language}
额外要求：{requirements}

请只返回代码，不要解释。如果需要，可以添加必要的注释。""",
        "email": """请帮我撰写一封邮件：

主题：{subject}
收件人：{recipient}
内容要点：{instruction}
语气：{tone}

请生成完整的邮件正文。""",
        "document": """请撰写以下文档：

文档类型：{doc_type}
主题：{instruction}
大纲/要求：{requirements}

请生成完整的文档内容。""",
        "summary": """请对以下内容进行总结：

{content}

总结要求：{requirements}
""",
    }
    
    def __init__(self, config=None, llm_client=None):
        super().__init__(config)
        self.llm_client = llm_client
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行编写操作"""
        if not self.llm_client:
            return ExecutorResult(
                success=False,
                message="编写功能需要配置LLM客户端",
                error="NoLLMClient"
            )
        
        try:
            if operation == "compose.text":
                return self._compose_text(parameters)
            elif operation == "compose.code":
                return self._compose_code(parameters)
            elif operation == "compose.email":
                return self._compose_email(parameters)
            elif operation == "compose.document":
                return self._compose_document(parameters)
            elif operation == "compose.summary":
                return self._compose_summary(parameters)
            else:
                return ExecutorResult(False, f"不支持的操作: {operation}")
        except Exception as e:
            return ExecutorResult(False, f"编写失败: {e}")
    
    def _compose_text(self, params: Dict) -> ExecutorResult:
        """编写文本"""
        instruction = params.get("instruction") or params.get("prompt") or params.get("content")
        requirements = params.get("requirements", "")
        save_path = params.get("save_path")
        
        if not instruction:
            return ExecutorResult(False, "缺少编写指令")
        
        prompt = self.PROMPTS["text"].format(
            instruction=instruction,
            requirements=requirements or "清晰、准确"
        )
        
        try:
            response = self.llm_client.chat(prompt)
            
            # 保存到文件（如果指定）
            if save_path:
                path = Path(save_path).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(response, encoding='utf-8')
            
            self._log_action("compose_text", f"Generated {len(response)} chars")
            
            return ExecutorResult(
                success=True,
                message="文本生成成功",
                data={
                    "content": response,
                    "length": len(response),
                    "saved_to": str(save_path) if save_path else None,
                }
            )
        except Exception as e:
            return ExecutorResult(False, f"生成失败: {e}")
    
    def _compose_code(self, params: Dict) -> ExecutorResult:
        """编写代码"""
        instruction = params.get("instruction") or params.get("task")
        language = params.get("language", "python")
        requirements = params.get("requirements", "")
        save_path = params.get("save_path")
        
        if not instruction:
            return ExecutorResult(False, "缺少编写指令")
        
        prompt = self.PROMPTS["code"].format(
            instruction=instruction,
            language=language,
            requirements=requirements or "代码简洁、有适当注释"
        )
        
        try:
            response = self.llm_client.chat(prompt)
            
            # 提取代码块
            code = self._extract_code(response, language)
            
            # 保存到文件
            if save_path:
                path = Path(save_path).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(code, encoding='utf-8')
            
            self._log_action("compose_code", f"Generated {language} code")
            
            return ExecutorResult(
                success=True,
                message=f"{language} 代码生成成功",
                data={
                    "code": code,
                    "language": language,
                    "lines": code.count('\n') + 1,
                    "saved_to": str(save_path) if save_path else None,
                }
            )
        except Exception as e:
            return ExecutorResult(False, f"生成失败: {e}")
    
    def _compose_email(self, params: Dict) -> ExecutorResult:
        """编写邮件"""
        subject = params.get("subject", "")
        recipient = params.get("recipient") or params.get("to", "")
        instruction = params.get("instruction") or params.get("content")
        tone = params.get("tone", "专业、礼貌")
        
        if not instruction:
            return ExecutorResult(False, "缺少邮件内容要点")
        
        prompt = self.PROMPTS["email"].format(
            subject=subject or "待定",
            recipient=recipient or "收件人",
            instruction=instruction,
            tone=tone
        )
        
        try:
            response = self.llm_client.chat(prompt)
            
            self._log_action("compose_email", f"Generated email")
            
            return ExecutorResult(
                success=True,
                message="邮件生成成功",
                data={
                    "subject": subject,
                    "recipient": recipient,
                    "body": response,
                }
            )
        except Exception as e:
            return ExecutorResult(False, f"生成失败: {e}")
    
    def _compose_document(self, params: Dict) -> ExecutorResult:
        """编写文档"""
        doc_type = params.get("doc_type") or params.get("type", "通用文档")
        instruction = params.get("instruction") or params.get("topic")
        requirements = params.get("requirements", "")
        save_path = params.get("save_path")
        
        if not instruction:
            return ExecutorResult(False, "缺少文档主题")
        
        prompt = self.PROMPTS["document"].format(
            doc_type=doc_type,
            instruction=instruction,
            requirements=requirements or "结构清晰、内容完整"
        )
        
        try:
            response = self.llm_client.chat(prompt)
            
            if save_path:
                path = Path(save_path).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(response, encoding='utf-8')
            
            self._log_action("compose_document", f"Generated {doc_type}")
            
            return ExecutorResult(
                success=True,
                message=f"{doc_type}生成成功",
                data={
                    "content": response,
                    "type": doc_type,
                    "saved_to": str(save_path) if save_path else None,
                }
            )
        except Exception as e:
            return ExecutorResult(False, f"生成失败: {e}")
    
    def _compose_summary(self, params: Dict) -> ExecutorResult:
        """生成摘要"""
        content = params.get("content") or params.get("text")
        requirements = params.get("requirements", "简洁明了，突出重点")
        file_path = params.get("file_path")
        
        # 从文件读取内容
        if not content and file_path:
            path = Path(file_path).expanduser()
            if path.exists():
                content = path.read_text(encoding='utf-8')
        
        if not content:
            return ExecutorResult(False, "缺少要总结的内容")
        
        prompt = self.PROMPTS["summary"].format(
            content=content,
            requirements=requirements
        )
        
        try:
            response = self.llm_client.chat(prompt)
            
            self._log_action("compose_summary", f"Summarized {len(content)} chars")
            
            return ExecutorResult(
                success=True,
                message="摘要生成成功",
                data={
                    "summary": response,
                    "original_length": len(content),
                    "summary_length": len(response),
                }
            )
        except Exception as e:
            return ExecutorResult(False, f"生成失败: {e}")
    
    def _extract_code(self, text: str, language: str) -> str:
        """从响应中提取代码"""
        import re
        
        # 尝试匹配代码块
        pattern = rf'```(?:{language})?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        # 如果没有代码块，返回原文
        return text.strip()
    
    def set_llm_client(self, llm_client) -> None:
        """设置LLM客户端"""
        self.llm_client = llm_client

