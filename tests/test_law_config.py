from pathlib import Path

from src.config import AppConfig, load_law_config, select_channel_notifier_config


def test_load_law_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "law.yaml"
    config_path.write_text(
        """
law:
  language: zh
  use_google_search: false
  history_days: 30
  jurisdiction: cn_primary
  level:
    start: beginner
    progression: gradual
  schedule:
    weekday_style: concept
    weekend_style: case_review
  syllabus:
    - 创业法律常识
    - 股权结构与股东权利
""",
        encoding="utf-8",
    )

    config = load_law_config(config_path)

    assert config.language == "zh"
    assert config.use_google_search is False
    assert config.history_days == 30
    assert config.jurisdiction == "cn_primary"
    assert config.level_start == "beginner"
    assert config.weekday_style == "concept"
    assert config.weekend_style == "case_review"
    assert config.syllabus == ["创业法律常识", "股权结构与股东权利"]


def test_select_law_notifier_uses_only_law_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        wechat_webhook_url="https://book-wechat.example",
        law_feishu_webhook_url="https://law-feishu.example",
        law_wechat_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "law")

    assert channel_config.feishu_webhook_url == "https://law-feishu.example"
    assert channel_config.wechat_webhook_url is None
    assert channel_config.notification_title == "每日法学"


def test_select_law_notifier_does_not_use_book_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        law_feishu_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "law")

    assert channel_config.feishu_webhook_url is None
