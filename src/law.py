"""每日法学（创业法律）内容生成。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from src.config import AppConfig, LawConfig
from src.law_progress import LawProgress, LawRecord, recent_topics
from src.llm_client import call_with_auto_provider

logger = logging.getLogger(__name__)

DISCLAIMER = "本内容仅供学习参考，不构成法律意见；具体问题请咨询执业律师。"

SYSTEM_PROMPT = f"""你是一位擅长用通俗中文讲解创业法律常识的中文老师。

你的任务：每天生成一篇简短、准确、由浅入深的法学学习内容，重点面向创始人、合伙人、员工与投资人等创业角色。

硬性要求：
1. 以中国法为主；如需提及境外规则，必须明确标注「对比/参考」
2. 内容必须适合非法律专业读者，优先使用创业场景
3. 不得编造具体案号、判决结果或未核实的法条原文；不确定时写「概括说明」
4. 如果引用现实事件或最新法规变化，必须保持谨慎，避免未经证实的断言
5. 正文末尾必须包含免责声明：{DISCLAIMER}
6. 严格按用户要求的 Markdown 结构输出，不要输出多余前言"""

USER_PROMPT_TEMPLATE = """今天是 {today}（{weekday}，{timezone}）。

课程第 {day} 天。
今日学习模块：{module}
今日难度：{level}
今日内容样式：{style}
法域侧重：{jurisdiction_note}

最近已学主题（请避免重复）：
{history_block}

请生成一篇每日法学推送。

如果今日内容样式是 concept，请使用以下 Markdown：

## 今日法学｜主题名

### 一句话理解
用一句话讲清楚核心法律概念或规则。

### 创业场景
用创始人/合伙人/员工/投资人等角色，描述一个常见创业场景。

### 稍微深入一点
用 2-4 句话补充法律要点、边界或常见误解。

### 今天想一想
提出一个创业者当天可以观察或思考的问题。

### 延伸阅读
推荐一本真实存在的书、法规导读或经典章节。

### 免责声明
{disclaimer}

如果今日内容样式是 case_review，请使用以下 Markdown：

## 周末法学案例｜案例名

### 现象
描述一个常见创业纠纷或合规现象（可虚构典型场景，但不要捏造真实案号）。

### 法律要点
用 1-2 个法律概念解释，不要超过 5 句话。

### 本周复盘
把案例和最近学习主题联系起来。

### 你可以怎么观察
给一个下周创业实践中可以留意的观察角度。

### 免责声明
{disclaimer}

---
在全文最后单独一行输出元数据（不要放进正文任何小节）：
META: topic=主题名; module={module}; level={level}; style={style}"""

WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

JURISDICTION_NOTES = {
    "cn_primary": "以中国法为主，可偶尔补充国际/对比视角",
}


@dataclass
class LawResult:
    message: str
    record: LawRecord


def _today_context(timezone: str) -> Tuple[str, str, int]:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    return now.date().isoformat(), WEEKDAYS_ZH[now.weekday()], now.weekday()


def _format_history_block(state: LawProgress) -> str:
    topics = recent_topics(state, 20)
    if not topics:
        return "（暂无）"
    return "\n".join(f"- {topic}" for topic in topics)


def _pick_module(law: LawConfig, day: int) -> str:
    if not law.syllabus:
        return "创业法律常识"
    idx = min((max(day, 1) - 1) // 7, len(law.syllabus) - 1)
    return law.syllabus[idx]


def _pick_level(law: LawConfig, day: int) -> str:
    if law.level_progression != "gradual":
        return law.level_start
    if day <= 30:
        return law.level_start
    if day <= 90:
        return "intermediate"
    return "advanced"


def _pick_style(law: LawConfig, weekday_index: int) -> str:
    return law.weekend_style if weekday_index >= 5 else law.weekday_style


def _jurisdiction_note(law: LawConfig) -> str:
    return JURISDICTION_NOTES.get(law.jurisdiction, "以中国法为主")


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
    match = re.search(r"##\s*(?:今日法学|周末法学案例)｜(.+)", content)
    return match.group(1).strip() if match else None


def _strip_meta_line(content: str) -> str:
    return re.sub(r"\nMETA:.*$", "", content, flags=re.S).strip()


def _ensure_disclaimer(message: str) -> str:
    if DISCLAIMER in message:
        return message
    return f"{message.rstrip()}\n\n{DISCLAIMER}"


def generate_daily_law(
    config: AppConfig,
    law: LawConfig,
    state: LawProgress,
) -> Optional[LawResult]:
    if not config.cursor_api_key and not config.gemini_api_key:
        logger.error("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY")
        return None

    today, weekday, weekday_index = _today_context(config.schedule_timezone)
    module = _pick_module(law, state.current_day)
    level = _pick_level(law, state.current_day)
    style = _pick_style(law, weekday_index)
    history_block = _format_history_block(state)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        weekday=weekday,
        timezone=config.schedule_timezone,
        day=state.current_day,
        module=module,
        level=level,
        style=style,
        jurisdiction_note=_jurisdiction_note(law),
        history_block=history_block,
        disclaimer=DISCLAIMER,
    )

    raw = call_with_auto_provider(
        config=config,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=1800,
        use_google_search=law.use_google_search,
    )
    if not raw:
        return None

    topic, parsed_module, parsed_level, parsed_style = _parse_meta(raw)
    record = LawRecord(
        date=today,
        day=state.current_day,
        topic=topic or _parse_topic_from_markdown(raw) or "未知主题",
        module=parsed_module or module,
        level=parsed_level or level,
        style=parsed_style or style,
    )
    message = _ensure_disclaimer(_strip_meta_line(raw))
    return LawResult(message=message, record=record)
