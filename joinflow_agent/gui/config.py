"""
GUI Agent 统一配置
==================

集中管理 API Key 和模型配置
"""

# OpenRouter API Key（统一配置）
# 之后替换时只需修改这里
OPENROUTER_API_KEY = "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"

# 默认模型配置
DEFAULT_MODEL = "openrouter/google/gemini-2.0-flash-exp:free"  # 视觉模型（免费）
DEFAULT_TEXT_MODEL = "openrouter/mistralai/mistral-7b-instruct:free"  # 文本模型（免费）

# 备选模型（付费，更稳定）
BACKUP_MODEL = "openrouter/openai/gpt-4o-mini"

# API 配置
DEFAULT_API_KEY = OPENROUTER_API_KEY
DEFAULT_BASE_URL = None  # OpenRouter 不需要设置 base_url，litellm 会自动处理


def get_api_key() -> str:
    """获取 API Key"""
    import os
    # 优先使用环境变量，否则使用默认值
    return os.environ.get("OPENROUTER_API_KEY", OPENROUTER_API_KEY)


def get_model_config() -> dict:
    """获取模型配置"""
    return {
        "model": DEFAULT_MODEL,
        "api_key": get_api_key(),
        "base_url": DEFAULT_BASE_URL,
    }

