"""每日经济学学习内容生成。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from src.config import AppConfig, EconomicsConfig
from src.economics_progress import EconomicsProgress, EconomicsRecord, recent_topics
from src.llm_client import call_with_auto_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位擅长把经济学讲清楚的中文老师。

你的任务：每天生成一篇简短、准确、由浅入深的经济学学习内容。

硬性要求：
1. 从基础概念开始，循序渐进，不要堆砌术语
2. 内容必须适合非经济学专业读者
3. 案例可以来自生活、商业或公开市场现象，但不要编造具体数据
4. 如果引用现实事件或最新现象，必须保持谨慎，避免未经证实的断言
5. 严格按用户要求的 Markdown 结构输出，不要输出多余前言"""

USER_PROMPT_TEMPLATE = """今天是 {today}（{weekday}，{timezone}）。

课程第 {day} 天。
今日学习模块：{module}
今日难度：{level}
今日内容样式：{style}

最近已学主题（请避免重复）：
{history_block}

请生成一篇每日经济学推送。

如果今日内容样式是 concept，请使用以下 Markdown：

## 今日经济学｜主题名

### 一句话理解
用一句话讲清楚核心概念。

### 生活例子
用一个普通人容易理解的例子说明。

### 稍微深入一点
用 2-4 句话补充机制、边界或常见误解。

### 今天想一想
提出一个可以当天观察或思考的问题。

### 延伸阅读
推荐一本真实存在的书或一个经典章节。

如果今日内容样式是 case_review，请使用以下 Markdown：

## 周末经济学案例｜案例名

### 现象
描述一个常见生活/商业/市场现象。

### 经济学解释
用 1-2 个经济学概念解释，不要超过 5 句话。

### 本周复盘
把案例和最近学习主题联系起来。

### 你可以怎么观察
给一个下周可以留意的观察角度。

---
在全文最后单独一行输出元数据（不要放进正文任何小节）：
META: topic=主题名; module={module}; level={level}; style={style}"""

WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@dataclass
class EconomicsResult:
    message: str
    record: EconomicsRecord


def _today_context(timezone: str) -> Tuple[str, str, int]:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    return now.date().isoformat(), WEEKDAYS_ZH[now.weekday()], now.weekday()


def _format_history_block(state: EconomicsProgress) -> str:
    topics = recent_topics(state, 20)
    if not topics:
        return "（暂无）"
    return "\n".join(f"- {topic}" for topic in topics)


def _pick_module(economics: EconomicsConfig, day: int) -> str:
    if not economics.syllabus:
        return "基础概念"
    idx = min((max(day, 1) - 1) // 7, len(economics.syllabus) - 1)
    return economics.syllabus[idx]


def _pick_level(economics: EconomicsConfig, day: int) -> str:
    if economics.level_progression != "gradual":
        return economics.level_start
    if day <= 30:
        return economics.level_start
    if day <= 90:
        return "intermediate"
    return "advanced"


def _pick_style(economics: EconomicsConfig, weekday_index: int) -> str:
    return economics.weekend_style if weekday_index >= 5 else economics.weekday_style


def _parse_meta(content: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    match = re.search(
        r"^META:\s*topic=([^;]+);\s*module=([^;]+);\s*level=([^;]+);\s*style=(.+?)\s*$",
        content,
        re.M,
    )
    if not match:
        return None, None, None, None
    return tuple(part.strip() for part in match.groups())  # type: ignore[return-value]


def _parse_topic_from_markdown(content: str) -> Optional[str]:
    match = re.search(r"##\s*(?:今日经济学|周末经济学案例)｜(.+)", content)
    return match.group(1).strip() if match else None


def _strip_meta_line(content: str) -> str:
    return re.sub(r"\nMETA:.*$", "", content, flags=re.S).strip()


def generate_daily_economics(
    config: AppConfig,
    economics: EconomicsConfig,
    state: EconomicsProgress,
) -> Optional[EconomicsResult]:
    if not config.cursor_api_key and not config.gemini_api_key:
        logger.error("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY")
        return None

    today, weekday, weekday_index = _today_context(config.schedule_timezone)
    module = _pick_module(economics, state.current_day)
    level = _pick_level(economics, state.current_day)
    style = _pick_style(economics, weekday_index)
    history_block = _format_history_block(state)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        weekday=weekday,
        timezone=config.schedule_timezone,
        day=state.current_day,
        module=module,
        level=level,
        style=style,
        history_block=history_block,
    )

    raw = call_with_auto_provider(
        config=config,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=1800,
        use_google_search=economics.use_google_search,
    )
    if not raw:
        return None

    topic, parsed_module, parsed_level, parsed_style = _parse_meta(raw)
    record = EconomicsRecord(
        date=today,
        day=state.current_day,
        topic=topic or _parse_topic_from_markdown(raw) or "未知主题",
        module=parsed_module or module,
        level=parsed_level or level,
        style=parsed_style or style,
    )
    return EconomicsResult(message=_strip_meta_line(raw), record=record)
