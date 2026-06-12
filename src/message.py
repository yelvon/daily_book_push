"""推送消息组装。"""

from __future__ import annotations

from typing import Optional

from src.config import BookConfig


def build_message(
    book: BookConfig,
    day_count: int,
    progress_pct: float,
    segment: str,
    ai_summary: Optional[str],
    next_book_title: str,
    is_finished: bool,
) -> str:
    title = f"## 《{book.title}》"
    if book.author:
        title += f" · {book.author}"
    title += f" · Day {day_count + 1} · 进度 {progress_pct}%"

    if is_finished:
        title += " · 本章已读完"

    lines = [title, "", "### 今日正文", segment.strip(), ""]

    lines.extend(["### AI 摘要", ""])
    if ai_summary:
        lines.append(ai_summary.strip())
    else:
        lines.append("_（AI 摘要生成失败或未启用，仅推送正文）_")

    lines.extend(["", "---", f"下次轮播：**{next_book_title}**"])
    return "\n".join(lines)


def build_all_finished_message() -> str:
    return "## 每日读书\n\n所有已启用书籍均已读完。可在 `config/books.yaml` 添加新书或重置进度。"
