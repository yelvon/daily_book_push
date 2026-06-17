"""LLM provider 选择逻辑测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import AppConfig
from src.llm_client import available_providers, call_with_auto_provider


def _config(
    *,
    cursor_api_key: str | None = None,
    gemini_api_key: str | None = None,
) -> AppConfig:
    return AppConfig(
        root_dir=Path("/tmp/daily_book_push"),
        cursor_api_key=cursor_api_key,
        gemini_api_key=gemini_api_key,
    )


def test_available_providers_cursor_only() -> None:
    config = _config(cursor_api_key="cursor_key")
    assert available_providers(config) == ["cursor"]


def test_available_providers_gemini_only() -> None:
    config = _config(gemini_api_key="gemini_key")
    assert available_providers(config) == ["gemini"]


def test_available_providers_cursor_first() -> None:
    config = _config(cursor_api_key="cursor_key", gemini_api_key="gemini_key")
    assert available_providers(config) == ["cursor", "gemini"]


def test_available_providers_none() -> None:
    config = _config()
    assert available_providers(config) == []


def test_call_with_auto_provider_none_configured() -> None:
    config = _config()
    assert call_with_auto_provider(
        config=config,
        system_prompt="sys",
        user_prompt="user",
    ) is None


@patch("src.llm_client.cursor_completion")
def test_call_with_auto_provider_uses_cursor(mock_cursor) -> None:
    mock_cursor.return_value = "cursor result"
    config = _config(cursor_api_key="cursor_key", gemini_api_key="gemini_key")

    result = call_with_auto_provider(
        config=config,
        system_prompt="sys",
        user_prompt="user",
    )

    assert result == "cursor result"
    mock_cursor.assert_called_once()


@patch("src.llm_client._call_gemini_with_fallback")
@patch("src.llm_client.cursor_completion")
def test_call_with_auto_provider_falls_back_to_gemini(mock_cursor, mock_gemini) -> None:
    mock_cursor.side_effect = RuntimeError("cursor down")
    mock_gemini.return_value = "gemini result"
    config = _config(cursor_api_key="cursor_key", gemini_api_key="gemini_key")

    result = call_with_auto_provider(
        config=config,
        system_prompt="sys",
        user_prompt="user",
    )

    assert result == "gemini result"
    mock_cursor.assert_called_once()
    mock_gemini.assert_called_once()


@patch("src.llm_client._call_gemini_with_fallback")
def test_call_with_auto_provider_gemini_only(mock_gemini) -> None:
    mock_gemini.return_value = "gemini only"
    config = _config(gemini_api_key="gemini_key")

    result = call_with_auto_provider(
        config=config,
        system_prompt="sys",
        user_prompt="user",
    )

    assert result == "gemini only"
    mock_gemini.assert_called_once()
