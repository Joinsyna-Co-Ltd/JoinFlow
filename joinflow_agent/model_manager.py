"""
多模型管理器
============

为每个 Agent 类型提供多个可用模型，支持：
- 模型自动切换（当一个模型限流时自动切换到备用模型）
- 按 Agent 类型配置最适合的模型
- 统一的 API 调用接口
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent 类型"""
    LLM = "llm"           # 大模型 Agent（文本处理、推理）
    VISION = "vision"     # 视觉 Agent（图像理解、屏幕分析）
    CODE = "code"         # 代码 Agent（代码生成、执行）
    BROWSER = "browser"   # 浏览器 Agent（网页操作）
    OS = "os"             # 系统 Agent（本机操作）
    DATA = "data"         # 数据 Agent（数据分析）


@dataclass
class ModelConfig:
    """模型配置"""
    id: str
    name: str
    provider: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    enabled: bool = True
    is_free: bool = False
    supports_vision: bool = False
    supports_function_call: bool = True
    max_tokens: int = 4096
    description: str = ""
    priority: int = 0  # 优先级，数字越小优先级越高
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "api_base": self.api_base,
            "api_key": self.api_key,
            "enabled": self.enabled,
            "is_free": self.is_free,
            "supports_vision": self.supports_vision,
            "supports_function_call": self.supports_function_call,
            "max_tokens": self.max_tokens,
            "description": self.description,
            "priority": self.priority,
        }


# OpenRouter API Key（统一配置）
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY", 
    "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"
)


# 预定义的模型列表（按 Agent 类型分组）
AGENT_MODELS: Dict[AgentType, List[ModelConfig]] = {
    # 大模型 Agent - 通用文本处理
    AgentType.LLM: [
        ModelConfig(
            id="openrouter/mistralai/mistral-7b-instruct:free",
            name="Mistral 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=0,
            description="OpenRouter 免费模型，响应快速"
        ),
        ModelConfig(
            id="openrouter/google/gemma-2-9b-it:free",
            name="Gemma 2 9B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=1,
            description="Google Gemma 2 免费模型"
        ),
        ModelConfig(
            id="openrouter/meta-llama/llama-3.2-3b-instruct:free",
            name="Llama 3.2 3B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=2,
            description="Meta Llama 轻量免费模型"
        ),
        ModelConfig(
            id="openrouter/qwen/qwen-2-7b-instruct:free",
            name="Qwen 2 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=3,
            description="阿里通义千问免费模型"
        ),
        ModelConfig(
            id="openrouter/huggingfaceh4/zephyr-7b-beta:free",
            name="Zephyr 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=4,
            description="HuggingFace 免费模型"
        ),
        ModelConfig(
            id="openrouter/openchat/openchat-7b:free",
            name="OpenChat 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=5,
            description="OpenChat 免费模型"
        ),
        # 付费备选
        ModelConfig(
            id="openrouter/openai/gpt-4o-mini",
            name="GPT-4o Mini (付费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=False,
            priority=10,
            description="OpenAI 高质量模型"
        ),
    ],
    
    # 视觉 Agent - 图像理解
    AgentType.VISION: [
        ModelConfig(
            id="openrouter/google/gemini-2.0-flash-exp:free",
            name="Gemini 2.0 Flash (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            supports_vision=True,
            priority=0,
            description="Google 免费视觉模型"
        ),
        ModelConfig(
            id="openrouter/google/gemini-exp-1206:free",
            name="Gemini Exp 1206 (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            supports_vision=True,
            priority=1,
            description="Google 实验性免费模型"
        ),
        ModelConfig(
            id="openrouter/meta-llama/llama-3.2-11b-vision-instruct:free",
            name="Llama 3.2 Vision 11B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            supports_vision=True,
            priority=2,
            description="Meta 视觉模型"
        ),
        # 付费备选
        ModelConfig(
            id="openrouter/openai/gpt-4o",
            name="GPT-4o (付费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=False,
            supports_vision=True,
            priority=10,
            description="OpenAI 最强视觉模型"
        ),
        ModelConfig(
            id="openrouter/anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet (付费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=False,
            supports_vision=True,
            priority=11,
            description="Anthropic 视觉模型"
        ),
    ],
    
    # 代码 Agent - 代码生成
    AgentType.CODE: [
        ModelConfig(
            id="openrouter/mistralai/mistral-7b-instruct:free",
            name="Mistral 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=0,
            description="适合简单代码任务"
        ),
        ModelConfig(
            id="openrouter/google/gemma-2-9b-it:free",
            name="Gemma 2 9B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=1,
            description="Google 代码能力不错"
        ),
        ModelConfig(
            id="openrouter/qwen/qwen-2-7b-instruct:free",
            name="Qwen 2 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=2,
            description="Qwen 代码能力较强"
        ),
        # 付费备选
        ModelConfig(
            id="openrouter/anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet (付费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=False,
            priority=10,
            description="代码能力最强"
        ),
        ModelConfig(
            id="openrouter/openai/gpt-4o",
            name="GPT-4o (付费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=False,
            priority=11,
            description="OpenAI 代码模型"
        ),
    ],
    
    # 浏览器 Agent
    AgentType.BROWSER: [
        ModelConfig(
            id="openrouter/mistralai/mistral-7b-instruct:free",
            name="Mistral 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=0,
            description="网页内容理解"
        ),
        ModelConfig(
            id="openrouter/google/gemma-2-9b-it:free",
            name="Gemma 2 9B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=1,
            description="文本分析"
        ),
    ],
    
    # 系统 Agent
    AgentType.OS: [
        ModelConfig(
            id="openrouter/mistralai/mistral-7b-instruct:free",
            name="Mistral 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            supports_function_call=True,
            priority=0,
            description="系统命令理解"
        ),
        ModelConfig(
            id="openrouter/google/gemma-2-9b-it:free",
            name="Gemma 2 9B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=1,
            description="意图理解"
        ),
        ModelConfig(
            id="openrouter/qwen/qwen-2-7b-instruct:free",
            name="Qwen 2 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=2,
            description="中文理解强"
        ),
    ],
    
    # 数据 Agent
    AgentType.DATA: [
        ModelConfig(
            id="openrouter/mistralai/mistral-7b-instruct:free",
            name="Mistral 7B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=0,
            description="数据分析"
        ),
        ModelConfig(
            id="openrouter/google/gemma-2-9b-it:free",
            name="Gemma 2 9B (免费)",
            provider="openrouter",
            api_key=OPENROUTER_API_KEY,
            is_free=True,
            priority=1,
            description="数据处理"
        ),
    ],
}


class ModelManager:
    """多模型管理器"""
    
    def __init__(self):
        self.models = AGENT_MODELS.copy()
        self.failed_models: Dict[str, float] = {}  # 记录失败的模型和时间
        self.current_models: Dict[AgentType, str] = {}  # 当前使用的模型
        self._init_current_models()
    
    def _init_current_models(self):
        """初始化每个 Agent 类型的当前模型（选择优先级最高的）"""
        for agent_type, models in self.models.items():
            enabled_models = [m for m in models if m.enabled]
            if enabled_models:
                # 按优先级排序，选择第一个
                enabled_models.sort(key=lambda m: m.priority)
                self.current_models[agent_type] = enabled_models[0].id
    
    def get_model(self, agent_type: AgentType) -> Optional[ModelConfig]:
        """获取指定 Agent 类型的当前模型"""
        model_id = self.current_models.get(agent_type)
        if model_id:
            return self.get_model_by_id(model_id)
        return None
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelConfig]:
        """根据模型 ID 获取配置"""
        for models in self.models.values():
            for model in models:
                if model.id == model_id:
                    return model
        return None
    
    def get_models_for_agent(self, agent_type: AgentType) -> List[ModelConfig]:
        """获取指定 Agent 类型的所有可用模型"""
        models = self.models.get(agent_type, [])
        enabled = [m for m in models if m.enabled]
        enabled.sort(key=lambda m: m.priority)
        return enabled
    
    def get_next_model(self, agent_type: AgentType, current_model_id: str) -> Optional[ModelConfig]:
        """获取下一个可用模型（用于自动切换）"""
        models = self.get_models_for_agent(agent_type)
        current_idx = None
        
        for i, model in enumerate(models):
            if model.id == current_model_id:
                current_idx = i
                break
        
        if current_idx is not None and current_idx + 1 < len(models):
            return models[current_idx + 1]
        
        # 如果没有更多模型，返回第一个（循环）
        if models:
            return models[0]
        
        return None
    
    def mark_model_failed(self, model_id: str):
        """标记模型失败（用于临时禁用）"""
        import time
        self.failed_models[model_id] = time.time()
        logger.warning(f"Model {model_id} marked as failed")
    
    def is_model_available(self, model_id: str) -> bool:
        """检查模型是否可用"""
        import time
        if model_id in self.failed_models:
            # 5 分钟后重试
            if time.time() - self.failed_models[model_id] > 300:
                del self.failed_models[model_id]
                return True
            return False
        return True
    
    def switch_model(self, agent_type: AgentType, model_id: str) -> bool:
        """切换指定 Agent 类型的模型"""
        model = self.get_model_by_id(model_id)
        if model and model.enabled:
            self.current_models[agent_type] = model_id
            logger.info(f"Switched {agent_type.value} agent to model: {model.name}")
            return True
        return False
    
    async def call_llm(
        self, 
        agent_type: AgentType,
        messages: List[Dict],
        **kwargs
    ) -> Optional[str]:
        """调用 LLM，支持自动重试和切换模型"""
        import litellm
        
        models = self.get_models_for_agent(agent_type)
        last_error = None
        
        for model in models:
            if not self.is_model_available(model.id):
                continue
            
            try:
                # 设置 API Key - 根据模型类型设置正确的环境变量
                if model.api_key:
                    if "openrouter" in model.id.lower() or model.api_base and "openrouter" in model.api_base.lower():
                        os.environ["OPENROUTER_API_KEY"] = model.api_key
                    else:
                        os.environ["OPENAI_API_KEY"] = model.api_key
                
                # 构建 litellm 调用参数
                call_kwargs = {
                    "model": model.id,
                    "messages": messages,
                    **kwargs
                }
                
                # 如果有 api_base，添加到调用参数
                if model.api_base:
                    call_kwargs["api_base"] = model.api_base
                
                # 如果有 api_key，直接传递给 litellm
                if model.api_key:
                    call_kwargs["api_key"] = model.api_key
                
                response = await litellm.acompletion(**call_kwargs)
                
                # 成功，更新当前模型
                self.current_models[agent_type] = model.id
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # 检查是否是限流错误
                if "rate" in error_str or "429" in error_str or "limit" in error_str:
                    logger.warning(f"Model {model.id} rate limited, trying next...")
                    self.mark_model_failed(model.id)
                else:
                    logger.error(f"Model {model.id} error: {e}")
                
                continue
        
        # 所有模型都失败
        if last_error:
            raise last_error
        
        return None
    
    def call_llm_sync(
        self,
        agent_type: AgentType,
        messages: List[Dict],
        **kwargs
    ) -> Optional[str]:
        """同步调用 LLM"""
        import litellm
        
        models = self.get_models_for_agent(agent_type)
        last_error = None
        
        for model in models:
            if not self.is_model_available(model.id):
                continue
            
            try:
                # 设置 API Key - 根据模型类型设置正确的环境变量
                if model.api_key:
                    if "openrouter" in model.id.lower() or model.api_base and "openrouter" in model.api_base.lower():
                        os.environ["OPENROUTER_API_KEY"] = model.api_key
                    else:
                        os.environ["OPENAI_API_KEY"] = model.api_key
                
                # 构建 litellm 调用参数
                call_kwargs = {
                    "model": model.id,
                    "messages": messages,
                    **kwargs
                }
                
                # 如果有 api_base，添加到调用参数
                if model.api_base:
                    call_kwargs["api_base"] = model.api_base
                
                # 如果有 api_key，直接传递给 litellm
                if model.api_key:
                    call_kwargs["api_key"] = model.api_key
                
                response = litellm.completion(**call_kwargs)
                
                self.current_models[agent_type] = model.id
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                if "rate" in error_str or "429" in error_str or "limit" in error_str:
                    logger.warning(f"Model {model.id} rate limited, trying next...")
                    self.mark_model_failed(model.id)
                else:
                    logger.error(f"Model {model.id} error: {e}")
                
                continue
        
        if last_error:
            raise last_error
        
        return None
    
    def get_status(self) -> Dict:
        """获取模型管理器状态"""
        status = {
            "current_models": {},
            "available_models": {},
            "failed_models": list(self.failed_models.keys()),
        }
        
        for agent_type in AgentType:
            current = self.current_models.get(agent_type)
            models = self.get_models_for_agent(agent_type)
            
            status["current_models"][agent_type.value] = current
            status["available_models"][agent_type.value] = [
                {
                    "id": m.id,
                    "name": m.name,
                    "is_free": m.is_free,
                    "available": self.is_model_available(m.id),
                }
                for m in models
            ]
        
        return status


# 全局单例
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """获取模型管理器单例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def get_model_for_agent(agent_type: str) -> Optional[ModelConfig]:
    """便捷函数：获取指定 Agent 类型的模型"""
    manager = get_model_manager()
    try:
        agent_enum = AgentType(agent_type)
        return manager.get_model(agent_enum)
    except ValueError:
        return None


def call_llm_with_fallback(
    agent_type: str,
    messages: List[Dict],
    **kwargs
) -> Optional[str]:
    """便捷函数：调用 LLM（带自动降级）"""
    manager = get_model_manager()
    try:
        agent_enum = AgentType(agent_type)
        return manager.call_llm_sync(agent_enum, messages, **kwargs)
    except ValueError:
        # 默认使用 LLM agent
        return manager.call_llm_sync(AgentType.LLM, messages, **kwargs)

