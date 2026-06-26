"""每日商业案例学习进度。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List


@dataclass
class BusinessRecord:
    date: str
    day: int
    case: str
    company: str
    module: str
    level: str
    style: str

    @classmethod
    def from_dict(cls, data: dict) -> "BusinessRecord":
        return cls(
            date=str(data.get("date", "")),
            day=int(data.get("day", 0)),
            case=str(data.get("case", "")),
            company=str(data.get("company", "")),
            module=str(data.get("module", "")),
            level=str(data.get("level", "")),
            style=str(data.get("style", "")),
        )

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "day": self.day,
            "case": self.case,
            "company": self.company,
            "module": self.module,
            "level": self.level,
            "style": self.style,
        }

    def key(self) -> str:
        return f"{self.case.strip()}|{self.company.strip()}".lower()


@dataclass
class BusinessProgress:
    current_day: int = 1
    last_case: str = ""
    history: List[BusinessRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "BusinessProgress":
        items = [BusinessRecord.from_dict(item) for item in data.get("history") or []]
        return cls(
            current_day=int(data.get("current_day", 1)),
            last_case=str(data.get("last_case", "")),
            history=items,
        )

    def to_dict(self) -> dict:
        return {
            "current_day": self.current_day,
            "last_case": self.last_case,
            "history": [item.to_dict() for item in self.history],
        }


def load_business_progress(path: Path) -> BusinessProgress:
    if not path.exists():
        return BusinessProgress()
    with path.open("r", encoding="utf-8") as f:
        return BusinessProgress.from_dict(json.load(f))


def save_business_progress(path: Path, state: BusinessProgress) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_record(state: BusinessProgress, record: BusinessRecord) -> None:
    for item in state.history:
        if item.key() == record.key():
            state.last_case = item.case
            return
    state.history.append(record)
    state.last_case = record.case
    state.current_day = max(state.current_day, record.day + 1)


def recent_cases(state: BusinessProgress, limit: int) -> List[str]:
    items = state.history[-limit:] if limit > 0 else list(state.history)
    return [f"{item.case} / {item.company}" for item in items]


def prune_history(state: BusinessProgress, keep_days: int) -> BusinessProgress:
    if keep_days <= 0:
        return state
    cutoff = date.today() - timedelta(days=keep_days)
    kept: List[BusinessRecord] = []
    for item in state.history:
        try:
            item_date = date.fromisoformat(item.date)
        except ValueError:
            continue
        if item_date >= cutoff:
            kept.append(item)
    return BusinessProgress(
        current_day=state.current_day,
        last_case=state.last_case,
        history=kept,
    )
