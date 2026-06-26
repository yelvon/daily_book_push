from pathlib import Path

from src.config import AppConfig, load_business_config, select_channel_notifier_config


def test_load_business_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "business.yaml"
    config_path.write_text(
        """
business:
  language: zh
  use_google_search: false
  history_days: 30
  level:
    start: beginner
    progression: gradual
  schedule:
    weekday_style: case
    weekend_style: case_review
  preferences:
    audience: early_stage_founder
    company_scope: global_and_china
    avoid_news_summary: true
  syllabus:
    - 商业模式基础
    - 定价与收入模型
""",
        encoding="utf-8",
    )

    config = load_business_config(config_path)

    assert config.language == "zh"
    assert config.use_google_search is False
    assert config.history_days == 30
    assert config.level_start == "beginner"
    assert config.weekday_style == "case"
    assert config.weekend_style == "case_review"
    assert config.audience == "early_stage_founder"
    assert config.company_scope == "global_and_china"
    assert config.avoid_news_summary is True
    assert config.syllabus == ["商业模式基础", "定价与收入模型"]


def test_select_business_notifier_uses_only_business_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        wechat_webhook_url="https://book-wechat.example",
        business_feishu_webhook_url="https://business-feishu.example",
        business_wechat_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "business")

    assert channel_config.feishu_webhook_url == "https://business-feishu.example"
    assert channel_config.wechat_webhook_url is None
    assert channel_config.notification_title == "每日商业案例"


def test_select_business_notifier_does_not_use_book_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        business_feishu_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "business")

    assert channel_config.feishu_webhook_url is None
