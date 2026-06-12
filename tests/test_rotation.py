from src.config import BookConfig
from src.progress import BookProgress, ProgressState
from src.rotation import get_active_books, next_rotation_index, pick_book, peek_next_book_title


def _books():
    return [
        BookConfig(id="a", file="a.txt", title="A", enabled=True, daily_chars=100),
        BookConfig(id="b", file="b.txt", title="B", enabled=True, daily_chars=100),
        BookConfig(id="c", file="c.txt", title="C", enabled=False, daily_chars=100),
    ]


def test_get_active_books_skips_disabled_and_finished():
    state = ProgressState(
        books={"a": BookProgress(finished=True), "b": BookProgress(finished=False)}
    )
    active = get_active_books(_books(), state)
    assert [b.id for b in active] == ["b"]


def test_pick_book_round_robin():
    state = ProgressState(rotation_index=1)
    pick = pick_book(_books(), state)
    assert pick is not None
    assert pick.book.id == "b"
    assert pick.index == 1


def test_pick_book_force_id():
    state = ProgressState()
    pick = pick_book(_books(), state, force_book_id="b")
    assert pick is not None
    assert pick.book.id == "b"


def test_next_rotation_index_wraps():
    assert next_rotation_index(1, 2) == 0
    assert next_rotation_index(0, 2) == 1


def test_peek_next_book_title():
    active = get_active_books(_books(), ProgressState())
    title = peek_next_book_title(active, next_rotation_index(0, len(active)))
    assert title == "B"
