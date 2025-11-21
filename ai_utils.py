from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_DOU_BAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/bots"
DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class AIConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def resolve_ai_config(
    provider: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    api_key: Optional[str],
    default_model: Optional[str],
) -> AIConfig:
    env_provider = os.environ.get("AI_PROVIDER")
    resolved_provider = (provider or env_provider or "doubao").lower()

    if resolved_provider == "doubao":
        key = api_key or os.environ.get("ARK_API_KEY")
        if not key:
            raise SystemExit("Missing ARK_API_KEY for Doubao provider.")
        mdl = model or os.environ.get("ARK_BOT_MODEL") or default_model
        if not mdl:
            raise SystemExit("Missing Doubao model id (set --ai-model or ARK_BOT_MODEL).")
        url = base_url or os.environ.get("ARK_BASE_URL") or DEFAULT_DOU_BAO_BASE_URL
    elif resolved_provider in {"qwen", "dashscope"}:
        key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not key:
            raise SystemExit("Missing DASHSCOPE_API_KEY for Qwen provider.")
        mdl = model or os.environ.get("DASHSCOPE_MODEL") or default_model or "qwen3-max"
        url = base_url or os.environ.get("DASHSCOPE_BASE_URL") or DEFAULT_QWEN_BASE_URL
    else:
        key = api_key or os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise SystemExit(
                f"Missing API key for provider '{resolved_provider}'. Set --ai-api-key or AI_API_KEY/OPENAI_API_KEY."
            )
        mdl = model or os.environ.get("AI_MODEL") or os.environ.get("OPENAI_MODEL") or default_model
        if not mdl:
            raise SystemExit(
                f"Missing model id for provider '{resolved_provider}'. Set --ai-model or AI_MODEL/OPENAI_MODEL."
            )
        url = base_url or os.environ.get("AI_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        if not url:
            raise SystemExit(
                f"Missing base URL for provider '{resolved_provider}'. Set --ai-base-url or AI_BASE_URL/OPENAI_BASE_URL."
            )

    return AIConfig(provider=resolved_provider, base_url=url, api_key=key, model=mdl)


def create_openai_client(config: AIConfig):
    from openai import OpenAI

    return OpenAI(base_url=config.base_url, api_key=config.api_key)
