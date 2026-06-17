"""LLM 调用封装：Cursor 优先，Gemini 备用。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import AppConfig
from src.cursor_client import completion as cursor_completion

logger = logging.getLogger(__name__)


def available_providers(config: AppConfig) -> List[str]:
    providers: List[str] = []
    if config.cursor_api_key:
        providers.append("cursor")
    if config.gemini_api_key:
        providers.append("gemini")
    return providers


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _gemini_completion(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    use_google_search: bool = False,
) -> str:
    kwargs: Dict[str, Any] = {
        "model": model,
        "api_key": api_key,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if use_google_search and _supports_google_search(model):
        kwargs["tools"] = [{"googleSearch": {}}]

    response = litellm.completion(**kwargs)
    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM 返回空内容")
    return content.strip()


def _supports_google_search(model: str) -> bool:
    return "gemini" in model.lower()


def _call_gemini_with_fallback(
    *,
    config: AppConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    use_google_search: bool,
) -> str:
    models = [config.gemini_model]
    if config.gemini_model_fallback:
        models.append(config.gemini_model_fallback)

    last_error: Optional[Exception] = None
    for model in models:
        try:
            search = use_google_search and _supports_google_search(model)
            return _gemini_completion(
                api_key=config.gemini_api_key or "",
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                use_google_search=search,
            )
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini 模型 %s 调用失败: %s", model, exc)
    if last_error:
        raise last_error
    raise ValueError("未配置可用的 Gemini 模型")


def call_with_auto_provider(
    *,
    config: AppConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    use_google_search: bool = False,
) -> Optional[str]:
    providers = available_providers(config)
    if not providers:
        logger.error("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY")
        return None

    for provider in providers:
        try:
            if provider == "cursor":
                return cursor_completion(
                    api_key=config.cursor_api_key or "",
                    model=config.cursor_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    cwd=config.root_dir,
                )
            return _call_gemini_with_fallback(
                config=config,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                use_google_search=use_google_search,
            )
        except Exception as exc:
            logger.warning("%s 调用失败，尝试下一个 provider: %s", provider, exc)

    return None
