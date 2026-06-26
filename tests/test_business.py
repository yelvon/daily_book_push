from pathlib import Path
from unittest.mock import patch

from src.business import generate_daily_business
from src.business_progress import BusinessProgress, BusinessRecord
from src.config import AppConfig, BusinessConfig


def _app_config() -> AppConfig:
    return AppConfig(root_dir=Path("/tmp/daily_book_push"), gemini_api_key="gemini_key")


def test_generate_daily_business_uses_weekday_case_style() -> None:
    business = BusinessConfig(syllabus=["商业模式基础", "定价与收入模型"])
    state = BusinessProgress(current_day=1, history=[])

    with patch("src.business.datetime") as mock_datetime, patch(
        "src.business.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 每日商业案例｜Costco 低毛利会员制\n\n内容\n\n"
            "META: case=Costco 低毛利会员制; company=Costco; module=商业模式基础; level=beginner; style=case"
        )

        result = generate_daily_business(_app_config(), business, state)

    assert result is not None
    assert result.record.case == "Costco 低毛利会员制"
    assert result.record.company == "Costco"
    assert result.record.style == "case"
    assert "META:" not in result.message
    assert "今日内容样式：case" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_business_uses_weekend_case_review_style() -> None:
    business = BusinessConfig(syllabus=["商业模式基础"])
    state = BusinessProgress(current_day=6, history=[])

    with patch("src.business.datetime") as mock_datetime, patch(
        "src.business.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-27"
        mock_datetime.now.return_value.weekday.return_value = 5
        mock_call.return_value = (
            "## 周末商业复盘｜会员制商业模式\n\n内容\n\n"
            "META: case=会员制商业模式; company=综合案例; module=商业模式基础; level=beginner; style=case_review"
        )

        result = generate_daily_business(_app_config(), business, state)

    assert result is not None
    assert result.record.style == "case_review"
    assert "今日内容样式：case_review" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_business_includes_recent_cases_for_avoidance() -> None:
    business = BusinessConfig(syllabus=["商业模式基础"])
    state = BusinessProgress(
        current_day=2,
        history=[
            BusinessRecord(
                "2026-06-23",
                1,
                "Costco 低毛利会员制",
                "Costco",
                "商业模式基础",
                "beginner",
                "case",
            )
        ],
    )

    with patch("src.business.datetime") as mock_datetime, patch(
        "src.business.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 每日商业案例｜Spotify 免费增值模式\n\n内容\n\n"
            "META: case=Spotify 免费增值模式; company=Spotify; module=商业模式基础; level=beginner; style=case"
        )

        result = generate_daily_business(_app_config(), business, state)

    assert result is not None
    assert result.record.company == "Spotify"
    assert "Costco 低毛利会员制 / Costco" in mock_call.call_args.kwargs["user_prompt"]
