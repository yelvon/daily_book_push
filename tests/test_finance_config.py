from pathlib import Path

from src.config import AppConfig, load_finance_config, select_channel_notifier_config


def test_load_finance_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "finance.yaml"
    config_path.write_text(
        """
finance:
  language: zh
  use_google_search: false
  history_days: 30
  level:
    start: beginner
    progression: gradual
  schedule:
    weekday_style: concept
    weekend_style: case_review
  syllabus:
    - 股票基础
    - 基金投资
""",
        encoding="utf-8",
    )

    config = load_finance_config(config_path)

    assert config.language == "zh"
    assert config.use_google_search is False
    assert config.history_days == 30
    assert config.level_start == "beginner"
    assert config.weekday_style == "concept"
    assert config.weekend_style == "case_review"
    assert config.syllabus == ["股票基础", "基金投资"]


def test_select_finance_notifier_uses_only_finance_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        wechat_webhook_url="https://book-wechat.example",
        finance_feishu_webhook_url="https://finance-feishu.example",
        finance_wechat_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "finance")

    assert channel_config.feishu_webhook_url == "https://finance-feishu.example"
    assert channel_config.wechat_webhook_url is None
    assert channel_config.notification_title == "每日金融投资"
