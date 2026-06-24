from unittest.mock import patch

from src.config import AppConfig
from src.notifier.wecom import WecomNotifier


@patch("src.notifier.wecom.requests.post")
def test_wecom_notifier_downgrades_markdown_for_personal_wechat(mock_post) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"errcode": 0}
    config = AppConfig(wechat_webhook_url="https://wecom.example", wechat_msg_type="markdown")

    assert WecomNotifier(config).send("## 测试\n**重点**") is True

    payload = mock_post.call_args.kwargs["json"]
    assert payload["msgtype"] == "text"
    assert "##" not in payload["text"]["content"]
    assert "**" not in payload["text"]["content"]
    assert "测试" in payload["text"]["content"]


@patch("src.notifier.wecom.requests.post")
def test_wecom_notifier_sends_markdown_when_personal_compat_disabled(mock_post) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"errcode": 0}
    config = AppConfig(
        wechat_webhook_url="https://wecom.example",
        wechat_msg_type="markdown",
        wechat_personal_compat=False,
    )

    assert WecomNotifier(config).send("## 测试") is True

    payload = mock_post.call_args.kwargs["json"]
    assert payload["msgtype"] == "markdown"
    assert "**测试**" in payload["markdown"]["content"]
