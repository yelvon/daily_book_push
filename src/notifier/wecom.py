"""企业微信 Webhook 通知（精简版）。"""

from __future__ import annotations

import logging
import time

import requests

from src.config import AppConfig
from src.notifier.chunk import chunk_content_by_max_bytes
from src.notifier.wecom_format import adapt_markdown_for_wework, strip_markdown

logger = logging.getLogger(__name__)

_TEXT_MAX_BYTES = 2048
_MARKDOWN_MAX_BYTES = 4096


class WecomNotifier:
    def __init__(self, config: AppConfig) -> None:
        self._url = config.wechat_webhook_url
        self._requested_msg_type = config.wechat_msg_type.lower()
        self._personal_compat = config.wechat_personal_compat
        self._max_bytes = config.wechat_max_bytes
        self._verify_ssl = config.webhook_verify_ssl

    def send(self, content: str) -> bool:
        if not self._url:
            return False

        prepared = self._prepare_content(content)
        max_bytes = self._effective_max_bytes()

        if len(prepared.encode("utf-8")) > max_bytes:
            return self._send_chunked(prepared, max_bytes)
        return self._send_once(prepared)

    def _effective_msg_type(self) -> str:
        if self._personal_compat and self._requested_msg_type in {"markdown", "markdown_v2"}:
            if self._requested_msg_type != "text":
                logger.info(
                    "WECHAT_MSG_TYPE=%s 已自动降级为 text（个人微信仅支持纯文本）",
                    self._requested_msg_type,
                )
            return "text"
        return self._requested_msg_type

    def _effective_max_bytes(self) -> int:
        if self._effective_msg_type() == "text":
            return min(self._max_bytes, _TEXT_MAX_BYTES)
        return min(self._max_bytes, _MARKDOWN_MAX_BYTES)

    def _prepare_content(self, content: str) -> str:
        msg_type = self._effective_msg_type()
        if msg_type == "text":
            return strip_markdown(content)
        if msg_type == "markdown_v2":
            return content.strip()
        if msg_type == "markdown":
            return adapt_markdown_for_wework(content)
        logger.warning("未知 WECHAT_MSG_TYPE=%s，按 text 发送以兼容个人微信", msg_type)
        return strip_markdown(content)

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
        msg_type = self._effective_msg_type()
        if msg_type == "text":
            return {"msgtype": "text", "text": {"content": content}}
        if msg_type == "markdown_v2":
            return {"msgtype": "markdown_v2", "markdown_v2": {"content": content}}
        return {"msgtype": "markdown", "markdown": {"content": content}}
