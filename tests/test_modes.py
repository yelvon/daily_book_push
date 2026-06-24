from datetime import date
from argparse import Namespace
from unittest.mock import patch

from src.config import RecommendConfig
from src.economics import EconomicsResult
from src.economics_progress import EconomicsRecord


def test_alternate_even_day_read():
    cfg = RecommendConfig(alternate_even_day="read")
    from main import _resolve_alternate_mode

    with patch("main.date") as mock_date:
        mock_date.today.return_value.toordinal.return_value = 100  # even
        assert _resolve_alternate_mode(cfg) == "read"
        mock_date.today.return_value.toordinal.return_value = 101  # odd
        assert _resolve_alternate_mode(cfg) == "recommend"


def test_run_economics_dry_run_prints_without_saving(capsys):
    from main import run_economics

    args = Namespace(dry_run=True)
    result = EconomicsResult(
        message="## 今日经济学｜机会成本",
        record=EconomicsRecord(
            date="2026-06-24",
            day=1,
            topic="机会成本",
            module="基础概念",
            level="beginner",
            style="concept",
        ),
    )

    with patch("main.load_app_config"), patch("main.load_economics_config"), patch(
        "main.load_economics_progress"
    ), patch("main.prune_economics_history") as mock_prune, patch(
        "main.generate_daily_economics", return_value=result
    ), patch(
        "main.save_economics_progress"
    ) as mock_save:
        mock_prune.side_effect = lambda state, keep_days: state

        code = run_economics(args)

    assert code == 0
    assert "今日经济学" in capsys.readouterr().out
    mock_save.assert_not_called()
