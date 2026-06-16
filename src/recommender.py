"""每日 AI 荐书。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

from src.config import AppConfig, RecommendConfig
from src.llm_client import call_with_fallback
from src.recommend_history import RecommendRecord

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位博览群书的阅读顾问，擅长用精炼中文帮人发现值得读的好书。

你的任务：每天推荐一本真实出版过的书，并提炼可立即吸收的精华。

硬性要求：
1. 只推荐真实存在的书，不得虚构书名、作者或引文
2. 金句优先引用原著或权威译本；无法确认原文时，标注「意译」或「概括」
3. 不得与「最近已推荐」列表重复（同一本书即使副标题不同也算重复）
4. 输出语言：简体中文
5. 严格按用户要求的 Markdown 结构输出，不要输出多余前言"""

USER_PROMPT_TEMPLATE = """今天是 {today}（{weekday}，{timezone}）。

今日侧重类别：{focus_category}
用户感兴趣的领域：{categories}

最近已推荐（请勿重复）：
{history_block}

请推荐 **一本** 今天最值得读的书，输出以下 Markdown（保留标题层级）：

## 📚 今日荐书｜《书名》
**作者**：… ｜ **类别**：… ｜ **推荐指数**：⭐⭐⭐⭐☆（1-5星）

### 为什么今天推荐它
用 2-3 句话说明：与今日/当下生活的关联，或为什么现在读它正合适。

### 一句话概括
不超过 40 字。

### 精华观点
- 3-5 条，每条一句话，可操作、可复述

### 金句摘录
- 2-4 条，格式：「引文」— 出处/章节（如无法确认出处则标注「概括」）

### 适合谁读
- 1-2 句话点明读者画像

### 阅读建议
- 建议读法（精读/跳读/配合哪章先读）或一本延伸阅读

---
在全文最后单独一行输出元数据（不要放进正文任何小节）：
META: title=书名; author=作者"""


WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@dataclass
class RecommendResult:
    message: str
    record: RecommendRecord


def _today_context(timezone: str) -> Tuple[str, str]:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    return now.date().isoformat(), WEEKDAYS_ZH[now.weekday()]


def _pick_focus_category(categories: List[str], today: str) -> str:
    if not categories:
        return "综合"
    idx = date.fromisoformat(today).toordinal() % len(categories)
    return categories[idx]


def _format_history_block(records: List[RecommendRecord]) -> str:
    if not records:
        return "（暂无）"
    lines = []
    for item in records:
        author = f" / {item.author}" if item.author else ""
        lines.append(f"- {item.date}：《{item.title}》{author}")
    return "\n".join(lines)


def _parse_meta(content: str) -> Tuple[Optional[str], Optional[str]]:
    match = re.search(r"^META:\s*title=([^;]+);\s*author=(.+?)\s*$", content, re.M)
    if not match:
        return None, None
    return match.group(1).strip(), match.group(2).strip()


def _parse_title_from_markdown(content: str) -> Optional[str]:
    match = re.search(r"##\s*📚\s*今日荐书｜《([^》]+)》", content)
    if match:
        return match.group(1).strip()
    match = re.search(r"《([^》]+)》", content)
    return match.group(1).strip() if match else None


def _strip_meta_line(content: str) -> str:
    return re.sub(r"\nMETA:.*$", "", content, flags=re.S).strip()


def generate_daily_recommendation(
    config: AppConfig,
    recommend: RecommendConfig,
    recent_records: List[RecommendRecord],
) -> Optional[RecommendResult]:
    if not config.gemini_api_key:
        logger.error("未配置 GEMINI_API_KEY")
        return None

    today, weekday = _today_context(config.schedule_timezone)
    focus = _pick_focus_category(recommend.categories, today) if recommend.rotate_categories else "综合"
    history_block = _format_history_block(recent_records) if recommend.avoid_repeat else "（本次不要求去重）"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        weekday=weekday,
        timezone=config.schedule_timezone,
        focus_category=focus,
        categories="、".join(recommend.categories) or "综合",
        history_block=history_block,
    )

    models = [config.gemini_model]
    if config.gemini_model_fallback:
        models.append(config.gemini_model_fallback)

    raw = call_with_fallback(
        api_key=config.gemini_api_key,
        models=models,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=2048,
        use_google_search=recommend.use_google_search,
    )
    if not raw:
        return None

    record = extract_record_from_content(raw, today)
    message = _strip_meta_line(raw)
    return RecommendResult(message=message, record=record)


def extract_record_from_content(content: str, today: str) -> RecommendRecord:
    title, author = _parse_meta(content)
    if not title:
        title = _parse_title_from_markdown(content) or "未知书名"
    if not author:
        author = ""
    return RecommendRecord(date=today, title=title, author=author)
