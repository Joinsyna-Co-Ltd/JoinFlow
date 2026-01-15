"""
LLM客户端
"""
import os
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息"""
    role: str  # system, user, assistant
    content: str


class LLMClient:
    """
    LLM客户端
    
    支持多种LLM提供商
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 默认模型
        if not self.model:
            self.model = self._default_model()
        
        # 初始化客户端
        self._client = None
        self._init_client()
    
    def _default_model(self) -> str:
        """获取默认模型"""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-sonnet-20240229",
            "azure": "gpt-4",
            "deepseek": "deepseek-chat",
            "ollama": "llama2",
        }
        return defaults.get(self.provider, "gpt-4o-mini")
    
    def _init_client(self) -> None:
        """初始化客户端"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            elif self.provider == "anthropic":
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            elif self.provider == "deepseek":
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key or os.environ.get("DEEPSEEK_API_KEY"),
                    base_url=self.base_url or "https://api.deepseek.com",
                )
            elif self.provider == "ollama":
                # Ollama使用OpenAI兼容接口
                from openai import OpenAI
                self._client = OpenAI(
                    api_key="ollama",
                    base_url=self.base_url or "http://localhost:11434/v1",
                )
        except ImportError as e:
            logger.warning(f"无法导入 {self.provider} 客户端库: {e}")
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {e}")
    
    def chat(
        self,
        message: str,
        system_prompt: str = None,
        history: List[Message] = None,
    ) -> str:
        """
        对话
        
        Args:
            message: 用户消息
            system_prompt: 系统提示
            history: 历史消息
            
        Returns:
            str: 回复内容
        """
        messages = []
        
        # 系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 历史消息
        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
        
        # 用户消息
        messages.append({"role": "user", "content": message})
        
        # 调用API
        if self.provider in ["openai", "deepseek", "ollama"]:
            return self._chat_openai(messages)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, system_prompt)
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")
    
    def _chat_openai(self, messages: List[Dict]) -> str:
        """OpenAI格式调用"""
        if not self._client:
            raise RuntimeError("LLM客户端未初始化")
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        return response.choices[0].message.content
    
    def _chat_anthropic(self, messages: List[Dict], system_prompt: str = None) -> str:
        """Anthropic格式调用"""
        if not self._client:
            raise RuntimeError("LLM客户端未初始化")
        
        # 分离系统消息
        user_messages = [m for m in messages if m["role"] != "system"]
        
        response = self._client.messages.create(
            model=self.model,
            system=system_prompt or "",
            messages=user_messages,
            max_tokens=self.max_tokens,
        )
        
        return response.content[0].text
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self._client is not None

