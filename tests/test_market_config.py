from pathlib import Path

from src.config import AppConfig, load_market_config, select_channel_notifier_config


def test_load_market_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "market.yaml"
    config_path.write_text(
        """
market:
  language: zh
  use_google_search: false
  lookahead_days: 90
  max_events_per_section: 6
  regions:
    - 中国
    - 美国
  asset_classes:
    - A股
    - 美股
  event_types:
    - 宏观数据
    - 央行会议
  reliability:
    require_status_label: true
    allow_watchlist: true
    require_source_note: true
""",
        encoding="utf-8",
    )

    config = load_market_config(config_path)

    assert config.language == "zh"
    assert config.use_google_search is False
    assert config.lookahead_days == 90
    assert config.max_events_per_section == 6
    assert config.regions == ["中国", "美国"]
    assert config.asset_classes == ["A股", "美股"]
    assert config.event_types == ["宏观数据", "央行会议"]
    assert config.require_status_label is True
    assert config.allow_watchlist is True
    assert config.require_source_note is True


def test_select_market_notifier_uses_only_market_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        wechat_webhook_url="https://book-wechat.example",
        market_feishu_webhook_url="https://market-feishu.example",
        market_wechat_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "market")

    assert channel_config.feishu_webhook_url == "https://market-feishu.example"
    assert channel_config.wechat_webhook_url is None
    assert channel_config.notification_title == "每日市场事件雷达"


def test_select_market_notifier_does_not_use_book_webhooks() -> None:
    config = AppConfig(
        feishu_webhook_url="https://book-feishu.example",
        market_feishu_webhook_url=None,
    )

    channel_config = select_channel_notifier_config(config, "market")

    assert channel_config.feishu_webhook_url is None
