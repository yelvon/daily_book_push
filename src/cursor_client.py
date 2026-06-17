"""Cursor SDK 调用封装。"""

from __future__ import annotations

import logging
from pathlib import Path

from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

logger = logging.getLogger(__name__)


def completion(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    cwd: Path,
) -> str:
    message = f"{system_prompt.strip()}\n\n---\n\n{user_prompt.strip()}"
    result = Agent.prompt(
        message,
        AgentOptions(
            api_key=api_key,
            model=model,
            local=LocalAgentOptions(cwd=str(cwd)),
        ),
    )
    if result.status == "error":
        raise ValueError(f"Cursor Agent 执行失败: {result.id}")
    content = (result.result or "").strip()
    if not content:
        raise ValueError("Cursor 返回空内容")
    logger.info("Cursor 调用成功，model=%s", model)
    return content
