from pathlib import Path
from unittest.mock import patch

from src.config import AppConfig, MarketConfig
from src.market import generate_daily_market_radar
from src.market_events import MarketEventRecord, MarketEventsState


def _app_config() -> AppConfig:
    return AppConfig(root_dir=Path("/tmp/daily_book_push"), gemini_api_key="gemini_key")


def test_generate_daily_market_radar_builds_90_day_prompt() -> None:
    market = MarketConfig(
        lookahead_days=90,
        regions=["中国", "美国", "全球"],
        asset_classes=["A股", "美股", "美债"],
        event_types=["宏观数据", "央行会议"],
    )
    state = MarketEventsState(history=[])

    with patch("src.market.datetime") as mock_datetime, patch(
        "src.market.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-26"
        mock_datetime.now.return_value.weekday.return_value = 4
        mock_call.return_value = (
            "## 每日市场事件雷达｜2026-06-26\n\n内容\n\n"
            "META: top_risk=美国非农就业数据; risk_level=high; event_count=5"
        )

        result = generate_daily_market_radar(_app_config(), market, state)

    assert result is not None
    assert result.record.top_risk == "美国非农就业数据"
    assert result.record.risk_level == "high"
    assert result.record.event_count == 5
    assert "META:" not in result.message
    prompt = mock_call.call_args.kwargs["user_prompt"]
    assert "未来 90 天" in prompt
    assert "中国、美国、全球" in prompt
    assert "confirmed / scheduled / watchlist" in prompt


def test_generate_daily_market_radar_includes_recent_events() -> None:
    market = MarketConfig()
    state = MarketEventsState(
        history=[
            MarketEventRecord(
                "2026-06-25",
                "FOMC 议息会议",
                "美国",
                "2026-07-29",
                "confirmed",
                "high",
            )
        ]
    )

    with patch("src.market.datetime") as mock_datetime, patch(
        "src.market.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-26"
        mock_datetime.now.return_value.weekday.return_value = 4
        mock_call.return_value = (
            "## 每日市场事件雷达｜2026-06-26\n\n内容\n\n"
            "META: top_risk=中国 PMI; risk_level=medium; event_count=4"
        )

        result = generate_daily_market_radar(_app_config(), market, state)

    assert result is not None
    assert "FOMC 议息会议 / 美国 / 2026-07-29 / confirmed" in mock_call.call_args.kwargs[
        "user_prompt"
    ]


def test_generate_daily_market_radar_requires_search_when_enabled() -> None:
    market = MarketConfig(use_google_search=True)
    state = MarketEventsState(history=[])

    with patch("src.market.datetime") as mock_datetime, patch(
        "src.market.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-26"
        mock_datetime.now.return_value.weekday.return_value = 4
        mock_call.return_value = (
            "## 每日市场事件雷达｜2026-06-26\n\n内容\n\n"
            "META: top_risk=OPEC+ 会议; risk_level=medium; event_count=3"
        )

        generate_daily_market_radar(_app_config(), market, state)

    assert mock_call.call_args.kwargs["use_google_search"] is True
