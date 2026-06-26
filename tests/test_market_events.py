from pathlib import Path

from src.market_events import (
    MarketEventRecord,
    MarketEventsState,
    append_event,
    load_market_events,
    prune_history,
    recent_events,
    save_market_events,
)


def test_load_missing_market_events_initializes_state(tmp_path: Path) -> None:
    state = load_market_events(tmp_path / "missing.json")

    assert state.last_run_date == ""
    assert state.history == []


def test_append_event_deduplicates_same_event() -> None:
    state = MarketEventsState(history=[])
    record = MarketEventRecord(
        date="2026-06-26",
        event="美国非农就业数据",
        region="美国",
        event_date="2026-07-03",
        status="confirmed",
        risk_level="high",
    )

    append_event(state, record)
    append_event(state, record)

    assert state.last_run_date == "2026-06-26"
    assert len(state.history) == 1


def test_recent_events_limit() -> None:
    state = MarketEventsState(
        last_run_date="2026-06-26",
        history=[
            MarketEventRecord("2026-06-24", "事件1", "美国", "2026-07-01", "confirmed", "medium"),
            MarketEventRecord("2026-06-25", "事件2", "中国", "待确认", "watchlist", "low"),
            MarketEventRecord("2026-06-26", "事件3", "全球", "2026-07-10", "scheduled", "high"),
        ],
    )

    assert recent_events(state, 2) == [
        "事件2 / 中国 / 待确认 / watchlist",
        "事件3 / 全球 / 2026-07-10 / scheduled",
    ]


def test_save_and_load_market_events_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "market_events.json"
    state = MarketEventsState(
        last_run_date="2026-06-26",
        history=[
            MarketEventRecord(
                "2026-06-26",
                "FOMC 议息会议",
                "美国",
                "2026-07-29",
                "confirmed",
                "high",
            )
        ],
    )

    save_market_events(path, state)
    loaded = load_market_events(path)

    assert loaded.last_run_date == "2026-06-26"
    assert loaded.history[0].event == "FOMC 议息会议"


def test_prune_history_keeps_recent_records() -> None:
    state = MarketEventsState(
        history=[
            MarketEventRecord("2020-01-01", "旧事件", "美国", "2020-01-02", "confirmed", "low"),
            MarketEventRecord("2099-01-01", "新事件", "美国", "2099-01-02", "confirmed", "high"),
        ]
    )

    pruned = prune_history(state, keep_days=180)

    assert [item.event for item in pruned.history] == ["新事件"]
