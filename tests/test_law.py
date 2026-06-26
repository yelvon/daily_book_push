from pathlib import Path
from unittest.mock import patch

from src.config import AppConfig, LawConfig
from src.law import DISCLAIMER, generate_daily_law
from src.law_progress import LawProgress, LawRecord


def _app_config() -> AppConfig:
    return AppConfig(root_dir=Path("/tmp/daily_book_push"), gemini_api_key="gemini_key")


def test_generate_daily_law_uses_weekday_concept_style() -> None:
    law = LawConfig(syllabus=["创业法律常识", "股权结构与股东权利"])
    state = LawProgress(current_day=1, history=[])

    with patch("src.law.datetime") as mock_datetime, patch(
        "src.law.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日法学｜竞业限制\n\n内容\n\n"
            f"{DISCLAIMER}\n\n"
            "META: topic=竞业限制; module=创业法律常识; level=beginner; style=concept"
        )

        result = generate_daily_law(_app_config(), law, state)

    assert result is not None
    assert result.record.topic == "竞业限制"
    assert result.record.style == "concept"
    assert DISCLAIMER in result.message
    assert "META:" not in result.message
    assert "今日内容样式：concept" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_law_uses_weekend_case_review_style() -> None:
    law = LawConfig(syllabus=["创业法律常识"])
    state = LawProgress(current_day=6, history=[])

    with patch("src.law.datetime") as mock_datetime, patch(
        "src.law.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-27"
        mock_datetime.now.return_value.weekday.return_value = 5
        mock_call.return_value = (
            "## 周末法学案例｜联合创始人离职\n\n内容\n\n"
            f"{DISCLAIMER}\n\n"
            "META: topic=联合创始人离职; module=创业法律常识; level=beginner; style=case_review"
        )

        result = generate_daily_law(_app_config(), law, state)

    assert result is not None
    assert result.record.style == "case_review"
    assert "今日内容样式：case_review" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_law_includes_recent_topics_for_avoidance() -> None:
    law = LawConfig(syllabus=["创业法律常识"])
    state = LawProgress(
        current_day=2,
        history=[
            LawRecord("2026-06-23", 1, "竞业限制", "创业法律常识", "beginner", "concept")
        ],
    )

    with patch("src.law.datetime") as mock_datetime, patch(
        "src.law.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日法学｜保密协议\n\n内容\n\n"
            f"{DISCLAIMER}\n\n"
            "META: topic=保密协议; module=创业法律常识; level=beginner; style=concept"
        )

        result = generate_daily_law(_app_config(), law, state)

    assert result is not None
    assert "竞业限制" in mock_call.call_args.kwargs["user_prompt"]
