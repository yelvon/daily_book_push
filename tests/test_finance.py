from pathlib import Path
from unittest.mock import patch

from src.config import AppConfig, FinanceConfig
from src.finance import generate_daily_finance
from src.finance_progress import FinanceProgress, FinanceRecord


def _app_config() -> AppConfig:
    return AppConfig(root_dir=Path("/tmp/daily_book_push"), gemini_api_key="gemini_key")


def test_generate_daily_finance_uses_weekday_concept_style() -> None:
    finance = FinanceConfig(syllabus=["股票基础", "基金投资"])
    state = FinanceProgress(current_day=1, history=[])

    with patch("src.finance.datetime") as mock_datetime, patch(
        "src.finance.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日金融投资｜市盈率\n\n内容\n\n"
            "META: topic=市盈率; module=股票基础; level=beginner; style=concept"
        )

        result = generate_daily_finance(_app_config(), finance, state)

    assert result is not None
    assert result.record.topic == "市盈率"
    assert result.record.module == "股票基础"
    assert result.record.style == "concept"
    assert "META:" not in result.message
    assert "今日内容样式：concept" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_finance_uses_weekend_case_review_style() -> None:
    finance = FinanceConfig(syllabus=["股票基础"])
    state = FinanceProgress(current_day=6, history=[])

    with patch("src.finance.datetime") as mock_datetime, patch(
        "src.finance.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-27"
        mock_datetime.now.return_value.weekday.return_value = 5
        mock_call.return_value = (
            "## 周末金融案例｜2015年A股波动\n\n内容\n\n"
            "META: topic=2015年A股波动; module=股票基础; level=beginner; style=case_review"
        )

        result = generate_daily_finance(_app_config(), finance, state)

    assert result is not None
    assert result.record.style == "case_review"
    assert "今日内容样式：case_review" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_finance_includes_recent_topics_for_avoidance() -> None:
    finance = FinanceConfig(syllabus=["股票基础"])
    state = FinanceProgress(
        current_day=2,
        history=[
            FinanceRecord("2026-06-23", 1, "市盈率", "股票基础", "beginner", "concept")
        ],
    )

    with patch("src.finance.datetime") as mock_datetime, patch(
        "src.finance.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日金融投资｜市净率\n\n内容\n\n"
            "META: topic=市净率; module=股票基础; level=beginner; style=concept"
        )

        result = generate_daily_finance(_app_config(), finance, state)

    assert result is not None
    assert result.record.topic == "市净率"
    assert "市盈率" in mock_call.call_args.kwargs["user_prompt"]


def test_generate_daily_finance_uses_report_reading_style_for_report_modules() -> None:
    finance = FinanceConfig(syllabus=["股票基础", "基本面分析", "财报研读入门"])
    state = FinanceProgress(current_day=22, history=[])

    with patch("src.finance.datetime") as mock_datetime, patch(
        "src.finance.call_with_auto_provider"
    ) as mock_call:
        mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2026-06-24"
        mock_datetime.now.return_value.weekday.return_value = 2
        mock_call.return_value = (
            "## 今日财报研读｜利润表结构\n\n内容\n\n"
            "META: topic=利润表结构; module=财报研读入门; level=beginner; style=report_reading"
        )

        result = generate_daily_finance(_app_config(), finance, state)

    assert result is not None
    assert result.record.topic == "利润表结构"
    assert result.record.module == "财报研读入门"
    assert result.record.style == "report_reading"
    assert "今日内容样式：report_reading" in mock_call.call_args.kwargs["user_prompt"]
    assert "今日财报研读" in mock_call.call_args.kwargs["user_prompt"]
