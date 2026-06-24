from pathlib import Path
from unittest.mock import patch

from src.config import AppConfig, EconomicsConfig
from src.economics import generate_daily_economics
from src.economics_progress import EconomicsProgress, EconomicsRecord


def _app_config() -> AppConfig:
    return AppConfig(root_dir=Path("/tmp/daily_book_push"), gemini_api_key="gemini_key")


def test_generate_daily_economics_uses_weekday_concept_style() -> None:
    economics = EconomicsConfig(syllabus=["基础概念", "供给与需求"])
    state = EconomicsProgress(current_day=1, history=[])

    with patch("src.economics.datetime") as mock_datetime, patch(
        "src.economics.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日经济学｜机会成本\n\n内容\n\n"
            "META: topic=机会成本; module=基础概念; level=beginner; style=concept"
        )

        result = generate_daily_economics(_app_config(), economics, state)

    assert result is not None
    assert result.record.topic == "机会成本"
    assert result.record.module == "基础概念"
    assert result.record.style == "concept"
    assert "META:" not in result.message
    assert "今日内容样式：concept" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_economics_uses_weekend_case_review_style() -> None:
    economics = EconomicsConfig(syllabus=["基础概念"])
    state = EconomicsProgress(current_day=6, history=[])

    with patch("src.economics.datetime") as mock_datetime, patch(
        "src.economics.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-27"
        mock_datetime.now.return_value.weekday.return_value = 5
        mock_call.return_value = (
            "## 周末经济学案例｜第二杯半价\n\n内容\n\n"
            "META: topic=第二杯半价; module=基础概念; level=beginner; style=case_review"
        )

        result = generate_daily_economics(_app_config(), economics, state)

    assert result is not None
    assert result.record.style == "case_review"
    assert "今日内容样式：case_review" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_economics_includes_recent_topics_for_avoidance() -> None:
    economics = EconomicsConfig(syllabus=["基础概念"])
    state = EconomicsProgress(
        current_day=2,
        history=[
            EconomicsRecord("2026-06-23", 1, "机会成本", "基础概念", "beginner", "concept")
        ],
    )

    with patch("src.economics.datetime") as mock_datetime, patch(
        "src.economics.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日经济学｜边际成本\n\n内容\n\n"
            "META: topic=边际成本; module=基础概念; level=beginner; style=concept"
        )

        result = generate_daily_economics(_app_config(), economics, state)

    assert result is not None
    assert result.record.topic == "边际成本"
    assert "机会成本" in mock_call.call_args.kwargs["user_prompt"]
