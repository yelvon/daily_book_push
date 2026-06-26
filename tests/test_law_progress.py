from pathlib import Path

from src.law_progress import (
    LawProgress,
    LawRecord,
    append_record,
    load_law_progress,
    prune_history,
    recent_topics,
    save_law_progress,
)


def test_load_missing_progress_initializes_state(tmp_path: Path) -> None:
    state = load_law_progress(tmp_path / "missing.json")

    assert state.current_day == 1
    assert state.last_topic == ""
    assert state.history == []


def test_append_record_advances_day_and_deduplicates_topic() -> None:
    state = LawProgress(current_day=1, history=[])
    record = LawRecord(
        date="2026-06-24",
        day=1,
        topic="竞业限制",
        module="劳动合同与用工合规",
        level="beginner",
        style="concept",
    )

    append_record(state, record)
    append_record(state, record)

    assert state.current_day == 2
    assert state.last_topic == "竞业限制"
    assert len(state.history) == 1


def test_recent_topics_limit() -> None:
    state = LawProgress(
        current_day=4,
        history=[
            LawRecord("2026-06-21", 1, "主题1", "创业法律常识", "beginner", "concept"),
            LawRecord("2026-06-22", 2, "主题2", "创业法律常识", "beginner", "concept"),
            LawRecord("2026-06-23", 3, "主题3", "创业法律常识", "beginner", "concept"),
        ],
    )

    assert recent_topics(state, 2) == ["主题2", "主题3"]


def test_save_and_load_progress_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "law_progress.json"
    state = LawProgress(
        current_day=2,
        last_topic="竞业限制",
        history=[
            LawRecord(
                "2026-06-24",
                1,
                "竞业限制",
                "劳动合同与用工合规",
                "beginner",
                "concept",
            )
        ],
    )

    save_law_progress(path, state)
    loaded = load_law_progress(path)

    assert loaded.current_day == 2
    assert loaded.last_topic == "竞业限制"
    assert loaded.history[0].topic == "竞业限制"
