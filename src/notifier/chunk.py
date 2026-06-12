"""长消息按字节分批（精简自 daily_stock_analysis formatters）。"""

from __future__ import annotations

import re
from typing import List

MIN_MAX_BYTES = 40
TRUNCATION_SUFFIX = "\n\n...(本段内容过长已截断)"
PAGE_MARKER_PREFIX = "\n\n📄"
PAGE_MARKER_SAFE_BYTES = 16

BREAK_PATTERN = re.compile(r"(\n---\n|\n### |\n## |\n\n)")


def _bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def _page_marker(index: int, total: int) -> str:
    return f"{PAGE_MARKER_PREFIX} {index + 1}/{total}"


def slice_at_max_bytes(text: str, max_bytes: int) -> tuple[str, str]:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text, ""
    chunk = encoded[:max_bytes]
    while chunk:
        try:
            return chunk.decode("utf-8"), encoded[len(chunk) :].decode("utf-8")
        except UnicodeDecodeError:
            chunk = chunk[:-1]
    return "", text


def _chunk_by_max_bytes(content: str, max_bytes: int) -> List[str]:
    if _bytes(content) <= max_bytes:
        return [content]
    sections: List[str] = []
    suffix = TRUNCATION_SUFFIX
    effective = max_bytes - _bytes(suffix)
    if effective <= 0:
        effective = max_bytes
        suffix = ""
    remaining = content
    while remaining:
        chunk, remaining = slice_at_max_bytes(remaining, effective)
        if remaining.strip():
            sections.append(chunk + suffix)
        else:
            sections.append(chunk)
            break
    return sections


def _chunk_by_separators(content: str) -> tuple[List[str], str]:
    for separator in ("\n---\n", "\n### ", "\n## ", "\n\n"):
        if separator in content:
            return content.split(separator), separator
    return [content], ""


def chunk_content_by_max_bytes(content: str, max_bytes: int, add_page_marker: bool = False) -> List[str]:
    if add_page_marker:
        max_bytes = max_bytes - PAGE_MARKER_SAFE_BYTES

    def _chunk(text: str, limit: int) -> List[str]:
        if limit < MIN_MAX_BYTES:
            raise ValueError(f"max_bytes={limit} 过小，无法安全分片")
        if _bytes(text) <= limit:
            return [text]

        sections, separator = _chunk_by_separators(text)
        if separator == "" and len(sections) == 1:
            return _chunk_by_max_bytes(text, limit)

        chunks: List[str] = []
        current: List[str] = []
        current_bytes = 0
        separator_bytes = _bytes(separator) if separator else 0
        effective = limit - separator_bytes

        for section in sections:
            section_with_sep = section + separator
            section_bytes = _bytes(section_with_sep)
            if section_bytes > effective:
                if current:
                    chunks.append("".join(current))
                    current = []
                    current_bytes = 0
                section_chunks = _chunk(section, effective)
                if section_chunks:
                    section_chunks[-1] = section_chunks[-1] + separator
                chunks.extend(section_chunks)
                continue

            if current_bytes + section_bytes > effective:
                if current:
                    chunks.append("".join(current))
                current = [section_with_sep]
                current_bytes = section_bytes
            else:
                current.append(section_with_sep)
                current_bytes += section_bytes

        if current:
            joined = "".join(current)
            if separator and joined.endswith(separator):
                joined = joined[: -len(separator)]
            chunks.append(joined)
        return chunks

    chunks = _chunk(content, max_bytes)
    if add_page_marker:
        total = len(chunks)
        chunks = [chunk + _page_marker(i, total) for i, chunk in enumerate(chunks)]
    return chunks
