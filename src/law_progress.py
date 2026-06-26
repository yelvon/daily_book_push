"""每日法学学习进度。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List


@dataclass
class LawRecord:
    date: str
    day: int
    topic: str
    module: str
    level: str
    style: str

    @classmethod
    def from_dict(cls, data: dict) -> "LawRecord":
        return cls(
            date=str(data.get("date", "")),
            day=int(data.get("day", 0)),
            topic=str(data.get("topic", "")),
            module=str(data.get("module", "")),
            level=str(data.get("level", "")),
            style=str(data.get("style", "")),
        )

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "day": self.day,
            "topic": self.topic,
            "module": self.module,
            "level": self.level,
            "style": self.style,
        }

    def key(self) -> str:
        return self.topic.strip().lower()


@dataclass
class LawProgress:
    current_day: int = 1
    last_topic: str = ""
    history: List[LawRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "LawProgress":
        items = [LawRecord.from_dict(item) for item in data.get("history") or []]
        return cls(
            current_day=int(data.get("current_day", 1)),
            last_topic=str(data.get("last_topic", "")),
            history=items,
        )

    def to_dict(self) -> dict:
        return {
            "current_day": self.current_day,
            "last_topic": self.last_topic,
            "history": [item.to_dict() for item in self.history],
        }


def load_law_progress(path: Path) -> LawProgress:
    if not path.exists():
        return LawProgress()
    with path.open("r", encoding="utf-8") as f:
        return LawProgress.from_dict(json.load(f))


def save_law_progress(path: Path, state: LawProgress) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_record(state: LawProgress, record: LawRecord) -> None:
    for item in state.history:
        if item.key() == record.key():
            state.last_topic = item.topic
            return
    state.history.append(record)
    state.last_topic = record.topic
    state.current_day = max(state.current_day, record.day + 1)


def recent_topics(state: LawProgress, limit: int) -> List[str]:
    items = state.history[-limit:] if limit > 0 else list(state.history)
    return [item.topic for item in items]


def prune_history(state: LawProgress, keep_days: int) -> LawProgress:
    if keep_days <= 0:
        return state
    cutoff = date.today() - timedelta(days=keep_days)
    kept: List[LawRecord] = []
    for item in state.history:
        try:
            item_date = date.fromisoformat(item.date)
        except ValueError:
            continue
        if item_date >= cutoff:
            kept.append(item)
    return LawProgress(
        current_day=state.current_day,
        last_topic=state.last_topic,
        history=kept,
    )
