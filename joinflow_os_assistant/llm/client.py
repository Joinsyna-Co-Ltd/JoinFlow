"""
LLM客户端 - 统一的大模型接口
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class LLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def chat_with_history(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """带历史的聊天"""
        pass


class SimpleLLMClient(LLMClient):
    """
    简单LLM客户端
    
    支持OpenAI兼容的API（包括本地部署的模型）
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self._client = None
    
    def _get_client(self):
        """获取OpenAI客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError("需要安装 openai: pip install openai")
        return self._client
    
    def chat(self, prompt: str, **kwargs) -> str:
        """发送聊天请求"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat_with_history(messages, **kwargs)
    
    def chat_with_history(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """带历史的聊天"""
        try:
            client = self._get_client()
            
            response = client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM请求失败: {e}")
            raise


class MockLLMClient(LLMClient):
    """
    模拟LLM客户端（用于测试）
    """
    
    def __init__(self):
        self.responses = {}
    
    def add_response(self, prompt_contains: str, response: str) -> None:
        """添加模拟响应"""
        self.responses[prompt_contains] = response
    
    def chat(self, prompt: str, **kwargs) -> str:
        """返回模拟响应"""
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # 默认响应
        return json.dumps({
            "intent_type": "UNKNOWN",
            "confidence": 0.5,
            "entities": [],
            "description": "模拟响应",
        })
    
    def chat_with_history(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """带历史的聊天"""
        last_message = messages[-1]["content"] if messages else ""
        return self.chat(last_message, **kwargs)


class LocalLLMClient(LLMClient):
    """
    本地LLM客户端
    
    支持 Ollama、LM Studio 等本地模型
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",  # Ollama默认端口
        model: str = "llama2",
        provider: str = "ollama",  # ollama, lmstudio
    ):
        self.base_url = base_url
        self.model = model
        self.provider = provider
    
    def chat(self, prompt: str, **kwargs) -> str:
        """发送聊天请求"""
        import requests
        
        if self.provider == "ollama":
            return self._ollama_chat(prompt, **kwargs)
        elif self.provider == "lmstudio":
            return self._lmstudio_chat(prompt, **kwargs)
        else:
            raise ValueError(f"不支持的provider: {self.provider}")
    
    def chat_with_history(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """带历史的聊天"""
        # 简单实现：将历史拼接
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"
        
        return self.chat(prompt, **kwargs)
    
    def _ollama_chat(self, prompt: str, **kwargs) -> str:
        """Ollama聊天"""
        import requests
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": kwargs.get("model", self.model),
                "prompt": prompt,
                "stream": False,
            },
            timeout=120
        )
        
        if response.ok:
            return response.json().get("response", "")
        else:
            raise Exception(f"Ollama请求失败: {response.text}")
    
    def _lmstudio_chat(self, prompt: str, **kwargs) -> str:
        """LM Studio聊天（OpenAI兼容API）"""
        import requests
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": kwargs.get("model", self.model),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120
        )
        
        if response.ok:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"LM Studio请求失败: {response.text}")


def create_llm_client(
    provider: str = "openai",
    **kwargs
) -> LLMClient:
    """
    创建LLM客户端
    
    Args:
        provider: 提供者 (openai, ollama, lmstudio, mock)
        **kwargs: 其他参数
    
    Returns:
        LLMClient: LLM客户端实例
    """
    if provider == "openai":
        return SimpleLLMClient(**kwargs)
    elif provider == "ollama":
        return LocalLLMClient(provider="ollama", **kwargs)
    elif provider == "lmstudio":
        return LocalLLMClient(provider="lmstudio", **kwargs)
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"不支持的provider: {provider}")

