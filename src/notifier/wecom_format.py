"""企业微信消息格式转换。"""

from __future__ import annotations

import re


def strip_markdown(text: str) -> str:
    """去除 Markdown 语法，用于个人微信兼容的 text 消息。"""
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 \2", text)

    protected_urls: list[str] = []

    def _protect_url(match: re.Match[str]) -> str:
        protected_urls.append(match.group(0))
        return f"@@URLTOKEN{len(protected_urls) - 1}@@"

    text = re.sub(r"https?://[^\s<>\]]+", _protect_url, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)__(?!\s)(.+?)(?<!\s)__(?!\w)", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", text)
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    text = re.sub(r"!\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"<font[^>]*>(.+?)</font>", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    for idx, url in enumerate(protected_urls):
        text = text.replace(f"@@URLTOKEN{idx}@@", url)
    return text.strip()


def adapt_markdown_for_wework(text: str) -> str:
    """将通用 Markdown 适配为企业微信 markdown（v1）支持的子集。"""
    text = re.sub(r"<font[^>]*>(.+?)</font>", r"\1", text)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*]{3,}\s*$", "\n\n", text, flags=re.MULTILINE)
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()
