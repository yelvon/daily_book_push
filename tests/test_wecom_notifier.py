from unittest.mock import patch

from src.config import AppConfig
from src.notifier.wecom import WecomNotifier


@patch("src.notifier.wecom.requests.post")
def test_wecom_notifier_sends_markdown(mock_post) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"errcode": 0}
    config = AppConfig(wechat_webhook_url="https://wecom.example", wechat_msg_type="markdown")

    assert WecomNotifier(config).send("## 测试") is True

    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"]["msgtype"] == "markdown"
