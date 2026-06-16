"""LiteLLM 调用封装。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def completion(
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
    name = model.lower()
    return "gemini" in name


def call_with_fallback(
    *,
    api_key: str,
    models: List[str],
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    use_google_search: bool = False,
) -> Optional[str]:
    for model in models:
        try:
            search = use_google_search and _supports_google_search(model)
            return completion(
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                use_google_search=search,
            )
        except Exception as exc:
            logger.warning("模型 %s 调用失败: %s", model, exc)
    return None
