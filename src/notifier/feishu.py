"""飞书 Webhook 通知（精简版）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from typing import Dict

import requests

from src.config import AppConfig
from src.notifier.chunk import MIN_MAX_BYTES, PAGE_MARKER_SAFE_BYTES, chunk_content_by_max_bytes

logger = logging.getLogger(__name__)
_SEND_TIMEOUT = 30


class FeishuNotifier:
    def __init__(self, config: AppConfig) -> None:
        self._url = config.feishu_webhook_url
        self._secret = (config.feishu_webhook_secret or "").strip()
        self._keyword = (config.feishu_webhook_keyword or "").strip()
        self._max_bytes = config.feishu_max_bytes
        self._verify_ssl = config.webhook_verify_ssl

    def send(self, content: str) -> bool:
        if not self._url:
            return False

        keyword_prefix = f"{self._keyword}\n" if self._keyword else ""
        keyword_overhead = len(keyword_prefix.encode("utf-8"))
        effective_max = self._max_bytes - keyword_overhead
        payload_bytes = len(content.encode("utf-8")) + keyword_overhead

        if payload_bytes > self._max_bytes:
            min_chunk = MIN_MAX_BYTES + PAGE_MARKER_SAFE_BYTES
            if effective_max < min_chunk:
                logger.error("飞书分片预算不足")
                return False
            return self._send_chunked(content, effective_max, keyword_prefix)

        return self._send_once(keyword_prefix + content)

    def _send_chunked(self, content: str, max_bytes: int, keyword_prefix: str) -> bool:
        chunks = chunk_content_by_max_bytes(content, max_bytes, add_page_marker=True)
        success = 0
        for i, chunk in enumerate(chunks):
            prefix = keyword_prefix if i == 0 else ""
            if self._send_once(prefix + chunk):
                success += 1
            else:
                logger.error("飞书第 %d/%d 批发送失败", i + 1, len(chunks))
            if i < len(chunks) - 1:
                time.sleep(1)
        return success == len(chunks)

    def _build_security_fields(self) -> Dict[str, str]:
        if not self._secret:
            return {}
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self._secret}"
        sign = base64.b64encode(
            hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        ).decode("utf-8")
        return {"timestamp": timestamp, "sign": sign}

    def _send_once(self, content: str) -> bool:
        card = {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "每日读书"}},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": content}}],
        }
        payloads = [
            {"msg_type": "interactive", "card": card},
            {"msg_type": "text", "content": {"text": content}},
        ]
        security = self._build_security_fields()
        for payload in payloads:
            request_payload = dict(payload)
            request_payload.update(security)
            try:
                response = requests.post(
                    self._url,
                    json=request_payload,
                    timeout=_SEND_TIMEOUT,
                    verify=self._verify_ssl,
                )
            except requests.RequestException as exc:
                logger.error("飞书请求异常: %s", exc)
                return False

            if response.status_code != 200:
                continue
            try:
                result = response.json()
            except ValueError:
                continue
            code = result.get("code") if isinstance(result, dict) else None
            if code is None and isinstance(result, dict):
                code = result.get("StatusCode")
            if code == 0:
                return True
        return False
