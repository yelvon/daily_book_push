"""按字数切分书籍正文。"""

from __future__ import annotations

import re
from dataclasses import dataclass

BREAK_PATTERN = re.compile(r"(\n\n|[。！？!?]\s*|\n)")


@dataclass
class SplitResult:
    segment: str
    new_offset: int
    progress_pct: float
    is_finished: bool


def split_text(text: str, offset: int, daily_chars: int) -> SplitResult:
    total = len(text)
    if offset >= total:
        return SplitResult(segment="", new_offset=total, progress_pct=100.0, is_finished=True)

    target_end = min(offset + daily_chars, total)
    if target_end >= total:
        segment = text[offset:total]
        return SplitResult(
            segment=segment,
            new_offset=total,
            progress_pct=100.0,
            is_finished=True,
        )

    search_start = target_end
    search_end = min(target_end + 200, total)
    window = text[search_start:search_end]

    break_at = _find_break(window)
    if break_at >= 0:
        end = search_start + break_at + 1
    else:
        end = target_end

    end = max(end, offset + 1)
    end = min(end, total)
    segment = text[offset:end].strip()
    if not segment:
        segment = text[offset:target_end]
        end = target_end

    new_offset = end
    progress_pct = round(new_offset / total * 100, 1) if total else 100.0
    is_finished = new_offset >= total
    return SplitResult(
        segment=segment,
        new_offset=new_offset,
        progress_pct=progress_pct,
        is_finished=is_finished,
    )


def _find_break(window: str) -> int:
    best = -1
    for match in BREAK_PATTERN.finditer(window):
        best = match.end()
    return best
