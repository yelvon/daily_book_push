"""每日市场事件雷达。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from src.config import AppConfig, MarketConfig
from src.llm_client import call_with_auto_provider
from src.market_events import MarketEventsState, recent_events

logger = logging.getLogger(__name__)

DISCLAIMER = "仅供事件观察，不构成投资建议。"

SYSTEM_PROMPT = f"""你是一位严谨的全球宏观和金融市场事件日历分析师。

你的任务：每天生成一份未来市场事件雷达，帮助用户提前关注未来 90 天内可能影响金融市场的重要事件。

硬性要求：
1. 必须优先确认官方、交易所、央行、统计机构或权威财经日历
2. 不得编造具体日期、会议、数据发布时间；无法确认时写「待确认」
3. 每个重点事件必须标注状态：confirmed / scheduled / watchlist
4. 必须覆盖未来 7 天、30 天、90 天三个窗口
5. 每个重点事件要说明影响资产和可能影响路径
6. 不得输出买入、卖出、做多、做空等交易建议
7. 正文必须包含说明：{DISCLAIMER}
8. 严格按用户要求的 Markdown 结构输出，不要输出多余前言"""

USER_PROMPT_TEMPLATE = """今天是 {today}（{weekday}，{timezone}）。

请生成一份每日市场事件雷达，覆盖未来 {lookahead_days} 天。

重点区域：{regions}
重点资产：{asset_classes}
重点事件类型：{event_types}
每个小节最多事件数：{max_events_per_section}
必须标注状态：{require_status_label}
允许 watchlist：{allow_watchlist}
需要信息可靠性说明：{require_source_note}

最近已推送事件（请避免完全重复）：
{history_block}

请输出以下 Markdown 结构：

## 每日市场事件雷达｜{today}

### 今日重点
- 事件名
  - 时间：北京时间 ...（无法确认写「待确认」）
  - 地区：中国 / 美国 / 全球
  - 状态：confirmed / scheduled / watchlist
  - 影响资产：A股 / 港股 / 美股 / 美债 / 美元 / 人民币 / 黄金 / 原油 / 商品 / 加密资产
  - 为什么重要：...

### 未来 7 天
- 事件 A：关注点...

### 未来 30 天
- 事件 A：关注点...

### 未来 90 天
- 事件 A：关注点...

### 风险等级
高 / 中 / 低，并解释原因。

### 今天的观察问题
如果关键数据超预期或不及预期，哪个资产可能先反应？

### 信息可靠性说明
说明 confirmed / scheduled / watchlist 的含义，并写明：{disclaimer}

---
在全文最后单独一行输出元数据（不要放进正文任何小节）：
META: top_risk=最重要事件; risk_level=high|medium|low; event_count=N"""

WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@dataclass
class MarketSummaryRecord:
    date: str
    top_risk: str
    risk_level: str
    event_count: int


@dataclass
class MarketRadarResult:
    message: str
    record: MarketSummaryRecord


def _today_context(timezone: str) -> Tuple[str, str]:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    return now.date().isoformat(), WEEKDAYS_ZH[now.weekday()]


def _format_history_block(state: MarketEventsState) -> str:
    events = recent_events(state, 20)
    if not events:
        return "（暂无）"
    return "\n".join(f"- {item}" for item in events)


def _parse_meta(content: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    match = re.search(
        r"^META:\s*top_risk=([^;]+);\s*risk_level=([^;]+);\s*event_count=(\d+)\s*$",
        content,
        re.M,
    )
    if not match:
        return None, None, None
    return match.group(1).strip(), match.group(2).strip(), int(match.group(3))


def _strip_meta_line(content: str) -> str:
    return re.sub(r"\nMETA:.*$", "", content, flags=re.S).strip()


def generate_daily_market_radar(
    config: AppConfig,
    market: MarketConfig,
    state: MarketEventsState,
) -> Optional[MarketRadarResult]:
    if not config.cursor_api_key and not config.gemini_api_key:
        logger.error("未配置 CURSOR_API_KEY 或 GEMINI_API_KEY")
        return None

    today, weekday = _today_context(config.schedule_timezone)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        weekday=weekday,
        timezone=config.schedule_timezone,
        lookahead_days=market.lookahead_days,
        regions="、".join(market.regions),
        asset_classes="、".join(market.asset_classes),
        event_types="、".join(market.event_types),
        max_events_per_section=market.max_events_per_section,
        require_status_label="是" if market.require_status_label else "否",
        allow_watchlist="是" if market.allow_watchlist else "否",
        require_source_note="是" if market.require_source_note else "否",
        history_block=_format_history_block(state),
        disclaimer=DISCLAIMER,
    )

    raw = call_with_auto_provider(
        config=config,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=2400,
        use_google_search=market.use_google_search,
    )
    if not raw:
        return None

    top_risk, risk_level, event_count = _parse_meta(raw)
    record = MarketSummaryRecord(
        date=today,
        top_risk=top_risk or "未知事件",
        risk_level=risk_level or "medium",
        event_count=event_count or 0,
    )
    return MarketRadarResult(message=_strip_meta_line(raw), record=record)
