"""荐书历史记录，用于去重。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional


@dataclass
class RecommendRecord:
    date: str
    title: str
    author: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "RecommendRecord":
        return cls(
            date=str(data.get("date", "")),
            title=str(data.get("title", "")),
            author=str(data.get("author", "")),
        )

    def to_dict(self) -> dict:
        return {"date": self.date, "title": self.title, "author": self.author}

    def key(self) -> str:
        return f"{self.title.strip()}|{self.author.strip()}".lower()


@dataclass
class RecommendHistory:
    history: List[RecommendRecord]

    @classmethod
    def from_dict(cls, data: dict) -> "RecommendHistory":
        items = [RecommendRecord.from_dict(item) for item in data.get("history") or []]
        return cls(history=items)

    def to_dict(self) -> dict:
        return {"history": [item.to_dict() for item in self.history]}


def load_recommend_history(path: Path) -> RecommendHistory:
    if not path.exists():
        return RecommendHistory(history=[])
    with path.open("r", encoding="utf-8") as f:
        return RecommendHistory.from_dict(json.load(f))


def save_recommend_history(path: Path, state: RecommendHistory) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        f.write("\n")


def prune_history(state: RecommendHistory, keep_days: int) -> RecommendHistory:
    if keep_days <= 0:
        return state
    cutoff = date.today() - timedelta(days=keep_days)
    kept: List[RecommendRecord] = []
    for item in state.history:
        try:
            item_date = date.fromisoformat(item.date)
        except ValueError:
            continue
        if item_date >= cutoff:
            kept.append(item)
    return RecommendHistory(history=kept)


def recent_titles(state: RecommendHistory, limit: int) -> List[RecommendRecord]:
    return state.history[-limit:] if limit > 0 else list(state.history)


def append_record(state: RecommendHistory, record: RecommendRecord) -> None:
    for item in state.history:
        if item.key() == record.key():
            return
    state.history.append(record)
