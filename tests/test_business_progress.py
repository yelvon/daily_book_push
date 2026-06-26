from pathlib import Path

from src.business_progress import (
    BusinessProgress,
    BusinessRecord,
    append_record,
    load_business_progress,
    recent_cases,
    save_business_progress,
)


def test_load_missing_progress_initializes_state(tmp_path: Path) -> None:
    state = load_business_progress(tmp_path / "missing.json")

    assert state.current_day == 1
    assert state.last_case == ""
    assert state.history == []


def test_append_record_advances_day_and_deduplicates_case() -> None:
    state = BusinessProgress(current_day=1, history=[])
    record = BusinessRecord(
        date="2026-06-24",
        day=1,
        case="Costco 低毛利会员制",
        company="Costco",
        module="商业模式基础",
        level="beginner",
        style="case",
    )

    append_record(state, record)
    append_record(state, record)

    assert state.current_day == 2
    assert state.last_case == "Costco 低毛利会员制"
    assert len(state.history) == 1


def test_recent_cases_limit() -> None:
    state = BusinessProgress(
        current_day=4,
        history=[
            BusinessRecord("2026-06-21", 1, "案例1", "公司1", "商业模式基础", "beginner", "case"),
            BusinessRecord("2026-06-22", 2, "案例2", "公司2", "商业模式基础", "beginner", "case"),
            BusinessRecord("2026-06-23", 3, "案例3", "公司3", "商业模式基础", "beginner", "case"),
        ],
    )

    assert recent_cases(state, 2) == ["案例2 / 公司2", "案例3 / 公司3"]


def test_save_and_load_progress_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "business_progress.json"
    state = BusinessProgress(
        current_day=2,
        last_case="Costco 低毛利会员制",
        history=[
            BusinessRecord(
                "2026-06-24",
                1,
                "Costco 低毛利会员制",
                "Costco",
                "商业模式基础",
                "beginner",
                "case",
            )
        ],
    )

    save_business_progress(path, state)
    loaded = load_business_progress(path)

    assert loaded.current_day == 2
    assert loaded.last_case == "Costco 低毛利会员制"
    assert loaded.history[0].company == "Costco"
