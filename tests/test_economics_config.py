from pathlib import Path

from src.config import AppConfig, load_economics_config, select_channel_notifier_config


def test_load_economics_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "economics.yaml"
    config_path.write_text(
        """
economics:
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
    - 基础概念
    - 供给与需求
""",
        encoding="utf-8",
    )

    config = load_economics_config(config_path)

    assert config.language == "zh"
    assert config.use_google_search is False
    assert config.history_days == 30
    assert config.level_start == "beginner"
    assert config.weekday_style == "concept"
    assert config.weekend_style == "case_review"
    assert config.syllabus == ["基础概念", "供给与需求"]


def test_select_economics_notifier_uses_only_economics_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        wechat_webhook_url="https://book-wechat.example",
        economics_feishu_webhook_url="https://econ-feishu.example",
        economics_wechat_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "economics")

    assert channel_config.feishu_webhook_url == "https://econ-feishu.example"
    assert channel_config.wechat_webhook_url is None
    assert channel_config.notification_title == "每日经济学"


def test_select_default_notifier_keeps_book_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        economics_feishu_webhook_url="https://econ-feishu.example",
    )

    channel_config = select_channel_notifier_config(config, "books")

    assert channel_config.feishu_webhook_url == "https://book-feishu.example"
    assert channel_config.notification_title == "每日读书"
