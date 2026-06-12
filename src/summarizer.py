"""LiteLLM 摘要生成。"""

from __future__ import annotations

import logging
from typing import Optional

import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import AppConfig, BookConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位阅读助手。根据用户提供的书籍片段，输出简洁中文 Markdown，严格包含以下三节：

【今日摘要】
用 2-3 句话概括本节内容。

【精华要点】
- 列出 3-5 条要点

【金句】
- 引用或改写 1-2 句原文精华

要求：客观忠实原文，不编造情节；语言简练。"""


def summarize_segment(config: AppConfig, book: BookConfig, segment: str) -> Optional[str]:
    if not config.ai_enabled:
        return None
    if not config.gemini_api_key:
        logger.warning("未配置 GEMINI_API_KEY，跳过 AI 摘要")
        return None
    if not segment.strip():
        return None

    user_prompt = (
        f"书名：《{book.title}》\n"
        f"作者：{book.author or '未知'}\n\n"
        f"今日阅读片段：\n{segment}"
    )

    models = [config.gemini_model]
    if config.gemini_model_fallback:
        models.append(config.gemini_model_fallback)

    for model in models:
        try:
            result = _call_litellm(config.gemini_api_key, model, user_prompt)
            if result:
                return result.strip()
        except Exception as exc:
            logger.warning("模型 %s 摘要失败: %s", model, exc)

    return None


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _call_litellm(api_key: str, model: str, user_prompt: str) -> str:
    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM 返回空内容")
    return content
