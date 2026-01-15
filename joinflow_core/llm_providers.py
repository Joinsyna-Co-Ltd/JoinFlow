"""
JoinFlow LLM Providers Registry
================================

Complete support for all major LLM providers worldwide.

Supported Providers:
- OpenAI (GPT-4, GPT-4o, o1, o3)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini Pro, Gemini Ultra)
- DeepSeek (deepseek-chat, deepseek-coder)
- Mistral AI (mistral-large, mistral-medium)
- 阿里云通义千问 (Qwen)
- 百度文心一言 (ERNIE)
- 智谱AI (GLM-4)
- MiniMax (abab)
- 月之暗面 Moonshot
- 零一万物 (Yi)
- 字节跳动豆包 (Doubao)
- 讯飞星火 (Spark)
- Cohere
- Together AI
- Groq
- Perplexity
- Fireworks AI
- Azure OpenAI
- AWS Bedrock
- 本地模型 (Ollama, LM Studio, vLLM)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ProviderCategory(Enum):
    """Provider categories"""
    INTERNATIONAL = "international"
    CHINESE = "chinese"
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class LLMProvider:
    """LLM Provider configuration"""
    id: str
    name: str
    category: ProviderCategory
    api_base: str
    api_key_env: str
    models: List[Dict]
    supports_streaming: bool = True
    supports_function_calling: bool = True
    supports_vision: bool = False
    description: str = ""
    website: str = ""
    docs_url: str = ""
    pricing_url: str = ""


# ============================================
# International Providers
# ============================================

OPENAI = LLMProvider(
    id="openai",
    name="OpenAI",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.openai.com/v1",
    api_key_env="OPENAI_API_KEY",
    supports_vision=True,
    description="OpenAI - GPT系列模型，最强大的通用AI模型",
    website="https://openai.com",
    docs_url="https://platform.openai.com/docs",
    pricing_url="https://openai.com/pricing",
    models=[
        {"id": "gpt-4o", "name": "GPT-4o", "context": 128000, "vision": True, "cost_per_1k_input": 0.005, "cost_per_1k_output": 0.015},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": 128000, "vision": True, "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0006},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": 128000, "vision": True, "cost_per_1k_input": 0.01, "cost_per_1k_output": 0.03},
        {"id": "gpt-4", "name": "GPT-4", "context": 8192, "cost_per_1k_input": 0.03, "cost_per_1k_output": 0.06},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": 16385, "cost_per_1k_input": 0.0005, "cost_per_1k_output": 0.0015},
        {"id": "o1-preview", "name": "o1 Preview", "context": 128000, "reasoning": True, "cost_per_1k_input": 0.015, "cost_per_1k_output": 0.06},
        {"id": "o1-mini", "name": "o1 Mini", "context": 128000, "reasoning": True, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.012},
        {"id": "o3-mini", "name": "o3 Mini", "context": 128000, "reasoning": True, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.012},
    ]
)

ANTHROPIC = LLMProvider(
    id="anthropic",
    name="Anthropic",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.anthropic.com/v1",
    api_key_env="ANTHROPIC_API_KEY",
    supports_vision=True,
    description="Anthropic - Claude系列，安全可控的AI助手",
    website="https://anthropic.com",
    docs_url="https://docs.anthropic.com",
    pricing_url="https://anthropic.com/pricing",
    models=[
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context": 200000, "vision": True, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context": 200000, "vision": True, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.005},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context": 200000, "vision": True, "cost_per_1k_input": 0.015, "cost_per_1k_output": 0.075},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context": 200000, "vision": True, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context": 200000, "vision": True, "cost_per_1k_input": 0.00025, "cost_per_1k_output": 0.00125},
    ]
)

GOOGLE = LLMProvider(
    id="google",
    name="Google AI",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://generativelanguage.googleapis.com/v1beta",
    api_key_env="GOOGLE_API_KEY",
    supports_vision=True,
    description="Google Gemini - 多模态AI模型",
    website="https://ai.google.dev",
    docs_url="https://ai.google.dev/docs",
    pricing_url="https://ai.google.dev/pricing",
    models=[
        {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash", "context": 1000000, "vision": True, "cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context": 2000000, "vision": True, "cost_per_1k_input": 0.00125, "cost_per_1k_output": 0.005},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context": 1000000, "vision": True, "cost_per_1k_input": 0.000075, "cost_per_1k_output": 0.0003},
        {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro", "context": 32000, "cost_per_1k_input": 0.0005, "cost_per_1k_output": 0.0015},
    ]
)

MISTRAL = LLMProvider(
    id="mistral",
    name="Mistral AI",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.mistral.ai/v1",
    api_key_env="MISTRAL_API_KEY",
    supports_vision=True,
    description="Mistral AI - 欧洲领先的开源大模型",
    website="https://mistral.ai",
    docs_url="https://docs.mistral.ai",
    pricing_url="https://mistral.ai/pricing",
    models=[
        {"id": "mistral-large-latest", "name": "Mistral Large", "context": 128000, "cost_per_1k_input": 0.002, "cost_per_1k_output": 0.006},
        {"id": "mistral-medium-latest", "name": "Mistral Medium", "context": 32000, "cost_per_1k_input": 0.0027, "cost_per_1k_output": 0.0081},
        {"id": "mistral-small-latest", "name": "Mistral Small", "context": 32000, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.003},
        {"id": "pixtral-large-latest", "name": "Pixtral Large", "context": 128000, "vision": True, "cost_per_1k_input": 0.002, "cost_per_1k_output": 0.006},
        {"id": "codestral-latest", "name": "Codestral", "context": 32000, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.003},
        {"id": "open-mixtral-8x22b", "name": "Mixtral 8x22B", "context": 64000, "cost_per_1k_input": 0.002, "cost_per_1k_output": 0.006},
        {"id": "open-mixtral-8x7b", "name": "Mixtral 8x7B", "context": 32000, "cost_per_1k_input": 0.0007, "cost_per_1k_output": 0.0007},
    ]
)

COHERE = LLMProvider(
    id="cohere",
    name="Cohere",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.cohere.ai/v1",
    api_key_env="COHERE_API_KEY",
    description="Cohere - 企业级NLP解决方案",
    website="https://cohere.com",
    docs_url="https://docs.cohere.com",
    pricing_url="https://cohere.com/pricing",
    models=[
        {"id": "command-r-plus", "name": "Command R+", "context": 128000, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
        {"id": "command-r", "name": "Command R", "context": 128000, "cost_per_1k_input": 0.0005, "cost_per_1k_output": 0.0015},
        {"id": "command", "name": "Command", "context": 4096, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.002},
        {"id": "command-light", "name": "Command Light", "context": 4096, "cost_per_1k_input": 0.0003, "cost_per_1k_output": 0.0006},
    ]
)

GROQ = LLMProvider(
    id="groq",
    name="Groq",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.groq.com/openai/v1",
    api_key_env="GROQ_API_KEY",
    description="Groq - 超快速推理，LPU加速",
    website="https://groq.com",
    docs_url="https://console.groq.com/docs",
    pricing_url="https://groq.com/pricing",
    models=[
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "context": 128000, "cost_per_1k_input": 0.00059, "cost_per_1k_output": 0.00079},
        {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B", "context": 128000, "cost_per_1k_input": 0.00059, "cost_per_1k_output": 0.00079},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "context": 128000, "cost_per_1k_input": 0.00005, "cost_per_1k_output": 0.00008},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": 32768, "cost_per_1k_input": 0.00024, "cost_per_1k_output": 0.00024},
        {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "context": 8192, "cost_per_1k_input": 0.0002, "cost_per_1k_output": 0.0002},
    ]
)

TOGETHER = LLMProvider(
    id="together",
    name="Together AI",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.together.xyz/v1",
    api_key_env="TOGETHER_API_KEY",
    description="Together AI - 开源模型云平台",
    website="https://together.ai",
    docs_url="https://docs.together.ai",
    pricing_url="https://together.ai/pricing",
    models=[
        {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "name": "Llama 3.3 70B Turbo", "context": 128000, "cost_per_1k_input": 0.00088, "cost_per_1k_output": 0.00088},
        {"id": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo", "name": "Llama 3.1 405B Turbo", "context": 128000, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.003},
        {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "name": "Llama 3.1 70B Turbo", "context": 128000, "cost_per_1k_input": 0.00088, "cost_per_1k_output": 0.00088},
        {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "name": "Llama 3.1 8B Turbo", "context": 128000, "cost_per_1k_input": 0.00018, "cost_per_1k_output": 0.00018},
        {"id": "mistralai/Mixtral-8x22B-Instruct-v0.1", "name": "Mixtral 8x22B", "context": 65536, "cost_per_1k_input": 0.0012, "cost_per_1k_output": 0.0012},
        {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo", "name": "Qwen 2.5 72B Turbo", "context": 32768, "cost_per_1k_input": 0.0012, "cost_per_1k_output": 0.0012},
        {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1", "context": 65536, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.007},
    ]
)

PERPLEXITY = LLMProvider(
    id="perplexity",
    name="Perplexity AI",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.perplexity.ai",
    api_key_env="PERPLEXITY_API_KEY",
    description="Perplexity - 实时联网搜索增强AI",
    website="https://perplexity.ai",
    docs_url="https://docs.perplexity.ai",
    pricing_url="https://perplexity.ai/pricing",
    models=[
        {"id": "llama-3.1-sonar-huge-128k-online", "name": "Sonar Huge (Online)", "context": 128000, "online": True, "cost_per_1k_input": 0.005, "cost_per_1k_output": 0.005},
        {"id": "llama-3.1-sonar-large-128k-online", "name": "Sonar Large (Online)", "context": 128000, "online": True, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.001},
        {"id": "llama-3.1-sonar-small-128k-online", "name": "Sonar Small (Online)", "context": 128000, "online": True, "cost_per_1k_input": 0.0002, "cost_per_1k_output": 0.0002},
        {"id": "llama-3.1-sonar-large-128k-chat", "name": "Sonar Large (Chat)", "context": 128000, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.001},
    ]
)

FIREWORKS = LLMProvider(
    id="fireworks",
    name="Fireworks AI",
    category=ProviderCategory.INTERNATIONAL,
    api_base="https://api.fireworks.ai/inference/v1",
    api_key_env="FIREWORKS_API_KEY",
    description="Fireworks AI - 高性能模型推理",
    website="https://fireworks.ai",
    docs_url="https://docs.fireworks.ai",
    pricing_url="https://fireworks.ai/pricing",
    models=[
        {"id": "accounts/fireworks/models/llama-v3p3-70b-instruct", "name": "Llama 3.3 70B", "context": 128000, "cost_per_1k_input": 0.0009, "cost_per_1k_output": 0.0009},
        {"id": "accounts/fireworks/models/llama-v3p1-405b-instruct", "name": "Llama 3.1 405B", "context": 128000, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.003},
        {"id": "accounts/fireworks/models/qwen2p5-72b-instruct", "name": "Qwen 2.5 72B", "context": 32768, "cost_per_1k_input": 0.0009, "cost_per_1k_output": 0.0009},
        {"id": "accounts/fireworks/models/deepseek-r1", "name": "DeepSeek R1", "context": 65536, "cost_per_1k_input": 0.002, "cost_per_1k_output": 0.008},
        {"id": "accounts/fireworks/models/mixtral-8x22b-instruct", "name": "Mixtral 8x22B", "context": 65536, "cost_per_1k_input": 0.0009, "cost_per_1k_output": 0.0009},
    ]
)


# ============================================
# Chinese Providers (国内提供商)
# ============================================

DEEPSEEK = LLMProvider(
    id="deepseek",
    name="DeepSeek (深度求索)",
    category=ProviderCategory.CHINESE,
    api_base="https://api.deepseek.com/v1",
    api_key_env="DEEPSEEK_API_KEY",
    supports_vision=False,
    description="DeepSeek - 国产高性价比模型，推理能力强",
    website="https://deepseek.com",
    docs_url="https://platform.deepseek.com/api-docs",
    pricing_url="https://platform.deepseek.com/api-docs/pricing",
    models=[
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "context": 64000, "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00028},
        {"id": "deepseek-reasoner", "name": "DeepSeek R1", "context": 64000, "reasoning": True, "cost_per_1k_input": 0.00055, "cost_per_1k_output": 0.00219},
        {"id": "deepseek-coder", "name": "DeepSeek Coder", "context": 64000, "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00028},
    ]
)

QWEN = LLMProvider(
    id="qwen",
    name="通义千问 (Qwen)",
    category=ProviderCategory.CHINESE,
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key_env="DASHSCOPE_API_KEY",
    supports_vision=True,
    description="阿里云通义千问 - 阿里巴巴大模型",
    website="https://tongyi.aliyun.com",
    docs_url="https://help.aliyun.com/zh/dashscope",
    pricing_url="https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-thousand-questions-metering-and-billing",
    models=[
        {"id": "qwen-max", "name": "Qwen Max", "context": 32000, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.0084},
        {"id": "qwen-plus", "name": "Qwen Plus", "context": 131072, "cost_per_1k_input": 0.00056, "cost_per_1k_output": 0.00168},
        {"id": "qwen-turbo", "name": "Qwen Turbo", "context": 131072, "cost_per_1k_input": 0.00028, "cost_per_1k_output": 0.00084},
        {"id": "qwen-long", "name": "Qwen Long", "context": 10000000, "cost_per_1k_input": 0.00007, "cost_per_1k_output": 0.00028},
        {"id": "qwen-vl-max", "name": "Qwen VL Max", "context": 32000, "vision": True, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.0084},
        {"id": "qwen-vl-plus", "name": "Qwen VL Plus", "context": 8000, "vision": True, "cost_per_1k_input": 0.0011, "cost_per_1k_output": 0.0033},
        {"id": "qwen-coder-plus", "name": "Qwen Coder Plus", "context": 131072, "cost_per_1k_input": 0.0049, "cost_per_1k_output": 0.0049},
    ]
)

BAIDU = LLMProvider(
    id="baidu",
    name="文心一言 (ERNIE)",
    category=ProviderCategory.CHINESE,
    api_base="https://aip.baidubce.com/rpc/2.0/ai_custom/v1",
    api_key_env="BAIDU_API_KEY",
    supports_vision=True,
    description="百度文心一言 - 百度大模型",
    website="https://yiyan.baidu.com",
    docs_url="https://cloud.baidu.com/doc/WENXINWORKSHOP",
    pricing_url="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7",
    models=[
        {"id": "ernie-4.0-8k", "name": "ERNIE 4.0", "context": 8192, "cost_per_1k_input": 0.017, "cost_per_1k_output": 0.017},
        {"id": "ernie-4.0-turbo-8k", "name": "ERNIE 4.0 Turbo", "context": 8192, "cost_per_1k_input": 0.0042, "cost_per_1k_output": 0.0084},
        {"id": "ernie-3.5-8k", "name": "ERNIE 3.5", "context": 8192, "cost_per_1k_input": 0.0017, "cost_per_1k_output": 0.0033},
        {"id": "ernie-3.5-128k", "name": "ERNIE 3.5 128K", "context": 128000, "cost_per_1k_input": 0.0025, "cost_per_1k_output": 0.005},
        {"id": "ernie-speed-8k", "name": "ERNIE Speed", "context": 8192, "cost_per_1k_input": 0.0006, "cost_per_1k_output": 0.0008},
        {"id": "ernie-speed-128k", "name": "ERNIE Speed 128K", "context": 128000, "cost_per_1k_input": 0.0006, "cost_per_1k_output": 0.0008},
        {"id": "ernie-lite-8k", "name": "ERNIE Lite", "context": 8192, "cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0},
    ]
)

ZHIPU = LLMProvider(
    id="zhipu",
    name="智谱AI (GLM)",
    category=ProviderCategory.CHINESE,
    api_base="https://open.bigmodel.cn/api/paas/v4",
    api_key_env="ZHIPU_API_KEY",
    supports_vision=True,
    description="智谱AI - GLM系列，清华技术背景",
    website="https://www.zhipuai.cn",
    docs_url="https://open.bigmodel.cn/dev/api",
    pricing_url="https://open.bigmodel.cn/pricing",
    models=[
        {"id": "glm-4-plus", "name": "GLM-4 Plus", "context": 128000, "cost_per_1k_input": 0.007, "cost_per_1k_output": 0.007},
        {"id": "glm-4-0520", "name": "GLM-4", "context": 128000, "cost_per_1k_input": 0.014, "cost_per_1k_output": 0.014},
        {"id": "glm-4-air", "name": "GLM-4 Air", "context": 128000, "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00014},
        {"id": "glm-4-airx", "name": "GLM-4 AirX", "context": 8192, "cost_per_1k_input": 0.0014, "cost_per_1k_output": 0.0014},
        {"id": "glm-4-flash", "name": "GLM-4 Flash", "context": 128000, "cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0},
        {"id": "glm-4-long", "name": "GLM-4 Long", "context": 1000000, "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00014},
        {"id": "glm-4v-plus", "name": "GLM-4V Plus", "context": 8192, "vision": True, "cost_per_1k_input": 0.014, "cost_per_1k_output": 0.014},
        {"id": "glm-4v", "name": "GLM-4V", "context": 2048, "vision": True, "cost_per_1k_input": 0.007, "cost_per_1k_output": 0.007},
        {"id": "codegeex-4", "name": "CodeGeeX 4", "context": 128000, "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00014},
    ]
)

MOONSHOT = LLMProvider(
    id="moonshot",
    name="月之暗面 (Moonshot/Kimi)",
    category=ProviderCategory.CHINESE,
    api_base="https://api.moonshot.cn/v1",
    api_key_env="MOONSHOT_API_KEY",
    supports_vision=False,
    description="月之暗面Kimi - 超长上下文，200万tokens",
    website="https://www.moonshot.cn",
    docs_url="https://platform.moonshot.cn/docs",
    pricing_url="https://platform.moonshot.cn/docs/pricing",
    models=[
        {"id": "moonshot-v1-8k", "name": "Moonshot 8K", "context": 8000, "cost_per_1k_input": 0.0017, "cost_per_1k_output": 0.0017},
        {"id": "moonshot-v1-32k", "name": "Moonshot 32K", "context": 32000, "cost_per_1k_input": 0.0033, "cost_per_1k_output": 0.0033},
        {"id": "moonshot-v1-128k", "name": "Moonshot 128K", "context": 128000, "cost_per_1k_input": 0.0083, "cost_per_1k_output": 0.0083},
    ]
)

YI = LLMProvider(
    id="yi",
    name="零一万物 (Yi)",
    category=ProviderCategory.CHINESE,
    api_base="https://api.lingyiwanwu.com/v1",
    api_key_env="YI_API_KEY",
    supports_vision=True,
    description="零一万物 - 李开复创办，Yi系列大模型",
    website="https://www.lingyiwanwu.com",
    docs_url="https://platform.lingyiwanwu.com/docs",
    pricing_url="https://platform.lingyiwanwu.com/docs/pricing",
    models=[
        {"id": "yi-large", "name": "Yi Large", "context": 32000, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.0028},
        {"id": "yi-large-turbo", "name": "Yi Large Turbo", "context": 16000, "cost_per_1k_input": 0.0017, "cost_per_1k_output": 0.0017},
        {"id": "yi-medium", "name": "Yi Medium", "context": 16000, "cost_per_1k_input": 0.00035, "cost_per_1k_output": 0.00035},
        {"id": "yi-medium-200k", "name": "Yi Medium 200K", "context": 200000, "cost_per_1k_input": 0.0017, "cost_per_1k_output": 0.0017},
        {"id": "yi-spark", "name": "Yi Spark", "context": 16000, "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00014},
        {"id": "yi-vision", "name": "Yi Vision", "context": 4096, "vision": True, "cost_per_1k_input": 0.00084, "cost_per_1k_output": 0.00084},
    ]
)

MINIMAX = LLMProvider(
    id="minimax",
    name="MiniMax",
    category=ProviderCategory.CHINESE,
    api_base="https://api.minimax.chat/v1",
    api_key_env="MINIMAX_API_KEY",
    supports_vision=False,
    description="MiniMax - 国产大模型，擅长多轮对话",
    website="https://www.minimaxi.com",
    docs_url="https://platform.minimaxi.com/document",
    pricing_url="https://platform.minimaxi.com/document/price",
    models=[
        {"id": "abab6.5s-chat", "name": "ABAB 6.5s", "context": 245760, "cost_per_1k_input": 0.0014, "cost_per_1k_output": 0.0014},
        {"id": "abab6.5-chat", "name": "ABAB 6.5", "context": 8192, "cost_per_1k_input": 0.0042, "cost_per_1k_output": 0.0042},
        {"id": "abab5.5s-chat", "name": "ABAB 5.5s", "context": 16000, "cost_per_1k_input": 0.0007, "cost_per_1k_output": 0.0007},
        {"id": "abab5.5-chat", "name": "ABAB 5.5", "context": 16000, "cost_per_1k_input": 0.0021, "cost_per_1k_output": 0.0021},
    ]
)

DOUBAO = LLMProvider(
    id="doubao",
    name="豆包 (Doubao)",
    category=ProviderCategory.CHINESE,
    api_base="https://ark.cn-beijing.volces.com/api/v3",
    api_key_env="DOUBAO_API_KEY",
    supports_vision=True,
    description="字节跳动豆包 - 抖音系大模型",
    website="https://www.volcengine.com/product/doubao",
    docs_url="https://www.volcengine.com/docs/82379",
    pricing_url="https://www.volcengine.com/docs/82379/1099320",
    models=[
        {"id": "doubao-pro-32k", "name": "Doubao Pro 32K", "context": 32000, "cost_per_1k_input": 0.001, "cost_per_1k_output": 0.002},
        {"id": "doubao-pro-128k", "name": "Doubao Pro 128K", "context": 128000, "cost_per_1k_input": 0.0007, "cost_per_1k_output": 0.0013},
        {"id": "doubao-lite-32k", "name": "Doubao Lite 32K", "context": 32000, "cost_per_1k_input": 0.00042, "cost_per_1k_output": 0.00084},
        {"id": "doubao-lite-128k", "name": "Doubao Lite 128K", "context": 128000, "cost_per_1k_input": 0.00011, "cost_per_1k_output": 0.00028},
    ]
)

SPARK = LLMProvider(
    id="spark",
    name="讯飞星火 (Spark)",
    category=ProviderCategory.CHINESE,
    api_base="https://spark-api-open.xf-yun.com/v1",
    api_key_env="SPARK_API_KEY",
    supports_vision=True,
    description="讯飞星火 - 科大讯飞大模型",
    website="https://xinghuo.xfyun.cn",
    docs_url="https://www.xfyun.cn/doc/spark",
    pricing_url="https://xinghuo.xfyun.cn/sparkapi",
    models=[
        {"id": "4.0Ultra", "name": "Spark 4.0 Ultra", "context": 128000, "cost_per_1k_input": 0.014, "cost_per_1k_output": 0.014},
        {"id": "max-32k", "name": "Spark Max 32K", "context": 32000, "cost_per_1k_input": 0.0042, "cost_per_1k_output": 0.0042},
        {"id": "pro-128k", "name": "Spark Pro 128K", "context": 128000, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.0028},
        {"id": "lite", "name": "Spark Lite", "context": 4000, "cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0},
    ]
)

BAICHUAN = LLMProvider(
    id="baichuan",
    name="百川智能 (Baichuan)",
    category=ProviderCategory.CHINESE,
    api_base="https://api.baichuan-ai.com/v1",
    api_key_env="BAICHUAN_API_KEY",
    supports_vision=False,
    description="百川智能 - 搜狗创始人王小川创办",
    website="https://www.baichuan-ai.com",
    docs_url="https://platform.baichuan-ai.com/docs",
    pricing_url="https://platform.baichuan-ai.com/price",
    models=[
        {"id": "Baichuan4", "name": "Baichuan 4", "context": 32000, "cost_per_1k_input": 0.014, "cost_per_1k_output": 0.014},
        {"id": "Baichuan3-Turbo", "name": "Baichuan 3 Turbo", "context": 32000, "cost_per_1k_input": 0.0017, "cost_per_1k_output": 0.0017},
        {"id": "Baichuan3-Turbo-128k", "name": "Baichuan 3 Turbo 128K", "context": 128000, "cost_per_1k_input": 0.0033, "cost_per_1k_output": 0.0033},
        {"id": "Baichuan2-Turbo", "name": "Baichuan 2 Turbo", "context": 32000, "cost_per_1k_input": 0.0011, "cost_per_1k_output": 0.0011},
    ]
)

STEPFUN = LLMProvider(
    id="stepfun",
    name="阶跃星辰 (Step)",
    category=ProviderCategory.CHINESE,
    api_base="https://api.stepfun.com/v1",
    api_key_env="STEPFUN_API_KEY",
    supports_vision=True,
    description="阶跃星辰 - 万亿参数多模态大模型",
    website="https://www.stepfun.com",
    docs_url="https://platform.stepfun.com/docs",
    pricing_url="https://platform.stepfun.com/docs/pricing/pricing",
    models=[
        {"id": "step-2-16k", "name": "Step 2 16K", "context": 16000, "cost_per_1k_input": 0.0056, "cost_per_1k_output": 0.019},
        {"id": "step-1-256k", "name": "Step 1 256K", "context": 256000, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.014},
        {"id": "step-1-128k", "name": "Step 1 128K", "context": 128000, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.014},
        {"id": "step-1-32k", "name": "Step 1 32K", "context": 32000, "cost_per_1k_input": 0.0021, "cost_per_1k_output": 0.0098},
        {"id": "step-1v-8k", "name": "Step 1V 8K", "context": 8000, "vision": True, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.014},
    ]
)

SENSENOVA = LLMProvider(
    id="sensenova",
    name="商汤日日新 (SenseNova)",
    category=ProviderCategory.CHINESE,
    api_base="https://api.sensenova.cn/v1",
    api_key_env="SENSENOVA_API_KEY",
    supports_vision=True,
    description="商汤日日新 - 商汤科技大模型",
    website="https://www.sensetime.com",
    docs_url="https://console.sensecore.cn/help/docs",
    pricing_url="https://console.sensecore.cn/help/docs/pricing",
    models=[
        {"id": "SenseChat-5", "name": "SenseChat 5", "context": 128000, "cost_per_1k_input": 0.014, "cost_per_1k_output": 0.014},
        {"id": "SenseChat-Turbo", "name": "SenseChat Turbo", "context": 32000, "cost_per_1k_input": 0.0028, "cost_per_1k_output": 0.0028},
        {"id": "SenseChat-128K", "name": "SenseChat 128K", "context": 128000, "cost_per_1k_input": 0.0084, "cost_per_1k_output": 0.0084},
        {"id": "SenseChat-Vision", "name": "SenseChat Vision", "context": 4096, "vision": True, "cost_per_1k_input": 0.014, "cost_per_1k_output": 0.014},
    ]
)


# ============================================
# Cloud Providers (云服务)
# ============================================

AZURE = LLMProvider(
    id="azure",
    name="Azure OpenAI",
    category=ProviderCategory.CLOUD,
    api_base="",  # Requires custom endpoint
    api_key_env="AZURE_OPENAI_API_KEY",
    supports_vision=True,
    description="Microsoft Azure OpenAI Service - 企业级OpenAI服务",
    website="https://azure.microsoft.com/products/ai-services/openai-service",
    docs_url="https://learn.microsoft.com/azure/ai-services/openai",
    pricing_url="https://azure.microsoft.com/pricing/details/cognitive-services/openai-service",
    models=[
        {"id": "gpt-4o", "name": "GPT-4o (Azure)", "context": 128000, "vision": True},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Azure)", "context": 128000, "vision": True},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo (Azure)", "context": 128000, "vision": True},
        {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo (Azure)", "context": 16385},
    ]
)

BEDROCK = LLMProvider(
    id="bedrock",
    name="AWS Bedrock",
    category=ProviderCategory.CLOUD,
    api_base="",  # Uses AWS SDK
    api_key_env="AWS_ACCESS_KEY_ID",
    supports_vision=True,
    description="Amazon Bedrock - AWS托管的多模型服务",
    website="https://aws.amazon.com/bedrock",
    docs_url="https://docs.aws.amazon.com/bedrock",
    pricing_url="https://aws.amazon.com/bedrock/pricing",
    models=[
        {"id": "anthropic.claude-3-5-sonnet-20241022-v2:0", "name": "Claude 3.5 Sonnet (Bedrock)", "context": 200000, "vision": True},
        {"id": "anthropic.claude-3-opus-20240229-v1:0", "name": "Claude 3 Opus (Bedrock)", "context": 200000, "vision": True},
        {"id": "meta.llama3-1-70b-instruct-v1:0", "name": "Llama 3.1 70B (Bedrock)", "context": 128000},
        {"id": "mistral.mistral-large-2407-v1:0", "name": "Mistral Large (Bedrock)", "context": 128000},
        {"id": "amazon.titan-text-premier-v1:0", "name": "Titan Text Premier", "context": 32000},
    ]
)


# ============================================
# Local Providers (本地部署)
# ============================================

OLLAMA = LLMProvider(
    id="ollama",
    name="Ollama (本地)",
    category=ProviderCategory.LOCAL,
    api_base="http://localhost:11434/v1",
    api_key_env="",  # No API key needed
    supports_vision=True,
    description="Ollama - 本地运行开源大模型",
    website="https://ollama.ai",
    docs_url="https://github.com/ollama/ollama/blob/main/docs/api.md",
    pricing_url="",  # Free
    models=[
        {"id": "llama3.3:latest", "name": "Llama 3.3 (Local)", "context": 128000, "local": True},
        {"id": "llama3.2:latest", "name": "Llama 3.2 (Local)", "context": 128000, "local": True},
        {"id": "llama3.1:latest", "name": "Llama 3.1 (Local)", "context": 128000, "local": True},
        {"id": "qwen2.5:latest", "name": "Qwen 2.5 (Local)", "context": 32768, "local": True},
        {"id": "deepseek-r1:latest", "name": "DeepSeek R1 (Local)", "context": 65536, "local": True},
        {"id": "deepseek-coder-v2:latest", "name": "DeepSeek Coder V2 (Local)", "context": 128000, "local": True},
        {"id": "mixtral:latest", "name": "Mixtral (Local)", "context": 32768, "local": True},
        {"id": "phi3:latest", "name": "Phi-3 (Local)", "context": 128000, "local": True},
        {"id": "gemma2:latest", "name": "Gemma 2 (Local)", "context": 8192, "local": True},
        {"id": "llava:latest", "name": "LLaVA (Local)", "context": 4096, "vision": True, "local": True},
    ]
)

LM_STUDIO = LLMProvider(
    id="lmstudio",
    name="LM Studio (本地)",
    category=ProviderCategory.LOCAL,
    api_base="http://localhost:1234/v1",
    api_key_env="",
    supports_vision=True,
    description="LM Studio - 本地图形化模型运行工具",
    website="https://lmstudio.ai",
    docs_url="https://lmstudio.ai/docs",
    pricing_url="",
    models=[
        {"id": "local-model", "name": "本地模型 (LM Studio)", "context": 8192, "local": True},
    ]
)

VLLM = LLMProvider(
    id="vllm",
    name="vLLM (本地/服务器)",
    category=ProviderCategory.LOCAL,
    api_base="http://localhost:8000/v1",
    api_key_env="",
    description="vLLM - 高性能LLM推理服务器",
    website="https://vllm.ai",
    docs_url="https://docs.vllm.ai",
    pricing_url="",
    models=[
        {"id": "local-model", "name": "本地模型 (vLLM)", "context": 8192, "local": True},
    ]
)

XINFERENCE = LLMProvider(
    id="xinference",
    name="Xinference (本地)",
    category=ProviderCategory.LOCAL,
    api_base="http://localhost:9997/v1",
    api_key_env="",
    supports_vision=True,
    description="Xinference - 分布式推理框架",
    website="https://inference.readthedocs.io",
    docs_url="https://inference.readthedocs.io/en/latest",
    pricing_url="",
    models=[
        {"id": "local-model", "name": "本地模型 (Xinference)", "context": 8192, "local": True},
    ]
)


# ============================================
# Provider Registry
# ============================================

ALL_PROVIDERS: Dict[str, LLMProvider] = {
    # International
    "openai": OPENAI,
    "anthropic": ANTHROPIC,
    "google": GOOGLE,
    "mistral": MISTRAL,
    "cohere": COHERE,
    "groq": GROQ,
    "together": TOGETHER,
    "perplexity": PERPLEXITY,
    "fireworks": FIREWORKS,
    
    # Chinese
    "deepseek": DEEPSEEK,
    "qwen": QWEN,
    "baidu": BAIDU,
    "zhipu": ZHIPU,
    "moonshot": MOONSHOT,
    "yi": YI,
    "minimax": MINIMAX,
    "doubao": DOUBAO,
    "spark": SPARK,
    "baichuan": BAICHUAN,
    "stepfun": STEPFUN,
    "sensenova": SENSENOVA,
    
    # Cloud
    "azure": AZURE,
    "bedrock": BEDROCK,
    
    # Local
    "ollama": OLLAMA,
    "lmstudio": LM_STUDIO,
    "vllm": VLLM,
    "xinference": XINFERENCE,
}

# Category-based grouping
PROVIDERS_BY_CATEGORY = {
    ProviderCategory.INTERNATIONAL: [
        OPENAI, ANTHROPIC, GOOGLE, MISTRAL, COHERE, GROQ, 
        TOGETHER, PERPLEXITY, FIREWORKS
    ],
    ProviderCategory.CHINESE: [
        DEEPSEEK, QWEN, BAIDU, ZHIPU, MOONSHOT, YI, 
        MINIMAX, DOUBAO, SPARK, BAICHUAN, STEPFUN, SENSENOVA
    ],
    ProviderCategory.CLOUD: [AZURE, BEDROCK],
    ProviderCategory.LOCAL: [OLLAMA, LM_STUDIO, VLLM, XINFERENCE],
}


def get_provider(provider_id: str) -> Optional[LLMProvider]:
    """Get provider by ID"""
    return ALL_PROVIDERS.get(provider_id.lower())


def get_all_providers() -> List[LLMProvider]:
    """Get all providers"""
    return list(ALL_PROVIDERS.values())


def get_providers_by_category(category: ProviderCategory) -> List[LLMProvider]:
    """Get providers by category"""
    return PROVIDERS_BY_CATEGORY.get(category, [])


def detect_provider(model_id: str) -> str:
    """Auto-detect provider based on model ID"""
    model_id_lower = model_id.lower()
    
    # Check each provider's models
    for provider_id, provider in ALL_PROVIDERS.items():
        for model in provider.models:
            if model["id"].lower() == model_id_lower or model_id_lower in model["id"].lower():
                return provider_id
    
    # Fallback to keyword detection
    keyword_mapping = {
        'openai': ['gpt', 'o1', 'o3', 'davinci', 'text-embedding'],
        'anthropic': ['claude'],
        'google': ['gemini', 'palm', 'bard'],
        'mistral': ['mistral', 'mixtral', 'codestral', 'pixtral'],
        'deepseek': ['deepseek'],
        'qwen': ['qwen'],
        'baidu': ['ernie'],
        'zhipu': ['glm', 'codegeex'],
        'moonshot': ['moonshot'],
        'yi': ['yi-'],
        'minimax': ['abab'],
        'doubao': ['doubao'],
        'spark': ['spark'],
        'baichuan': ['baichuan'],
        'stepfun': ['step-'],
        'cohere': ['command'],
        'groq': ['llama', 'mixtral', 'gemma'],
        'ollama': [':latest', 'llama3', 'qwen2'],
    }
    
    for provider, keywords in keyword_mapping.items():
        if any(kw in model_id_lower for kw in keywords):
            return provider
    
    return 'openai'  # Default


def get_api_base(provider_id: str) -> str:
    """Get default API base for provider"""
    provider = get_provider(provider_id)
    return provider.api_base if provider else "https://api.openai.com/v1"


def get_api_key_env(provider_id: str) -> str:
    """Get environment variable name for API key"""
    provider = get_provider(provider_id)
    return provider.api_key_env if provider else "OPENAI_API_KEY"


def get_all_models() -> List[Dict]:
    """Get all models from all providers"""
    all_models = []
    for provider in ALL_PROVIDERS.values():
        for model in provider.models:
            all_models.append({
                **model,
                "provider": provider.id,
                "provider_name": provider.name,
            })
    return all_models


def search_models(query: str) -> List[Dict]:
    """Search models by name or ID"""
    query_lower = query.lower()
    results = []
    for model in get_all_models():
        if query_lower in model["id"].lower() or query_lower in model["name"].lower():
            results.append(model)
    return results

