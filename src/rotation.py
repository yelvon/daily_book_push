"""轮播选书逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.config import BookConfig
from src.progress import ProgressState


@dataclass
class RotationPick:
    book: BookConfig
    index: int
    active_books: List[BookConfig]


def get_active_books(books: List[BookConfig], state: ProgressState) -> List[BookConfig]:
    active: List[BookConfig] = []
    for book in books:
        if not book.enabled:
            continue
        prog = state.books.get(book.id)
        if prog and prog.finished:
            continue
        active.append(book)
    return active


def pick_book(
    books: List[BookConfig],
    state: ProgressState,
    force_book_id: Optional[str] = None,
) -> Optional[RotationPick]:
    active = get_active_books(books, state)
    if not active:
        return None

    if force_book_id:
        for idx, book in enumerate(active):
            if book.id == force_book_id:
                return RotationPick(book=book, index=idx, active_books=active)
        raise ValueError(f"书籍 {force_book_id} 不可用（未启用或已读完）")

    idx = state.rotation_index % len(active)

    return RotationPick(book=active[idx], index=idx, active_books=active)


def next_rotation_index(current_index: int, active_count: int) -> int:
    if active_count <= 0:
        return 0
    return (current_index + 1) % active_count


def peek_next_book_title(active_books: List[BookConfig], next_index: int) -> str:
    if not active_books:
        return "无"
    return active_books[next_index % len(active_books)].title
