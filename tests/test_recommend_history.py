from src.recommend_history import (
    RecommendHistory,
    RecommendRecord,
    append_record,
    prune_history,
    recent_titles,
)


def test_append_dedup():
    state = RecommendHistory(history=[])
    append_record(state, RecommendRecord(date="2026-01-01", title="国富论", author="斯密"))
    append_record(state, RecommendRecord(date="2026-01-02", title="国富论", author="斯密"))
    assert len(state.history) == 1


def test_prune_history():
    state = RecommendHistory(
        history=[
            RecommendRecord(date="2020-01-01", title="旧书"),
            RecommendRecord(date="2099-01-01", title="新书"),
        ]
    )
    pruned = prune_history(state, keep_days=90)
    assert len(pruned.history) == 1
    assert pruned.history[0].title == "新书"


def test_recent_titles_limit():
    state = RecommendHistory(
        history=[RecommendRecord(date=f"2026-01-{i:02d}", title=f"书{i}") for i in range(1, 6)]
    )
    recent = recent_titles(state, 3)
    assert [r.title for r in recent] == ["书3", "书4", "书5"]
