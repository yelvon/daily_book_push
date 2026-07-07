from datetime import date
from argparse import Namespace
from unittest.mock import patch

from src.config import RecommendConfig
from src.business import BusinessResult
from src.business_progress import BusinessRecord
from src.economics import EconomicsResult
from src.economics_progress import EconomicsRecord
from src.finance import FinanceResult
from src.finance_progress import FinanceRecord
from src.law import LawResult
from src.law_progress import LawRecord
from src.market import MarketRadarResult, MarketSummaryRecord


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


def test_run_law_dry_run_prints_without_saving(capsys):
    from main import run_law

    args = Namespace(dry_run=True)
    result = LawResult(
        message="## 今日法学｜竞业限制",
        record=LawRecord(
            date="2026-06-24",
            day=1,
            topic="竞业限制",
            module="劳动合同与用工合规",
            level="beginner",
            style="concept",
        ),
    )

    with patch("main.load_app_config"), patch("main.load_law_config"), patch(
        "main.load_law_progress"
    ), patch("main.prune_law_history") as mock_prune, patch(
        "main.generate_daily_law", return_value=result
    ), patch(
        "main.save_law_progress"
    ) as mock_save:
        mock_prune.side_effect = lambda state, keep_days: state

        code = run_law(args)

    assert code == 0
    assert "今日法学" in capsys.readouterr().out
    mock_save.assert_not_called()


def test_run_business_dry_run_prints_without_saving(capsys):
    from main import run_business

    args = Namespace(dry_run=True)
    result = BusinessResult(
        message="## 每日商业案例｜Costco 低毛利会员制",
        record=BusinessRecord(
            date="2026-06-24",
            day=1,
            case="Costco 低毛利会员制",
            company="Costco",
            module="商业模式基础",
            level="beginner",
            style="case",
        ),
    )

    with patch("main.load_app_config"), patch("main.load_business_config"), patch(
        "main.load_business_progress"
    ), patch("main.prune_business_history") as mock_prune, patch(
        "main.generate_daily_business", return_value=result
    ), patch(
        "main.save_business_progress"
    ) as mock_save:
        mock_prune.side_effect = lambda state, keep_days: state

        code = run_business(args)

    assert code == 0
    assert "每日商业案例" in capsys.readouterr().out
    mock_save.assert_not_called()


def test_run_finance_dry_run_prints_without_saving(capsys):
    from main import run_finance

    args = Namespace(dry_run=True)
    result = FinanceResult(
        message="## 今日金融投资｜市盈率",
        record=FinanceRecord(
            date="2026-06-24",
            day=1,
            topic="市盈率",
            module="股票基础",
            level="beginner",
            style="concept",
        ),
    )

    with patch("main.load_app_config"), patch("main.load_finance_config"), patch(
        "main.load_finance_progress"
    ), patch("main.prune_finance_history") as mock_prune, patch(
        "main.generate_daily_finance", return_value=result
    ), patch(
        "main.save_finance_progress"
    ) as mock_save:
        mock_prune.side_effect = lambda state, keep_days: state

        code = run_finance(args)

    assert code == 0
    assert "今日金融投资" in capsys.readouterr().out
    mock_save.assert_not_called()


def test_run_market_dry_run_prints_without_saving(capsys):
    from main import run_market

    args = Namespace(dry_run=True)
    result = MarketRadarResult(
        message="## 每日市场事件雷达｜2026-06-26",
        record=MarketSummaryRecord(
            date="2026-06-26",
            top_risk="美国非农就业数据",
            risk_level="high",
            event_count=5,
        ),
    )

    with patch("main.load_app_config"), patch("main.load_market_config"), patch(
        "main.load_market_events"
    ), patch("main.prune_market_history") as mock_prune, patch(
        "main.generate_daily_market_radar", return_value=result
    ), patch(
        "main.save_market_events"
    ) as mock_save:
        mock_prune.side_effect = lambda state, keep_days: state

        code = run_market(args)

    assert code == 0
    assert "每日市场事件雷达" in capsys.readouterr().out
    mock_save.assert_not_called()
