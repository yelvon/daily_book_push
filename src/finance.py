"""每日金融投资学习内容生成。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from src.config import AppConfig, FinanceConfig
from src.finance_progress import FinanceProgress, FinanceRecord, recent_topics
from src.llm_client import call_with_auto_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位擅长把金融投资知识讲清楚的中文老师。

你的任务：每天生成一篇简短、准确、由浅入深的金融投资学习内容，覆盖股票证券、基金、期权、期货、量化交易、财报研读等主题。

硬性要求：
1. 从基础概念开始，循序渐进，不要堆砌术语
2. 内容必须适合非金融专业读者，但保持专业准确
3. 案例可以来自公开市场现象或经典投资场景，但不要编造具体股价、收益率或内幕信息
4. 不得给出具体买卖建议、荐股或预测涨跌
5. 如果引用现实事件或最新现象，必须保持谨慎，避免未经证实的断言
6. 严格按用户要求的 Markdown 结构输出，不要输出多余前言
7. 全文末尾必须包含免责声明：本内容仅供学习参考，不构成投资建议。"""

USER_PROMPT_TEMPLATE = """今天是 {today}（{weekday}，{timezone}）。

课程第 {day} 天。
今日学习模块：{module}
今日难度：{level}
今日内容样式：{style}

最近已学主题（请避免重复）：
{history_block}

请生成一篇每日金融投资推送。

如果今日内容样式是 concept，请使用以下 Markdown：

## 今日金融投资｜主题名

### 一句话理解
用一句话讲清楚核心概念。

### 生活/市场例子
用一个普通人或投资者容易理解的例子说明。

### 稍微深入一点
用 2-4 句话补充机制、边界或常见误解。

### 常见误区
指出 1-2 个新手容易犯的错误。

### 今天想一想
提出一个可以当天观察或思考的问题。

### 延伸阅读
推荐一本真实存在的书或一个经典章节。

如果今日内容样式是 report_reading，请使用以下 Markdown：

## 今日财报研读｜主题名

### 这份报表在讲什么
用 2-3 句话说明该报表/科目的作用，以及它在投资分析中的位置。

### 关键科目或指标
列出 2-4 个核心科目或指标，逐一解释含义与阅读要点。

### 读表步骤
给出 3-5 步可操作的阅读顺序，帮助读者建立结构化读财报习惯。

### 常见陷阱
指出 1-2 个读财报时容易误判或忽略的问题。

### 实操练习
给一个可当天完成的练习方向（如：应优先看哪张表、哪几行），不要指定具体买入标的或编造公司数据。

如果今日内容样式是 case_review，请使用以下 Markdown：

## 周末金融案例｜案例名

### 现象
描述一个常见市场现象或经典投资场景。

### 金融逻辑
用 1-2 个金融概念解释，不要超过 5 句话。

### 本周复盘
把案例和最近学习主题联系起来。

### 风险提醒
指出该案例中的关键风险点或教训。

### 你可以怎么观察
给一个下周可以留意的观察角度。

如果今日学习模块与财报研读相关，且内容样式是 case_review，标题请使用「周末财报案例」，并在「金融逻辑」中强调如何从报表角度解读该案例。

---
在全文最后单独一行输出元数据（不要放进正文任何小节）：
META: topic=主题名; module={module}; level={level}; style={style}"""

WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@dataclass
class FinanceResult:
    message: str
    record: FinanceRecord


def _today_context(timezone: str) -> Tuple[str, str, int]:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    return now.date().isoformat(), WEEKDAYS_ZH[now.weekday()], now.weekday()


def _format_history_block(state: FinanceProgress) -> str:
    topics = recent_topics(state, 20)
    if not topics:
        return "（暂无）"
    return "\n".join(f"- {topic}" for topic in topics)


def _pick_module(finance: FinanceConfig, day: int) -> str:
    if not finance.syllabus:
        return "股票基础"
    idx = min((max(day, 1) - 1) // 7, len(finance.syllabus) - 1)
    return finance.syllabus[idx]


def _pick_level(finance: FinanceConfig, day: int) -> str:
    if finance.level_progression != "gradual":
        return finance.level_start
    if day <= 30:
        return finance.level_start
    if day <= 90:
        return "intermediate"
    return "advanced"


def _pick_style(finance: FinanceConfig, weekday_index: int, module: str) -> str:
    if "财报" in module and weekday_index < 5:
        return "report_reading"
    return finance.weekend_style if weekday_index >= 5 else finance.weekday_style


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
    match = re.search(r"##\s*(?:今日金融投资|今日财报研读|周末金融案例|周末财报案例)｜(.+)", content)
    return match.group(1).strip() if match else None


def _strip_meta_line(content: str) -> str:
    return re.sub(r"\nMETA:.*$", "", content, flags=re.S).strip()


def generate_daily_finance(
    config: AppConfig,
    finance: FinanceConfig,
    state: FinanceProgress,
) -> Optional[FinanceResult]:
    if not config.cursor_api_key and not config.gemini_api_key:
        logger.error("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY")
        return None

    today, weekday, weekday_index = _today_context(config.schedule_timezone)
    module = _pick_module(finance, state.current_day)
    level = _pick_level(finance, state.current_day)
    style = _pick_style(finance, weekday_index, module)
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
        use_google_search=finance.use_google_search,
    )
    if not raw:
        return None

    topic, parsed_module, parsed_level, parsed_style = _parse_meta(raw)
    record = FinanceRecord(
        date=today,
        day=state.current_day,
        topic=topic or _parse_topic_from_markdown(raw) or "未知主题",
        module=parsed_module or module,
        level=parsed_level or level,
        style=parsed_style or style,
    )
    return FinanceResult(message=_strip_meta_line(raw), record=record)
