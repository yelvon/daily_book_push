"""LiteLLM / Cursor 摘要生成。"""

from __future__ import annotations

import logging
from typing import Optional

from src.config import AppConfig, BookConfig
from src.llm_client import call_with_auto_provider

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
    if not config.cursor_api_key and not config.gemini_api_key:
        logger.warning("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY，跳过 AI 摘要")
        return None
    if not segment.strip():
        return None

    user_prompt = (
        f"书名：《{book.title}》\n"
        f"作者：{book.author or '未知'}\n\n"
        f"今日阅读片段：\n{segment}"
    )

    return call_with_auto_provider(
        config=config,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1024,
        use_google_search=False,
    )
