from pathlib import Path

from src.economics_progress import (
    EconomicsProgress,
    EconomicsRecord,
    append_record,
    load_economics_progress,
    prune_history,
    recent_topics,
    save_economics_progress,
)


def test_load_missing_progress_initializes_state(tmp_path: Path) -> None:
    state = load_economics_progress(tmp_path / "missing.json")

    assert state.current_day == 1
    assert state.last_topic == ""
    assert state.history == []


def test_save_and_load_progress_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "economics_progress.json"
    state = EconomicsProgress(
        current_day=2,
        last_topic="机会成本",
        history=[
            EconomicsRecord(
                date="2026-06-24",
                day=1,
                topic="机会成本",
                module="基础概念",
                level="beginner",
                style="concept",
            )
        ],
    )

    save_economics_progress(path, state)
    loaded = load_economics_progress(path)

    assert loaded.current_day == 2
    assert loaded.last_topic == "机会成本"
    assert loaded.history[0].topic == "机会成本"


def test_append_record_advances_day_and_deduplicates_topic() -> None:
    state = EconomicsProgress(current_day=1, history=[])
    record = EconomicsRecord(
        date="2026-06-24",
        day=1,
        topic="机会成本",
        module="基础概念",
        level="beginner",
        style="concept",
    )

    append_record(state, record)
    append_record(state, record)

    assert state.current_day == 2
    assert state.last_topic == "机会成本"
    assert len(state.history) == 1


def test_recent_topics_limit() -> None:
    state = EconomicsProgress(
        current_day=4,
        history=[
            EconomicsRecord("2026-06-21", 1, "主题1", "基础概念", "beginner", "concept"),
            EconomicsRecord("2026-06-22", 2, "主题2", "基础概念", "beginner", "concept"),
            EconomicsRecord("2026-06-23", 3, "主题3", "基础概念", "beginner", "concept"),
        ],
    )

    assert recent_topics(state, 2) == ["主题2", "主题3"]


def test_prune_history_keeps_recent_records() -> None:
    state = EconomicsProgress(
        current_day=3,
        history=[
            EconomicsRecord("2020-01-01", 1, "旧主题", "基础概念", "beginner", "concept"),
            EconomicsRecord("2099-01-01", 2, "新主题", "基础概念", "beginner", "concept"),
        ],
    )

    pruned = prune_history(state, keep_days=90)

    assert [item.topic for item in pruned.history] == ["新主题"]
