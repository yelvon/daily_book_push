"""每日商业案例内容生成。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from src.business_progress import BusinessProgress, BusinessRecord, recent_cases
from src.config import AppConfig, BusinessConfig
from src.llm_client import call_with_auto_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位擅长拆解商业案例的创业顾问。

你的任务：每天生成一篇简短、准确、可迁移的商业案例学习内容，帮助早期创业者训练商业判断力。

硬性要求：
1. 只分析真实存在的公司、产品、商业模式或公开案例，不得虚构事实
2. 如果使用近期信息，必须保持谨慎，避免未经证实的断言
3. 这不是新闻摘要，要提炼商业机制和创业者可迁移启发
4. 不要把大公司打法直接套到小团队，必须指出适用边界或误用风险
5. 严格按用户要求的 Markdown 结构输出，不要输出多余前言"""

USER_PROMPT_TEMPLATE = """今天是 {today}（{weekday}，{timezone}）。

课程第 {day} 天。
今日学习模块：{module}
今日难度：{level}
今日内容样式：{style}
目标读者：{audience}
公司范围：{company_scope}
避免新闻摘要：{avoid_news_summary}

最近已学案例（请避免重复）：
{history_block}

请生成一篇每日商业案例推送。

如果今日内容样式是 case，请使用以下 Markdown：

## 每日商业案例｜案例名

### 现象
描述一个公司、产品、商业模式或关键决策。

### 核心逻辑
解释它为什么成立，背后是哪种商业机制。

### 创业者启发
提炼一个可以迁移到小团队/创业项目里的判断。

### 风险提醒
指出这个模式的边界、误用风险或反例。

### 延伸思考
给一个今天可以想的问题。

如果今日内容样式是 case_review，请使用以下 Markdown：

## 周末商业复盘｜主题名

### 本周共同线索
总结最近案例背后的共同规律。

### 一个反直觉点
指出创业者容易误判的地方。

### 可迁移框架
给一个小框架，帮助以后看商业案例。

### 下周观察题
给一个下周观察公司/产品时可用的问题。

---
在全文最后单独一行输出元数据（不要放进正文任何小节）：
META: case=案例名; company=公司名; module={module}; level={level}; style={style}"""

WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@dataclass
class BusinessResult:
    message: str
    record: BusinessRecord


def _today_context(timezone: str) -> Tuple[str, str, int]:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    return now.date().isoformat(), WEEKDAYS_ZH[now.weekday()], now.weekday()


def _format_history_block(state: BusinessProgress) -> str:
    cases = recent_cases(state, 20)
    if not cases:
        return "（暂无）"
    return "\n".join(f"- {item}" for item in cases)


def _pick_module(business: BusinessConfig, day: int) -> str:
    if not business.syllabus:
        return "商业模式基础"
    idx = min((max(day, 1) - 1) // 7, len(business.syllabus) - 1)
    return business.syllabus[idx]


def _pick_level(business: BusinessConfig, day: int) -> str:
    if business.level_progression != "gradual":
        return business.level_start
    if day <= 30:
        return business.level_start
    if day <= 90:
        return "intermediate"
    return "advanced"


def _pick_style(business: BusinessConfig, weekday_index: int) -> str:
    return business.weekend_style if weekday_index >= 5 else business.weekday_style


def _parse_meta(content: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    match = re.search(
        r"^META:\s*case=([^;]+);\s*company=([^;]+);\s*module=([^;]+);\s*level=([^;]+);\s*style=(.+?)\s*$",
        content,
        re.M,
    )
    if not match:
        return None, None, None, None, None
    return tuple(part.strip() for part in match.groups())  # type: ignore[return-value]


def _parse_case_from_markdown(content: str) -> Optional[str]:
    match = re.search(r"##\s*(?:每日商业案例|周末商业复盘)｜(.+)", content)
    return match.group(1).strip() if match else None


def _strip_meta_line(content: str) -> str:
    return re.sub(r"\nMETA:.*$", "", content, flags=re.S).strip()


def generate_daily_business(
    config: AppConfig,
    business: BusinessConfig,
    state: BusinessProgress,
) -> Optional[BusinessResult]:
    if not config.cursor_api_key and not config.gemini_api_key:
        logger.error("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY")
        return None

    today, weekday, weekday_index = _today_context(config.schedule_timezone)
    module = _pick_module(business, state.current_day)
    level = _pick_level(business, state.current_day)
    style = _pick_style(business, weekday_index)
    history_block = _format_history_block(state)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        weekday=weekday,
        timezone=config.schedule_timezone,
        day=state.current_day,
        module=module,
        level=level,
        style=style,
        audience=business.audience,
        company_scope=business.company_scope,
        avoid_news_summary="是" if business.avoid_news_summary else "否",
        history_block=history_block,
    )

    raw = call_with_auto_provider(
        config=config,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=1800,
        use_google_search=business.use_google_search,
    )
    if not raw:
        return None

    case, company, parsed_module, parsed_level, parsed_style = _parse_meta(raw)
    record = BusinessRecord(
        date=today,
        day=state.current_day,
        case=case or _parse_case_from_markdown(raw) or "未知案例",
        company=company or "未知公司",
        module=parsed_module or module,
        level=parsed_level or level,
        style=parsed_style or style,
    )
    return BusinessResult(message=_strip_meta_line(raw), record=record)
