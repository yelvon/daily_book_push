"""通知渠道聚合。"""

from __future__ import annotations

import logging
from typing import List

from src.config import AppConfig
from src.notifier.feishu import FeishuNotifier
from src.notifier.wecom import WecomNotifier

logger = logging.getLogger(__name__)


def send_message(config: AppConfig, content: str) -> bool:
    """向所有已配置渠道发送消息，任一成功即视为部分成功。"""
    notifiers = []
    if config.feishu_webhook_url:
        notifiers.append(("feishu", FeishuNotifier(config)))
    if config.wechat_webhook_url:
        notifiers.append(("wecom", WecomNotifier(config)))

    if not notifiers:
        logger.error("未配置 FEISHU_WEBHOOK_URL 或 WECHAT_WEBHOOK_URL")
        return False

    results: List[bool] = []
    for name, notifier in notifiers:
        ok = notifier.send(content)
        logger.info("渠道 %s 发送%s", name, "成功" if ok else "失败")
        results.append(ok)
    return any(results)
