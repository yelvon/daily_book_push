"""阅读进度读写。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class BookProgress:
    offset: int = 0
    total_chars: int = 0
    finished: bool = False
    last_push_date: Optional[str] = None
    day_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BookProgress":
        return cls(
            offset=int(data.get("offset", 0)),
            total_chars=int(data.get("total_chars", 0)),
            finished=bool(data.get("finished", False)),
            last_push_date=data.get("last_push_date"),
            day_count=int(data.get("day_count", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offset": self.offset,
            "total_chars": self.total_chars,
            "finished": self.finished,
            "last_push_date": self.last_push_date,
            "day_count": self.day_count,
        }


@dataclass
class ProgressState:
    rotation_index: int = 0
    last_book_id: Optional[str] = None
    books: Dict[str, BookProgress] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.books is None:
            self.books = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressState":
        books_raw = data.get("books") or {}
        books = {book_id: BookProgress.from_dict(item) for book_id, item in books_raw.items()}
        return cls(
            rotation_index=int(data.get("rotation_index", 0)),
            last_book_id=data.get("last_book_id"),
            books=books,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rotation_index": self.rotation_index,
            "last_book_id": self.last_book_id,
            "books": {book_id: prog.to_dict() for book_id, prog in self.books.items()},
        }


def load_progress(path: Path) -> ProgressState:
    if not path.exists():
        return ProgressState()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return ProgressState.from_dict(data)


def save_progress(path: Path, state: ProgressState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_or_init_book_progress(state: ProgressState, book_id: str, total_chars: int) -> BookProgress:
    if book_id not in state.books:
        state.books[book_id] = BookProgress(total_chars=total_chars)
    prog = state.books[book_id]
    if prog.total_chars <= 0:
        prog.total_chars = total_chars
    return prog


def reset_book_progress(state: ProgressState, book_id: str) -> None:
    state.books[book_id] = BookProgress()


def record_push(
    state: ProgressState,
    book_id: str,
    new_offset: int,
    is_finished: bool,
    rotation_index: int,
) -> None:
    prog = state.books[book_id]
    prog.offset = new_offset
    prog.finished = is_finished
    prog.last_push_date = date.today().isoformat()
    prog.day_count += 1
    state.last_book_id = book_id
    state.rotation_index = rotation_index
