"""每日市场事件雷达状态。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List


@dataclass
class MarketEventRecord:
    date: str
    event: str
    region: str
    event_date: str
    status: str
    risk_level: str

    @classmethod
    def from_dict(cls, data: dict) -> "MarketEventRecord":
        return cls(
            date=str(data.get("date", "")),
            event=str(data.get("event", "")),
            region=str(data.get("region", "")),
            event_date=str(data.get("event_date", "")),
            status=str(data.get("status", "")),
            risk_level=str(data.get("risk_level", "")),
        )

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "event": self.event,
            "region": self.region,
            "event_date": self.event_date,
            "status": self.status,
            "risk_level": self.risk_level,
        }

    def key(self) -> str:
        return f"{self.event.strip()}|{self.region.strip()}|{self.event_date.strip()}|{self.status.strip()}".lower()


@dataclass
class MarketEventsState:
    last_run_date: str = ""
    history: List[MarketEventRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "MarketEventsState":
        items = [MarketEventRecord.from_dict(item) for item in data.get("history") or []]
        return cls(last_run_date=str(data.get("last_run_date", "")), history=items)

    def to_dict(self) -> dict:
        return {
            "last_run_date": self.last_run_date,
            "history": [item.to_dict() for item in self.history],
        }


def load_market_events(path: Path) -> MarketEventsState:
    if not path.exists():
        return MarketEventsState()
    with path.open("r", encoding="utf-8") as f:
        return MarketEventsState.from_dict(json.load(f))


def save_market_events(path: Path, state: MarketEventsState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_event(state: MarketEventsState, record: MarketEventRecord) -> None:
    state.last_run_date = record.date
    for item in state.history:
        if item.key() == record.key():
            return
    state.history.append(record)


def recent_events(state: MarketEventsState, limit: int) -> List[str]:
    items = state.history[-limit:] if limit > 0 else list(state.history)
    return [f"{item.event} / {item.region} / {item.event_date} / {item.status}" for item in items]


def prune_history(state: MarketEventsState, keep_days: int) -> MarketEventsState:
    if keep_days <= 0:
        return state
    cutoff = date.today() - timedelta(days=keep_days)
    kept: List[MarketEventRecord] = []
    for item in state.history:
        try:
            item_date = date.fromisoformat(item.date)
        except ValueError:
            continue
        if item_date >= cutoff:
            kept.append(item)
    return MarketEventsState(last_run_date=state.last_run_date, history=kept)
