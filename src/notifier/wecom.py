"""企业微信 Webhook 通知（精简版）。"""

from __future__ import annotations

import logging
import time

from src.config import AppConfig
from src.notifier.chunk import chunk_content_by_max_bytes

logger = logging.getLogger(__name__)


class WecomNotifier:
    def __init__(self, config: AppConfig) -> None:
        self._url = config.wechat_webhook_url
        self._msg_type = config.wechat_msg_type
        self._max_bytes = config.wechat_max_bytes
        self._verify_ssl = config.webhook_verify_ssl

    def send(self, content: str) -> bool:
        if not self._url:
            return False

        if self._msg_type == "text":
            max_bytes = min(self._max_bytes, 2000)
        else:
            max_bytes = self._max_bytes

        if len(content.encode("utf-8")) > max_bytes:
            return self._send_chunked(content, max_bytes)
        return self._send_once(content)

    def _send_chunked(self, content: str, max_bytes: int) -> bool:
        chunks = chunk_content_by_max_bytes(content, max_bytes, add_page_marker=True)
        success = 0
        for i, chunk in enumerate(chunks):
            if self._send_once(chunk):
                success += 1
            else:
                logger.error("企业微信第 %d/%d 批发送失败", i + 1, len(chunks))
            if i < len(chunks) - 1:
                time.sleep(1)
        return success == len(chunks)

    def _send_once(self, content: str) -> bool:
        payload = self._build_payload(content)
        try:
            response = requests.post(
                self._url,
                json=payload,
                timeout=30,
                verify=self._verify_ssl,
            )
        except requests.RequestException as exc:
            logger.error("企业微信请求异常: %s", exc)
            return False

        if response.status_code != 200:
            logger.error("企业微信 HTTP %s", response.status_code)
            return False
        result = response.json()
        if result.get("errcode") == 0:
            return True
        logger.error("企业微信返回错误: %s", result)
        return False

    def _build_payload(self, content: str) -> dict:
        if self._msg_type == "text":
            return {"msgtype": "text", "text": {"content": content}}
        return {"msgtype": "markdown", "markdown": {"content": content}}
